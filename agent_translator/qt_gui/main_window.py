"""Main window for the Agent Translator GUI.

Layout (top to bottom):
1. Input/output file selection
2. API settings (base URL, key, model, chunk size, temperature, language)
3. Translate / Cancel buttons
4. Progress bar + status
5. Log output
6. Translated output preview
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..core import TranslatorConfig
from .config import AppSettings, load_settings, save_settings
from .worker import TranslationThread

SUPPORTED_LANGUAGES = [
    "Polish",
    "English",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Ukrainian",
    "Czech",
    "Dutch",
    "Russian",
]


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Agent Translator")
        self.resize(900, 720)

        self._settings = load_settings()
        self._thread: TranslationThread | None = None

        self._build_ui()
        self._load_settings_into_ui()
        self._set_idle_state()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)

        root.addWidget(self._build_files_group())
        root.addWidget(self._build_settings_group())

        controls = QHBoxLayout()
        self.translate_btn = QPushButton("Tłumacz")
        self.translate_btn.setObjectName("translateBtn")
        self.translate_btn.clicked.connect(self._on_translate)
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self._on_cancel)
        controls.addWidget(self.translate_btn)
        controls.addWidget(self.cancel_btn)
        controls.addStretch(1)
        root.addLayout(controls)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setObjectName("outputSplitter")

        log_box = QGroupBox("Log")
        log_layout = QVBoxLayout(log_box)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_box)

        preview_box = QGroupBox("Podgląd tłumaczenia")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_view = QPlainTextEdit()
        self.preview_view.setObjectName("previewView")
        self.preview_view.setReadOnly(True)
        preview_layout.addWidget(self.preview_view)
        splitter.addWidget(preview_box)

        splitter.setSizes([300, 300])
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)

    def _build_files_group(self) -> QGroupBox:
        box = QGroupBox("Pliki")
        grid = QGridLayout(box)

        self.input_path = QLineEdit()
        self.input_path.setObjectName("inputPath")
        self.input_path.setPlaceholderText("Plik wejściowy do tłumaczenia")
        input_browse = QPushButton("Przeglądaj...")
        input_browse.clicked.connect(self._on_browse_input)

        self.output_path = QLineEdit()
        self.output_path.setObjectName("outputPath")
        self.output_path.setPlaceholderText("Plik wyjściowy (tłumaczenie)")
        output_browse = QPushButton("Przeglądaj...")
        output_browse.clicked.connect(self._on_browse_output)

        grid.addWidget(QLabel("Wejście:"), 0, 0)
        grid.addWidget(self.input_path, 0, 1)
        grid.addWidget(input_browse, 0, 2)
        grid.addWidget(QLabel("Wyjście:"), 1, 0)
        grid.addWidget(self.output_path, 1, 1)
        grid.addWidget(output_browse, 1, 2)
        grid.setColumnStretch(1, 1)
        return box

    def _build_settings_group(self) -> QGroupBox:
        box = QGroupBox("Ustawienia API")
        form = QFormLayout(box)

        self.base_url = QLineEdit()
        self.base_url.setObjectName("baseUrl")
        self.api_key = QLineEdit()
        self.api_key.setObjectName("apiKey")
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.model = QLineEdit()
        self.model.setObjectName("model")
        self.chunk_size = QSpinBox()
        self.chunk_size.setObjectName("chunkSize")
        self.chunk_size.setRange(500, 100_000)
        self.chunk_size.setSingleStep(500)
        self.temperature = QDoubleSpinBox()
        self.temperature.setObjectName("temperature")
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setDecimals(1)
        self.language = QComboBox()
        self.language.setObjectName("language")
        self.language.addItems(SUPPORTED_LANGUAGES)

        form.addRow("Base URL:", self.base_url)
        form.addRow("API key:", self.api_key)
        form.addRow("Model:", self.model)
        form.addRow("Rozmiar chunka:", self.chunk_size)
        form.addRow("Temperatura:", self.temperature)
        form.addRow("Język docelowy:", self.language)
        return box

    # ------------------------------------------------------------- helpers --

    def _build_config(self) -> TranslatorConfig:
        return TranslatorConfig(
            base_url=self.base_url.text().strip(),
            api_key=self.api_key.text().strip(),
            model=self.model.text().strip(),
            chunk_size=self.chunk_size.value(),
            temperature=self.temperature.value(),
            target_language=self.language.currentText(),
        )

    def _collect_settings(self) -> AppSettings:
        settings = AppSettings(
            base_url=self.base_url.text().strip(),
            api_key=self.api_key.text().strip(),
            model=self.model.text().strip(),
            chunk_size=self.chunk_size.value(),
            temperature=self.temperature.value(),
            target_language=self.language.currentText(),
            last_input=self.input_path.text().strip(),
            last_output=self.output_path.text().strip(),
        )
        return settings

    def _load_settings_into_ui(self) -> None:
        s = self._settings
        self.base_url.setText(s.base_url)
        self.api_key.setText(s.api_key)
        self.model.setText(s.model)
        self.chunk_size.setValue(s.chunk_size)
        self.temperature.setValue(s.temperature)
        index = self.language.findText(s.target_language)
        if index >= 0:
            self.language.setCurrentIndex(index)
        self.input_path.setText(s.last_input)
        self.output_path.setText(s.last_output)

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _set_idle_state(self) -> None:
        self.translate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)

    def _set_running_state(self) -> None:
        self.translate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

    # ------------------------------------------------------------ handlers --

    def _on_browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik wejściowy", self.input_path.text()
        )
        if path:
            self.input_path.setText(path)
            if not self.output_path.text().strip():
                self.output_path.setText(_default_output_path(path))

    def _on_browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Wybierz plik wyjściowy", self.output_path.text()
        )
        if path:
            self.output_path.setText(path)

    def _on_translate(self) -> None:
        input_path = self.input_path.text().strip()
        output_path = self.output_path.text().strip()

        if not input_path:
            QMessageBox.warning(self, "Brak pliku wejściowego", "Wskaż plik wejściowy.")
            return
        if not Path(input_path).is_file():
            QMessageBox.warning(self, "Brak pliku", f"Plik nie istnieje:\n{input_path}")
            return
        if not output_path:
            output_path = _default_output_path(input_path)
            self.output_path.setText(output_path)

        config = self._build_config()
        self.log_view.clear()
        self.preview_view.clear()
        self._set_running_state()
        self._append_log(f"Start: {input_path} -> {output_path}")

        save_settings(self._collect_settings())

        self._thread = TranslationThread(config, input_path, output_path)
        self._thread.progress.connect(self._on_progress)
        self._thread.log.connect(self._append_log)
        self._thread.finished.connect(self._on_finished)
        self._thread.failed.connect(self._on_failed)
        self._thread.start()

    def _on_cancel(self) -> None:
        if self._thread is not None:
            self._append_log("Anulowanie...")
            self._thread.cancel()
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, current: int, total: int) -> None:
        percent = int(current * 100 / total) if total else 0
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{current}/{total} ({percent}%)")

    def _on_finished(self, output_path: str) -> None:
        self._set_idle_state()
        self.progress_bar.setValue(100)
        self._append_log(f"Zakończono: {output_path}")
        self._show_preview(output_path)

    def _on_failed(self, message: str) -> None:
        self._set_idle_state()
        self._append_log(f"BŁĄD: {message}")
        QMessageBox.critical(self, "Błąd tłumaczenia", message)

    def _show_preview(self, output_path: str) -> None:
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                self.preview_view.setPlainText(f.read())
        except OSError as exc:
            self._append_log(f"Nie można wczytać podglądu: {exc}")

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._thread is not None:
            self._thread.stop()
        save_settings(self._collect_settings())
        super().closeEvent(event)


def _default_output_path(input_path: str) -> str:
    """Return ``name_pl.ext`` next to the input file."""
    path = Path(input_path)
    return str(path.with_name(f"{path.stem}_pl{path.suffix}"))
