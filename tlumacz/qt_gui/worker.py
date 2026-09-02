"""Background worker that runs translation off the UI thread.

Follows the safe ``QObject`` + ``moveToThread`` pattern:
- the worker exposes a ``run`` slot invoked when the thread starts,
- results/progress/log messages are delivered back via queued signals,
- cancellation is requested through an atomic flag checked by the core.

Lifecycle is managed explicitly (``stop()`` calls ``quit()`` + ``wait()``)
instead of ``deleteLater`` to avoid the classic PySide pitfall where a
queued ``QThread::quit`` is never delivered after the main event loop
has already stopped.

Cancellation (see DEBUG_QT.md item C): a ``multiprocessing.Event`` is
shared with the isolated translation process. Setting it (a) makes
``Translator.translate_file``'s cooperative ``is_cancelled`` check exit
between chunks and (b) wakes a watcher thread inside the child process
that closes any in-flight HTTP client, unblocking a chunk that is mid
-generation instead of waiting for it to finish. ``TranslateWorker.cancel()``
itself only sets that event and returns immediately, so it is safe to call
from the GUI thread. Escalating to ``process.terminate()``/``kill()`` if the
process does not exit quickly is handled entirely inside ``run()``, which
already executes on the background QThread - so ``QThread.terminate()`` is
never needed for the interactive Cancel button.
"""

from __future__ import annotations

import logging
import multiprocessing as mp
import queue
import threading
import time
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from ..core import Translator, TranslatorConfig, TranslationCancelledError
from ..server import LlamaServer, ServerStartError

logger = logging.getLogger(__name__)

# How long to wait, after cancellation is requested, before escalating from
# cooperative cancellation to a plain SIGTERM, and then to SIGKILL. Kept
# short since the cooperative path (closing the HTTP client) is expected to
# unblock the child within a second or two in the common case.
_CANCEL_TERMINATE_AFTER_S = 1.5
_CANCEL_KILL_AFTER_S = 3.0


def _translation_process_entry(
    config: TranslatorConfig,
    input_path: str,
    output_path: str,
    events: Any,
    cancel_event: Any,
) -> None:
    """Run translation in a killable child process."""
    def progress(current: int, total: int) -> None:
        events.put(("progress", current, total))

    def log(message: str) -> None:
        events.put(("log", message))

    translator = Translator(config)

    def _watch_cancel() -> None:
        # Blocks until the parent process sets cancel_event, then closes
        # any HTTP client currently in flight so a blocked chunk unblocks
        # promptly instead of running to completion or to its 300s timeout.
        cancel_event.wait()
        translator.cancel()

    watcher = threading.Thread(target=_watch_cancel, daemon=True)
    watcher.start()

    try:
        translator.translate_file(
            input_path,
            output_path,
            progress_callback=progress,
            log_callback=log,
            is_cancelled=cancel_event.is_set,
        )
    except TranslationCancelledError as exc:
        events.put(("cancelled", str(exc)))
    except Exception as exc:  # noqa: BLE001
        events.put(("failed", f"{type(exc).__name__}: {exc}"))
    else:
        events.put(("finished", output_path))


class TranslateWorker(QObject):
    """Run ``Translator.translate_file`` on a worker thread."""

    progress = Signal(int, int)  # current, total
    log = Signal(str)
    finished = Signal(str)  # output path
    failed = Signal(str)  # error message

    def __init__(self, config: TranslatorConfig, input_path: str, output_path: str) -> None:
        super().__init__()
        self._config = config
        self._input_path = input_path
        self._output_path = output_path
        self._cancelled = False
        self._process: mp.Process | None = None
        self._events = None
        self._cancel_event = None

    def cancel(self) -> None:
        """Request cancellation. Non-blocking: safe to call from any thread,
        including the GUI thread. See module docstring for how this is
        actually carried out without ``QThread.terminate()``.
        """
        self._cancelled = True
        if self._cancel_event is not None:
            self._cancel_event.set()

    def run(self) -> None:
        """Monitor translation running in a killable child process, and
        escalate cancellation (terminate, then kill) here in the background
        thread if the cooperative path does not exit the process quickly.
        """
        if self._cancelled:
            self.failed.emit("Translation was cancelled.")
            return

        context = mp.get_context("spawn")
        events = context.Queue()
        cancel_event = context.Event()
        self._events = events
        self._cancel_event = cancel_event
        process = context.Process(
            target=_translation_process_entry,
            args=(self._config, self._input_path, self._output_path, events, cancel_event),
            daemon=True,
        )
        self._process = process
        process.start()

        terminal_event = None
        cancel_requested_at: float | None = None
        escalated_terminate = False
        escalated_kill = False
        while process.is_alive() or not events.empty():
            if self._cancelled and cancel_requested_at is None:
                cancel_requested_at = time.monotonic()
            if cancel_requested_at is not None and process.is_alive():
                waited = time.monotonic() - cancel_requested_at
                if waited > _CANCEL_KILL_AFTER_S and not escalated_kill:
                    process.kill()
                    escalated_kill = True
                elif waited > _CANCEL_TERMINATE_AFTER_S and not escalated_terminate:
                    process.terminate()
                    escalated_terminate = True
            try:
                event = events.get(timeout=0.1)
            except queue.Empty:
                continue
            kind = event[0]
            if kind == "progress":
                self.progress.emit(event[1], event[2])
            elif kind == "log":
                self.log.emit(event[1])
            else:
                terminal_event = event
                break

        if process.is_alive() and terminal_event is not None:
            process.join(timeout=0.2)
        else:
            process.join(timeout=0.5)

        if self._cancelled:
            self.failed.emit("Translation was cancelled.")
        elif terminal_event is not None:
            if terminal_event[0] == "finished":
                self.finished.emit(terminal_event[1])
            else:
                self.failed.emit(terminal_event[1])
        elif process.exitcode != 0:
            self.failed.emit(f"Translation process exited with code {process.exitcode}.")
        else:
            self.failed.emit("Translation process ended without a result.")
        self._process = None
        self._events = None
        self._cancel_event = None


