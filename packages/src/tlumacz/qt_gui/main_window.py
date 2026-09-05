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

from ..glossary import Glossary
from ..i18n import t, set_language, get_language, Language
from ..preprocess import DEFAULT_SKIP_PATTERNS
from ..server import SERVER_MODEL_ALIAS, LlamaServer, ServerConfig
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
from .theme import apply_theme
from .worker import ServerManager, ServerState, TranslationThread

try:  # optional; only used when the managed server is running
    from ..server import LlamaServer, ServerConfig
except ImportError:  # pragma: no cover
    LlamaServer = None  # type: ignore[assignment,misc]
    ServerConfig = None  # type: ignore[assignment,misc]

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
        # --- ServerManager: centralny zarządca serwera ---
        self._server_starting_up = False  # rozróżnia auto-start od restartu
        self._server_manager = self._create_server_manager(server)
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
        self._config_file_present = (config_dir() / "config.json").is_file()

        self._build_ui()
        self._load_settings_into_ui()
        self._loading = False
        self._set_idle_state()
        # Auto-start serwera po zbudowaniu UI (log_view musi istnieć)
        if (server is None and self._settings.auto_start_server
                and self._settings.server_gguf_path):
            self._server_starting_up = True
            self._append_log("Uruchamianie serwera lokalnego...")
            self._server_manager.start()
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

    def _create_server_manager(self, server: object | None) -> ServerManager:
        """Utwórz i skonfiguruj ServerManager.

        Jeśli przekazano istniejący serwer (np. z CLI), użyj go bezpośrednio.
        W przeciwnym razie utwórz konfigurację z ustawień i połącz sygnały.
        """
        if server is not None:
            # Przekazany serwer — utwórz manager w stanie RUNNING
            manager = ServerManager()
            manager.server = server
            # Ustaw stan na RUNNING bez uruchamiania
            manager._state = ServerState.RUNNING
        else:
            # Utwórz konfigurację z ustawień aplikacji
            config = self._build_server_config()
            manager = ServerManager(config)

        # Połącz sygnały ServerManager z callbackami GUI
        manager.server_started.connect(self._on_server_started)
        manager.server_stopped.connect(self._on_server_stopped)
        manager.server_error.connect(self._on_server_error)
        manager.operation_finished.connect(self._on_operation_finished)

        return manager

    def _build_server_config(self) -> "ServerConfig | None":
        """Zbuduj ServerConfig z aktualnych ustawień.

        Zwraca None jeśli nie wskazano pliku GGUF (brak zarządzanego serwera).
        """
        if ServerConfig is None or not self._settings.server_gguf_path:
            return None
        return ServerConfig(
            gguf_path=self._settings.server_gguf_path,
            port=self._settings.server_port,
            compute_mode=self._settings.server_compute_mode,
            chat_template=self._settings.server_chat_template or "",
            parallel=1,
        )

    def _build_config_updates(self) -> dict:
        """Zbuduj słownik config_updates dla restartu serwera z aktualnych ustawień GUI."""
        settings = self._collect_settings()
        return {
            "port": settings.server_port,
            "parallel": 1,
            "compute_mode": settings.server_compute_mode,
            "gguf_path": settings.server_gguf_path,
            "chat_template": settings.server_chat_template or "",
        }

    def _on_server_started(self, base_url: str) -> None:
        """Callback: serwer uruchomiony pomyślnie."""
        self.base_url.setText(base_url)
        # Ustaw model na "local" w combo box
        local_index = self.model.findText(SERVER_MODEL_ALIAS)
        if local_index >= 0:
            self.model.setCurrentIndex(local_index)
        else:
            self.model.setEditText(SERVER_MODEL_ALIAS)
        self._update_restart_button_label()

        if self._server_starting_up:
            # Auto-start przy uruchomieniu programu — tylko log
            self._server_starting_up = False
            self._append_log(f"Serwer lokalny uruchomiony: {base_url}")
        else:
            # Restart lub ręczne uruchomienie — pokaż komunikat
            self._append_log(f"Serwer lokalny uruchomiony: {base_url}")
            QMessageBox.information(
                self, "Serwer lokalny", "Serwer został pomyślnie uruchomiony."
            )

    def _on_server_stopped(self) -> None:
        """Callback: serwer zatrzymany."""
        self._update_restart_button_label()
        self._append_log("Serwer lokalny zatrzymany.")

    def _on_server_error(self, message: str) -> None:
        """Callback: błąd operacji na serwerze."""
        self._update_restart_button_label()
        self._append_log(f"BŁĄD serwera: {message}")
        if self._server_starting_up:
            self._server_starting_up = False
        QMessageBox.critical(
            self, "Serwer lokalny", f"Błąd operacji na serwerze:\n{message}"
        )

    def _on_operation_finished(self) -> None:
        """Callback: zakończono operację na serwerze (start/stop/restart)."""
        self._update_restart_button_label()

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
        layout.addLayout(language_row)

        self.help_view = QTextBrowser()
        self.help_view.setObjectName("helpView")
        self.help_view.setOpenExternalLinks(True)
        layout.addWidget(self.help_view, 1)

        self._update_help()
        return tab

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
        # Etykiety server - iteruj po wierszach QFormLayout
        server_keys = [
            "settings.port", "settings.compute_mode",
            "settings.gguf_path", "settings.chat_template",
            "settings.parallel",
        ]
        for row_idx, key in enumerate(server_keys):
            item = self.server_form.itemAt(row_idx, QFormLayout.ItemRole.LabelRole)
            if item and item.widget():
                item.widget().setText(t(key))
        # Serwer
        self.restart_server_btn.setText(t("button.restart_server"))
        self.gguf_browse.setText(t("button.browse"))
        # Checkboxy server
        self.auto_start_server.setText(t("settings.auto_start"))
        self.cache_clear_after_translation.setText(t("settings.clear_cache"))
        # ComboBox chat template - przebuduj items
        self.server_chat_template.clear()
        self.server_chat_template.addItem(t("settings.chat_jinja"), "")
        self.server_chat_template.addItem(t("settings.chat_chatml"), "chatml")
        self.server_chat_template.addItem(t("settings.chat_translategemma"), "translategemma")
        # Przyciski glosariusza
        self.glossary_browse.setText(t("button.browse"))
        self.add_entry_btn.setText(t("button.add_entry"))
        self.glossary_count_label.setText(t("glossary.no_file"))
        # Przyciski skilli
        self.refresh_skills_btn.setText(t("button.refresh"))
        self.import_skill_btn.setText(t("button.import_skill"))
        self.new_skill_btn.setText(t("button.new_skill"))

    def _help_text_pl(self) -> str:
        return """
<h2>Tłumacz — pomoc</h2>
<p>Tłumacz to narzędzie do tłumaczenia dokumentów (Markdown, TXT, HTML,
PDF, DOCX, ODT, EPUB) za pomocą modeli LLM zgodnych z API OpenAI.
Pliki EPUB, DOCX, ODT i PDF są tłumaczone z zachowaniem oryginalnego formatu.</p>

<h3>1. Konfiguracja modelu (zakładka „Ustawienia”)</h3>
<ul>
<li><b>Base URL</b> — adres serwera zgodnego z API OpenAI,
np. <code>http://127.0.0.1:8080/v1</code> dla lokalnego llama.cpp/ollama.</li>
<li><b>API key</b> — token uwierzytelniający wysyłany jako
<code>Authorization: Bearer</code>. Lokalne serwery zwykle go ignorują
(domyślny placeholder <code>ollama</code>); przy zdalnych usługach wpisz
tu swój klucz.</li>
<li><b>Model</b> — nazwa modelu dostępna na serwerze.</li>
<li><b>Rozmiar bloku</b> — wielkość fragmentu tekstu wysyłanego do modelu.</li>
<li><b>Temperatura</b> — stopień losowości odpowiedzi (niżej = bardziej
deterministycznie).</li>
<li><b>Język docelowy</b> — język, na który ma być tłumaczony tekst.</li>
<li><b>Własny prompt</b> — opcjonalny prompt zastępujący domyślny
(styl, terminologia, ton); glosariusz i skille są dodawane niezależnie.</li>
</ul>

<h3>2. Serwer lokalny</h3>
<p>Program może sam uruchomić serwer llama.cpp: wskaż plik <code>.gguf</code>
i port, a następnie zaznacz „Uruchamiaj serwer razem z programem”.
Jeśli używasz własnego serwera, zostaw pole GGUF puste.</p>

<h3>3. Glosariusz</h3>
<p>Plik CSV dwukolumnowy <code>źródło,tłumaczenie</code>. Wpisy wymuszają
stałe tłumaczenia dla wybranych terminów. Nagłówek (<code>source,target</code>
lub <code>Pattern,Substitution</code>) oraz prefiks <code>#</code>
w tłumaczeniu są obsługiwane automatycznie. Wpisy można dodawać też
przyciskiem „Dodaj wpis”.</p>

<h3>4. Skille</h3>
<p>Instrukcje dla modelu dopasowane do formatu pliku (Markdown, TXT, HTML).
Włącz skille, których używasz — instrukcje pasującego skilla zostaną
wstrzyknięte do promptu podczas tłumaczenia. Własne skille możesz dodać
przyciskiem <b>„Nowy skilla..."</b> (kopiuje szablon) albo jako pliki
<code>.md</code> w <code>~/.config/tlumacz/skills/</code>.
Frontmatter: <code>name</code> (nazwa), <code>formats</code>
(rozszerzenia oddzielone przecinkiem), opcjonalnie <code>skip_patterns</code>
(regexy linii nietłumaczonych dla tego formatu). Skilla użytkownika
o tej samej nazwie zastępuje wbudowany.</p>

<h3>5. Motyw</h3>
<p>Motyw „Systemowy” podąża za kolorem pulpitu; możesz też wymusić
jasny lub ciemny.</p>

<h3>6. Plik konfiguracji</h3>
<p>Ustawienia są zapisywane w
<code>~/.config/tlumacz/config.json</code>. Pola: <code>base_url</code>,
<code>api_key</code>, <code>model</code>, <code>chunk_size</code>,
<code>temperature</code>, <code>target_language</code>, <code>theme</code>,
<code>glossary_path</code>, <code>system_prompt</code>,
<code>enabled_skills</code>, <code>skip_line_patterns</code>,
<code>server_port</code>, <code>server_gguf_path</code>,
<code>server_chat_template</code>, <code>server_parallel</code>,
<code>auto_start_server</code>, <code>model_profiles</code>, <code>last_input</code>,
<code>last_output</code>.</p>
<p>Uszkodzony plik lub pola o błędnym typie są naprawiane wartościami
domyślnymi, a program pokazuje stosowny komunikat. Przycisk
„Przywróć domyślne" zapisuje kopię zapasową i wraca do ustawień
domyślnych (zachowując ścieżki plików i glosariusza).</p>

<h3>7. Tabela parametrów</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Parametr</th><th>Co robi</th><th>Ile ustawić</th><th>Dlaczego</th></tr>
<tr><td>Base URL</td><td>Adres serwera API zgodnego z OpenAI.</td>
<td>np. <code>http://127.0.0.1:18080/v1</code></td>
<td>Serwer musi być osiągalny i mówić po protokole OpenAI.</td></tr>
<tr><td>API key</td><td>Token <code>Authorization: Bearer</code>.</td>
<td><code>ollama</code> przy lokalnym serwerze</td>
<td>Lokalne serwery ignorują klucz; zdalne wymagają prawdziwego.</td></tr>
<tr><td>Model</td><td>Nazwa modelu na serwerze.</td>
<td>np. <code>local</code> przy własnym serwerze</td>
<td>Musi być dostępny na wskazanym serwerze.</td></tr>
<tr><td>Rozmiar bloku</td><td>Wielkość fragmentu tekstu w jednym wywołaniu (znaki).</td>
<td><b>4000–6000</b></td>
<td>Mniejszy = lepszy kontekst sekcji, ale więcej wywołań;
większy = mniej wywołań, ale ryzyko obcięcia i utraty spójności.</td></tr>
<tr><td>Temperatura</td><td>Losowość odpowiedzi modelu.</td>
<td><b>0.1–0.3</b></td>
<td>Niska = wierne, deterministyczne tłumaczenie; wyższa = swobodny styl.</td></tr>
<tr><td>Język docelowy</td><td>Język wyniku tłumaczenia.</td>
<td>Twój język</td>
<td>Tekst już w tym języku jest zwracany bez zmian.</td></tr>
<tr><td>Własny prompt</td><td>Zamienia domyślny prompt tłumaczenia.</td>
<td>opcjonalnie</td>
<td>Styl, terminologia, ton; glosariusz i skille dodawane niezależnie.</td></tr>
<tr><td>Pomijane linie (regex)</td><td>Linie, których nie tłumaczymy.</td>
<td>puste (auto)</td>
<td>Zaawansowane; zwykle niepotrzebne — wzorce pochodzą ze skilla formatu.</td></tr>
<tr><td>Glosariusz</td><td>Plik CSV <code>źródło,tłumaczenie</code>.</td>
<td>opcjonalnie</td>
<td>Wymusza stałe tłumaczenia wybranych terminów.</td></tr>
<tr><td>Skille</td><td>Instrukcje dla modelu per format pliku.</td>
<td>zaznacz używane</td>
<td>Automatyczne dopasowanie po rozszerzeniu pliku wejściowego.</td></tr>
<tr><td>Port</td><td>Port serwera lokalnego.</td>
<td>np. <b>18080</b></td>
<td>Musi być wolny; różny od portów innych usług.</td></tr>
<tr><td>Plik modelu (GGUF)</td><td>Model uruchamiany samodzielnie przez program.</td>
<td>ścieżka do <code>.gguf</code></td>
<td>Puste = używasz własnego serwera (Base URL).</td></tr>
<tr><td>Szablon czatu</td><td>Sposób formatowania rozmowy z modelem.</td>
<td>Auto (jinja), dla transl. gemma: chatml</td>
<td>chatml rozwiązuje modele z uszkodzonym szablonem jinja.</td></tr>
<tr><td>Równoległość (parallel)</td><td>Liczba równoległych slotów llama-server.</td>
<td><b>1–8</b></td>
<td>Większa wartość pozwala obsługiwać kilka bloków jednocześnie, ale zwiększa zużycie zasobów.</td></tr>
<tr><td>Motyw</td><td>Wygląd okna.</td>
<td>system / jasny / ciemny</td>
<td>Kwestia preferencji; „system" podąża za pulpitem.</td></tr>
<tr><td>Auto-start serwera</td><td>Uruchamia llama.cpp razem z programem.</td>
<td>włącz przy użyciu GGUF</td>
<td>Wyłącz, gdy używasz własnego, już działającego serwera.</td></tr>
</table>

<h3>8. Formaty binarne — wynik w oryginalnym formacie</h3>
<p>Od wersji 0.19 pliki <b>EPUB, DOCX i ODT</b> są tłumaczone z zachowaniem
formatu 1:1 — wynik ma to samo rozszerzenie co plik wejściowy
(<code>.epub</code>, <code>.docx</code>, <code>.odt</code>). Tłumaczony jest
tylko tekst wewnątrz dokumentu; struktura, style, tabele i pozostałe pliki
archiwum (obrazki, czcionki, ustawienia) zostają nietknięte.</p>
<p><b>PDF</b> — tłumaczenie tekstowe z zachowaniem układu strony.
Tekst jest wyodrębniany z pozycjami (PyMuPDF), tłumaczony i wstawiany
z powrotem w oryginalnych pozycjach z zachowaniem rozmiaru czcionki.
Obrazki i inne elementy nietekstowe są zachowywane. OCR nie jest
obsługiwane (tylko tekstowe PDF).</p>
"""

    def _help_text_en(self) -> str:
        return """
<h2>Tłumacz — help</h2>
<p>Tłumacz is a tool for translating documents (Markdown, TXT, HTML,
PDF, DOCX, ODT, EPUB) using LLM models that speak the OpenAI-compatible API.
EPUB, DOCX, ODT and PDF files are translated while keeping the original format.</p>

<h3>1. Model setup (Settings tab)</h3>
<ul>
<li><b>Base URL</b> — address of an OpenAI-compatible server,
e.g. <code>http://127.0.0.1:8080/v1</code> for local llama.cpp/ollama.</li>
<li><b>API key</b> — authentication token sent as
<code>Authorization: Bearer</code>. Local servers usually ignore it
(the default <code>ollama</code> placeholder); for remote services put
your real key here.</li>
<li><b>Model</b> — the model name available on the server.</li>
<li><b>Chunk size</b> — how large a piece of text is sent to the model.</li>
<li><b>Temperature</b> — response randomness (lower = more deterministic).</li>
<li><b>Target language</b> — the language to translate into.</li>
<li><b>Custom prompt</b> — optional prompt replacing the default one
(style, terminology, tone); glossary and skills are appended on top.</li>
</ul>

<h3>2. Local server</h3>
<p>The app can start a llama.cpp server itself: pick a <code>.gguf</code>
file and a port, then tick “start the server with the app”.
Leave the GGUF field empty when using your own server.</p>

<h3>3. Glossary</h3>
<p>A two-column CSV file <code>source,translation</code>. Entries enforce
fixed translations for chosen terms. A header row
(<code>source,target</code> or <code>Pattern,Substitution</code>) and a
<code>#</code> prefix in the translation are handled automatically.
Entries can also be added with the “Add entry” button.</p>

<h3>4. Skills</h3>
<p>Model instructions matched to the file format (Markdown, TXT, HTML).
Enable the skills you use — the instructions of a matching skill are
injected into the prompt during translation. You can add your own skills
with the <b>“New skill...”</b> button (copies a template) or as
<code>.md</code> files in <code>~/.config/tlumacz/skills/</code>.
Frontmatter: <code>name</code> (name), <code>formats</code>
(extensions separated by commas), optionally <code>skip_patterns</code>
(regexes of lines not to translate for this format). A user skill with
the same name as a bundled one replaces it.</p>

<h3>5. Theme</h3>
<p>“System” follows the desktop color scheme; you can force light or dark.</p>

<h3>6. Configuration file</h3>
<p>Settings are stored in <code>~/.config/tlumacz/config.json</code>.
Fields: <code>base_url</code>, <code>api_key</code>, <code>model</code>,
<code>chunk_size</code>, <code>temperature</code>,
<code>target_language</code>, <code>theme</code>, <code>glossary_path</code>,
<code>system_prompt</code>, <code>enabled_skills</code>,
<code>skip_line_patterns</code>, <code>server_port</code>,
<code>server_gguf_path</code>, <code>server_chat_template</code>,
<code>auto_start_server</code>, <code>last_input</code>,
<code>last_output</code>.</p>
<p>A corrupt file or wrong-typed fields are repaired with defaults and the
app shows a message about it. The “Restore defaults” button saves a backup
copy and returns to the default settings (keeping file and glossary paths).</p>

<h3>7. Parameter table</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Parameter</th><th>What it does</th><th>Recommended</th><th>Why</th></tr>
<tr><td>Base URL</td><td>Address of an OpenAI-compatible server.</td>
<td>e.g. <code>http://127.0.0.1:18080/v1</code></td>
<td>The server must be reachable and speak the OpenAI protocol.</td></tr>
<tr><td>API key</td><td><code>Authorization: Bearer</code> token.</td>
<td><code>ollama</code> for local servers</td>
<td>Local servers ignore the key; remote ones need a real one.</td></tr>
<tr><td>Model</td><td>Model name available on the server.</td>
<td>e.g. <code>local</code> with the managed server</td>
<td>Must exist on the configured server.</td></tr>
<tr><td>Chunk size</td><td>Size of the text fragment sent in one call (chars).</td>
<td><b>4000–6000</b></td>
<td>Smaller = better section context but more calls;
larger = fewer calls but risk of truncation and lost coherence.</td></tr>
<tr><td>Temperature</td><td>Response randomness.</td>
<td><b>0.1–0.3</b></td>
<td>Low = faithful, deterministic translation; higher = freer style.</td></tr>
<tr><td>Target language</td><td>Output language of the translation.</td>
<td>Your language</td>
<td>Text already in this language is returned unchanged.</td></tr>
<tr><td>Custom prompt</td><td>Replaces the default translation prompt.</td>
<td>optional</td>
<td>Style, terminology, tone; glossary and skills are added on top.</td></tr>
<tr><td>Skip lines (regex)</td><td>Lines that are not translated.</td>
<td>empty (auto)</td>
<td>Advanced; usually unnecessary — patterns come from the format skill.</td></tr>
<tr><td>Glossary</td><td>CSV file <code>source,translation</code>.</td>
<td>optional</td>
<td>Enforces fixed translations for chosen terms.</td></tr>
<tr><td>Skills</td><td>Model instructions per file format.</td>
<td>tick the ones you use</td>
<td>Automatically matched by the input file extension.</td></tr>
<tr><td>Port</td><td>Port of the local server.</td>
<td>e.g. <b>18080</b></td>
<td>Must be free and distinct from other services.</td></tr>
<tr><td>Model file (GGUF)</td><td>Model started automatically by the app.</td>
<td>path to a <code>.gguf</code></td>
<td>Empty = you use your own server (Base URL).</td></tr>
<tr><td>Chat template</td><td>How the conversation is formatted.</td>
<td>Auto (jinja); chatml for transl. gemma</td>
<td>chatml fixes models with a broken jinja template.</td></tr>
<tr><td>Theme</td><td>Window appearance.</td>
<td>system / light / dark</td>
<td>Preference; “system” follows the desktop.</td></tr>
<tr><td>Auto-start server</td><td>Starts llama.cpp together with the app.</td>
<td>on when using a GGUF</td>
<td>Turn off when using your own running server.</td></tr>
</table>

<h3>8. Binary formats — result in the original format</h3>
<p>Since v0.19 the <b>EPUB, DOCX and ODT</b> files are translated while keeping
the original format 1:1 — the result keeps the same extension as the input
(<code>.epub</code>, <code>.docx</code>, <code>.odt</code>). Only the text
inside the document is translated; the structure, styles, tables and all other
archive files (images, fonts, settings) stay untouched.</p>
<p><b>PDF</b> — text translation preserving page layout. Text is extracted
with positions (PyMuPDF), translated and inserted back at original positions
preserving font size. Images and other non-text elements are preserved.
OCR is not supported (text PDFs only).</p>
"""

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
            "- Cloud models: skonfigurowane modele chmurowe\n"
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

        self.server_port.setToolTip(
            "Port, na którym ma nasłuchiwać serwer lokalny.\n"
            "Musi być wolny i różny od innych usług (np. 18080)."
        )

        gguf_row = QHBoxLayout()
        self.server_gguf_path = QLineEdit()
        self.server_gguf_path.setObjectName("serverGgufPath")
        self.server_gguf_path.setPlaceholderText(
            "Ścieżka do pliku modelu .gguf (opcjonalnie)"
        )
        self.server_gguf_path.setToolTip(
            "Ścieżka do pliku modelu .gguf uruchamianego samodzielnie.\n"
            "Puste = korzystasz z własnego serwera (Base URL)."
        )
        self.gguf_browse = QPushButton(t("button.browse"))
        self.gguf_browse.clicked.connect(self._on_browse_gguf)
        gguf_row.addWidget(self.server_gguf_path, 1)
        gguf_row.addWidget(self.gguf_browse)

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
        self.server_chat_template.addItem(t("settings.chat_translategemma"), "translategemma")
        self.server_chat_template.setToolTip(
            "Szablon czatu używany przy starcie serwera.\n"
            "jinja = natywny szablon modelu — zwykle działa.\n"
            "chatml = dla modeli, których szablon jinja jest nieprawidłowy.\n"
            "translategemma = dla modelu TranslateGemma (kody języków)."
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

        row = 0
        self.server_form.addRow(t("settings.port"), self.server_port)
        self._server_label_keys[row] = "settings.port"; row += 1
        self.server_form.addRow(t("settings.compute_mode"), self.server_compute_mode)
        self._server_label_keys[row] = "settings.compute_mode"; row += 1
        self.server_form.addRow(t("settings.gguf_path"), gguf_row)
        self._server_label_keys[row] = "settings.gguf_path"; row += 1
        self.server_form.addRow(t("settings.chat_template"), self.server_chat_template)
        self._server_label_keys[row] = "settings.chat_template"; row += 1
        self.server_form.addRow(t("settings.parallel"), self.server_parallel)
        self._server_label_keys[row] = "settings.parallel"; row += 1
        self.server_form.addRow(self.auto_start_server)
        self.server_form.addRow(self.cache_clear_after_translation)

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
        # Gdy serwer zarządzany, wymuś "local"
        if self._server is not None:
            model = SERVER_MODEL_ALIAS

        return TranslatorConfig(
            base_url=self.base_url.text().strip(),
            api_key=self.api_key.text().strip(),
            model=model,
            chat_template_kwargs=(
                {"enable_thinking": False}
                if self._server is not None
                else None
            ),
            chunk_size=self.chunk_size.value(),
            temperature=self.temperature.value(),
            parallel=self.server_parallel.value(),
            target_language=self.language.currentData() or "wykryj do pl",
            glossary_path=self.glossary_path.text().strip() or None,
            system_prompt=self.prompt_edit.toPlainText().strip() or None,
            enabled_skills=self._enabled_skill_names(),
            skip_line_patterns=self._skip_pattern_list(),
            cache_clear_after_translation=self.cache_clear_after_translation.isChecked(),
        )

    def _collect_settings(self) -> AppSettings:
        model = self.model.currentText().strip()
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
        settings.server_port = self.server_port.value()
        settings.server_compute_mode = self.server_compute_mode.currentData()
        settings.server_gguf_path = self.server_gguf_path.text().strip()
        settings.server_chat_template = self.server_chat_template.currentData()
        settings.server_parallel = self.server_parallel.value()
        settings.auto_start_server = self.auto_start_server.isChecked()
        settings.cache_clear_after_translation = self.cache_clear_after_translation.isChecked()
        return settings

    def _populate_model_combo(self) -> None:
        """Wypełnij combo box modelami: cloud + LOCAL + puste pole."""
        self.model.clear()
        # Dodaj cloud models
        for cloud_model in CLOUD_MODELS_CONFIG:
            self.model.addItem(cloud_model["name"], cloud_model)
        # Dodaj separator
        self.model.insertSeparator(self.model.count())
        # Dodaj LOCAL
        self.model.addItem("LOCAL", {"name": "LOCAL"})
        # Dodaj puste pole dla ręcznego wprowadzania
        self.model.addItem("", None)

    def _on_model_changed(self, model_name: str) -> None:
        """Obsługa zmiany modelu — automatyczne ustawienie base_url i api_key."""
        if self._loading:
            return

        # Sprawdź czy to cloud model
        cloud_config = None
        for item in CLOUD_MODELS_CONFIG:
            if item["name"] == model_name:
                cloud_config = item
                break

        if cloud_config:
            # Cloud model — ustaw base_url z konfiguracji
            self.base_url.setText(cloud_config["base_url"])
            # Zachowaj api_key z ustawień (użytkownik musi wpisać swój klucz)
        elif model_name == "LOCAL":
            # LOCAL — przywróć ostatnie ustawienia lokalne
            self.base_url.setText(self._settings.last_local_base_url)
            self.api_key.setText(self._settings.last_local_api_key)
        # else: puste pole lub własny model — nie zmieniaj base_url/api_key

    def _load_settings_into_ui(self) -> None:
        s = self._settings
        self.base_url.setText(s.base_url)
        if self._server is not None:
            server_url = self._server.config.base_url
            self.base_url.setText(server_url)
            self._append_log(f"Własny serwer uruchomiony: {server_url}")
        self.api_key.setText(s.api_key)
        # Ustaw model w combo box
        model_text = SERVER_MODEL_ALIAS if self._server is not None else s.model
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
        self.server_port.setValue(s.server_port)
        mode_index = self.server_compute_mode.findData(s.server_compute_mode)
        self.server_compute_mode.setCurrentIndex(mode_index if mode_index >= 0 else 0)
        self.server_gguf_path.setText(s.server_gguf_path)
        template_index = self.server_chat_template.findData(s.server_chat_template)
        self.server_chat_template.setCurrentIndex(template_index)
        self.server_parallel.setValue(s.server_parallel)
        self.auto_start_server.setChecked(s.auto_start_server)
        self.cache_clear_after_translation.setChecked(s.cache_clear_after_translation)

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
        else:
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
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

    def _on_browse_gguf(self) -> None:
        path = self._browse_file(
            "Wybierz plik modelu (GGUF)",
            self.server_gguf_path.text(),
            "GGUF files (*.gguf);;Wszystkie pliki (*)",
        )
        if path:
            self.server_gguf_path.setText(path)
            save_settings(self._collect_settings())

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
        """Update restart button label, tooltip and enabled state.

        Logic depends on 2 factors:
        - Server running state (is_running)
        - Auto-start checkbox state (auto_start_server.isChecked())

        4 cases:
        1. Running + box checked  → "Restart serwera"
        2. Running + box unchecked → "Zatrzymaj serwer"
        3. Stopped + box checked   → "Uruchom serwer"
        4. Stopped + box unchecked → info message (still enabled!)
        """
        box_checked = self.auto_start_server.isChecked()
        is_running = self._server_manager.is_running

        if is_running and box_checked:
            self.restart_server_btn.setText(t("button.restart_server"))
            self.restart_server_btn.setToolTip(
                "Zatrzymaj zarządzany llama-server i uruchom go ponownie "
                "z aktualnymi ustawieniami."
            )
        elif is_running and not box_checked:
            self.restart_server_btn.setText(t("button.stop_server"))
            self.restart_server_btn.setToolTip(
                "Zatrzymaj zarządzany llama-server."
            )
        elif not is_running and box_checked:
            self.restart_server_btn.setText(t("button.start_server"))
            self.restart_server_btn.setToolTip(
                "Uruchom zarządzany llama-server z aktualnymi ustawieniami."
            )
        else:  # not is_running and not box_checked
            self.restart_server_btn.setText(
                t("button.check_auto_start")
            )
            self.restart_server_btn.setToolTip(
                "Aby uruchomić serwer, zaznacz opcję "
                "„Uruchamiaj serwer razem z programem”."
            )
        # Przycisk ZAWSZE aktywny
        self.restart_server_btn.setEnabled(True)

    def _on_restart_server(self) -> None:
        """Handle the smart restart button based on server state and auto-start checkbox.

        4 cases:
        1. Running + box checked  → restart (stop + start)
        2. Running + box unchecked → stop only
        3. Stopped + box checked   → start
        4. Stopped + box unchecked → show info message
        """
        logger.info("_on_restart_server() called")
        box_checked = self.auto_start_server.isChecked()
        is_running = self._server_manager.is_running

        # Case 4: Stopped + box unchecked → show info message
        if not is_running and not box_checked:
            QMessageBox.information(
                self,
                "Serwer lokalny",
                "Aby uruchomić serwer, zaznacz opcję "
                "„Uruchamiaj serwer razem z programem”.",
            )
            return

        # Stop any active translation thread
        if self._is_thread_running(self._thread):
            logger.info("_on_restart_server(): stopping active translation thread")
            self._append_log("Zatrzymywanie aktywnego tłumaczenia...")
            if not self._thread.stop():
                self._append_log("Worker nie zakończył się łagodnie.")
        self._thread = None

        # Check if operation already in progress
        if self._server_manager.state in (ServerState.STARTING, ServerState.STOPPING):
            logger.info("_on_restart_server(): operation already in progress")
            self._append_log("Operacja na serwerze już trwa.")
            return

        # Create server if it doesn't exist
        if self._server_manager.server is None:
            logger.info("_on_restart_server(): creating server from settings")
            settings = self._collect_settings()
            server = LlamaServer(
                ServerConfig(
                    port=settings.server_port,
                    parallel=settings.server_parallel,
                    compute_mode=settings.server_compute_mode,
                    gguf_path=settings.server_gguf_path,
                    chat_template=settings.server_chat_template or "",
                )
            )
            self._server_manager.server = server
            self._server_manager._state = ServerState.IDLE

        # Save settings
        settings = self._collect_settings()
        save_settings(settings)
        config_updates = self._build_config_updates()

        # Case 1: Running + box checked → restart
        if is_running and box_checked:
            logger.info("_on_restart_server(): case 1 - restart")
            self.restart_server_btn.setEnabled(False)
            self._append_log("Restart llama-server...")
            self._server_manager.restart(config_updates)

        # Case 2: Running + box unchecked → stop
        elif is_running and not box_checked:
            logger.info("_on_restart_server(): case 2 - stop")
            self.restart_server_btn.setEnabled(False)
            self._append_log("Zatrzymywanie llama-server...")
            self._server_manager.stop()

        # Case 3: Stopped + box checked → start
        elif not is_running and box_checked:
            logger.info("_on_restart_server(): case 3 - start")
            self.restart_server_btn.setEnabled(False)
            self._append_log("Uruchamianie llama-server...")
            self._server_manager.restart(config_updates)

        logger.info("_on_restart_server(): delegated to ServerManager")

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

        # Zaznacz pasujący skill
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
        # Zapisz ustawienia i deleguj restart do ServerManager
        settings = self._collect_settings()
        save_settings(settings)
        config_updates = self._build_config_updates()
        self._append_log("llama-server po anulowaniu nie odpowiada — ponowne uruchamianie...")
        self._server_manager.restart(config_updates)

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
        """Zatrzymaj i wyczyść thread po zakończeniu tłumaczenia."""
        thread = self._thread
        if thread is not None:
            # Zatrzymaj thread (cancel + quit + wait)
            thread.stop()
            self._thread = None

    def _show_preview(self, output_path: str) -> None:
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                self.preview_view.setPlainText(f.read())
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
