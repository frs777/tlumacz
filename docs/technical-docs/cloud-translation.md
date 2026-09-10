# Tłumaczenie w chmurze — Tłumacz

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05

---

## Spis treści

1. [Przegląd](#przegląd)
2. [Konfiguracja modeli chmurowych](#konfiguracja-modeli-chmurowych)
3. [Google Gemini](#google-gemini)
4. [OpenAI i inne API](#openai-i-inne-api)
5. [Przełączanie między chmurą a lokalnym serwerem](#przełączanie-między-chmurą-a-lokalnym-serwerem)
6. [Zarządzanie kluczami API](#zarządzanie-kluczami-api)
7. [Rate limits i koszty](#rate-limits-i-koszty)
8. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Przegląd

Tłumacz obsługuje tłumaczenie w chmurze przez dowolne API zgodne z OpenAI Chat Completions. Dzięki temu możesz używać modeli chmurowych bez konieczności uruchamiania lokalnego serwera.

### Zalety tłumaczenia w chmurze

- **Brak wymagań sprzętowych** — nie potrzebujesz GPU ani dużej ilości RAM
- **Szybkość** — modele chmurowe są zazwyczaj szybsze niż lokalne
- **Jakość** — duże modele (Gemini, GPT-4) oferują wyższą jakość tłumaczenia
- **Dostępność** — działa na każdym komputerze z dostępem do internetu

### Wady

- **Koszt** — płatne API (choć niektóre mają darmowe limity)
- **Prywatność** — dokumenty są wysyłane do zewnętrznych serwerów
- **Rate limits** — ograniczenia liczby zapytań na minutę
- **Internet** — wymaga stabilnego połączenia

---

## Konfiguracja modeli chmurowych

### Plik cloud_models.json

Tłumacz wczytuje konfigurację modeli chmurowych z pliku `cloud_models.json`:

**Lokalizacja (kolejność priorytetu):**
1. `tlumacz/cloud_models.json` (katalog projektu)
2. `~/.config/tlumacz/cloud_models.json` (katalog użytkownika)

**Format:**
```json
{
  "cloud_models": [
    {
      "name": "gemini-3.5-flash",
      "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "api_key": "",
      "description": "Google Gemini 3.5 Flash - szybki model chmurowy"
    },
    {
      "name": "gemini-3.5-flash-lite",
      "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "api_key": "",
      "description": "Google Gemini 3.5 Flash Lite - najszybszy, prawie nieograniczony (60 RPM)"
    }
  ]
}
```

### Wczytywanie konfiguracji

```python
def _load_cloud_models_config() -> list[dict[str, str]]:
    """Load cloud models configuration from cloud_models.json."""
    # 1. Sprawdź katalog projektu
    project_config = Path(__file__).parent.parent.parent / "cloud_models.json"
    if project_config.is_file():
        with open(project_config, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cloud_models", [])
    
    # 2. Sprawdź katalog użytkownika
    user_config = config_dir() / "cloud_models.json"
    if user_config.is_file():
        with open(user_config, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cloud_models", [])
    
    # 3. Domyślna konfiguracja
    return [
        {
            "name": "gemini-3.5-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": "",
            "description": "Google Gemini 3.5 Flash",
        },
        {
            "name": "gemini-3.5-flash-lite",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": "",
            "description": "Google Gemini 3.5 Flash Lite",
        },
    ]
```

### Combo box modeli w GUI

Pole „Model" w zakładce „API i serwer" to **QComboBox** z:

1. **Modelami chmurowymi** (z `cloud_models.json`)
2. **Separatorem** (linia pozioma)
3. **LOCAL** — przywraca ustawienia lokalnego serwera
4. **(wprowadź ręcznie)** — pole tekstowe dla własnego modelu

```python
# Wypełnienie combo box
for model_config in CLOUD_MODELS_CONFIG:
    self.model.addItem(model_config["name"])
self.model.insertSeparator(self.model.count())
self.model.addItem("LOCAL")
self.model.addItem("(wprowadź ręcznie)")
```

---

## Google Gemini

### Modele

| Model | Opis | Limit RPM | Cena |
|-------|------|-----------|------|
| **gemini-3.5-flash** | Szybki model ogólnego przeznaczenia | 60 | Darmowy (do pewnego limitu) |
| **gemini-3.5-flash-lite** | Najszybszy, prawie nieograniczony | 1500 | Darmowy |

### Konfiguracja krok po kroku

#### 1. Uzyskanie klucza API Google AI Studio

1. Przejdź do [Google AI Studio](https://aistudio.google.com/)
2. Zaloguj się kontem Google
3. Kliknij **„Get API Key"** w lewym menu
4. Kliknij **„Create API Key"**
5. Wybierz projekt Google Cloud (lub utwórz nowy)
6. Skopiuj wygenerowany klucz

#### 2. Konfiguracja w Tłumaczu

1. Otwórz Tłumacz
2. Przejdź do zakładki **„API i serwer"**
3. W polu **„Model"** wybierz `gemini-3.5-flash` lub `gemini-3.5-flash-lite`
4. Base URL zostanie ustawiony automatycznie: `https://generativelanguage.googleapis.com/v1beta/openai/`
5. Wprowadź klucz API w polu **„API key"**
6. Kliknij **„Tłumacz"** w zakładce „Tłumaczenie"

### Przykład użycia

**Plik wejściowy:** `dokument.md` (angielski)

**Konfiguracja:**
- Model: `gemini-3.5-flash`
- API key: `AIzaSy...` (twój klucz)
- Base URL: `https://generativelanguage.googleapis.com/v1beta/openai/` (automatycznie)
- Język docelowy: `wykryj do pl`

**Wynik:** Przetłumaczony dokument w języku polskim z zachowaniem formatowania Markdown.

### Ograniczenia Gemini

- **Rate limit** — 60 RPM (flash) lub 1500 RPM (flash-lite)
- **Maksymalny rozmiar żądania** — 20 MB
- **Kontekst** — 1M tokenów (flash) lub 1M tokenów (flash-lite)
- **Darmowy tier** — ograniczona liczba zapytań dziennie

---

## OpenAI i inne API

### OpenAI (GPT-4, GPT-3.5)

**Konfiguracja:**
```json
{
  "name": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "description": "OpenAI GPT-4 Turbo"
}
```

**Uzyskanie klucza API:**
1. Przejdź do [OpenAI Platform](https://platform.openai.com/)
2. Zaloguj się lub załóż konto
3. Przejdź do „API Keys"
4. Kliknij „Create new secret key"
5. Skopiuj klucz (zaczyna się od `sk-`)

### Anthropic (Claude)

**Konfiguracja:**
```json
{
  "name": "claude-3-opus-20240229",
  "base_url": "https://api.anthropic.com/v1",
  "api_key": "sk-ant-...",
  "description": "Anthropic Claude 3 Opus"
}
```

**Uwaga:** Anthropic nie jest natywnie zgodny z OpenAI API. Wymaga proxy lub adaptera.

### Inne serwery zgodne z OpenAI

Tłumacz działa z dowolnym serwerem zgodnym z OpenAI Chat Completions API:

- **Groq** — `https://api.groq.com/openai/v1`
- **Together AI** — `https://api.together.xyz/v1`
- **Mistral AI** — `https://api.mistral.ai/v1`
- **Azure OpenAI** — `https://YOUR_RESOURCE.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT`
- **Własny serwer** — np. vLLM, Text Generation Inference

---

## Przełączanie między chmurą a lokalnym serwerem

### Pamięć ustawień lokalnych

Tłumacz zapamiętuje ostatnie ustawienia lokalnego serwera w `config.json`:

```json
{
  "last_local_base_url": "http://127.0.0.1:18080/v1",
  "last_local_api_key": "ollama",
  "last_local_model": "local"
}
```

### Mechanizm przełączania

Kiedy zmieniasz model w combo box, wywoływana jest metoda `_on_model_changed()`:

```python
def _on_model_changed(self, model_name: str) -> None:
    """Handle model selection change."""
    if model_name == "LOCAL":
        # Przywróć ustawienia lokalnego serwera
        self.base_url.setText(self._settings.last_local_base_url)
        self.api_key.setText(self._settings.last_local_api_key)
        self.model.setEditText(self._settings.last_local_model)
    elif model_name == "(wprowadź ręcznie)":
        # Wyczyść pola dla ręcznej konfiguracji
        self.base_url.clear()
        self.api_key.clear()
        self.model.setEditText("")
    else:
        # Model chmurowy — ustaw Base URL i API key z konfiguracji
        for config in CLOUD_MODELS_CONFIG:
            if config["name"] == model_name:
                self.base_url.setText(config["base_url"])
                if config.get("api_key"):
                    self.api_key.setText(config["api_key"])
                break
```

### Zapamiętywanie ustawień lokalnych

Przed przełączeniem na chmurę Tłumacz zapisuje aktualne ustawienia lokalne:

```python
def _collect_settings(self) -> AppSettings:
    """Collect settings from GUI."""
    settings = AppSettings(...)
    
    # Zapamiętaj ustawienia lokalne jeśli używamy LOCAL
    if self.model.currentText() == "LOCAL":
        settings.last_local_base_url = self.base_url.text()
        settings.last_local_api_key = self.api_key.text()
        settings.last_local_model = "local"
    
    return settings
```

### Przykład przepływu

1. **Start** — używasz lokalnego serwera (`http://127.0.0.1:18080/v1`)
2. **Przełącz na chmurę** — wybierz `gemini-3.5-flash` z combo box
   - Base URL automatycznie ustawiony na `https://generativelanguage.googleapis.com/v1beta/openai/`
   - Wprowadzasz klucz API
3. **Tłumaczysz w chmurze** — dokumenty są tłumaczone przez Gemini
4. **Powrót do lokalnego** — wybierz `LOCAL` z combo box
   - Base URL przywrócony na `http://127.0.0.1:18080/v1`
   - API key przywrócony na `ollama`
   - Model przywrócony na `local`

---

## Zarządzanie kluczami API

### Bezpieczeństwo

**Uwaga:** Klucze API są przechowywane w `~/.config/tlumacz/config.json` jako **zwykły tekst**.

**Zalecenia:**
- Nie udostępniaj pliku `config.json`
- Ustaw uprawnienia do pliku: `chmod 600 ~/.config/tlumacz/config.json`
- Rozważ użycie menedżera haseł (np. KeePass, Bitwarden)
- Regularnie rotuj klucze API

### Przechowywanie kluczy

Klucze API są przechowywane w dwóch miejscach:

1. **cloud_models.json** — domyślne klucze dla modeli chmurowych (opcjonalne)
2. **config.json** — aktualnie używany klucz API (pole `api_key`)

### Rotacja kluczy

Jeśli podejrzewasz wyciek klucza:

1. **Google AI Studio:**
   - Przejdź do [Google AI Studio](https://aistudio.google.com/)
   - Kliknij „Get API Key"
   - Kliknij „Revoke" przy starym kluczu
   - Wygeneruj nowy klucz

2. **OpenAI:**
   - Przejdź do [OpenAI Platform](https://platform.openai.com/)
   - Kliknij „API Keys"
   - Kliknij „Revoke" przy starym kluczu
   - Kliknij „Create new secret key"

---

## Rate limits i koszty

### Google Gemini

| Model | Limit RPM | Limit TPM | Cena (input) | Cena (output) |
|-------|-----------|-----------|--------------|---------------|
| gemini-3.5-flash | 60 | 1M | Darmowy* | Darmowy* |
| gemini-3.5-flash-lite | 1500 | 1M | Darmowy* | Darmowy* |

*Darmowy tier ma dzienne limity. Po przekroczeniu musisz przejść na płatny plan.

### OpenAI

| Model | Cena (input) | Cena (output) |
|-------|--------------|---------------|
| gpt-4-turbo | $10 / 1M tokenów | $30 / 1M tokenów |
| gpt-3.5-turbo | $0.50 / 1M tokenów | $1.50 / 1M tokenów |

### Szacowanie kosztów

**Przykład:** Tłumaczenie dokumentu 10 000 słów (~13 000 tokenów)

**Gemini 3.5 Flash:**
- Input: 13 000 tokenów × $0 = $0
- Output: 13 000 tokenów × $0 = $0
- **Koszt: $0** (w darmowym tierze)

**GPT-4 Turbo:**
- Input: 13 000 tokenów × $10 / 1M = $0.13
- Output: 13 000 tokenów × $30 / 1M = $0.39
- **Koszt: $0.52**

### Optymalizacja kosztów

1. **Użyj cache** — włącz „Czyść cache po tłumaczeniu" = OFF dla powtarzających się dokumentów
2. **Zmniejsz chunk_size** — mniejsze fragmenty = mniej zmarnowanych tokenów
3. **Użyj tańszych modeli** — Gemini Flash Lite jest darmowy i szybki
4. **Monitoruj użycie** — sprawdzaj dashboard Google AI Studio lub OpenAI

---

## Rozwiązywanie problemów

### Błąd 401 Unauthorized

**Przyczyna:** Nieprawidłowy klucz API.

**Rozwiązanie:**
1. Sprawdź czy klucz API jest poprawny
2. Sprawdź czy klucz nie wygasł
3. Wygeneruj nowy klucz API

### Błąd 429 Too Many Requests

**Przyczyna:** Przekroczono rate limit.

**Rozwiązanie:**
1. Poczekaj minutę i spróbuj ponownie
2. Zmniejsz `parallel` w ustawieniach
3. Przełącz na model z wyższym limitem (np. `gemini-3.5-flash-lite`)
4. Zwiększ `chunk_size` aby zmniejszyć liczbę zapytań

### Błąd 404 Not Found

**Przyczyna:** Nieprawidłowy Base URL lub nazwa modelu.

**Rozwiązanie:**
1. Sprawdź Base URL (np. `https://generativelanguage.googleapis.com/v1beta/openai/`)
2. Sprawdź nazwę modelu (np. `gemini-3.5-flash`)
3. Sprawdź dokumentację API dostawcy

### Timeout

**Przyczyna:** Serwer nie odpowiada w czasie.

**Rozwiązanie:**
1. Sprawdź połączenie internetowe
2. Spróbuj ponownie za chwilę
3. Zmniejsz `chunk_size` aby przyspieszyć
4. Przełącz na inny model chmurowy

### Brak odpowiedzi (pusty wynik)

**Przyczyna:** Model zwrócił pustą odpowiedź.

**Rozwiązanie:**
1. Sprawdź logi w zakładce „Tłumaczenie"
2. Zwiększ `max_tokens` w kodzie (obecnie skalowane proporcjonalnie do `chunk_size`)
3. Zmień model na bardziej niezawodny (np. Gemini Flash)

---

## Porównanie chmury i lokalnego serwera

| Cecha | Chmura | Lokalny serwer |
|-------|--------|----------------|
| **Wymagania sprzętowe** | Brak | GPU + RAM |
| **Szybkość** | Szybka | Zależy od sprzętu |
| **Jakość** | Wysoka | Zależy od modelu |
| **Koszt** | Płatne (lub darmowy tier) | Darmowe |
| **Prywatność** | Dokumenty w chmurze | Wszystko lokalnie |
| **Rate limits** | Tak | Brak |
| **Internet** | Wymagany | Nie wymagany |
| **Konfiguracja** | Prosta (klucz API) | Średnia (GGUF, port, szablon) |

### Kiedy używać chmury

- Brak GPU lub mało RAM
- Potrzebujesz wysokiej jakości tłumaczenia
- Tłumaczysz rzadko (wystarczy darmowy tier)
- Nie chcesz konfigurować lokalnego serwera

### Kiedy używać lokalnego serwera

- Masz GPU z VRAM
- Tłumaczysz dużo (brak rate limits)
- Prywatność jest kluczowa
- Nie masz stabilnego internetu
- Chcesz pełną kontrolę nad modelem

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
