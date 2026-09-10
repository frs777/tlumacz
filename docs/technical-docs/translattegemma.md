# Wdrożenie specjalnego formatu wiadomości dla TranslateGemma

**Data:** 2026-09-07  
**Status:** Plan  
**Autor:** Qwen Code

---

## Cel

Wdrożyć specjalny format wiadomości dla modelu TranslateGemma, który wymaga specyficznej struktury z kodami języków.

---

## Kontekst

Model TranslateGemma ma specjalny szablon czatu który wymaga:
```python
messages=[
    {"role": "user", "content": [
        {
            "type": "text",
            "source_lang_code": "en",  # kod języka źródłowego
            "target_lang_code": "pl",  # kod języka docelowego
            "text": "tekst do tłumaczenia"
        }
    ]}
]
```

Obecny format (standardowy):
```python
messages=[
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_content},
]
```

---

## Plan wdrożenia

### Krok 1: Dodać mapowanie języków na kody

**Plik:** `tlumacz/core.py`

**Lokalizacja:** Na początku pliku, po importach

**Kod:**
```python
# Mapowanie nazw języków na kody ISO 639-1
LANGUAGE_CODES = {
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
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Portuguese": "pt",
    "Turkish": "tr",
    "Vietnamese": "vi",
    "Thai": "th",
    "Indonesian": "id",
    "Malay": "ms",
    "Hindi": "hi",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Persian": "fa",
    "Hebrew": "he",
    "Greek": "el",
    "Bulgarian": "bg",
    "Romanian": "ro",
    "Hungarian": "hu",
    "Finnish": "fi",
    "Swedish": "sv",
    "Norwegian": "no",
    "Danish": "da",
    "Icelandic": "is",
    "Estonian": "et",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Croatian": "hr",
    "Serbian": "sr",
    "Bosnian": "bs",
    "Macedonian": "mk",
    "Albanian": "sq",
    "Montenegrin": "cnr",
    "Welsh": "cy",
    "Irish": "ga",
    "Scottish Gaelic": "gd",
    "Breton": "br",
    "Basque": "eu",
    "Catalan": "ca",
    "Galician": "gl",
    "Maltese": "mt",
    "Luxembourgish": "lb",
    "Romansh": "rm",
    "Faroese": "fo",
    "Sami": "se",
    "Greenlandic": "kl",
    "Esperanto": "eo",
    "Latin": "la",
    "auto": "auto",  # automatyczna detekcja
}


def get_language_code(language_name: str) -> str:
    """Pobierz kod języka ISO 639-1 z nazwy języka.
    
    Args:
        language_name: Nazwa języka (np. "Polish", "English")
        
    Returns:
        Kod języka (np. "pl", "en") lub "auto" jeśli nie znaleziono
    """
    return LANGUAGE_CODES.get(language_name, "auto")
```

**Uzasadnienie:**
- Centralne mapowanie języków
- Łatwe rozszerzanie
- Fallback na "auto" dla nieznanych języków

---

### Krok 2: Dodać funkcję budowania wiadomości dla TranslateGemma

**Plik:** `tlumacz/core.py`

**Lokalizacja:** W klasie `Translator`, przed metodą `_translate_chunk()`

**Kod:**
```python
def _build_translategemma_messages(
    self, chunk: str, source_lang: str = "auto"
) -> list[dict]:
    """Zbuduj wiadomości w formacie TranslateGemma.
    
    Args:
        chunk: Tekst do przetłumaczenia
        source_lang: Kod języka źródłowego (domyślnie "auto")
        
    Returns:
        Lista wiadomości w formacie TranslateGemma
    """
    # Pobierz kod języka docelowego
    target_lang_code = get_language_code(self.config.target_language)
    
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "source_lang_code": source_lang,
                    "target_lang_code": target_lang_code,
                    "text": chunk,
                }
            ],
        }
    ]
```

**Uzasadnienie:**
- Osobna funkcja dla czytelności
- Łatwe testowanie
- Możliwość rozszerzenia o detekcję języka

---

### Krok 3: Zmodyfikować `_translate_chunk()` do używania specjalnego formatu

**Plik:** `tlumacz/core.py`

**Lokalizacja:** Metoda `_translate_chunk()`, sekcja budowania `request_kwargs`

**Obecny kod (linie ~320-330):**
```python
request_kwargs: dict = {
    "model": self.config.model,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ],
    "temperature": self.config.temperature,
    "max_tokens": max_tokens,
}
```

**Nowy kod:**
```python
# Wybierz format wiadomości w zależności od szablonu czatu
if self.config.chat_template == "translategemma":
    # TranslateGemma wymaga specjalnego formatu z kodami języków
    messages = self._build_translategemma_messages(chunk)
    # Nie używaj system prompt dla TranslateGemma
else:
    # Standardowy format dla innych modeli
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

request_kwargs: dict = {
    "model": self.config.model,
    "messages": messages,
    "temperature": self.config.temperature,
    "max_tokens": max_tokens,
}
```

**Uzasadnienie:**
- Warunkowe użycie formatu tylko dla translategemma
- Brak system prompt dla translategemma (model nie używa)
- Zachowanie kompatybilności z innymi modelami

---

### Krok 4: Dodać detekcję języka źródłowego (opcjonalnie)

**Plik:** `tlumacz/core.py`

