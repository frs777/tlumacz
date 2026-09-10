"""Testy systemu lokalizacji (i18n).

Moduł i18n.py nie miał wcześniej testów. Te testy weryfikują:
- Poprawność tłumaczeń PL i EN
- Funkcję t() z parametrami
- Zachowanie dla brakujących kluczy
- Kompletność tłumaczeń (wszystkie klucze PL mają odpowiedniki EN)
- Funkcje globalne set_language/get_language/t
"""

import pytest


class TestI18nClass:
    """Testy klasy I18n."""

    def test_init_default_language(self):
        """Domyślny język to polski."""
        from tlumacz.i18n import I18n
        
        i18n = I18n()
        assert i18n.language == "pl"

    def test_init_with_language(self):
        """Można utworzyć I18n z konkretnym językiem."""
        from tlumacz.i18n import I18n
        
        i18n_en = I18n("en")
        assert i18n_en.language == "en"
        
        i18n_pl = I18n("pl")
        assert i18n_pl.language == "pl"

    def test_set_language(self):
        """Setter language powinien zmieniać język."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        assert i18n.language == "pl"
        
        i18n.language = "en"
        assert i18n.language == "en"

    def test_t_existing_key_pl(self):
        """t() powinno zwracać polskie tłumaczenie dla istniejącego klucza."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        assert i18n.t("tab.translation") == "Tłumaczenie"
        assert i18n.t("button.translate") == "Tłumacz"
        assert i18n.t("button.cancel") == "Anuluj"

    def test_t_existing_key_en(self):
        """t() powinno zwracać angielskie tłumaczenie dla istniejącego klucza."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("en")
        
        assert i18n.t("tab.translation") == "Translation"
        assert i18n.t("button.translate") == "Translate"
        assert i18n.t("button.cancel") == "Cancel"

    def test_t_missing_key_returns_key(self):
        """t() powinno zwracać klucz gdy tłumaczenie nie istnieje."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        # Brakujący klucz — zwraca sam klucz
        assert i18n.t("nonexistent.key") == "nonexistent.key"
        assert i18n.t("another.missing.key") == "another.missing.key"

    def test_t_with_params(self):
        """t() powinno podstawiać parametry do tłumaczenia."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        # Klucz z parametrami: "log.extracting_text": "Wyodrębnianie tekstu z pliku .{ext}..."
        result = i18n.t("log.extracting_text", ext="md")
        assert result == "Wyodrębnianie tekstu z pliku .md..."
        
        # Więcej parametrów
        result = i18n.t("log.translating_block", current=5, total=10)
        assert result == "Tłumaczenie bloku 5/10..."

    def test_t_with_params_en(self):
        """t() powinno podstawiać parametry do angielskiego tłumaczenia."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("en")
        
        result = i18n.t("log.extracting_text", ext="pdf")
        assert result == "Extracting text from .pdf file..."

    def test_t_with_invalid_params(self):
        """t() powinno obsługiwać błędne parametry bez crasha."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        # Nadmiarowe parametry — powinny być zignorowane
        result = i18n.t("button.translate", extra="value")
        assert result == "Tłumacz"
        
        # Brakujące parametry — format() rzuci wyjątek, ale t() go łapie
        # i zwraca tekst bez podstawienia
        result = i18n.t("log.extracting_text")  # brakuje ext
        # Powinno zwrócić surowy tekst z {ext} lub oryginalny klucz
        assert "ext" in result or "Wyodrębnianie" in result

    def test_t_with_numeric_params(self):
        """t() powinno obsługiwać parametry numeryczne."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        result = i18n.t("log.found_text_blocks", count=42)
        assert "42" in result

    def test_t_with_float_params(self):
        """t() powinno obsługiwać parametry float z formatowaniem."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        # "log.text_not_fitting": "... z {from_size:.1f} na {to_size:.1f}"
        result = i18n.t("log.text_not_fitting", from_size=12.5, to_size=10.0)
        assert "12.5" in result
        assert "10.0" in result


class TestGlobalFunctions:
    """Testy funkcji globalnych set_language/get_language/t."""

    def test_set_and_get_language(self):
        """set_language i get_language powinny działać poprawnie."""
        from tlumacz.i18n import set_language, get_language
        
        # Domyślnie polski
        set_language("pl")
        assert get_language() == "pl"
        
        # Zmień na angielski
        set_language("en")
        assert get_language() == "en"
        
        # Zmień z powrotem
        set_language("pl")
        assert get_language() == "pl"

    def test_global_t_function(self):
        """Globalna funkcja t() powinna zwracać tłumaczenia dla aktualnego języka."""
        from tlumacz.i18n import set_language, t
        
        set_language("pl")
        assert t("button.translate") == "Tłumacz"
        
        set_language("en")
        assert t("button.translate") == "Translate"
        
        # Przywróć polski
        set_language("pl")

    def test_global_t_with_params(self):
        """Globalna funkcja t() powinna obsługiwać parametry."""
        from tlumacz.i18n import set_language, t
        
        set_language("pl")
        result = t("log.translating_block", current=3, total=7)
        assert result == "Tłumaczenie bloku 3/7..."


class TestTranslationsCompleteness:
    """Testy kompletności tłumaczeń."""

    def test_pl_en_keys_match(self):
        """Wszystkie klucze PL powinny mieć odpowiedniki w EN."""
        from tlumacz.i18n import PL, EN
        
        pl_keys = set(PL.keys())
        en_keys = set(EN.keys())
        
        # Klucze w PL ale brak w EN
        missing_in_en = pl_keys - en_keys
        assert not missing_in_en, (
            f"Klucze brakujące w EN: {missing_in_en}"
        )
        
        # Klucze w EN ale brak w PL
        missing_in_pl = en_keys - pl_keys
        assert not missing_in_pl, (
            f"Klucze brakujące w PL: {missing_in_pl}"
        )

    def test_no_empty_translations(self):
        """Żadne tłumaczenie nie powinno być pustym stringiem."""
        from tlumacz.i18n import PL, EN
        
        for key, value in PL.items():
            assert value, f"Puste tłumaczenie PL dla klucza: {key}"
        
        for key, value in EN.items():
            assert value, f"Puste tłumaczenie EN dla klucza: {key}"

    def test_translations_dict_structure(self):
        """TRANSLATIONS powinno zawierać 'pl' i 'en'."""
        from tlumacz.i18n import TRANSLATIONS
        
        assert "pl" in TRANSLATIONS
        assert "en" in TRANSLATIONS
        assert isinstance(TRANSLATIONS["pl"], dict)
        assert isinstance(TRANSLATIONS["en"], dict)

    def test_key_categories(self):
        """Klucze powinny być pogrupowane w kategorie (tab., button., log., etc.)."""
        from tlumacz.i18n import PL
        
        categories = set()
        for key in PL.keys():
            if "." in key:
                category = key.split(".")[0]
                categories.add(category)
        
        # Powinny być główne kategorie
        expected_categories = {"tab", "button", "log", "settings", "msg", "files", "help"}
        for cat in expected_categories:
            assert cat in categories, f"Brak kategorii: {cat}"


class TestI18nEdgeCases:
    """Testy edge cases."""

    def test_unknown_language_falls_back_to_pl(self):
        """Nieznany język powinien fallbackować do polskiego."""
        from tlumacz.i18n import I18n
        
        # Nieznany język — powinien fallbackować do PL
        i18n = I18n("xx")  # type: ignore
        assert i18n.t("button.translate") == "Tłumacz"  # polskie tłumaczenie

    def test_special_characters_in_translations(self):
        """Tłumaczenia mogą zawierać specjalne znaki (polskie litery, etc.)."""
        from tlumacz.i18n import I18n
        
        i18n = I18n("pl")
        
        # Polskie znaki
        result = i18n.t("button.browse")
        assert "Przeglądaj" in result
        
        # Znaki specjalne w formacie
        result = i18n.t("settings.chat_jinja")
        assert "jinja" in result
