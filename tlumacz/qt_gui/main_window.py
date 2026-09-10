"""Main window for the Tłumacz GUI.

Tabs (top to bottom):
1. Tłumaczenie — input/output files, translate/cancel, progress, log, preview
2. Ustawienia — API settings, local server, glossary, skills
3. Pomoc — short help in Polish and English
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

from PySide6.QtCore import QDir, QElapsedTimer, QSettings, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
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
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..core import TranslatorConfig
from ..extract import is_binary_format
from ..glossary import Glossary
from ..i18n import t, set_language, get_language, Language
from ..preprocess import DEFAULT_SKIP_PATTERNS
from ..server import SERVER_MODEL_ALIAS, LlamaServer, ServerConfig
from ..version import APP_NAME, APP_VERSION
from ..skill import (
    discover_skills,
    new_skill_file,
    parse_skill,
    save_skill,
    user_skills_dir,
)
from .config import (
    AppSettings,
    CLOUD_MODELS_CONFIG,
    config_dir,
    load_settings,
    reset_settings,
    save_settings,
)
from .help_texts import help_text_pl, help_text_en
from .theme import apply_theme
from .worker import ServerManager, ServerState, TranslationThread
from .backend_manager import BackendManager, BackendConfig

SUPPORTED_LANGUAGES = [
    "Polski",
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

# Wartości (data) dla combo box — format "wykryj do X"
LANGUAGE_VALUES = {
    "Polski": "wykryj do pl",
    "English": "wykryj do en",
    "German": "wykryj do de",
    "French": "wykryj do fr",
    "Spanish": "wykryj do es",
    "Italian": "wykryj do it",
    "Ukrainian": "wykryj do uk",
    "Czech": "wykryj do cs",
    "Dutch": "wykryj do nl",
    "Russian": "wykryj do ru",
}

THEME_CHOICES = [
    ("Systemowy", "system"),
    ("Jasny", "light"),
    ("Ciemny", "dark"),
]

# Upper bound scanned when displaying the glossary entry count, so huge
# dictionaries do not freeze the UI during startup.
_GLOSSARY_COUNT_SCAN = 50_000

LANGUAGE_SUFFIXES = {
    "Polski": "pl",
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Ukrainian": "uk",
    "Czech": "cs",
    "Dutch": "nl",
    "Russian": "ru",
}


class MainWindow(QMainWindow):
    """Top-level application window."""

    @staticmethod
    def _is_thread_running(thread_obj) -> bool:
        """Safely check if a thread is running, handling deleted C++ objects.
        
        Returns False if the thread object is None or if the underlying
        QThread has been deleted by deleteLater.
        """
        if thread_obj is None:
            return False
        try:
            return thread_obj.thread.isRunning()
        except RuntimeError:
            # QThread was deleted by deleteLater
            return False

    def __init__(self, server: object | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Tłumacz")
        self.setMinimumSize(640, 480)

        # Przywróć rozmiar i pozycję okna z QSettings
        self._window_settings = QSettings("tlumacz", "Tłumacz")
        geometry = self._window_settings.value("windowGeometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            screen = QGuiApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                w = min(900, max(640, int(area.width() * 0.9)))
                h = min(720, max(480, int(area.height() * 0.9)))
                self.resize(w, h)
            else:
                self.resize(900, 720)

        self._settings, config_warning = load_settings()
        # --- BackendManager: centralny zarządca backendów ---
        self._server_starting_up = False  # rozróżnia auto-start od restartu
        self._backend_manager = self._create_backend_manager(server)
        self._server_manager = self._backend_manager._server_manager  # alias dla kompatybilności
        self._thread: TranslationThread | None = None
        self._elapsed_timer = QElapsedTimer()
        self._elapsed_display_timer = QTimer(self)
        self._elapsed_display_timer.setInterval(100)
        self._elapsed_display_timer.timeout.connect(self._update_elapsed_time)
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(120)
        self._spinner_timer.timeout.connect(self._advance_spinner)
        self._spinner_frames = ("◐", "◓", "◑", "◒")
        self._spinner_index = 0
        self._skills: list = []
        self._skill_checkboxes: list[QCheckBox] = []
        self._loading = True
        self._switching_backend = False  # Guard przed podwójnym wywołaniem _on_model_changed
        self._config_file_present = (config_dir() / "config.json").is_file()

        self._build_ui()
        self._load_settings_into_ui()
        self._loading = False
        self._set_idle_state()
        # Auto-start serwera po zbudowaniu UI (log_view musi istnieć)
        if server is None and self._settings.auto_start_server:
            backend = self._settings.backend_type
            # Sprawdź czy backend ma ścieżkę modelu
            has_model = (
                (backend == "llama" and self._settings.server_gguf_path) or
                (backend == "fastapi" and self._settings.fastapi_model_path) or
                (backend == "openvino" and self._settings.openvino_model_path)
            )
            if has_model:
                self._server_starting_up = True
                self._set_backend_controls_enabled(False)
                backend_names = {"llama": "llama.cpp", "fastapi": "FastAPI (TranslateGemma)", "openvino": "OpenVINO"}
                self._show_loading_dialog(backend_names.get(backend, backend))
                self._append_log(f"Uruchamianie serwera {backend}...")
                self._backend_manager.start()
        if config_warning:
            QMessageBox.warning(self, "Konfiguracja", config_warning)

    # ----------------------------------------------------- ServerManager ---

    @property
    def _server(self):
        """Alias do _server_manager.server — kompatybilność z tłumaczeniem."""
        return self._server_manager.server if self._server_manager else None

    @_server.setter
    def _server(self, value):
        """Setter aliasu — deleguje do _server_manager.server."""
        if self._server_manager:
            self._server_manager.server = value

    def _create_backend_manager(self, server: object | None) -> BackendManager:
        """Utwórz i skonfiguruj BackendManager.

        BackendManager zarządza trzema backendami:
        - llama.cpp (przez ServerManager)
        - Cloud API (bezpośredni URL)
        - FastAPI (przez FastAPIServerManager)

        Jeśli przekazano istniejący serwer (np. z CLI), użyj go bezpośrednio.
        """
        logger.info(f"_create_backend_manager() called, server={server}")
        logger.info(f"_settings.server_gguf_path: '{self._settings.server_gguf_path}'")
        logger.info(f"_settings.backend_type: {self._settings.backend_type}")

        # Utwórz konfigurację BackendManager z ustawień aplikacji
        backend_config = BackendConfig(
            backend_type=self._settings.backend_type,
            server_port=self._settings.server_port,
            server_gguf_path=self._settings.server_gguf_path,
            server_chat_template=self._settings.server_chat_template or "",
            server_compute_mode=self._settings.server_compute_mode,
            server_parallel=1,
            cloud_base_url=self._settings.base_url,
            cloud_api_key=self._settings.api_key,
            cloud_model=self._settings.model,
            fastapi_model_path=self._settings.fastapi_model_path,
            fastapi_host=self._settings.fastapi_host,
            fastapi_port=self._settings.fastapi_port,
            fastapi_device=self._settings.fastapi_device,
            fastapi_dtype=self._settings.fastapi_dtype,
            openvino_model_path=self._settings.openvino_model_path,
            openvino_device=self._settings.openvino_device,
        )

        manager = BackendManager(backend_config)

        # Utwórz ServerManager i wstrzyknij do BackendManager
        # ZAWSZE tworzymy z config - nawet gdy server jest przekazany
        server_config = self._build_server_config()
        logger.info(f"_build_server_config() returned: {server_config}")
        
        if server is not None:
            # Przekazany serwer (np. z CLI) — utwórz w stanie RUNNING
            logger.info("Creating ServerManager with passed server (RUNNING state)")
            server_manager = ServerManager(server_config)
            server_manager.server = server
            server_manager.set_state(ServerState.RUNNING)
        else:
            # Normalny przypadek — utwórz z konfiguracji
            server_manager = ServerManager(server_config)
            logger.info(f"ServerManager._config after creation: {server_manager._config}")

        manager.set_server_manager(server_manager)

        # Połącz sygnały BackendManager z callbackami GUI
        manager.backend_started.connect(self._on_server_started)
        manager.backend_stopped.connect(self._on_server_stopped)
        manager.backend_error.connect(self._on_server_error)
        manager.operation_finished.connect(self._on_operation_finished)
        manager.backend_loading.connect(self._on_backend_loading)

        logger.info(f"BackendManager created, _server_manager._config: {manager._server_manager._config}")
        return manager

    def _build_server_config(self) -> "ServerConfig | None":
        """Zbuduj ServerConfig z aktualnych ustawień.

        Zwraca None jeśli nie wskazano pliku GGUF (brak zarządzanego serwera).
        Pobiera ścieżkę bezpośrednio z GUI (nie z self._settings które może być nieaktualne).
        """
        # Pobierz z GUI jeśli dostępne, inaczej z _settings
        gguf_path = ""
        if hasattr(self, "server_model"):
            gguf_path = self.server_model.text().strip()
        if not gguf_path:
            gguf_path = self._settings.server_gguf_path
        if not gguf_path:
            return None
        return ServerConfig(
            gguf_path=gguf_path,
            port=self.server_port.value() if hasattr(self, "server_port") else self._settings.server_port,
            compute_mode=self.server_compute_mode.currentData() or "gpu" if hasattr(self, "server_compute_mode") else self._settings.server_compute_mode,
            chat_template=self.server_chat_template.currentData() or "" if hasattr(self, "server_chat_template") else self._settings.server_chat_template,
            parallel=1,
        )

    def _build_config_updates(self) -> dict:
        """Zbuduj słownik config_updates dla restartu serwera z aktualnych ustawień GUI."""
        settings = self._collect_settings()
        
        # Określ backend
        model_data = self.model.currentData()
        backend = "llama"
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")
        
        if backend == "fastapi":
            return {
                "port": settings.fastapi_port,
                "model_path": settings.fastapi_model_path,
                "dtype": settings.fastapi_dtype,
                "parallel": settings.fastapi_parallel,
            }
        elif backend == "openvino":
            return {
                "model_path": settings.openvino_model_path,
                "device": settings.openvino_device,
            }
        else:
            # llama.cpp
            return {
                "port": settings.server_port,
                "parallel": settings.server_parallel,
                "compute_mode": settings.server_compute_mode,
                "gguf_path": settings.server_gguf_path,
                "chat_template": settings.server_chat_template or "",
            }

    def _on_server_started(self, base_url: str) -> None:
        """Callback: serwer uruchomiony pomyślnie."""
        logger.info(f"_on_server_started called with base_url={base_url}")
        self.base_url.setText(base_url)
        # Nie zmieniaj typu serwera - zostaw obecny wybór
        self._update_restart_button_label()

        # Określ nazwę backendu na podstawie base_url
        if base_url.startswith("openvino://"):
            backend_name = "OpenVINO"
        elif "8001" in base_url or "fastapi" in base_url.lower():
            backend_name = "FastAPI"
        elif "18080" in base_url or "llama" in base_url.lower():
            backend_name = "llama.cpp"
        else:
            backend_name = "Serwer"

        if self._server_starting_up:
            # Auto-start przy uruchomieniu programu — tylko log
            logger.info(f"_on_server_started: _server_starting_up=True, auto-start")
            self._server_starting_up = False
            self._append_log(f"{backend_name} uruchomiony: {base_url}")
        else:
            # Restart lub ręczne uruchomienie — pokaż komunikat
            logger.info(f"_on_server_started: _server_starting_up=False, showing QMessageBox")
            self._append_log(f"{backend_name} uruchomiony: {base_url}")
            QMessageBox.information(
                self, backend_name, f"{backend_name} został pomyślnie uruchomiony."
            )
        self._set_backend_controls_enabled(True)
        self._close_loading_dialog()

    def _on_server_stopped(self) -> None:
        """Callback: serwer zatrzymany."""
        self._update_restart_button_label()
        # Określ nazwę backendu
        backend = self._backend_manager.get_active_backend()
        backend_name = {"llama": "llama.cpp", "fastapi": "FastAPI", "openvino": "OpenVINO"}.get(backend, "Serwer")
        self._append_log(f"{backend_name} zatrzymany.")

    def _on_server_error(self, message: str) -> None:
        """Callback: błąd operacji na serwerze."""
        self._update_restart_button_label()
        # Określ nazwę backendu
        backend = self._backend_manager.get_active_backend()
        backend_name = {"llama": "llama.cpp", "fastapi": "FastAPI", "openvino": "OpenVINO"}.get(backend, "Serwer")
        self._append_log(f"BŁĄD {backend_name}: {message}")
        if self._server_starting_up:
            self._server_starting_up = False
        QMessageBox.critical(
            self, backend_name, f"Błąd operacji na {backend_name}:\n{message}"
        )
        self._set_backend_controls_enabled(True)
        self._close_loading_dialog()

    def _on_operation_finished(self) -> None:
        """Callback: zakończono operację na serwerze (start/stop/restart).

        Nie odblokowuje GUI — to robią _on_server_started i _on_server_error.
        operation_finished jest emitowane też po stop, co mogłoby przedwcześnie
        odblokować GUI przy przełączaniu backendów.
        """
        self._update_restart_button_label()

    def _on_backend_loading(self, backend_name: str) -> None:
        """Callback: rozpoczęto ładowanie backendu — zablokuj GUI."""
        self._append_log(f"Ładowanie {backend_name}, proszę czekać...")
        self._set_backend_controls_enabled(False)
        self._show_loading_dialog(backend_name)

    def _show_loading_dialog(self, backend_name: str) -> None:
        """Pokaż modalny dialog z komunikatem o ładowaniu."""
        self._close_loading_dialog()
        self._loading_dialog = QDialog(self)
        self._loading_dialog.setModal(True)
        self._loading_dialog.setWindowTitle("Ładowanie")
        layout = QVBoxLayout(self._loading_dialog)
        label = QLabel(f"Ładowanie {backend_name}, proszę czekać...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self._loading_dialog.setFixedSize(350, 80)
        self._loading_dialog.show()

    def _close_loading_dialog(self) -> None:
        """Zamknij dialog ładowania jeśli jest otwarty."""
        dialog = getattr(self, "_loading_dialog", None)
        if dialog is not None:
            dialog.close()
            self._loading_dialog = None

    def _set_backend_controls_enabled(self, enabled: bool) -> None:
        """Włącz/wyłącz kontrolki backendu podczas ładowania."""
        self.model.setEnabled(enabled)
        self.restart_server_btn.setEnabled(enabled)
        self.server_port.setEnabled(enabled)
        self.server_model.setEnabled(enabled)
        self.model_browse.setEnabled(enabled)
        self.server_compute_mode.setEnabled(enabled)
        self.server_chat_template.setEnabled(enabled)
        self.server_parallel.setEnabled(enabled)
        self.server_dtype.setEnabled(enabled)
        self.server_openvino_device.setEnabled(enabled)
        self.auto_start_server.setEnabled(enabled)

    # ------------------------------------------------------------------ UI --

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        root.addWidget(self.tabs)

        # --- Tab: Tłumaczenie ------------------------------------------------
        translation_tab = QWidget()
        t_layout = QVBoxLayout(translation_tab)
        t_layout.addWidget(self._build_files_group())

        controls = QHBoxLayout()
        self.translate_btn = QPushButton(t("button.translate"))
        self.translate_btn.setObjectName("translateBtn")
        self.translate_btn.clicked.connect(self._on_translate)
        self.cancel_btn = QPushButton(t("button.cancel"))
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self._on_cancel)
        controls.addWidget(self.translate_btn)
        controls.addWidget(self.cancel_btn)
        controls.addStretch(1)
        t_layout.addLayout(controls)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        t_layout.addWidget(self.progress_bar)

        status_row = QHBoxLayout()
        self.spinner_label = QLabel(self._spinner_frames[0])
        self.spinner_label.setObjectName("spinnerLabel")
        self.spinner_label.setMinimumWidth(24)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinner_label.setVisible(False)
        status_row.addWidget(self.spinner_label)
        self.elapsed_label = QLabel("Czas: 00:00")
        self.elapsed_label.setObjectName("elapsedLabel")
        status_row.addWidget(self.elapsed_label)
        status_row.addStretch(1)
        t_layout.addLayout(status_row)

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
        t_layout.addWidget(splitter, 1)
        self.tabs.addTab(translation_tab, t("tab.translation"))

        # --- Tab: Ustawienia --------------------------------------------------
        # --- Tab: API i serwer --------------------------------------------------
        api_tab = QWidget()
        a_outer = QVBoxLayout(api_tab)
        a_outer.setContentsMargins(0, 0, 0, 0)
        a_scroll = QScrollArea()
        a_scroll.setObjectName("apiScroll")
        a_scroll.setWidgetResizable(True)
        a_scroll.setFrameShape(QFrame.Shape.NoFrame)
        a_inner = QWidget()
        a_layout = QVBoxLayout(a_inner)
        a_layout.setContentsMargins(8, 8, 8, 8)
        a_layout.addWidget(self._build_api_group())
        a_layout.addWidget(self._build_server_group())
        a_layout.addStretch(1)
        a_scroll.setWidget(a_inner)
        a_outer.addWidget(a_scroll)
        self.tabs.addTab(api_tab, t("tab.api_server"))

        # --- Tab: Dodatki (Glosariusz + Skille + Pozostałe) ---------------------
        extras_tab = QWidget()
        e_outer = QVBoxLayout(extras_tab)
        e_outer.setContentsMargins(0, 0, 0, 0)
        e_scroll = QScrollArea()
        e_scroll.setObjectName("extrasScroll")
        e_scroll.setWidgetResizable(True)
        e_scroll.setFrameShape(QFrame.Shape.NoFrame)
        e_inner = QWidget()
        e_layout = QVBoxLayout(e_inner)
        e_layout.setContentsMargins(8, 8, 8, 8)
        e_layout.addWidget(self._build_glossary_group())
        e_layout.addWidget(self._build_skills_group())
        e_layout.addWidget(self._build_other_group())
        restore_row = QHBoxLayout()
        self.restore_defaults_btn = QPushButton(t("button.restore_defaults"))
        self.restore_defaults_btn.setObjectName("restoreDefaultsBtn")
        self.restore_defaults_btn.clicked.connect(self._on_restore_defaults)
        self.restore_defaults_btn.setToolTip(
            "Zapisuje kopię obecnego config.json i przywraca domyślne ustawienia.\n"
            "Twoje ścieżki (ostatni plik wejściowy/wyjściowy, glosariusz) są zachowywane."
        )
        restore_row.addWidget(self.restore_defaults_btn)
        restore_row.addStretch(1)
        e_layout.addLayout(restore_row)
        e_layout.addStretch(1)
        e_scroll.setWidget(e_inner)
        e_outer.addWidget(e_scroll)
        self.tabs.addTab(extras_tab, t("tab.extras"))

        # --- Tab: Pomoc --------------------------------------------------------
        self.tabs.addTab(self._build_help_tab(), t("tab.help"))

        self.setCentralWidget(central)

    def _build_files_group(self) -> QGroupBox:
        self.files_group = QGroupBox(t("files.group"))
        grid = QGridLayout(self.files_group)

        self.input_path = QLineEdit()
        self.input_path.setObjectName("inputPath")
        self.input_path.setPlaceholderText("Plik wejściowy do tłumaczenia")
        self.input_path.textChanged.connect(self._auto_select_skill_for_input)
        self.input_browse = QPushButton(t("button.browse"))
        self.input_browse.clicked.connect(self._on_browse_input)

        self.output_path = QLineEdit()
        self.output_path.setObjectName("outputPath")
        self.output_path.setPlaceholderText("Plik wyjściowy (tłumaczenie)")
        self.output_browse = QPushButton(t("button.browse"))
        self.output_browse.clicked.connect(self._on_browse_output)

        self.input_label = QLabel(t("files.input"))
        self.output_label = QLabel(t("files.output"))
        grid.addWidget(self.input_label, 0, 0)
        grid.addWidget(self.input_path, 0, 1)
        grid.addWidget(self.input_browse, 0, 2)
        grid.addWidget(self.output_label, 1, 0)
        grid.addWidget(self.output_path, 1, 1)
        grid.addWidget(self.output_browse, 1, 2)
        grid.setColumnStretch(1, 1)
        return self.files_group

    def _build_glossary_group(self) -> QGroupBox:
        self.glossary_group = QGroupBox(t("settings.glossary_group"))
        layout = QVBoxLayout(self.glossary_group)

        file_row = QHBoxLayout()
        self.glossary_path = QLineEdit()
        self.glossary_path.setObjectName("glossaryPath")
        self.glossary_path.setPlaceholderText("Ścieżka do pliku CSV (źródło,tłumaczenie)")
        self.glossary_path.setToolTip(
            "Plik CSV dwukolumnowy źródło,tłumaczenie.\n"
            "Wpisy wymuszają stałe tłumaczenia dla wybranych terminów.\n"
            "Nagłówek oraz prefiks # w tłumaczeniu są obsługiwane automatycznie."
        )
        self.glossary_path.editingFinished.connect(self._on_glossary_path_edited)
        self.glossary_browse = QPushButton(t("button.browse"))
        self.glossary_browse.clicked.connect(self._on_browse_glossary)
        file_row.addWidget(self.glossary_path, 1)
        file_row.addWidget(self.glossary_browse)
        layout.addLayout(file_row)

        entry_row = QHBoxLayout()
        self.glossary_term = QLineEdit()
        self.glossary_term.setObjectName("glossaryTerm")
        self.glossary_term.setPlaceholderText("Termin (źródło)")
        self.glossary_target = QLineEdit()
        self.glossary_target.setObjectName("glossaryTarget")
        self.glossary_target.setPlaceholderText("Tłumaczenie")
        self.add_entry_btn = QPushButton(t("button.add_entry"))
        self.add_entry_btn.setObjectName("addGlossaryBtn")
        self.add_entry_btn.clicked.connect(self._on_add_glossary_entry)
        entry_row.addWidget(self.glossary_term, 1)
        entry_row.addWidget(self.glossary_target, 1)
        entry_row.addWidget(self.add_entry_btn)
        layout.addLayout(entry_row)

        self.glossary_count_label = QLabel(t("glossary.no_file"))
        self.glossary_count_label.setObjectName("glossaryCount")
        layout.addWidget(self.glossary_count_label)
        return self.glossary_group

    def _build_skills_group(self) -> QGroupBox:
        self.skills_group = QGroupBox(t("settings.skills_group"))
        layout = QVBoxLayout(self.skills_group)

        self._skill_row = QWidget()
        self._skill_row_layout = QVBoxLayout(self._skill_row)
        self._skill_row_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._skill_row)

        button_row = QHBoxLayout()
        self.refresh_skills_btn = QPushButton(t("button.refresh"))
        self.refresh_skills_btn.setObjectName("refreshSkillsBtn")
        self.refresh_skills_btn.clicked.connect(self._on_refresh_skills)
        self.import_skill_btn = QPushButton(t("button.import_skill"))
        self.import_skill_btn.setObjectName("importSkillBtn")
        self.import_skill_btn.clicked.connect(self._on_import_skill)
        self.new_skill_btn = QPushButton(t("button.new_skill"))
        self.new_skill_btn.setObjectName("newSkillBtn")
        self.new_skill_btn.clicked.connect(self._on_new_skill)
        button_row.addWidget(self.refresh_skills_btn)
        button_row.addWidget(self.import_skill_btn)
        button_row.addWidget(self.new_skill_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._reload_skills()
        return self.skills_group

    def _reload_skills(self) -> None:
        """Re-discover skills and rebuild the checkboxes, keeping enabled ones."""
        for checkbox in self._skill_checkboxes:
            self._skill_row_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self._skill_checkboxes.clear()

        self._skills = discover_skills()
        if not self._skills:
            label = QLabel("Brak dostępnych skilli. Dodaj plik .md w "
                           + str(user_skills_dir()) + " lub użyj „Importuj skilla...”.")
            label.setObjectName("noSkillsLabel")
            self._skill_row_layout.addWidget(label)
            return

        enabled = set(self._settings.enabled_skills)
        for skill in self._skills:
            checkbox = QCheckBox(
                f"{skill.name} — {', '.join(skill.formats)}"
            )
            checkbox.setObjectName(f"skill_{skill.name}")
            checkbox.toggled.connect(self._on_skills_changed)
            checkbox.setChecked(skill.name in enabled)
            self._skill_checkboxes.append(checkbox)
            self._skill_row_layout.addWidget(checkbox)

    def _on_refresh_skills(self) -> None:
        self._reload_skills()
        save_settings(self._collect_settings())
        self._append_log(f"Odświeżono listę skilli: {len(self._skills)}")

    def _on_import_skill(self) -> None:
        start = str(user_skills_dir()) if user_skills_dir().is_dir() else str(
            user_skills_dir()
        )
        path = self._browse_file(
            "Wybierz plik skilla (.md)",
            start,
            "Markdown (*.md);;Wszystkie pliki (*)",
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(
                self, "Skille", f"Nie można odczytać pliku: {exc}"
            )
            return
        skill = parse_skill(Path(path).name, text)
        if skill is None:
            QMessageBox.warning(
                self,
                "Skille",
                "To nie jest skilla: w nagłówku pliku brakuje pól "
                "`name` i `formats`.\n\nPrzykład:\n"
                "---\nname: Mój skilla\nformats: md, markdown\n---\n"
                "treść instrukcji",
            )
            return
        target = save_skill(
            "",
            skill.name,
            ", ".join(skill.formats),
            skill.text,
            ", ".join(skill.skip_patterns),
        )
        self._reload_skills()
        save_settings(self._collect_settings())
        self._append_log(f"Zaimportowano skillę: {target}")

    def _on_new_skill(self) -> None:
        try:
            target = new_skill_file()
        except OSError as exc:
            QMessageBox.critical(
                self, "Skille", f"Nie można utworzyć skilla: {exc}"
            )
            return
        self._reload_skills()
        save_settings(self._collect_settings())
        self._append_log(f"Utworzono nowy skilla: {target}")
        QMessageBox.information(
            self,
            "Nowy skilla",
            f"Utworzono plik szablonu:\n{target}\n\n"
            "Edytuj go (nazwa, formaty, opcjonalnie skip_patterns), "
            "zaznacz w listy i wciśnij „Odśwież”.",
        )

    def _build_help_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        language_row = QHBoxLayout()
        language_row.addWidget(QLabel("Język / Language:"))
        self.help_language = QComboBox()
        self.help_language.setObjectName("helpLanguage")
        self.help_language.addItem("Polski", "pl")
        self.help_language.addItem("English", "en")
        self.help_language.currentIndexChanged.connect(self._update_help)
        language_row.addWidget(self.help_language)
        language_row.addStretch(1)
        self.about_btn = QPushButton(t("button.about"))
        self.about_btn.setObjectName("aboutButton")
        self.about_btn.clicked.connect(self._show_about_dialog)
        language_row.addWidget(self.about_btn)
        layout.addLayout(language_row)

        self.help_view = QTextBrowser()
        self.help_view.setObjectName("helpView")
        self.help_view.setOpenExternalLinks(True)
        layout.addWidget(self.help_view, 1)

        self._update_help()
        return tab

    def _show_about_dialog(self) -> None:
        """Wyświetl podstawowe informacje o programie."""
        lang = get_language()
        if lang == "en":
            title = "About Tłumacz"
            text = (
                f"<h2>{APP_NAME}</h2>"
                f"<p><b>Version:</b> {APP_VERSION}</p>"
                "<p>AI-powered document translator with a Qt graphical interface.</p>"
                "<p>Supports local and cloud translation backends, including "
                "llama.cpp, FastAPI/Transformers, OpenVINO and Cloud API.</p>"
                "<p>License: MIT</p>"
            )
        else:
            title = "O programie"
            text = (
                f"<h2>{APP_NAME}</h2>"
                f"<p><b>Wersja:</b> {APP_VERSION}</p>"
                "<p>Program do tłumaczenia dokumentów z wykorzystaniem AI "
                "i graficznego interfejsu Qt.</p>"
                "<p>Obsługuje lokalne i chmurowe backendy tłumaczenia, w tym "
                "llama.cpp, FastAPI/Transformers, OpenVINO i Cloud API.</p>"
                "<p>Licencja: MIT</p>"
            )
        QMessageBox.about(self, title, text)

    def _update_help(self) -> None:
        lang = self.help_language.currentData()
        set_language(lang)
        self._refresh_ui_texts()
        if lang == "en":
            content = self._help_text_en()
        else:
            content = self._help_text_pl()
        self.help_view.setHtml(content)

    def _refresh_ui_texts(self) -> None:
        """Odświeża wszystkie teksty w GUI po zmianie języka."""
        # Nazwy zakładek
        self.tabs.setTabText(0, t("tab.translation"))
        self.tabs.setTabText(1, t("tab.api_server"))
        self.tabs.setTabText(2, t("tab.extras"))
        self.tabs.setTabText(3, t("tab.help"))
        # Przyciski
        self.translate_btn.setText(t("button.translate"))
        self.cancel_btn.setText(t("button.cancel"))
        self.restore_defaults_btn.setText(t("button.restore_defaults"))
        self.about_btn.setText(t("button.about"))
        # Grupy plików
        self.files_group.setTitle(t("files.group"))
        self.input_label.setText(t("files.input"))
        self.output_label.setText(t("files.output"))
        self.input_browse.setText(t("button.browse"))
        self.output_browse.setText(t("button.browse"))
        # Grupy ustawień
        self.api_group.setTitle(t("settings.api_group"))
        self.server_group.setTitle(t("settings.server_group"))
        self.glossary_group.setTitle(t("settings.glossary_group"))
        self.skills_group.setTitle(t("settings.skills_group"))
        self.other_group.setTitle(t("settings.other_group"))
        # Etykiety API - iteruj po wierszach QFormLayout
        api_keys = ["settings.base_url", "settings.api_key", "settings.model"]
        for row_idx, key in enumerate(api_keys):
            item = self.api_form.itemAt(row_idx, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                item.widget().setText(t(key))
        # Etykiety pozostałe - iteruj po wierszach QFormLayout
        other_keys = [
            "settings.block_size", "settings.temperature",
            "settings.target_language", "settings.theme",
            "settings.custom_prompt", "settings.skip_patterns",
        ]
        for row_idx, key in enumerate(other_keys):
            item = self.other_form.itemAt(row_idx, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                item.widget().setText(t(key))
        # Etykiety server - NIE aktualizuj, są ustawiane raz przy tworzeniu GUI
        # server_keys usunięte bo QFormLayout nie pozwala na dynamiczną zmianę etykiet
        # gdy pola są ukryte/pokazywane
        # Serwer
        self.restart_server_btn.setText(t("button.restart_server"))
        self.model_browse.setText(t("button.browse"))
        # Checkboxy server
        self.auto_start_server.setText(t("settings.auto_start"))
        self.cache_clear_after_translation.setText(t("settings.clear_cache"))
        # ComboBox chat template - przebuduj items
        self.server_chat_template.clear()
        self.server_chat_template.addItem(t("settings.chat_jinja"), "")
        self.server_chat_template.addItem(t("settings.chat_chatml"), "chatml")
        # Przyciski glosariusza
        self.glossary_browse.setText(t("button.browse"))
        self.add_entry_btn.setText(t("button.add_entry"))
        self.glossary_count_label.setText(t("glossary.no_file"))
        # Przyciski skilli
        self.refresh_skills_btn.setText(t("button.refresh"))
        self.import_skill_btn.setText(t("button.import_skill"))
        self.new_skill_btn.setText(t("button.new_skill"))

    def _help_text_pl(self) -> str:
        return help_text_pl()

    def _help_text_en(self) -> str:
        return help_text_en()

    def _build_api_group(self) -> QGroupBox:
        self.api_group = QGroupBox(t("settings.api_group"))
        self.api_form = QFormLayout(self.api_group)
        self._api_label_keys: dict[int, str] = {}

        self.base_url = QLineEdit()
        self.base_url.setObjectName("baseUrl")
        self.base_url.setToolTip(
            "Adres serwera API zgodnego z OpenAI.\n"
            "Dla lokalnego serwera: http://127.0.0.1:PORT/v1"
        )
        self.api_key = QLineEdit()
        self.api_key.setObjectName("apiKey")
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setToolTip(
            "Token uwierzytelniający (Authorization: Bearer).\n"
            "Lokalne serwery (llama.cpp, ollama) zwykle go ignorują."
        )
        self.model = QComboBox()
        self.model.setObjectName("model")
        self.model.setEditable(True)
        self.model.setToolTip(
            "Wybierz model:\n"
            "- LOCAL: lokalny serwer (pamięta ostatnie ustawienia)\n"
            "- Cloud models: skonfigurowane modele chmurowe (Gemini, OpenAI, etc.)\n"
            "- Puste pole: wprowadź własny model ręcznie"
        )
        self.model.currentTextChanged.connect(self._on_model_changed)
        self._populate_model_combo()

        row = 0
        self.api_form.addRow(t("settings.base_url"), self.base_url)
        self._api_label_keys[row] = "settings.base_url"; row += 1
        self.api_form.addRow(t("settings.api_key"), self.api_key)
        self._api_label_keys[row] = "settings.api_key"; row += 1
        self.api_form.addRow(t("settings.model"), self.model)
        self._api_label_keys[row] = "settings.model"; row += 1
        return self.api_group

    def _build_other_group(self) -> QGroupBox:
        self.other_group = QGroupBox(t("settings.other_group"))
        self.other_form = QFormLayout(self.other_group)
        self._other_label_keys: dict[int, str] = {}

        self.chunk_size = QSpinBox()
        self.chunk_size.setObjectName("chunkSize")
        self.chunk_size.setRange(500, 100_000)
        self.chunk_size.setSingleStep(500)
        self.chunk_size.setToolTip(
            "Wielkość fragmentu tekstu wysyłanego do modelu (w znakach).\n"
            "Mniejszy = lepszy kontekst sekcji, ale więcej wywołań API.\n"
            "Większy = mniej połączeń, ale ryzyko obcięcia/utraty spójności.\n"
            "Zalecane: 4000–6000 dla tłumaczenia na CPU."
        )
        self.temperature = QDoubleSpinBox()
        self.temperature.setObjectName("temperature")
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setDecimals(1)
        self.temperature.setToolTip(
            "Losowość odpowiedzi modelu.\n"
            "0.1–0.3 = wierne, deterministyczne tłumaczenie (zalecane).\n"
            "Wyższe wartości = bardziej swobodny styl."
        )
        self.language = QComboBox()
        self.language.setObjectName("language")
        for lang in SUPPORTED_LANGUAGES:
            self.language.addItem(lang, LANGUAGE_VALUES[lang])
        self.language.currentTextChanged.connect(self._on_language_changed)
        self.language.setToolTip("Język, na który ma być tłumaczony tekst.")

        self.theme = QComboBox()
        self.theme.setObjectName("theme")
        for label, value in THEME_CHOICES:
            self.theme.addItem(label, value)
        self.theme.currentIndexChanged.connect(self._on_theme_changed)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setObjectName("systemPrompt")
        self.prompt_edit.setPlaceholderText(
            "Opcjonalny własny prompt tłumaczenia (styl, terminologia, ton). "
            "Puste = domyślny prompt."
        )
        self.prompt_edit.setFixedHeight(70)

        self.skip_patterns_edit = QLineEdit()
        self.skip_patterns_edit.setObjectName("skipPatterns")
        self.skip_patterns_edit.setPlaceholderText(
            "Opcjonalne: własne regexy oddzielone przecinkiem. "
            "Puste = wzorce ze skilla dla danego formatu."
        )
        self.skip_patterns_edit.setToolTip(
            "Zaawansowane: wyrażenia regularne (regex) opisujące linie, których\n"
            "nie wolno tłumaczyć (np. metadane). Oddziel je przecinkami.\n"
            "Puste = automatyczne wzorce ze skilla dla danego formatu.\n"
            "Zwykle nie musisz nic tu wpisywać."
        )

        row = 0
        self.other_form.addRow(t("settings.block_size"), self.chunk_size)
        self._other_label_keys[row] = "settings.block_size"; row += 1
        self.other_form.addRow(t("settings.temperature"), self.temperature)
        self._other_label_keys[row] = "settings.temperature"; row += 1
        self.other_form.addRow(t("settings.target_language"), self.language)
        self._other_label_keys[row] = "settings.target_language"; row += 1
        self.other_form.addRow(t("settings.theme"), self.theme)
        self._other_label_keys[row] = "settings.theme"; row += 1
        self.other_form.addRow(t("settings.custom_prompt"), self.prompt_edit)
        self._other_label_keys[row] = "settings.custom_prompt"; row += 1
        self.other_form.addRow(t("settings.skip_patterns"), self.skip_patterns_edit)
        self._other_label_keys[row] = "settings.skip_patterns"; row += 1
        return self.other_group

    def _build_server_group(self) -> QGroupBox:
        self.server_group = QGroupBox(t("settings.server_group"))
        self.server_form = QFormLayout(self.server_group)
        self._server_label_keys: dict[int, str] = {}

        self.server_port = QSpinBox()
        self.server_port.setObjectName("serverPort")
        self.server_port.setRange(1024, 65535)
        self.server_port.setSingleStep(100)
        self.server_port.valueChanged.connect(self._on_port_changed)

        self.server_port.setToolTip(
            "Port, na którym ma nasłuchiwać serwer lokalny.\n"
            "Musi być wolny i różny od innych usług (np. 18080)."
        )

        # Model (wspólne pole dla llama.cpp i FastAPI)
        model_row = QHBoxLayout()
        self.server_model = QLineEdit()
        self.server_model.setObjectName("serverModel")
        self.server_model.setPlaceholderText("Ścieżka do modelu")
        self.server_model.setToolTip(
            "Ścieżka do modelu.\n"
            "llama.cpp: plik .gguf\n"
            "FastAPI: katalog z modelem Transformers"
        )
        self.model_browse = QPushButton(t("button.browse"))
        self.model_browse.clicked.connect(self._on_browse_model)
        model_row.addWidget(self.server_model, 1)
        model_row.addWidget(self.model_browse)

        # QComboBox dla modeli chmurowych (widoczny tylko dla chmury)
        self.server_cloud_model = QComboBox()
        self.server_cloud_model.setObjectName("serverCloudModel")
        for cloud_model in CLOUD_MODELS_CONFIG:
            self.server_cloud_model.addItem(cloud_model["name"], cloud_model)
        self.server_cloud_model.setToolTip(
            "Wybierz model chmurowy (Gemini, OpenAI, etc.)"
        )

        self.auto_start_server = QCheckBox(
            t("settings.auto_start")
        )
        self.auto_start_server.setObjectName("autoStartServer")
        self.auto_start_server.setToolTip(
            "Uruchom llama.cpp wraz z programem, gdy wskazano plik .gguf.\n"
            "Odznacz, jeśli używasz własnego, już działającego serwera."
        )
        self.auto_start_server.toggled.connect(self._update_restart_button_label)

        self.cache_clear_after_translation = QCheckBox(
            t("settings.clear_cache")
        )
        self.cache_clear_after_translation.setObjectName("cacheClearAfterTranslation")
        self.cache_clear_after_translation.setToolTip(
            "Automatycznie czyść cache tłumaczeń po zakończeniu każdego tłumaczenia.\n"
            "Zalecane przy testowaniu wydajności i dokładności.\n"
            "Odznacz aby zachować cache między tłumaczeniami (szybsze ponowne tłumaczenie tego samego pliku)."
        )

        self.restart_after_translation = QCheckBox(
            "Restart procesu po tłumaczeniu"
        )
        self.restart_after_translation.setObjectName("restartAfterTranslation")
        self.restart_after_translation.setToolTip(
            "Restartuje proces tłumaczenia po każdym pliku.\n"
            "Rozwiązuje problem z chunk_size po długim działaniu aplikacji."
        )

        self.server_compute_mode = QComboBox()
        self.server_compute_mode.setObjectName("serverComputeMode")
        self.server_compute_mode.addItem("GPU", "gpu")
        self.server_compute_mode.addItem("CPU", "cpu")
        self.server_compute_mode.setToolTip(
            "Tryb obliczeń llama-server. GPU używa dostępnego akceleratora; "
            "CPU wyłącza warstwy GPU i pozwala wykorzystać procesor.\n"
            "Zmiana wymaga restartu serwera."
        )

        self.server_chat_template = QComboBox()
        self.server_chat_template.setObjectName("serverChatTemplate")
        self.server_chat_template.addItem(t("settings.chat_jinja"), "")
        self.server_chat_template.addItem(t("settings.chat_chatml"), "chatml")
        self.server_chat_template.setToolTip(
            "Szablon czatu używany przy starcie serwera.\n"
            "jinja = natywny szablon modelu — zwykle działa.\n"
            "chatml = dla modeli, których szablon jinja jest nieprawidłowy."
        )

        self.server_parallel = QSpinBox()
        self.server_parallel.setObjectName("serverParallel")
        self.server_parallel.setRange(1, 4)
        self.server_parallel.setValue(1)
        self.server_parallel.setToolTip(
            "Liczba równoległych wątków tłumaczenia (1-4).\n"
            "Więcej wątków = szybciej, ale wymaga więcej RAM/VRAM.\n"
            "Dla parallel > 1 zwiększ ctx-size serwera (np. 16384)."
        )

        # Typ danych (tylko dla FastAPI)
        self.server_dtype = QComboBox()
        self.server_dtype.setObjectName("serverDtype")
        self.server_dtype.addItem("float16 (zalecany)", "float16")
        self.server_dtype.addItem("bfloat16", "bfloat16")
        self.server_dtype.addItem("float32 (wolniejszy)", "float32")
        self.server_dtype.setToolTip(
            "Typ danych dla modelu FastAPI (Transformers).\n"
            "float16 = zalecany dla GPU, bfloat16 = stabilny na CPU,\n"
            "float32 = wolniejszy ale najbardziej precyzyjny."
        )

        # Urządzenie OpenVINO (CPU/GPU/AUTO/MULTI)
        self.server_openvino_device = QComboBox()
        self.server_openvino_device.setObjectName("serverOpenvinoDevice")
        self.server_openvino_device.addItem("CPU", "CPU")
        self.server_openvino_device.addItem("GPU (iGPU)", "GPU")
        self.server_openvino_device.addItem("AUTO", "AUTO")
        self.server_openvino_device.addItem("Hybrydowy CPU+GPU", "MULTI:CPU,GPU")
        self.server_openvino_device.setToolTip(
            "Urządzenie wykonawcze dla backendu OpenVINO.\n"
            "CPU = stabilne, ~8 GB RAM.\n"
            "GPU = zintegrowana karta graficzna (iGPU), ~4 GB RAM.\n"
            "  Uwaga: OpenVINO GPU wspiera Intel iGPU.\n"
            "  Na AMD Radeon nastąpi automatyczny fallback na CPU.\n"
            "AUTO = OpenVINO wybierze optymalne urządzenie.\n"
            "Hybrydowy = CPU+GPU jednocześnie."
        )

        row = 0
        self.server_form.addRow(t("settings.port"), self.server_port)
        self._server_label_keys[row] = "settings.port"; row += 1
        self.server_form.addRow(t("settings.compute_mode"), self.server_compute_mode)
        self._server_label_keys[row] = "settings.compute_mode"; row += 1
        self.server_form.addRow(t("settings.gguf_path"), model_row)
        self._server_label_keys[row] = "settings.gguf_path"; row += 1
        self.server_form.addRow(t("settings.cloud_model"), self.server_cloud_model)
        self._server_label_keys[row] = "settings.cloud_model"; row += 1
        self.server_form.addRow(t("settings.chat_template"), self.server_chat_template)
        self._server_label_keys[row] = "settings.chat_template"; row += 1
        self.server_form.addRow(t("settings.parallel"), self.server_parallel)
        self._server_label_keys[row] = "settings.parallel"; row += 1
        self.server_form.addRow(t("settings.dtype"), self.server_dtype)
        self._server_label_keys[row] = "settings.dtype"; row += 1
        self.server_form.addRow("Urządzenie OpenVINO:", self.server_openvino_device)
        self._server_label_keys[row] = "settings.openvino_device"; row += 1
        self.server_form.addRow(self.auto_start_server)
        self.server_form.addRow(self.cache_clear_after_translation)
        self.server_form.addRow(self.restart_after_translation)

        self.restart_server_btn = QPushButton(t("button.restart_server"))
        self.restart_server_btn.setObjectName("restartServerBtn")
        self.restart_server_btn.setToolTip(
            "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
            "z aktualnymi ustawieniami."
        )
        self.restart_server_btn.clicked.connect(self._on_restart_server)
        # Przycisk aktywny gdy jest skonfigurowany plik GGUF (niezależnie od stanu serwera)
        self.restart_server_btn.setEnabled(bool(self._settings.server_gguf_path))
        self._update_restart_button_label()
        self.server_form.addRow(self.restart_server_btn)
        return self.server_group

    # ------------------------------------------------------------- helpers --

    def _build_config(self) -> TranslatorConfig:
        model = self.model.currentText().strip()
        # Gdy serwer zarządzany jest uruchomiony i model to "LOCAL" lub pusty,
        # użyj aliasu "local" — serwer obsługuje tylko model z GGUF.
        # Jeśli użytkownik wybrał model chmurowy, użyj go (edge case).
        if self._server is not None and (not model or model == "LOCAL"):
            model = SERVER_MODEL_ALIAS

        # Określ backend i ustaw odpowiedni chat_template
        model_data = self.model.currentData()
        backend = "llama"
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")

        # Dla FastAPI użyj specjalnego formatu TranslateGemma
        if backend == "fastapi":
            chat_template = "translategemma"
        else:
            chat_template = self.server_chat_template.currentData() or ""

        # OpenVINO — przekaż ścieżkę i device (pickle-safe dla multiprocessing)
        # Pobierz bezpośrednio z GUI (nie z self._settings które może być nieaktualne)
        openvino_model_path = ""
        openvino_device = "CPU"
        if backend == "openvino":
            openvino_model_path = self.server_model.text().strip()
            openvino_device = self.server_openvino_device.currentData() or "CPU"

        chunk_size_value = self.chunk_size.value()

        # Log do debug.log - BEZ try/except żeby zobaczyć błędy
        from pathlib import Path
        import time
        log_dir = Path.home() / ".config" / "tlumacz"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "debug.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} DEBUG _build_config: chunk_size={chunk_size_value}\n")

        return TranslatorConfig(
            base_url=self.base_url.text().strip(),
            api_key=self.api_key.text().strip(),
            model=model,
            chat_template=chat_template,
            chat_template_kwargs=(
                {"enable_thinking": False}
                if self._server is not None
                else None
            ),
            chunk_size=chunk_size_value,
            temperature=self.temperature.value(),
            parallel=self.server_parallel.value(),
            target_language=self.language.currentData() or "wykryj do pl",
            glossary_path=self.glossary_path.text().strip() or None,
            system_prompt=self.prompt_edit.toPlainText().strip() or None,
            enabled_skills=self._enabled_skill_names(),
            skip_line_patterns=self._skip_pattern_list(),
            cache_clear_after_translation=self.cache_clear_after_translation.isChecked(),
            openvino_model_path=openvino_model_path,
            openvino_device=openvino_device,
        )

    def _collect_settings(self) -> AppSettings:
        """Zbierz ustawienia z GUI — zachowaj istniejące pola z self._settings."""
        model = self.model.currentText().strip()
        
        # Zacznij od kopii istniejących ustawień
        settings = AppSettings(
            base_url=self.base_url.text().strip(),
            api_key=self.api_key.text().strip(),
            model=model,
            chunk_size=self.chunk_size.value(),
            temperature=self.temperature.value(),
            target_language=self.language.currentData() or "wykryj do pl",
            last_input=self.input_path.text().strip(),
            last_output=self.output_path.text().strip(),
        )
        
        # Zachowaj istniejące pola z self._settings
        settings.server_gguf_path = self._settings.server_gguf_path
        settings.fastapi_model_path = self._settings.fastapi_model_path
        settings.openvino_model_path = self._settings.openvino_model_path
        settings.fastapi_host = self._settings.fastapi_host
        settings.last_local_base_url = self._settings.last_local_base_url
        settings.last_local_api_key = self._settings.last_local_api_key
        settings.last_local_model = self._settings.last_local_model
        settings.model_profiles = self._settings.model_profiles
        settings.cloud_models = self._settings.cloud_models
        # Zachowaj ustawienia llama.cpp
        settings.server_port = self._settings.server_port
        settings.server_parallel = self._settings.server_parallel
        settings.server_compute_mode = self._settings.server_compute_mode
        settings.server_chat_template = self._settings.server_chat_template

        # Określ backend na podstawie wybranego modelu
        model_data = self.model.currentData()
        if model_data and isinstance(model_data, dict):
            settings.backend_type = model_data.get("backend", "cloud")
        elif model == "LOCAL":
            settings.backend_type = "llama"
        else:
            settings.backend_type = "cloud"

        # Zapamiętaj last_local_* gdy wybrany LOCAL
        if model == "LOCAL":
            settings.last_local_base_url = self.base_url.text().strip()
            settings.last_local_api_key = self.api_key.text().strip()
            settings.last_local_model = "local"

        settings.theme = self.theme_mode()
        settings.glossary_path = self.glossary_path.text().strip()
        settings.system_prompt = self.prompt_edit.toPlainText().strip()
        settings.enabled_skills = self._enabled_skill_names()
        settings.skip_line_patterns = self._skip_pattern_list()

        # Ustawienia serwera — zapisz w odpowiednich polach zależnie od backendu
        if settings.backend_type == "fastapi":
            settings.fastapi_port = self.server_port.value()
            settings.fastapi_model_path = self.server_model.text().strip()
            settings.fastapi_dtype = self.server_dtype.currentData()
            settings.fastapi_parallel = self.server_parallel.value()
        elif settings.backend_type == "openvino":
            settings.openvino_model_path = self.server_model.text().strip()
            settings.openvino_device = self.server_openvino_device.currentData() or "CPU"
        else:
            # llama.cpp (domyślnie)
            settings.server_port = self.server_port.value()
            settings.server_compute_mode = self.server_compute_mode.currentData()
            gguf_path = self.server_model.text().strip()
            if gguf_path:  # Tylko zapisz jeśli nie jest pusty
                settings.server_gguf_path = gguf_path
            settings.server_chat_template = self.server_chat_template.currentData()
            settings.server_parallel = self.server_parallel.value()

        settings.auto_start_server = self.auto_start_server.isChecked()
        settings.cache_clear_after_translation = self.cache_clear_after_translation.isChecked()
        settings.restart_after_translation = self.restart_after_translation.isChecked()
        return settings

    def _populate_model_combo(self) -> None:
        """Wypełnij combo box typami serwerów: backendy lokalne + chmura."""
        self.model.clear()
        # Backendy lokalne
        self.model.addItem("llama.cpp", {"name": "llama.cpp", "backend": "llama"})
        self.model.addItem("FastAPI (TranslateGemma)", {"name": "FastAPI (TranslateGemma)", "backend": "fastapi"})
        self.model.addItem("OpenVINO (TranslateGemma INT8)", {"name": "OpenVINO (TranslateGemma INT8)", "backend": "openvino"})
        # Chmura
        self.model.addItem("Chmura", {"name": "Chmura", "backend": "cloud"})

    def _on_model_changed(self, model_name: str) -> None:
        """Obsługa zmiany modelu — automatyczne ustawienie base_url, api_key i widoczność pól."""
        if self._loading:
            return
        if self._switching_backend:
            logger.info("_on_model_changed: pomijam podwójne wywołanie")
            return

        logger.info(f"_on_model_changed: model_name={model_name}")

        # Zapamiętaj obecną ścieżkę modelu przed przełączeniem
        current_model_path = self.server_model.text().strip()
        current_backend = self._settings.backend_type
        logger.info(f"_on_model_changed: current_backend={current_backend}, current_model_path={current_model_path}")
        if current_backend == "fastapi":
            if current_model_path:
                self._settings.fastapi_model_path = current_model_path
        elif current_backend == "openvino":
            if current_model_path:
                self._settings.openvino_model_path = current_model_path
        else:
            if current_model_path:
                self._settings.server_gguf_path = current_model_path

        # Określ nowy backend na podstawie danych modelu
        model_data = self.model.currentData()
        backend = "llama"  # domyślny
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")
        logger.info(f"_on_model_changed: model_data={model_data}, backend={backend}")

        # Zaktualizuj backend w settings
        self._settings.backend_type = backend

        if model_name == "llama.cpp":
            # llama.cpp — ustaw domyślny URL i port
            self.base_url.setText(f"http://127.0.0.1:{self._settings.server_port}/v1")
            self.server_port.setValue(self._settings.server_port)
        elif model_name == "FastAPI (TranslateGemma)":
            # FastAPI — ustaw domyślny URL i port
            self.base_url.setText(f"http://127.0.0.1:{self._settings.fastapi_port}/v1")
            self.server_port.setValue(self._settings.fastapi_port)
        elif model_name == "OpenVINO (TranslateGemma INT8)":
            # OpenVINO — pseudo-URL
            self.base_url.setText(f"openvino://{self._settings.openvino_device}")
        elif model_name == "Chmura":
            # Chmura — ustaw URL Gemini
            self.base_url.setText("https://generativelanguage.googleapis.com/v1")
        # else: własny model — nie zmieniaj base_url/api_key

        # Przywróć ścieżkę modelu dla nowego backendu
        if backend == "fastapi":
            self.server_model.setText(self._settings.fastapi_model_path)
        elif backend == "openvino":
            self.server_model.setText(self._settings.openvino_model_path)
        else:
            self.server_model.setText(self._settings.server_gguf_path)

        # Aktualizuj widoczność pól i nazwę bloku Serwer
        self._update_server_fields_visibility(backend)

        # Zapamiętaj stary backend PRZED aktualizacją
        old_backend = self._backend_manager.get_active_backend()

        # Aktualizuj backend_type w BackendManager (ważne dla start/stop)
        self._backend_manager._config.backend_type = backend

        # Ustaw flagę guardującą przed podwójnym wywołaniem
        self._switching_backend = True

        try:
            # Automatyczne zatrzymywanie/uruchamianie serwerów przy przełączaniu
            # Zatrzymuj STARY backend (nie nowy!)
            if old_backend == "llama":
                self._backend_manager.stop_llama()
            elif old_backend == "fastapi":
                self._backend_manager.stop_fastapi()
            elif old_backend == "openvino":
                self._backend_manager.stop_openvino()

            # Uruchom wybrany backend (jeśli ma ścieżkę modelu)
            if backend == "llama" and self._settings.server_gguf_path:
                self._set_backend_controls_enabled(False)
                self._show_loading_dialog("llama.cpp")
                self._backend_manager.start()
            elif backend == "fastapi" and self._settings.fastapi_model_path:
                self._set_backend_controls_enabled(False)
                self._show_loading_dialog("FastAPI (TranslateGemma)")
                self._backend_manager.start()
            elif backend == "openvino" and self._settings.openvino_model_path:
                self._set_backend_controls_enabled(False)
                self._show_loading_dialog("OpenVINO")
                self._backend_manager.start()
            elif backend == "cloud":
                # Cloud nie wymaga ładowania — emituj backend_started natychmiast
                self._backend_manager.start()
        finally:
            # Zdejmij flagę guardującą
            self._switching_backend = False

        # Aktualizuj _settings z GUI i zapisz
        self._settings = self._collect_settings()
        save_settings(self._settings)

    def _update_server_fields_visibility(self, backend: str) -> None:
        """Aktualizuj widoczność pól w bloku Serwer zależnie od backendu.

        Args:
            backend: 'llama', 'fastapi', 'openvino' lub 'cloud'
        """
        is_llama = backend == "llama"
        is_fastapi = backend == "fastapi"
        is_openvino = backend == "openvino"
        is_cloud = backend == "cloud"
        is_local = is_llama or is_fastapi or is_openvino

        # Zmień nazwę bloku Serwer
        if is_llama:
            self.server_group.setTitle("Serwer llama.cpp — lokalny")
        elif is_fastapi:
            self.server_group.setTitle("Serwer FastAPI — lokalny")
        elif is_openvino:
            self.server_group.setTitle("Backend OpenVINO — lokalny")
        else:
            self.server_group.setTitle("Serwer zewnętrzny — chmura")

        # Port — aktywny dla llama.cpp i FastAPI (nie OpenVINO)
        is_server = is_llama or is_fastapi
        self.server_port.setVisible(is_server)
        port_label = self.server_form.labelForField(self.server_port)
        if port_label:
            port_label.setVisible(is_server)

        # Obliczenia serwera — tylko llama.cpp (nie FastAPI, nie OpenVINO)
        self.server_compute_mode.setVisible(is_llama)
        compute_label = self.server_form.labelForField(self.server_compute_mode)
        if compute_label:
            compute_label.setVisible(is_llama)

        # Model (wspólne pole) — aktywny dla wszystkich lokalnych
        self.server_model.setVisible(is_local)
        self.model_browse.setVisible(is_local)
        model_label = self.server_form.labelForField(self.server_model)
        if model_label:
            model_label.setVisible(is_local)
        # Zmień placeholder/tooltip zależnie od backendu
        if is_llama:
            self.server_model.setPlaceholderText("Ścieżka do pliku .gguf")
            self.server_model.setToolTip("Ścieżka do pliku modelu GGUF dla llama.cpp.")
        elif is_fastapi:
            self.server_model.setPlaceholderText("Ścieżka do katalogu modelu")
            self.server_model.setToolTip(
                "Ścieżka do katalogu z modelem Transformers dla FastAPI.\n"
                "np. ~/Modele/hub/models--google--translategemma-4b-it"
            )
        elif is_openvino:
            self.server_model.setPlaceholderText("Ścieżka do katalogu modelu OpenVINO IR")
            self.server_model.setToolTip(
                "Ścieżka do katalogu z modelem OpenVINO INT8 dla TranslateGemma.\n"
                "np. ~/Modele/openvino/translategemma-4b-it-int8-ov"
            )

        # Model chmurowy (QComboBox) — tylko chmura
        self.server_cloud_model.setVisible(is_cloud)
        cloud_label = self.server_form.labelForField(self.server_cloud_model)
        if cloud_label:
            cloud_label.setVisible(is_cloud)

        # Szablon czatu — tylko llama.cpp
        self.server_chat_template.setVisible(is_llama)
        template_label = self.server_form.labelForField(self.server_chat_template)
        if template_label:
            template_label.setVisible(is_llama)

        # Wątki (parallel) — llama.cpp i FastAPI (nie OpenVINO)
        self.server_parallel.setVisible(is_server)
        parallel_label = self.server_form.labelForField(self.server_parallel)
        if parallel_label:
            parallel_label.setVisible(is_server)

        # Typ danych — tylko FastAPI
        self.server_dtype.setVisible(is_fastapi)
        dtype_label = self.server_form.labelForField(self.server_dtype)
        if dtype_label:
            dtype_label.setVisible(is_fastapi)

        # Urządzenie OpenVINO — tylko OpenVINO
        self.server_openvino_device.setVisible(is_openvino)
        ov_device_label = self.server_form.labelForField(self.server_openvino_device)
        if ov_device_label:
            ov_device_label.setVisible(is_openvino)

        # Checkboxy — llama.cpp i FastAPI
        self.auto_start_server.setVisible(is_local)
        self.cache_clear_after_translation.setVisible(is_local)

        # Przycisk restart — tylko serwery lokalne (ukryty dla chmury)
        self.restart_server_btn.setVisible(is_local)

        # Pole Klucz API — ukryj przy OpenVINO (nie używa klucza API)
        # Pokaż przy llama.cpp, FastAPI i Chmura
        api_key_visible = not is_openvino
        self.api_key.setVisible(api_key_visible)
        api_key_label = self.api_form.labelForField(self.api_key)
        if api_key_label:
            api_key_label.setVisible(api_key_visible)

    def _on_port_changed(self, port: int) -> None:
        """Aktualizuj Base URL gdy zmieni się port."""
        if self._loading:
            return
        # Określ backend
        model_data = self.model.currentData()
        backend = "llama"
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")
        # Aktualizuj base_url dla backendów lokalnych
        if backend in ("llama", "fastapi"):
            self.base_url.setText(f"http://127.0.0.1:{port}/v1")

    def _load_settings_into_ui(self) -> None:
        s = self._settings
        self.base_url.setText(s.base_url)
        if self._server is not None:
            server_url = self._server.config.base_url
            self.base_url.setText(server_url)
            self._append_log(f"Własny serwer uruchomiony: {server_url}")
        self.api_key.setText(s.api_key)
        
        # Ustaw combo box "Typ serwera" na ostatnio używany backend
        backend = s.backend_type
        backend_to_text = {
            "llama": "llama.cpp",
            "fastapi": "FastAPI (TranslateGemma)",
            "openvino": "OpenVINO (TranslateGemma INT8)",
            "cloud": "Chmura",
        }
        backend_text = backend_to_text.get(backend, "llama.cpp")
        backend_index = self.model.findText(backend_text)
        if backend_index >= 0:
            self.model.setCurrentIndex(backend_index)
        
        # Ustaw model w combo box (dla chmury) lub "local" (dla llama)
        if backend == "cloud":
            model_text = s.model
            model_index = self.model.findText(model_text)
            if model_index >= 0:
                self.model.setCurrentIndex(model_index)
            else:
                self.model.setEditText(model_text)
        
        self.chunk_size.setValue(s.chunk_size)
        self.temperature.setValue(s.temperature)
        # Ustaw język — szukaj po data (wartości "wykryj do X")
        lang_index = self.language.findData(s.target_language)
        if lang_index >= 0:
            self.language.setCurrentIndex(lang_index)
        theme_index = self.theme.findData(s.theme)
        if theme_index >= 0:
            self.theme.setCurrentIndex(theme_index)
        self.input_path.setText(s.last_input)
        self.output_path.setText(s.last_output)
        self.glossary_path.setText(s.glossary_path)
        self._refresh_glossary_count()
        self.prompt_edit.setPlainText(s.system_prompt)
        self.skip_patterns_edit.setText(
            ", ".join(s.skip_line_patterns or DEFAULT_SKIP_PATTERNS)
        )
        enabled = set(s.enabled_skills)
        for skill, checkbox in zip(self._skills, self._skill_checkboxes):
            checkbox.setChecked(skill.name in enabled)

        # Załaduj ustawienia serwera zależnie od backendu
        if s.backend_type == "fastapi":
            self.server_port.setValue(s.fastapi_port)
            self.server_model.setText(s.fastapi_model_path)
            dtype_index = self.server_dtype.findData(s.fastapi_dtype)
            self.server_dtype.setCurrentIndex(dtype_index if dtype_index >= 0 else 0)
            self.server_parallel.setValue(s.fastapi_parallel)
        elif s.backend_type == "openvino":
            self.server_model.setText(s.openvino_model_path)
            device_index = self.server_openvino_device.findData(s.openvino_device)
            self.server_openvino_device.setCurrentIndex(device_index if device_index >= 0 else 0)
        else:
            # llama.cpp (domyślnie)
            self.server_port.setValue(s.server_port)
            mode_index = self.server_compute_mode.findData(s.server_compute_mode)
            self.server_compute_mode.setCurrentIndex(mode_index if mode_index >= 0 else 0)
            self.server_model.setText(s.server_gguf_path)
            template_index = self.server_chat_template.findData(s.server_chat_template)
            self.server_chat_template.setCurrentIndex(template_index)
            self.server_parallel.setValue(s.server_parallel)

        self.auto_start_server.setChecked(s.auto_start_server)
        self.cache_clear_after_translation.setChecked(s.cache_clear_after_translation)
        self.restart_after_translation.setChecked(s.restart_after_translation)

        # Aktualizuj widoczność pól zależnie od backendu
        self._update_server_fields_visibility(s.backend_type)

    def _append_log(self, message: str) -> None:
        self.log_view.appendPlainText(message)

    def _format_elapsed(self, milliseconds: int) -> str:
        total_seconds = max(0, milliseconds // 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"Czas: {hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"Czas: {minutes:02d}:{seconds:02d}"

    def _update_elapsed_time(self) -> None:
        if self._elapsed_timer.isValid():
            self.elapsed_label.setText(
                self._format_elapsed(self._elapsed_timer.elapsed())
            )

    def _advance_spinner(self) -> None:
        self._spinner_index = (self._spinner_index + 1) % len(self._spinner_frames)
        self.spinner_label.setText(self._spinner_frames[self._spinner_index])

    def _start_activity_indicators(self) -> None:
        self._elapsed_timer.start()
        self._elapsed_display_timer.start()
        self._spinner_index = 0
        self.spinner_label.setText(self._spinner_frames[0])
        self.spinner_label.setVisible(True)
        self._spinner_timer.start()
        self._update_elapsed_time()

    def _stop_activity_indicators(self) -> None:
        if self._elapsed_timer.isValid():
            self._update_elapsed_time()
        self._elapsed_display_timer.stop()
        self._spinner_timer.stop()
        self.spinner_label.setVisible(False)

    def _set_idle_state(self) -> None:
        self.translate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._stop_activity_indicators()

    def _set_running_state(self) -> None:
        self.translate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0%")
        self._start_activity_indicators()

    # ------------------------------------------------------------ handlers --

    def _browse_file(
        self,
        title: str,
        start: str,
        filters: str,
        save: bool = False,
    ) -> str:
        """Open a file dialog that also shows hidden files and folders."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setNameFilter(filters)
        dialog.setFilter(
            QDir.Filter.Files
            | QDir.Filter.Dirs
            | QDir.Filter.Hidden
            | QDir.Filter.NoDotAndDotDot
        )
        if save:
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            # Dla zapisu - ustaw sugerowaną nazwę pliku
            if start:
                dialog.selectFile(start)
        else:
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            if start:
                dialog.setDirectory(start)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    def _browse_directory(self, title: str, start: str) -> str:
        """Open a directory selection dialog."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if start:
            dialog.setDirectory(start)
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            return dialog.selectedFiles()[0]
        return ""

    def _on_browse_input(self) -> None:
        path = self._browse_file(
            "Wybierz plik wejściowy",
            self.input_path.text(),
            "Dokumenty (*.md *.markdown *.txt *.text *.html *.htm "
            "*.pdf *.docx *.odt *.epub);;Markdown (*.md *.markdown);;"
            "Tekst (*.txt *.text);;HTML (*.html *.htm);;"
            "PDF (*.pdf);;Word (*.docx);;OpenDocument (*.odt);;"
            "EPUB (*.epub);;Wszystkie pliki (*)",
        )
        if path:
            self.input_path.setText(path)
            self.output_path.setText(
                _default_output_path(path, self.language.currentText())
            )

    def _on_browse_output(self) -> None:
        path = self._browse_file(
            "Wybierz plik wyjściowy",
            self.output_path.text(),
            "Wszystkie pliki (*)",
            save=True,
        )
        if path:
            self.output_path.setText(path)

    def _on_browse_model(self) -> None:
        """Wybierz model — plik GGUF dla llama.cpp, katalog dla FastAPI/OpenVINO."""
        # Określ backend
        model_data = self.model.currentData()
        backend = "llama"
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")

        if backend == "fastapi":
            path = self._browse_directory(
                "Wybierz katalog z modelem Transformers",
                self.server_model.text(),
            )
        elif backend == "openvino":
            path = self._browse_directory(
                "Wybierz katalog z modelem OpenVINO IR",
                self.server_model.text(),
            )
        else:
            # Dla llama.cpp wybierz plik GGUF
            path = self._browse_file(
                "Wybierz plik modelu (GGUF)",
                self.server_model.text(),
                "GGUF files (*.gguf);;Wszystkie pliki (*)",
            )
        if path:
            self.server_model.setText(path)
            # Zaktualizuj _settings i zapisz
            self._settings = self._collect_settings()
            save_settings(self._settings)

    def _on_browse_glossary(self) -> None:
        path = self._browse_file(
            "Wybierz plik glosariusza (CSV)",
            self.glossary_path.text(),
            "CSV files (*.csv);;Wszystkie pliki (*)",
        )
        if path:
            self.glossary_path.setText(path)
            self._on_glossary_path_edited()

    def _on_glossary_path_edited(self) -> None:
        """Odśwież liczbę wpisów glosariusza i zapisz ustawienia.

        Uwaga: _refresh_glossary_count czyta do _GLOSSARY_COUNT_SCAN (50k) wpisów.
        Dla bardzo dużych plików może to być wolne, ale editingFinished jest
        wywoływane tylko przy utracie fokusu, więc nie jest to częste.
        """
        save_settings(self._collect_settings())
        self._refresh_glossary_count()

    def _refresh_glossary_count(self) -> None:
        path = self.glossary_path.text().strip()
        if not path or not os.path.exists(path):
            self.glossary_count_label.setText("Brak pliku")
            return
        try:
            glossary = Glossary.from_csv(path, max_entries=_GLOSSARY_COUNT_SCAN)
        except OSError:
            self.glossary_count_label.setText("Nie można odczytać")
            return
        count = len(glossary)
        if count >= _GLOSSARY_COUNT_SCAN:
            self.glossary_count_label.setText(
                f"Liczba wpisów: ≥{_GLOSSARY_COUNT_SCAN}"
            )
        else:
            self.glossary_count_label.setText(f"Liczba wpisów: {count}")

    def _on_add_glossary_entry(self) -> None:
        source = self.glossary_term.text().strip()
        target = self.glossary_target.text().strip()
        if not source or not target:
            QMessageBox.warning(
                self, "Glosariusz", "Wpisz termin i jego tłumaczenie."
            )
            return
        path = self.glossary_path.text().strip()
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Nowy plik glosariusza",
                "glosariusz.csv",
                "CSV files (*.csv)",
            )
            if not path:
                return
            self.glossary_path.setText(path)

        glossary = (
            Glossary.from_csv(path) if os.path.exists(path) else Glossary()
        )
        if not glossary.add(source, target):
            QMessageBox.information(
                self, "Glosariusz", "Taki wpis już istnieje w glosariuszu."
            )
            return
        try:
            glossary.save(path)
        except OSError as exc:
            QMessageBox.critical(
                self, "Glosariusz", f"Nie można zapisać glosariusza: {exc}"
            )
            return
        self.glossary_term.clear()
        self.glossary_target.clear()
        self._on_glossary_path_edited()
        self._append_log(f"Glosariusz: dodano „{source} -> {target}” do {path}")

    def _update_restart_button_label(self) -> None:
        """Aktualizuj etykietę przycisku restart.

        Przycisk zawsze pokazuje "Restart serwera" — automatyczne
        start/stop jest obsługiwane przy przełączaniu backendów.
        """
        self.restart_server_btn.setText(t("button.restart_server"))
        self.restart_server_btn.setToolTip(
            "Zatrzymaj i uruchom ponownie aktywny serwer lokalny "
            "z aktualnymi ustawieniami."
        )
        # Przycisk zawsze aktywny dla backendów lokalnych
        self.restart_server_btn.setEnabled(True)

    def _on_restart_server(self) -> None:
        """Restart aktywnego serwera lokalnego.

        Automatyczne start/stop jest obsługiwane przy przełączaniu backendów.
        """
        logger.info("_on_restart_server() called")

        # Sprawdź backend
        model_data = self.model.currentData()
        backend = "llama"
        if model_data and isinstance(model_data, dict):
            backend = model_data.get("backend", "cloud")

        # Chmura — brak akcji (przycisk ukryty)
        if backend == "cloud":
            return

        # Zapisz ustawienia
        settings = self._collect_settings()
        save_settings(settings)
        config_updates = self._build_config_updates()

        # Wyczyść cache tłumaczeń
        from ..cache import TranslationCache
        cache = TranslationCache()
        cache.clear()
        self._append_log("Cache tłumaczeń wyczyszczony")

        # Restart aktywnego backendu
        self.restart_server_btn.setEnabled(False)
        self._set_backend_controls_enabled(False)
        backend_names = {"llama": "llama.cpp", "fastapi": "FastAPI (TranslateGemma)", "openvino": "OpenVINO"}
        self._show_loading_dialog(backend_names.get(backend, backend))
        self._append_log(f"Restart {backend}...")
        self._backend_manager.restart(config_updates, backend=backend)

    def _on_restore_defaults(self) -> None:
        if self._is_thread_running(self._thread):
            QMessageBox.warning(
                self,
                "Przywracanie",
                "Tłumaczenie jest w toku. Poczekaj na jego zakończenie.",
            )
            return
        reply = QMessageBox.question(
            self,
            "Przywróć domyślne",
            "Przywrócić wszystkie ustawienia do wartości domyślnych?\n"
            "Aktualny config.json zostanie zapisany jako kopia zapasowa.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        defaults, backup = reset_settings()
        self._settings = defaults
        self._loading = True
        self._load_settings_into_ui()
        self._loading = False
        message = "Przywrócono ustawienia domyślne."
        if backup:
            message += f"\nKopia zapasowa: {backup}"
        QMessageBox.information(self, "Przywróć domyślne", message)
        self._append_log("Przywrócono ustawienia domyślne.")

    def _on_language_changed(self, _language: str) -> None:
        input_path = self.input_path.text().strip()
        if input_path and not self.output_path.text().strip():
            self.output_path.setText(
                _default_output_path(input_path, _language)
            )

    def _enabled_skill_names(self) -> list[str]:
        return [
            skill.name
            for skill, checkbox in zip(self._skills, self._skill_checkboxes)
            if checkbox.isChecked()
        ]

    def _skip_pattern_list(self) -> list[str]:
        """Parse the regex field into a list, falling back to defaults."""
        raw = self.skip_patterns_edit.text().strip()
        if not raw:
            return list(DEFAULT_SKIP_PATTERNS)
        return [part.strip() for part in raw.split(",") if part.strip()]

    def _on_skills_changed(self) -> None:
        if self._loading:
            return
        save_settings(self._collect_settings())

    def _auto_select_skill_for_input(self, text: str) -> None:
        """Auto-check the skill whose format matches the input extension.

        Odznacza wszystkie skille, a następnie zaznacza pasujący do rozszerzenia pliku.
        Preferuje wbudowane skille (Markdown) nad użytkownika (lista_skilli).
        """
        if self._loading or not self._skill_checkboxes:
            return
        if not text.strip():
            return
        ext = Path(text.strip()).suffix.lower().lstrip(".")
        if not ext:
            return

        # Odznacz wszystkie skille
        for checkbox in self._skill_checkboxes:
            checkbox.setChecked(False)

        # Zaznacz pasujący skill - preferuj wbudowane (Markdown, HTML, etc.) nad użytkownika
        # Wbudowane skille mają nazwy angielskie, użytkownika polskie
        builtin_names = {"Markdown", "HTML", "DOCX", "ODT", "EPUB", "PDF", "Tekst zwykły"}
        
        # Najpierw szukaj wbudowanego skilla
        for skill, checkbox in zip(self._skills, self._skill_checkboxes):
            if ext in skill.formats and skill.name in builtin_names:
                checkbox.setChecked(True)
                self._append_log(f"Automatycznie wybrano skill: {skill.name}")
                return
        
        # Jeśli nie znaleziono wbudowanego, użyj pierwszego pasującego
        for skill, checkbox in zip(self._skills, self._skill_checkboxes):
            if ext in skill.formats:
                checkbox.setChecked(True)
                self._append_log(f"Automatycznie wybrano skill: {skill.name}")
                break

    def theme_mode(self) -> str:
        """Return the currently selected theme mode (``system``/``light``/``dark``)."""
        return self.theme.currentData() or "system"

    def _on_theme_changed(self) -> None:
        if self._loading:
            return
        save_settings(self._collect_settings())
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self.theme_mode())

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
            output_path = _default_output_path(
                input_path, self.language.currentText()
            )
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
        if self._is_thread_running(self._thread):
            self._append_log("Anulowanie...")
            self._thread.cancel()
            self.cancel_btn.setEnabled(False)
            # cancel() is non-blocking: it sets a shared event that (a) closes
            # the in-flight HTTP client so a blocked chunk unblocks quickly
            # and (b) is checked between chunks. The worker's own monitoring
            # loop (in TranslateWorker.run(), on the background thread) then
            # escalates to terminate/kill the child process if it does not
            # exit on its own within ~3s — see DEBUG_QT.md item C. No
            # QThread.terminate() is used for this interactive path.
            # Give that a bit of margin before checking on the server.
            QTimer.singleShot(3500, self._ensure_server_after_cancel)

    def _ensure_server_after_cancel(self) -> None:
        """Restart the managed llama-server if cancellation left it offline.

        Deleguje do ServerManager — ten wykonuje restart w tle (see
        DEBUG_QT.md item B).
        """
        if not self._server_manager.is_running and self._server_manager.server is None:
            # Brak zarządzanego serwera — nic do roboty
            return
        server = self._server
        if server is not None and server.is_running():
            self._append_log("llama-server po anulowaniu nadal działa.")
            return
        # Sprawdź czy operacja już trwa
        if self._server_manager.state in (ServerState.STARTING, ServerState.STOPPING):
            return
        # Zapisz ustawienia i deleguj restart do BackendManager
        settings = self._collect_settings()
        save_settings(settings)
        config_updates = self._build_config_updates()
        self._append_log("llama-server po anulowaniu nie odpowiada — ponowne uruchamianie...")
        self._backend_manager.restart(config_updates)

    def _on_progress(self, current: int, total: int) -> None:
        percent = int(current * 100 / total) if total else 0
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{current}/{total} ({percent}%)")

    def _on_finished(self, output_path: str) -> None:
        self._set_idle_state()
        self.progress_bar.setValue(100)
        self._append_log(f"Zakończono: {output_path}")
        self._show_preview(output_path)
        self._clear_finished_thread()

    def _on_failed(self, message: str) -> None:
        self._set_idle_state()
        self._append_log(f"BŁĄD: {message}")
        self._clear_finished_thread()
        QMessageBox.critical(self, "Błąd tłumaczenia", message)

    def _clear_finished_thread(self) -> None:
        """Wyczyść referencję do threadu po zakończeniu tłumaczenia.

        Thread już się zakończył (finished/failed signal), więc nie trzeba
        wywoływać stop() — wystarczy ustawić referencję na None.
        """
        if self._is_thread_running(self._thread):
            self._thread.stop()
            self._thread.thread.wait(5000)  # Czekaj max 5s
        self._thread = None

    def _show_preview(self, output_path: str) -> None:
        """Wyświetl podgląd przetłumaczonego pliku.

        Dla plików tekstowych (MD, TXT, HTML) wyświetla zawartość.
        Dla plików binarnych (DOCX, ODT, EPUB, PDF) wyświetla komunikat.
        """
        if is_binary_format(output_path):
            ext = Path(output_path).suffix.upper().lstrip(".")
            self.preview_view.setPlainText(
                f"Podgląd niedostępny dla plików {ext}.\n\n"
                f"Plik został zapisany w:\n{output_path}"
            )
            return
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                self.preview_view.setPlainText(f.read())
        except UnicodeDecodeError:
            self.preview_view.setPlainText(
                "Nie można wyświetlić podglądu — plik zawiera dane binarne."
            )
        except OSError as exc:
            self._append_log(f"Nie można wczytać podglądu: {exc}")

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # Zapisz rozmiar i pozycję okna
        self._window_settings.setValue("windowGeometry", self.saveGeometry())
        if self._thread is not None:
            stopped = self._thread.stop()
            if not stopped:
                self._append_log(t("log.thread_force_stopped"))
        if self._config_file_present or (config_dir() / "config.json").is_file():
            save_settings(self._collect_settings())
        super().closeEvent(event)


def _default_output_path(input_path: str, language: str) -> str:
    """Return ``name_<suffix>.ext`` next to the input file.

    The suffix follows the selected target language (``pl``, ``en``, ...).
    DOCX, ODT, EPUB and PDF are translated back to the original format, so they
    keep their extension.
    """
    suffix = LANGUAGE_SUFFIXES.get(language, "pl")
    path = Path(input_path)
    return str(path.with_name(f"{path.stem}_{suffix}{path.suffix}"))
