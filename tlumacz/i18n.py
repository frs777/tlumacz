"""System lokalizacji (i18n) dla Tłumacz.

Moduł zawiera tłumaczenia wszystkich komunikatów wyświetlanych użytkownikowi.
Domyślny język to polski (pl), dostępny jest również angielski (en).
"""

from __future__ import annotations

from typing import Literal

# Typy języków
Language = Literal["pl", "en"]

# Polskie tłumaczenia (domyślne)
PL = {
    # GUI - etykiety ustawień
    "settings.base_url": "Base URL:",
    "settings.api_key": "API key:",
    "settings.model": "Model:",
    "settings.block_size": "Rozmiar bloku:",
    "settings.temperature": "Temperatura:",
    "settings.target_language": "Język docelowy:",
    "settings.theme": "Motyw:",
    "settings.custom_prompt": "Własny prompt:",
    "settings.skip_patterns": "Zaawansowane — pomijane linie (regex):",
    
    # GUI - grupy ustawień
    "settings.server_group": "Serwer lokalny (llama.cpp / GGUF)",
    "settings.glossary_group": "Glosariusz",
    "settings.skills_group": "Skille",
    
    # GUI - przyciski
    "button.translate": "Tłumacz",
    "button.cancel": "Anuluj",
    "button.settings": "Ustawienia",
    "button.help": "Pomoc",
    "button.browse": "Przeglądaj...",
    "button.add_entry": "Dodaj wpis",
    "button.new_skill": "Nowy skilla...",
    "button.restart_server": "Restart serwera",
    
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
    "log.translating_block_of": "Tłumaczenie bloku {current}/{total}...",
    "log.text_not_fitting": "Tekst nie mieści się, zmniejszam czcionkę z {from_size:.1f} na {to_size:.1f}",
    "log.still_not_fitting": "Nadal nie mieści się, zmniejszam do {size:.1f}",
    "log.text_may_be_truncated": "Uwaga: tekst nie mieści się w bloku {block_num}, może być ucięty.",
    "log.saving_pdf": "Zapisywanie przetłumaczonego PDF...",
    "log.pdf_saved": "Zapisano przetłumaczony PDF: {path}",
    
    # Logi - błędy
    "log.error_cannot_translate": "Nie można przetłumaczyć pliku {format}: {error}",
    "log.error_building": "Błąd przy budowaniu {format}: {error}",
    "log.no_text_to_translate": "Brak tekstu do przetłumaczenia - kopiuję plik bez zmian.",
    
    # Pomoc - opisy
    "help.block_size_desc": "Wielkość fragmentu tekstu wysyłanego do modelu.",
    "help.parallel_desc": "Większa wartość pozwala obsługiwać kilka bloków jednocześnie, ale zwiększa zużycie zasobów.",
}

# Angielskie tłumaczenia
EN = {
    # GUI - settings labels
    "settings.base_url": "Base URL:",
    "settings.api_key": "API key:",
    "settings.model": "Model:",
    "settings.block_size": "Block size:",
    "settings.temperature": "Temperature:",
    "settings.target_language": "Target language:",
    "settings.theme": "Theme:",
    "settings.custom_prompt": "Custom prompt:",
    "settings.skip_patterns": "Advanced — skip patterns (regex):",
    
    # GUI - settings groups
    "settings.server_group": "Local server (llama.cpp / GGUF)",
    "settings.glossary_group": "Glossary",
    "settings.skills_group": "Skills",
    
    # GUI - buttons
    "button.translate": "Translate",
    "button.cancel": "Cancel",
    "button.settings": "Settings",
    "button.help": "Help",
    "button.browse": "Browse...",
    "button.add_entry": "Add entry",
    "button.new_skill": "New skill...",
    "button.restart_server": "Restart server",
    
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
    "log.translating_block_of": "Translating block {current}/{total}...",
    "log.text_not_fitting": "Text doesn't fit, reducing font from {from_size:.1f} to {to_size:.1f}",
    "log.still_not_fitting": "Still doesn't fit, reducing to {size:.1f}",
    "log.text_may_be_truncated": "Warning: text doesn't fit in block {block_num}, may be truncated.",
    "log.saving_pdf": "Saving translated PDF...",
    "log.pdf_saved": "Saved translated PDF: {path}",
    
    # Logs - errors
    "log.error_cannot_translate": "Cannot translate {format} file: {error}",
    "log.error_building": "Error building {format}: {error}",
    "log.no_text_to_translate": "No text to translate - copying file unchanged.",
    
    # Help - descriptions
    "help.block_size_desc": "Size of the text fragment sent to the model.",
    "help.parallel_desc": "Higher value allows processing multiple blocks simultaneously, but increases resource usage.",
}

# Słownik tłumaczeń
TRANSLATIONS = {
    "pl": PL,
    "en": EN,
}


class I18n:
    """Klasa do obsługi lokalizacji."""
    
    def __init__(self, language: Language = "pl"):
        """Inicjalizuje system tłumaczeń.
        
        Args:
            language: Kod języka ("pl" lub "en").
        """
        self._language = language
        self._translations = TRANSLATIONS.get(language, PL)
    
    @property
    def language(self) -> Language:
        """Zwraca aktualny język."""
        return self._language
    
    @language.setter
    def language(self, value: Language) -> None:
        """Ustawia język tłumaczeń."""
        self._language = value
        self._translations = TRANSLATIONS.get(value, PL)
    
    def t(self, key: str, **kwargs) -> str:
        """Zwraca przetłumaczony tekst.
        
        Args:
            key: Klucz tłumaczenia (np. "log.processing_blocks").
            **kwargs: Parametry do formatowania (np. count=5).
        
        Returns:
            Przetłumaczony tekst z podstawionymi parametrami.
        """
        text = self._translations.get(key, PL.get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                pass
        return text


# Globalna instancja (domyślnie polski)
_i18n = I18n("pl")


def set_language(language: Language) -> None:
    """Ustawia globalny język tłumaczeń."""
    global _i18n
    _i18n = I18n(language)


def t(key: str, **kwargs) -> str:
    """Zwraca przetłumaczony tekst dla aktualnego języka."""
    return _i18n.t(key, **kwargs)
