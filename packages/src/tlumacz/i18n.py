"""System lokalizacji (i18n) dla Tłumacz.

Moduł zawiera tłumaczenia wszystkich komunikatów wyświetlanych użytkownikowi.
Domyślny język to polski (pl), dostępny jest również angielski (en).
"""

from __future__ import annotations

from typing import Literal

Language = Literal["pl", "en"]

# ---------------------------------------------------------------------------
# Polskie tłumaczenia (domyślne)
# ---------------------------------------------------------------------------
PL = {
    # Nazwy zakładek
    "tab.translation": "Tłumaczenie",
    "tab.api_server": "API i serwer",
    "tab.extras": "Dodatki",
    "tab.help": "Pomoc",

    # Grupy plików
    "files.group": "Pliki",
    "files.input": "Plik wejściowy:",
    "files.output": "Plik wyjściowy:",

    # Grupy ustawień
    "settings.api_group": "Ustawienia API",
    "settings.server_group": "Serwer lokalny (llama.cpp / GGUF)",
    "settings.glossary_group": "Glosariusz",
    "settings.skills_group": "Skille",
    "settings.other_group": "Pozostałe ustawienia",

    # Etykiety ustawień
    "settings.base_url": "Base URL:",
    "settings.api_key": "API key:",
    "settings.model": "Model:",
    "settings.block_size": "Rozmiar bloku:",
    "settings.temperature": "Temperatura:",
    "settings.target_language": "Język docelowy:",
    "settings.theme": "Motyw:",
    "settings.custom_prompt": "Własny prompt:",
    "settings.skip_patterns": "Pomijane linie (regex):",
    "settings.port": "Port:",
    "settings.compute_mode": "Obliczenia serwera:",
    "settings.gguf_path": "Plik modelu (GGUF):",
    "settings.chat_template": "Szablon czatu:",
    "settings.parallel": "Wątki (parallel):",
    "settings.auto_start": "Uruchamiaj serwer razem z programem",
    "settings.clear_cache": "Czyść cache po każdym tłumaczeniu",
    "settings.glossary_path": "Plik glosariusza:",
    "glossary.no_file": "Brak pliku",
    "settings.chat_jinja": "jinja (natywny)",
    "settings.chat_chatml": "chatml",
    "settings.chat_translategemma": "translategemma (kody języków)",

    # Przyciski
    "button.translate": "Tłumacz",
    "button.cancel": "Anuluj",
    "button.browse": "Przeglądaj…",
    "button.add_entry": "Dodaj wpis",
    "button.refresh": "Odśwież",
    "button.import_skill": "Importuj skilla…",
    "button.new_skill": "Nowy skilla…",
    "button.restart_server": "Restart serwera",
    "button.start_server": "Uruchom serwer",
    "button.stop_server": "Zatrzymaj serwer",
    "button.check_auto_start": "Zaznacz box 'Uruchamiaj serwer razem z programem'",
    "button.restore_defaults": "Przywróć domyślne",

    # Pomoc
    "help.language_label": "Język / Language:",

    # Logi - tłumaczenie
    "log.extracting_text": "Wyodrębnianie tekstu z pliku .{ext}...",
    "log.using_glossary": "Używanie glosariusza: {path}",
    "log.using_skill": "Używanie skilla: {name}",
    "log.protected_fragments": "Chroniono {count} fragment(ów) kodu/URL",
    "log.processing_blocks": "Przetwarzanie {count} blok(ów)...",
    "log.translating_block": "Tłumaczenie bloku {current}/{total}...",
    "log.translating_segment": "Tłumaczenie segmentu {current}/{total}...",
    "log.translation_cancelled": "Tłumaczenie anulowane przez użytkownika.",
    "log.translation_saved": "Zapisano tłumaczenie do: {path}",

    # Logi - bufor
    "log.buffer_stats": "Bufor: {hits} trafień, {misses} pudł ({effectiveness}% skuteczności)",
    "log.buffer_no_lookups": "Bufor: brak zapytań",
    "log.buffer_cleared": "Bufor wyczyszczony po tłumaczeniu",
    "log.buffer_cleared_short": "Bufor wyczyszczony",

    # Logi - EPUB
    "log.extracting_epub": "Wyodrębnianie struktury z EPUB...",
    "log.found_xhtml_files": "Znaleziono {count} plik(ów) treści do przetłumaczenia.",
    "log.translating_file": "Tłumaczenie pliku {current}/{total}: {name}",
    "log.building_epub": "Budowanie przetłumaczonego EPUB...",
    "log.epub_saved": "Zapisano przetłumaczony EPUB: {path}",

    # Logi - DOCX/ODT
    "log.unpacking_archive": "Rozpakowywanie pliku .{ext}...",
    "log.found_content_files": "Znaleziono {count} plik(ów) treści do przetłumaczenia.",
    "log.building_archive": "Budowanie przetłumaczonego pliku {format}...",
    "log.archive_saved": "Zapisano przetłumaczony {format}: {path}",

    # Logi - PDF
    "log.extracting_pdf": "Ekstrakcja tekstu z PDF...",
    "log.no_text_in_pdf": "Plik PDF nie zawiera tekstu do przetłumaczenia.",
    "log.found_text_blocks": "Znaleziono {count} blok(ów) tekstu.",
    "log.text_not_fitting": "Tekst nie mieści się, zmniejszam czcionkę z {from_size:.1f} na {to_size:.1f}",
    "log.still_not_fitting": "Nadal nie mieści się, zmniejszam do {size:.1f}",
    "log.text_may_be_truncated": "Uwaga: tekst nie mieści się w bloku {block_num}, może być ucięty.",
    "log.saving_pdf": "Zapisywanie przetłumaczonego PDF...",
    "log.pdf_saved": "Zapisano przetłumaczony PDF: {path}",

    # Logi - błędy
    "log.error_cannot_translate": "Nie można przetłumaczyć pliku {format}: {error}",
    "log.error_building": "Błąd przy budowaniu {format}: {error}",
    "log.no_text_to_translate": "Brak tekstu do przetłumaczenia - kopiuję plik bez zmian.",
    "log.skills_refreshed": "Odświeżono listę skilli: {count}",
    "log.imported_skill": "Zaimportowano skillę: {path}",
    "log.created_skill": "Utworzono nowy skilla: {path}",
    "log.cannot_load_preview": "Nie można wczytać podglądu: {error}",
    "log.thread_force_stopped": "Ostrzeżenie: wątek tłumaczenia został zatrzymany siłą przy zamykaniu.",

    # Komunikaty
    "msg.config_title": "Konfiguracja",
    "msg.skills_title": "Skille",
    "msg.cannot_read_file": "Nie można odczytać pliku: {error}",
    "msg.not_a_skill": "To nie jest skilla: w nagłówku pliku brakuje pól {fields}",
    "msg.created_template": "Utworzono plik szablonu:\n{path}\n\nOtwórz go w edytorze i uzupełnij pola.",
    "msg.restore_confirm": "Zapisuje kopię obecnego config.json i przywraca domyślne ustawienia.\nTwoje ścieżki (ostatni plik wejściowy/wyjściowy, glosariusz) są zachowywane.",
    "msg.select_skill_file": "Wybierz plik skilla (.md)",
}

