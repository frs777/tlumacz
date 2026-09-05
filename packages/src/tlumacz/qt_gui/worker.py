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
import os
import queue
import re
import shutil
import signal
import subprocess
import threading
import time
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from ..core import Translator, TranslatorConfig, TranslationCancelledError
from ..i18n import t
from ..server import LlamaServer, ServerStartError, ServerConfig

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
            self.failed.emit(t("log.translation_cancelled"))
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
            self.failed.emit(t("log.translation_cancelled"))
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
        # Worker cleanup when thread finishes
        self.thread.finished.connect(self.worker.deleteLater)
        # Don't auto-delete thread - GUI manages lifecycle via _thread

    def _on_done(self) -> None:
        """Deprecated: kept for compatibility but no longer used."""
        pass

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

    def __init__(self, server: LlamaServer, config_updates: dict[str, Any], restart: bool = True) -> None:
        super().__init__()
        self._server = server
        self._config_updates = config_updates
        self._restart = restart

    def run(self) -> None:
        logger.info(f"ServerRestartWorker.run() ENTERED, restart={self._restart}, config_updates={self._config_updates}")
        logger.info(f"ServerRestartWorker.run() started, restart={self._restart}, config_updates={self._config_updates}")
        try:
            # Zatrzymaj serwer tylko jeśli działa
            if self._server.is_running():
                logger.info("ServerRestartWorker.run(): calling server.stop()")
                self._server.stop()
                logger.info("ServerRestartWorker.run(): server.stop() completed")
            else:
                logger.info("ServerRestartWorker.run(): server not running, skipping stop()")

            if not self._restart:
                # Only stop, don't start
                logger.info("ServerRestartWorker.run(): restart=False, skipping start()")
                logger.info("ServerRestartWorker.run(): emitting succeeded signal (stop only)")
                self.succeeded.emit(None)
                return

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


class ServerRestartThread(QObject):
    """Owns a ``ServerRestartWorker`` and its QThread.

    Mirrors :class:`TranslationThread`'s lifecycle pattern so the caller
    never blocks on the UI thread waiting for the server subprocess.
    """

    finished = Signal()  # Emitted when thread finishes

    def __init__(self, server: LlamaServer, config_updates: dict[str, Any], restart: bool = True) -> None:
        super().__init__()
        self.thread = QThread()
        self.worker = ServerRestartWorker(server, config_updates, restart)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        # Kluczowe: zakończ thread po zakończeniu workera
        self.worker.succeeded.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        # Worker cleanup when thread finishes
        self.thread.finished.connect(self.worker.deleteLater)
        # Emit finished signal when thread ends (for GUI to clear reference)
        self.thread.finished.connect(self._on_thread_finished)

    def _on_thread_finished(self) -> None:
        """Called when thread finishes. Emits finished signal for GUI."""
        logger.info("ServerRestartThread._on_thread_finished() called")
        self.finished.emit()

    def __del__(self) -> None:
        """Bezpieczne zakończenie thread przy niszczeniu obiektu."""
        if hasattr(self, 'thread') and self.thread.isRunning():
            logger.warning("ServerRestartThread.__del__(): thread still running, waiting...")
            self.thread.quit()
            self.thread.wait(3000)

    @property
    def succeeded(self) -> Signal:
        return self.worker.succeeded

    @property
    def failed(self) -> Signal:
        return self.worker.failed

    def start(self) -> None:
        logger.info(f"ServerRestartThread.start() called, thread={self.thread}")
        self.thread.start()
        logger.info(f"ServerRestartThread.start() completed, thread.isRunning={self.thread.isRunning()}")


# ============================================================================
# Nowa architektura: ServerManager + ServerWorker
# ============================================================================

class ServerState(Enum):
    """Stany serwera w ServerManager."""
    IDLE = "idle"           # brak serwera
    STARTING = "starting"   # w trakcie uruchamiania
    RUNNING = "running"     # serwer działa
    STOPPING = "stopping"   # w trakcie zatrzymywania


