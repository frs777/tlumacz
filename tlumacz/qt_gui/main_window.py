"""Main window for the Tłumacz GUI.

Tabs (top to bottom):
1. Tłumaczenie — input/output files, translate/cancel, progress, log, preview
2. Ustawienia — API settings, local server, glossary, skills
3. Pomoc — short help in Polish and English
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..core import TranslatorConfig
from ..glossary import Glossary
from ..skill import discover_skills
from .config import AppSettings, load_settings, save_settings
from .theme import apply_theme
from .worker import TranslationThread

try:  # optional; only used when the managed server is running
    from ..server import LlamaServer, ServerConfig
except ImportError:  # pragma: no cover
    LlamaServer = None  # type: ignore[assignment,misc]
    ServerConfig = None  # type: ignore[assignment,misc]

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

THEME_CHOICES = [
    ("Systemowy", "system"),
    ("Jasny", "light"),
    ("Ciemny", "dark"),
]

# Upper bound scanned when displaying the glossary entry count, so huge
# dictionaries do not freeze the UI during startup.
_GLOSSARY_COUNT_SCAN = 50_000

LANGUAGE_SUFFIXES = {
    "Polish": "pl",
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

    def __init__(self, server: object | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Tłumacz")
        self.resize(900, 720)

        self._settings, config_warning = load_settings()
        self._server = server
        self._thread: TranslationThread | None = None
        self._skills = discover_skills()
        self._skill_checkboxes: list[QCheckBox] = []

        self._build_ui()
        self._load_settings_into_ui()
        self._set_idle_state()
        if config_warning:
            QMessageBox.warning(self, "Konfiguracja", config_warning)

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
        self.translate_btn = QPushButton("Tłumacz")
        self.translate_btn.setObjectName("translateBtn")
        self.translate_btn.clicked.connect(self._on_translate)
        self.cancel_btn = QPushButton("Anuluj")
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
        self.tabs.addTab(translation_tab, "Tłumaczenie")

        # --- Tab: Ustawienia --------------------------------------------------
        settings_tab = QWidget()
        s_layout = QVBoxLayout(settings_tab)
        s_layout.addWidget(self._build_settings_group())
        s_layout.addWidget(self._build_server_group())
        s_layout.addWidget(self._build_glossary_group())
        s_layout.addWidget(self._build_skills_group())
        s_layout.addStretch(1)
        self.tabs.addTab(settings_tab, "Ustawienia")

        # --- Tab: Pomoc --------------------------------------------------------
        self.tabs.addTab(self._build_help_tab(), "Pomoc")

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

    def _build_glossary_group(self) -> QGroupBox:
        box = QGroupBox("Glosariusz (opcjonalny)")
        layout = QVBoxLayout(box)

        file_row = QHBoxLayout()
        self.glossary_path = QLineEdit()
        self.glossary_path.setObjectName("glossaryPath")
        self.glossary_path.setPlaceholderText("Ścieżka do pliku CSV (źródło,tłumaczenie)")
        self.glossary_path.editingFinished.connect(self._on_glossary_path_edited)
        glossary_browse = QPushButton("Przeglądaj...")
        glossary_browse.clicked.connect(self._on_browse_glossary)
        file_row.addWidget(self.glossary_path, 1)
        file_row.addWidget(glossary_browse)
        layout.addLayout(file_row)

        entry_row = QHBoxLayout()
        self.glossary_term = QLineEdit()
        self.glossary_term.setObjectName("glossaryTerm")
        self.glossary_term.setPlaceholderText("Termin (źródło)")
        self.glossary_target = QLineEdit()
        self.glossary_target.setObjectName("glossaryTarget")
        self.glossary_target.setPlaceholderText("Tłumaczenie")
        add_entry = QPushButton("Dodaj wpis")
        add_entry.setObjectName("addGlossaryBtn")
        add_entry.clicked.connect(self._on_add_glossary_entry)
        entry_row.addWidget(self.glossary_term, 1)
        entry_row.addWidget(self.glossary_target, 1)
        entry_row.addWidget(add_entry)
        layout.addLayout(entry_row)

        self.glossary_count_label = QLabel("Brak pliku")
        self.glossary_count_label.setObjectName("glossaryCount")
        layout.addWidget(self.glossary_count_label)
        return box

    def _build_skills_group(self) -> QGroupBox:
        box = QGroupBox("Skille (formaty tłumaczeń)")
        layout = QVBoxLayout(box)

        if not self._skills:
            layout.addWidget(QLabel("Brak dostępnych skilli."))
            return box

        for skill in self._skills:
            checkbox = QCheckBox(
                f"{skill.name} — {', '.join(skill.formats)}"
            )
            checkbox.setObjectName(f"skill_{skill.name}")
            checkbox.toggled.connect(self._on_skills_changed)
            self._skill_checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        return box

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
        if self.help_language.currentData() == "en":
            content = self._help_text_en()
        else:
            content = self._help_text_pl()
        self.help_view.setHtml(content)

    def _help_text_pl(self) -> str:
        return """