class TranslationThread:
    """Owns a worker QObject and its QThread.

    The thread is started with :meth:`start` and shut down with :meth:`stop`
    (or automatically when the window closes). Signals are exposed as
    read-only properties so the UI can connect to them.
    """

    def __init__(self, config: TranslatorConfig, input_path: str, output_path: str) -> None:
        self.thread = QThread()
        self.worker = TranslateWorker(config, input_path, output_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_done)
        self.worker.failed.connect(self._on_done)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def _on_done(self) -> None:
        """Mark completion; the owner performs final thread cleanup."""
        if self.thread.isRunning():
            self.thread.quit()

    @property
    def progress(self) -> Signal:
        return self.worker.progress

    @property
    def log(self) -> Signal:
        return self.worker.log

    @property
    def finished(self) -> Signal:
        return self.worker.finished

    @property
    def failed(self) -> Signal:
        return self.worker.failed

    def start(self) -> None:
        self.thread.start()

    def cancel(self) -> None:
        self.worker.cancel()

    def stop(self) -> bool:
        """Stop the monitor thread after terminating its child process.

        Used only at application shutdown (closeEvent), not by the
        interactive Cancel button (that path is handled entirely by the
        cooperative + escalating cancellation in ``TranslateWorker.run()``).
        The 5s wait comfortably covers the worker's own escalation deadline
        (see ``_CANCEL_KILL_AFTER_S``) before falling back to
        ``QThread.terminate()`` as a last resort so the app is never stuck
        unable to close.
        """
        self.worker.cancel()
        if not self.thread.isRunning():
            return True
        self.thread.quit()
        if self.thread.wait(5000):
            return True
        self.thread.terminate()
        self.thread.wait(1000)
        return not self.thread.isRunning()


class ServerRestartWorker(QObject):
    """Stop and (re)start the managed llama-server off the UI thread.

    ``server.start()``/``stop()`` themselves only spawn/kill a subprocess,
    but ``_wait_ready()`` polls the API for up to 60s and ``stop()`` can
    block up to 15s - both unsafe to run on the GUI thread (see DEBUG_QT.md
    item B). Moving them here keeps the "Restart serwera" button usable
    without freezing the window.
    """

    succeeded = Signal(object)  # chat template that worked, or None
    failed = Signal(str)

    def __init__(self, server: LlamaServer, config_updates: dict[str, Any]) -> None:
        super().__init__()
        self._server = server
        self._config_updates = config_updates

    def run(self) -> None:
        logger.info(f"ServerRestartWorker.run() started, config_updates={self._config_updates}")
        try:
            logger.info("ServerRestartWorker.run(): calling server.stop()")
            self._server.stop()
            logger.info("ServerRestartWorker.run(): server.stop() completed")
            for key, value in self._config_updates.items():
                setattr(self._server.config, key, value)
            logger.info("ServerRestartWorker.run(): calling server.start()")
            worked = self._server.start()
            logger.info(f"ServerRestartWorker.run(): server.start() returned worked={worked}")
        except ServerStartError as exc:
            logger.error(f"ServerRestartWorker.run(): ServerStartError: {exc}")
            self.failed.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            logger.error(f"ServerRestartWorker.run(): Exception: {type(exc).__name__}: {exc}")
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        logger.info("ServerRestartWorker.run(): emitting succeeded signal")
        self.succeeded.emit(worked)


class ServerRestartThread:
    """Owns a ``ServerRestartWorker`` and its QThread.

    Mirrors :class:`TranslationThread`'s lifecycle pattern so the caller
    never blocks on the UI thread waiting for the server subprocess.
    """

    def __init__(self, server: LlamaServer, config_updates: dict[str, Any]) -> None:
        self.thread = QThread()
        self.worker = ServerRestartWorker(server, config_updates)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.succeeded.connect(self._on_done)
        self.worker.failed.connect(self._on_done)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def _on_done(self) -> None:
        if self.thread.isRunning():
            self.thread.quit()

    @property
    def succeeded(self) -> Signal:
        return self.worker.succeeded

    @property
    def failed(self) -> Signal:
        return self.worker.failed

    def start(self) -> None:
        self.thread.start()