class ServerWorker(QObject):
    """Bazowa klasa dla operacji na serwerze."""

    finished = Signal()
    success = Signal(object)  # wynik operacji
    error = Signal(str)       # komunikat błędu

    def run(self) -> None:
        """Wykonaj operację. Wywoływane w wątku thread."""
        try:
            result = self._do_work()
            self.success.emit(result)
        except Exception as e:
            logger.error(f"ServerWorker.run() error: {type(e).__name__}: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def _do_work(self) -> Any:
        """Zaimplementuj w podklasie."""
        raise NotImplementedError


class StartWorker(ServerWorker):
    """Worker uruchamiający serwer."""

    def __init__(self, server: LlamaServer) -> None:
        super().__init__()
        self._server = server

    def _do_work(self) -> str | None:
        template = self._server.start()
        return template


class StopWorker(ServerWorker):
    """Worker zatrzymujący serwer."""

    def __init__(self, server: LlamaServer) -> None:
        super().__init__()
        self._server = server

    def _do_work(self) -> None:
        self._server.stop()


class RestartWorker(ServerWorker):
    """Worker restartujący serwer z nową konfiguracją."""

    def __init__(self, server: LlamaServer, config_updates: dict[str, Any]) -> None:
        super().__init__()
        self._server = server
        self._config_updates = config_updates

    def _do_work(self) -> str | None:
        self._server.stop()
        for key, value in self._config_updates.items():
            setattr(self._server.config, key, value)
        return self._server.start()


class ServerManager(QObject):
    """Centralny zarządca serwera - jedyny punkt kontaktu dla GUI."""

    server_started = Signal(str)      # base_url
    server_stopped = Signal()
    server_error = Signal(str)        # komunikat błędu
    operation_finished = Signal()     # po każdej operacji

    def __init__(self, config: ServerConfig | None = None) -> None:
        super().__init__()
        self._state = ServerState.IDLE
        self._server: LlamaServer | None = None
        self._thread: QThread | None = None
        self._worker: ServerWorker | None = None
        self._config = config

    @property
    def state(self) -> ServerState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._state == ServerState.RUNNING

    @property
    def server(self) -> LlamaServer | None:
        return self._server

    @server.setter
    def server(self, value: LlamaServer | None) -> None:
        self._server = value

    def start(self) -> None:
        """Uruchom serwer. Non-blocking."""
        if self._state != ServerState.IDLE:
            logger.warning(f"ServerManager.start(): invalid state {self._state}")
            return
        if self._config is None:
            self.server_error.emit("Brak konfiguracji serwera")
            return
        self._state = ServerState.STARTING
        # Utwórz serwer przed uruchomieniem workera
        self._server = LlamaServer(self._config)
        logger.info("ServerManager.start(): starting server")
        self._run_operation(StartWorker(self._server))

    def stop(self) -> None:
        """Zatrzymaj serwer. Non-blocking."""
        if self._state != ServerState.RUNNING:
            logger.warning(f"ServerManager.stop(): invalid state {self._state}")
            return
        if self._server is None:
            self._state = ServerState.IDLE
            return
        self._state = ServerState.STOPPING
        logger.info("ServerManager.stop(): stopping server")
        self._run_operation(StopWorker(self._server))

    def restart(self, config_updates: dict[str, Any]) -> None:
        """Restartuj serwer z nową konfiguracją. Non-blocking."""
        if self._state == ServerState.RUNNING and self._server is not None:
            self._state = ServerState.STOPPING
            logger.info("ServerManager.restart(): restarting server")
            self._run_operation(RestartWorker(self._server, config_updates))
        elif self._state == ServerState.IDLE:
            if self._server is not None:
                # Serwer istnieje (utworzony ręcznie) — uruchom go
                for key, value in config_updates.items():
                    setattr(self._server.config, key, value)
                self._state = ServerState.STARTING
                logger.info("ServerManager.restart(): starting existing server from IDLE")
                self._run_operation(StartWorker(self._server))
            else:
                self.start()
        else:
            logger.warning(f"ServerManager.restart(): invalid state {self._state}")

    def _run_operation(self, worker: ServerWorker) -> None:
        """Uruchom operację w tle z pełnym zarządzaniem cyklem życia."""
        # Sprawdź czy poprzednia operacja jeszcze trwa
        if self._thread is not None and self._thread.isRunning():
            logger.warning("ServerManager._run_operation(): previous thread still running, skipping")
            return

        # 1. Zabij osierocone procesy na porcie
        self._kill_orphaned_processes()

        # 2. Utwórz thread
        self._worker = worker
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        # 3. Połącz sygnały
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_operation_success)
        self._worker.error.connect(self._on_operation_error)
        # Kluczowe: worker.finished → thread.quit → thread.finished → _cleanup_thread
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        # 4. Uruchom
        self._thread.start()
        logger.info("ServerManager._run_operation(): thread started")

    def _on_operation_success(self, result: Any) -> None:
        """Wywoływane po pomyślnym zakończeniu operacji."""
        logger.info(f"ServerManager._on_operation_success(): result={result}")
        if self._state == ServerState.STARTING:
            self._state = ServerState.RUNNING
            if self._server is not None:
                self.server_started.emit(self._server.config.base_url)
        elif self._state == ServerState.STOPPING:
            # RestartWorker mógł uruchomić serwer po stopie — sprawdź czy działa
            if self._server is not None and self._server.is_running():
                self._state = ServerState.RUNNING
                self.server_started.emit(self._server.config.base_url)
            else:
                self._state = ServerState.IDLE
                self._server = None
                self.server_stopped.emit()

    def _on_operation_error(self, message: str) -> None:
        """Wywoływane po błędzie operacji."""
        logger.error(f"ServerManager._on_operation_error(): {message}")
        self._state = ServerState.IDLE
        self.server_error.emit(message)

    def _cleanup_thread(self) -> None:
        """Wywoływane po zakończeniu thread — czyści referencje i emituje sygnał."""
        logger.info("ServerManager._cleanup_thread(): cleaning up")
        self._thread = None
        self._worker = None
        self.operation_finished.emit()

    def _kill_orphaned_processes(self) -> None:
        """Zabij osierocone procesy llama-server na porcie."""
        if self._config is None:
            return
        port = self._config.port
        try:
            if not shutil.which("ss"):
                return
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True, text=True, timeout=5
            )
            # Sprawdź czy port jest zajęty przez inny proces
            for line in result.stdout.splitlines():
                if "pid=" in line:
                    match = re.search(r"pid=(\d+)", line)
                    if match:
                        pid = int(match.group(1))
                        # Sprawdź czy to nasz proces
                        if self._server is not None and self._server._process is not None:
                            if pid == self._server._process.pid:
                                continue
                        # Zabij osierocony proces
                        logger.info(f"ServerManager: killing orphaned process PID={pid}")
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(1)
                            try:
                                os.kill(pid, 0)  # Sprawdź czy nadal istnieje
                                os.kill(pid, signal.SIGKILL)
                            except OSError:
                                pass  # Proces się zakończył
                        except OSError as e:
                            logger.error(f"ServerManager: kill error: {e}")
        except Exception as e:
            logger.error(f"ServerManager: _kill_orphaned_processes error: {type(e).__name__}: {e}")