<h2>Tłumacz — pomoc</h2>
<p>Tłumacz to narzędzie do tłumaczenia dokumentów (Markdown, TXT, HTML)
za pomocą modeli LLM zgodnych z API OpenAI.</p>

<h3>1. Konfiguracja modelu (zakładka „Ustawienia”)</h3>
<ul>
<li><b>Base URL</b> — adres serwera zgodnego z API OpenAI,
np. <code>http://127.0.0.1:8080/v1</code> dla lokalnego llama.cpp/ollama.</li>
<li><b>API key</b> — token uwierzytelniający wysyłany jako
<code>Authorization: Bearer</code>. Lokalne serwery zwykle go ignorują
(domyślny placeholder <code>ollama</code>); przy zdalnych usługach wpisz
tu swój klucz.</li>
<li><b>Model</b> — nazwa modelu dostępna na serwerze.</li>
<li><b>Rozmiar chunka</b> — wielkość fragmentu tekstu wysyłanego do modelu.</li>
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
wstrzyknięte do promptu podczas tłumaczenia.</p>

<h3>5. Motyw</h3>
<p>Motyw „Systemowy” podąża za kolorem pulpitu; możesz też wymusić
jasny lub ciemny.</p>

<h3>6. Plik konfiguracji</h3>
<p>Ustawienia są zapisywane w
<code>~/.config/tlumacz/config.json</code>. Pola: <code>base_url</code>,
<code>api_key</code>, <code>model</code>, <code>chunk_size</code>,
<code>temperature</code>, <code>target_language</code>, <code>theme</code>,
<code>glossary_path</code>, <code>system_prompt</code>,
<code>enabled_skills</code>, <code>server_port</code>,
<code>server_gguf_path</code>, <code>auto_start_server</code>,
<code>last_input</code>, <code>last_output</code>.</p>
<p>Uszkodzony plik lub pola o błędnym typie są naprawiane wartościami
domyślnymi, a program pokazuje stosowny komunikat.</p>
"""

    def _help_text_en(self) -> str:
        return """
<h2>Tłumacz — help</h2>
<p>Tłumacz is a tool for translating documents (Markdown, TXT, HTML)
using LLM models that speak the OpenAI-compatible API.</p>

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
injected into the prompt during translation.</p>

<h3>5. Theme</h3>
<p>“System” follows the desktop color scheme; you can force light or dark.</p>

