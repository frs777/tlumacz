"""Background worker that runs translation off the UI thread.

Follows the safe ``QObject`` + ``moveToThread`` pattern:
- the worker exposes a ``run`` slot invoked when the thread starts,
- results/progress/log messages are delivered back via queued signals,
- cancellation is requested through an atomic flag checked by the core.

Lifecycle is managed explicitly (``stop()`` calls ``quit()`` + ``wait()``)
instead of ``deleteLater`` to avoid the classic PySide pitfall where a
queued ``QThread::quit`` is never delivered after the main event loop
has already stopped.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core import Translator, TranslatorConfig, TranslationCancelledError


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

    def cancel(self) -> None:
        """Request cancellation (safe to call from any thread)."""
        self._cancelled = True

    def run(self) -> None:
        """Slot executed on the worker thread."""
        translator = Translator(self._config)
        try:
            translator.translate_file(
                self._input_path,
                self._output_path,
                progress_callback=self.progress.emit,
                log_callback=self.log.emit,
                is_cancelled=lambda: self._cancelled,
            )
        except TranslationCancelledError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.finished.emit(self._output_path)


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

    def stop(self) -> None:
        """Stop the thread cleanly: cancel, quit and wait."""
        self.worker.cancel()
        if self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(15000):
                raise RuntimeError("Translation thread did not stop within 15 seconds")