**Lokalizacja:** W metodzie `_build_translategemma_messages()`

**Opcja A: Użyć "auto" (prostsze)**
```python
source_lang_code = "auto"  # Model sam wykryje język
```

**Opcja B: Detekcja języka (bardziej zaawansowane)**
```python
# Wymaga dodatkowej biblioteki np. langdetect
from langdetect import detect

def _detect_language(self, text: str) -> str:
    """Wykryj język tekstu."""
    try:
        return get_language_code(detect(text))
    except Exception:
        return "auto"
```

**Rekomendacja:** Zacząć od Opcji A ("auto"), dodać Opcję B jeśli będzie potrzeba.

---

### Krok 5: Zaktualizować testy

**Plik:** `tests/test_core.py`

**Testy do dodania:**

```python
def test_translategemma_message_format():
    """Test formatu wiadomości dla TranslateGemma."""
    config = TranslatorConfig(
        target_language="Polish",
        chat_template="translategemma",
        chunk_size=200,
        cache_enabled=False,
    )
    translator = Translator(config)
    
    # Test budowania wiadomości
    messages = translator._build_translategemma_messages("Hello world")
    
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert len(messages[0]["content"]) == 1
    assert messages[0]["content"][0]["type"] == "text"
    assert messages[0]["content"][0]["source_lang_code"] == "auto"
    assert messages[0]["content"][0]["target_lang_code"] == "pl"
    assert messages[0]["content"][0]["text"] == "Hello world"


def test_get_language_code():
    """Test mapowania języków na kody."""
    assert get_language_code("Polish") == "pl"
    assert get_language_code("English") == "en"
    assert get_language_code("German") == "de"
    assert get_language_code("Unknown") == "auto"
    assert get_language_code("auto") == "auto"
```

---

### Krok 6: Zaktualizować `_command()` w server.py

**Plik:** `tlumacz/server.py`

**Obecny kod:**
```python
elif chat_template == "translategemma":
    # TranslateGemma has special translation template - use standard Gemma 3
    command += ["--no-jinja", "--chat-template", "gemma"]
```

**Nowy kod:**
```python
elif chat_template == "translategemma":
    # TranslateGemma uses special translation template (built into model)
    # No --chat-template flag needed - model uses its native template
    pass  # Nie dodawaj żadnych flag template
```

**Uzasadnienie:**
- Model TranslateGemma ma wbudowany specjalny szablon
- Nie trzeba podawać `--chat-template gemma`
- Model sam użyje swojego szablonu z kodami języków

---

### Krok 7: Testy ręczne

**Scenariusze testowe:**

1. **Test podstawowy:**
   - Plik: `pliki testowe/TEST3/test3.txt`
   - Parametry: chunk_size=2000, parallel=2, template=translategemma
   - Oczekiwany czas: ~2:30
   - Oczekiwana jakość: ~70%+

2. **Test z różnymi językami:**
   - Plik z tekstem po angielsku, francusku, niemiecku
   - Sprawdzenie czy kody języków są poprawnie używane

3. **Test z "wykryj do X":**
   - Ustawienie: "wykryj do pl"
   - Sprawdzenie czy source_lang_code = "auto"

---

## Kryteria akceptacji

- [ ] Serwer uruchamia się z `translategemma` bez błędów
- [ ] Tłumaczenie działa poprawnie
- [ ] Kody języków są używane w wiadomościach
- [ ] Czas tłumaczenia ~2:30 dla test3.txt
- [ ] Jakość tłumaczenia ~70%+
- [ ] Wszystkie testy jednostkowe przechodzą
- [ ] Brak regresji dla innych szablonów (chatml, jinja)

---

## Ryzyka i mitigacja

### Ryzyko 1: Model nie obsługuje "auto" dla source_lang_code
**Mitigacja:** Dodać detekcję języka (Krok 4, Opcja B)

### Ryzyko 2: Format wiadomości jest niekompatybilny z wersją modelu
**Mitigacja:** Sprawdzić dokumentację modelu na HuggingFace

### Ryzyko 3: Brak system prompt pogarsza jakość tłumaczenia
**Mitigacja:** Dodać instrukcje w polu "text" zamiast system prompt

---

## Harmonogram

| Krok | Czas | Priorytet |
|------|------|-----------|
| 1. Mapowanie języków | 15 min | Wysoki |
| 2. Funkcja budowania wiadomości | 20 min | Wysoki |
| 3. Modyfikacja _translate_chunk() | 15 min | Wysoki |
| 4. Detekcja języka (opcjonalnie) | 30 min | Średni |
| 5. Testy jednostkowe | 30 min | Wysoki |
| 6. Aktualizacja server.py | 10 min | Wysoki |
| 7. Testy ręczne | 60 min | Wysoki |

**Łączny czas:** ~3 godziny

---

## Pliki do zmiany

1. `tlumacz/core.py` — mapowanie języków, funkcja budowania wiadomości, modyfikacja _translate_chunk()
2. `tlumacz/server.py` — usunięcie --chat-template gemma dla translategemma
3. `tests/test_core.py` — testy nowego formatu

---

## Cofnięcie zmian

W razie problemów:
```bash
git checkout tlumacz/core.py tlumacz/server.py tests/test_core.py
```

---

**Zatwierdzone przez użytkownika:** [do zatwierdzenia]  
**Data wdrożenia:** 2026-09-07