<h3>6. Configuration file</h3>
<p>Settings are stored in <code>~/.config/tlumacz/config.json</code>.
Fields: <code>base_url</code>, <code>api_key</code>, <code>model</code>,
<code>chunk_size</code>, <code>temperature</code>,
<code>target_language</code>, <code>theme</code>, <code>glossary_path</code>,
<code>system_prompt</code>, <code>enabled_skills</code>,
<code>server_port</code>, <code>server_gguf_path</code>,
<code>auto_start_server</code>, <code>last_input</code>,
<code>last_output</code>.</p>
<p>A corrupt file or wrong-typed fields are repaired with defaults and the
app shows a message about it.</p>
"""

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
        self.language.currentTextChanged.connect(self._on_language_changed)

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

        form.addRow("Base URL:", self.base_url)
        form.addRow("API key:", self.api_key)
        form.addRow("Model:", self.model)
        form.addRow("Rozmiar chunka:", self.chunk_size)
        form.addRow("Temperatura:", self.temperature)
        form.addRow("Język docelowy:", self.language)
        form.addRow("Motyw:", self.theme)
        form.addRow("Własny prompt:", self.prompt_edit)
        return box

    def _build_server_group(self) -> QGroupBox:
        box = QGroupBox("Serwer lokalny (llama.cpp / GGUF)")
        form = QFormLayout(box)

        self.server_port = QSpinBox()
        self.server_port.setObjectName("serverPort")
        self.server_port.setRange(1024, 65535)
        self.server_port.setSingleStep(100)

        gguf_row = QHBoxLayout()
        self.server_gguf_path = QLineEdit()
        self.server_gguf_path.setObjectName("serverGgufPath")
        self.server_gguf_path.setPlaceholderText(
            "Ścieżka do pliku modelu .gguf (opcjonalnie)"
        )
        gguf_browse = QPushButton("Przeglądaj...")
        gguf_browse.clicked.connect(self._on_browse_gguf)
        gguf_row.addWidget(self.server_gguf_path, 1)
        gguf_row.addWidget(gguf_browse)

        self.auto_start_server = QCheckBox(
            "Uruchamiaj serwer razem z programem"
        )
        self.auto_start_server.setObjectName("autoStartServer")

        form.addRow("Port:", self.server_port)
        form.addRow("Plik modelu (GGUF):", gguf_row)
        form.addRow(self.auto_start_server)
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
            glossary_path=self.glossary_path.text().strip() or None,
            system_prompt=self.prompt_edit.toPlainText().strip() or None,
            enabled_skills=self._enabled_skill_names(),
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
        settings.theme = self.theme_mode()
        settings.glossary_path = self.glossary_path.text().strip()
        settings.system_prompt = self.prompt_edit.toPlainText().strip()
        settings.enabled_skills = self._enabled_skill_names()
        settings.server_port = self.server_port.value()
        settings.server_gguf_path = self.server_gguf_path.text().strip()
        settings.auto_start_server = self.auto_start_server.isChecked()
        return settings

    def _load_settings_into_ui(self) -> None:
        s = self._settings
        self.base_url.setText(s.base_url)
        if self._server is not None:
            server_url = self._server.config.base_url
            self.base_url.setText(server_url)
            self._append_log(f"Własny serwer uruchomiony: {server_url}")
        self.api_key.setText(s.api_key)
        self.model.setText(s.model)
        self.chunk_size.setValue(s.chunk_size)
        self.temperature.setValue(s.temperature)
        index = self.language.findText(s.target_language)
        if index >= 0:
            self.language.setCurrentIndex(index)
        theme_index = self.theme.findData(s.theme)
        if theme_index >= 0:
            self.theme.setCurrentIndex(theme_index)
        self.input_path.setText(s.last_input)
        self.output_path.setText(s.last_output)
        self.glossary_path.setText(s.glossary_path)
        self._refresh_glossary_count()
        self.prompt_edit.setPlainText(s.system_prompt)
        enabled = set(s.enabled_skills)
        for skill, checkbox in zip(self._skills, self._skill_checkboxes):
            checkbox.setChecked(skill.name in enabled)
        self.server_port.setValue(s.server_port)
        self.server_gguf_path.setText(s.server_gguf_path)
        self.auto_start_server.setChecked(s.auto_start_server)

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
            self.output_path.setText(
                _default_output_path(path, self.language.currentText())
            )

    def _on_browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Wybierz plik wyjściowy", self.output_path.text()
        )
        if path:
            self.output_path.setText(path)

    def _on_browse_gguf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik modelu (GGUF)",
            self.server_gguf_path.text(),
            "GGUF files (*.gguf);;All files (*)",
        )
        if path:
            self.server_gguf_path.setText(path)
            save_settings(self._collect_settings())

    def _on_browse_glossary(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik glosariusza (CSV)",
            self.glossary_path.text(),
            "CSV files (*.csv);;All files (*)",
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

    def _on_skills_changed(self) -> None:
        save_settings(self._collect_settings())

    def theme_mode(self) -> str:
        """Return the currently selected theme mode (``system``/``light``/``dark``)."""
        return self.theme.currentData() or "system"

    def _on_theme_changed(self) -> None:
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


def _default_output_path(input_path: str, language: str) -> str:
    """Return ``name_<suffix>.ext`` next to the input file.

    The suffix follows the selected target language (``pl``, ``en``, ...).
    """
    suffix = LANGUAGE_SUFFIXES.get(language, "pl")
    path = Path(input_path)
    return str(path.with_name(f"{path.stem}_{suffix}{path.suffix}"))