# ---------------------------------------------------------------------------
# Angielskie tłumaczenia
# ---------------------------------------------------------------------------
EN = {
    # Tab names
    "tab.translation": "Translation",
    "tab.api_server": "API & Server",
    "tab.extras": "Extras",
    "tab.help": "Help",

    # File groups
    "files.group": "Files",
    "files.input": "Input file:",
    "files.output": "Output file:",

    # Settings groups
    "settings.api_group": "API Settings",
    "settings.server_group": "Local server (llama.cpp / GGUF)",
    "settings.glossary_group": "Glossary",
    "settings.skills_group": "Skills",
    "settings.other_group": "Other settings",

    # Settings labels
    "settings.base_url": "Base URL:",
    "settings.api_key": "API key:",
    "settings.model": "Model:",
    "settings.block_size": "Block size:",
    "settings.temperature": "Temperature:",
    "settings.target_language": "Target language:",
    "settings.theme": "Theme:",
    "settings.custom_prompt": "Custom prompt:",
    "settings.skip_patterns": "Skip patterns (regex):",
    "settings.port": "Port:",
    "settings.compute_mode": "Server compute:",
    "settings.gguf_path": "Model file (GGUF):",
    "settings.chat_template": "Chat template:",
    "settings.parallel": "Threads (parallel):",
    "settings.auto_start": "Start server with the app",
    "settings.clear_cache": "Clear cache after each translation",
    "settings.glossary_path": "Glossary file:",
    "glossary.no_file": "No file",
    "settings.chat_jinja": "jinja (native)",
    "settings.chat_chatml": "chatml",
    "settings.chat_translategemma": "translategemma (language codes)",

    # Buttons
    "button.translate": "Translate",
    "button.cancel": "Cancel",
    "button.browse": "Browse…",
    "button.add_entry": "Add entry",
    "button.refresh": "Refresh",
    "button.import_skill": "Import skill…",
    "button.new_skill": "New skill…",
    "button.restart_server": "Restart server",
    "button.start_server": "Start server",
    "button.stop_server": "Stop server",
    "button.check_auto_start": "Check 'Start server with the app' box",
    "button.restore_defaults": "Restore defaults",

    # Help
    "help.language_label": "Language / Język:",

    # Logs - translation
    "log.extracting_text": "Extracting text from .{ext} file...",
    "log.using_glossary": "Using glossary: {path}",
    "log.using_skill": "Using skill: {name}",
    "log.protected_fragments": "Protected {count} code/URL fragment(s)",
    "log.processing_blocks": "Processing {count} block(s)...",
    "log.translating_block": "Translating block {current}/{total}...",
    "log.translating_segment": "Translating segment {current}/{total}...",
    "log.translation_cancelled": "Translation cancelled by user.",
    "log.translation_saved": "Translation saved to: {path}",

    # Logs - buffer/cache
    "log.buffer_stats": "Cache: {hits} hits, {misses} misses ({effectiveness}% effectiveness)",
    "log.buffer_no_lookups": "Cache: no lookups",
    "log.buffer_cleared": "Cache cleared after translation",
    "log.buffer_cleared_short": "Cache cleared",

    # Logs - EPUB
    "log.extracting_epub": "Extracting structure from EPUB...",
    "log.found_xhtml_files": "Found {count} content file(s) to translate.",
    "log.translating_file": "Translating file {current}/{total}: {name}",
    "log.building_epub": "Building translated EPUB...",
    "log.epub_saved": "Saved translated EPUB: {path}",

    # Logs - DOCX/ODT
    "log.unpacking_archive": "Unpacking .{ext} file...",
    "log.found_content_files": "Found {count} content file(s) to translate.",
    "log.building_archive": "Building translated {format} file...",
    "log.archive_saved": "Saved translated {format}: {path}",

    # Logs - PDF
    "log.extracting_pdf": "Extracting text from PDF...",
    "log.no_text_in_pdf": "PDF file contains no text to translate.",
    "log.found_text_blocks": "Found {count} text block(s).",
    "log.text_not_fitting": "Text doesn't fit, reducing font from {from_size:.1f} to {to_size:.1f}",
    "log.still_not_fitting": "Still doesn't fit, reducing to {size:.1f}",
    "log.text_may_be_truncated": "Warning: text doesn't fit in block {block_num}, may be truncated.",
    "log.saving_pdf": "Saving translated PDF...",
    "log.pdf_saved": "Saved translated PDF: {path}",

    # Logs - errors
    "log.error_cannot_translate": "Cannot translate {format} file: {error}",
    "log.error_building": "Error building {format}: {error}",
    "log.no_text_to_translate": "No text to translate - copying file unchanged.",
    "log.skills_refreshed": "Refreshed skills list: {count}",
    "log.imported_skill": "Imported skill: {path}",
    "log.created_skill": "Created new skill: {path}",
    "log.cannot_load_preview": "Cannot load preview: {error}",
    "log.thread_force_stopped": "Warning: translation thread was force-stopped on close.",

    # Messages
    "msg.config_title": "Configuration",
    "msg.skills_title": "Skills",
    "msg.cannot_read_file": "Cannot read file: {error}",
    "msg.not_a_skill": "Not a skill file: missing header fields {fields}",
    "msg.created_template": "Created template file:\n{path}\n\nOpen it in an editor and fill in the fields.",
    "msg.restore_confirm": "Saves a copy of current config.json and restores defaults.\nYour paths (last input/output file, glossary) are preserved.",
    "msg.select_skill_file": "Select skill file (.md)",
}

# ---------------------------------------------------------------------------
TRANSLATIONS = {"pl": PL, "en": EN}


class I18n:
    """Klasa do obsługi lokalizacji."""

    def __init__(self, language: Language = "pl"):
        self._language = language
        self._translations = TRANSLATIONS.get(language, PL)

    @property
    def language(self) -> Language:
        return self._language

    @language.setter
    def language(self, value: Language) -> None:
        self._language = value
        self._translations = TRANSLATIONS.get(value, PL)

    def t(self, key: str, **kwargs) -> str:
        """Zwraca przetłumaczony tekst z podstawionymi parametrami."""
        text = self._translations.get(key, PL.get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                pass
        return text


_i18n = I18n("pl")


def set_language(language: Language) -> None:
    """Ustawia globalny język tłumaczeń."""
    global _i18n
    _i18n = I18n(language)


def get_language() -> Language:
    """Zwraca aktualny język."""
    return _i18n.language


def t(key: str, **kwargs) -> str:
    """Zwraca przetłumaczony tekst dla aktualnego języka."""
    return _i18n.t(key, **kwargs)
