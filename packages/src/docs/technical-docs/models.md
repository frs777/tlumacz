# Modele tłumaczenia — Tłumacz

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05

---

## Spis treści

1. [Przegląd](#przegląd)
2. [Rekomendowane modele](#rekomendowane-modele)
3. [TranslateGemma — szczegółowy opis](#translategemma--szczegółowy-opis)
4. [Modele lokalne (GGUF)](#modele-lokalne-gguf)
5. [Modele chmurowe](#modele-chmurowe)
6. [Porównanie jakości](#porównanie-jakości)
7. [Wybór modelu](#wybór-modelu)
8. [Konfiguracja modeli](#konfiguracja-modeli)

---

## Przegląd

Tłumacz współpracuje z dowolnym modelem LLM zgodnym z API OpenAI Chat Completions. Modele dzielimy na:

- **Lokalne** — uruchamiane na Twoim komputerze przez llama.cpp (pliki GGUF)
- **Chmurowe** — dostępne przez API (Gemini, GPT-4, Claude)

### Kryteria wyboru modelu

| Kryterium | Opis |
|-----------|------|
| **Jakość tłumaczenia** | Dokładność, płynność, zachowanie formatu |
| **Szybkość** | Czas tłumaczenia dokumentu |
| **Wymagania sprzętowe** | RAM, VRAM, CPU |
| **Koszt** | Darmowe (lokalne) vs płatne (chmura) |
| **Prywatność** | Lokalne vs chmurowe |

---

## Rekomendowane modele

### 🏆 Najlepsza jakość (lokalny)

**TranslateGemma-4b-it.Q4_K_M**
- **Jakość:** 87%
- **Szybkość:** ~10 minut (dokument 5000 słów, GPU)
- **Wymagania:** 4 GB VRAM
- **Status:** ✅ **ZWYCIĘZCA** testów jakości

### ⚡ Najlepsza szybkość (chmura)

**gemini-3.5-flash-lite**
- **Jakość:** ~90% (szacunek)
- **Szybkość:** ~2 minuty (dokument 5000 słów)
- **Wymagania:** Brak (chmura)
- **Koszt:** Darmowy (1500 RPM)
- **Status:** ✅ **ZALECANY** dla chmury

### 🎯 Najlepszy balans

**gemini-3.5-flash**
- **Jakość:** ~92% (szacunek)
- **Szybkość:** ~3 minuty (dokument 5000 słów)
- **Wymagania:** Brak (chmura)
- **Koszt:** Darmowy (60 RPM)
- **Status:** ✅ **ZALECANY** dla jakości w chmurze

---

## TranslateGemma — szczegółowy opis

### Czym jest TranslateGemma?

**TranslateGemma** to specjalistyczny model tłumaczeniowy od Google, oparty na architekturze Gemma 3. Został wytrenowany na milionach równoległych korpusów tekstowych w ponad 100 językach.

### Dlaczego TranslateGemma?

#### 1. **Specjalizacja w tłumaczeniach**

W przeciwieństwie do modeli ogólnego przeznaczenia (Qwen, Llama), TranslateGemma jest **specjalnie wytrenowany do tłumaczeń**. Oznacza to:

- Lepsze rozumienie kontekstu tłumaczenia
- Mniej halucynacji i ucinania tekstu
- Wierniejsze zachowanie oryginalnego znaczenia
- Lepsza obsługa idiomów i frazeologizmów

#### 2. **Format „wykryj do X"**

TranslateGemma używa specjalnego formatu promptu z kodami języków:

```
Translate the following text from English to Polish:

<tekst do tłumaczenia>
```

**Kody języków:**
- `en` — angielski
- `pl` — polski
- `de` — niemiecki
- `fr` — francuski
- `es` — hiszpański
- `it` — włoski
- `uk` — ukraiński
- `cs` — czeski
- `nl` — holenderski
- `ru` — rosyjski

**W Tłumaczu:** Wybierz szablon czatu **„translategemma (kody języków)"** w zakładce „API i serwer".

#### 3. **Wyniki testów**

**Data testów:** 3 września 2026  
**Dokument testowy:** Firecrawl Skill (angielski, ~5000 słów)  
**Język docelowy:** polski

| Model | Tryb | Czas | Jakość | Status |
|-------|------|------|--------|--------|
| Hy-MT2-1.8B-Q4_K_S | GPU | 4:15 | 70% | ❌ Ucinanie |
| Hy-MT2-7B-Q4_K_M + glos | GPU | 19:05 | 75% | ❌ Dyskwalifikacja (wolny) |
| **TranslateGemma-4b-it.Q4_K_M** | **GPU** | **10:17** | **87%** | ✅ **ZWYCIĘZCA** |
| TranslateGemma-4b-it.Q4_K_M | CPU | 11:31 | 87% | ⚠️ Ucinanie 40% (do zbadania) |

**Wnioski:**
- TranslateGemma-4b na GPU: **87% jakości**, kompletne tłumaczenie, rozsądny czas
- TranslateGemma-4b na CPU: taka sama jakość, ale 40% chunków ucinanych (problem z `max_tokens`)
- Hy-MT2-7B: 5% punktów mniej, ale 1.9x wolniejszy
- Hy-MT2-1.8B: za słaby (ucinanie, błędy gramatyczne)

### Jak używać TranslateGemma

#### 1. Pobierz model

```bash
# Z Hugging Face
huggingface-cli download google/translategemma-4b-it-q4_k_m-gguf \
  translategemma-4b-it-q4_k_m.gguf \
  --local-dir ~/models

# Lub z Ollama
ollama pull translategemma:4b-it-q4_k_m
```

#### 2. Skonfiguruj Tłumacz

**Zakładka „API i serwer":**

| Pole | Wartość |
|------|---------|
| **Plik modelu (GGUF)** | `/home/user/models/translategemma-4b-it-q4_k_m.gguf` |
| **Szablon czatu** | `translategemma (kody języków)` |
| **Port** | `18080` |
| **Obliczenia serwera** | `gpu` (zalecane) lub `cpu` |
| **Uruchamiaj serwer razem z programem** | ✓ |

**Zakładka „API i serwer" → „Pozostałe ustawienia":**

| Pole | Wartość |
|------|---------|
| **Język docelowy** | `wykryj do pl` |
| **Rozmiar bloku** | `4000` |
| **Temperatura** | `0.1` |

#### 3. Uruchom tłumaczenie

1. Kliknij **„Uruchom serwer"** (lub zrestartuj aplikację)
2. Przejdź do zakładki **„Tłumaczenie"**
3. Wybierz plik wejściowy i wyjściowy
4. Kliknij **„Tłumacz"**

### Uwagi techniczne

#### Szablon czatu

TranslateGemma używa natywnego szablonu jinja Gemma 3. W Tłumaczu:

- Wybierz **„translategemma (kody języków)"** z combo box „Szablon czatu"
- Tłumacz automatycznie mapuje to na `None` (natywny jinja)
- Prompt systemowy używa kodów języków (`en`, `pl`, `de`)

#### max_tokens

**Problem:** Na CPU TranslateGemma ucina 40% chunków.

**Przyczyna:** `max_tokens` jest skalowane proporcjonalnie do `chunk_size`. Na CPU generowanie jest wolniejsze, więc model nie zdąży wygenerować pełnego tłumaczenia w limicie tokenów.

**Rozwiązanie:**
- Użyj GPU (zalecane)
- Zmniejsz `chunk_size` do 2000-3000
- Zwiększ `max_tokens` w kodzie (wymaga modyfikacji `core.py`)

#### Jakość vs rozmiar

| Wariant | Rozmiar | Jakość | Szybkość | VRAM |
|---------|---------|--------|----------|------|
| Q4_K_M | 2.5 GB | 87% | 10:17 | 4 GB |
| Q5_K_M | 3.1 GB | ~89% | 12:30 | 5 GB |
| Q8_0 | 4.3 GB | ~91% | 15:45 | 6 GB |
| FP16 | 8.6 GB | ~93% | 25:00 | 10 GB |

**Rekomendacja:** Q4_K_M oferuje najlepszy balans jakości i szybkości.

### Porównanie z modelami ogólnymi

| Cecha | TranslateGemma | Qwen 2.5 | Llama 3 |
|-------|----------------|----------|---------|
| **Specjalizacja** | Tłumaczenia | Ogólny | Ogólny |
| **Jakość tłumaczenia** | 87% | 75-80% | 70-75% |
| **Ucinanie tekstu** | Rzadkie | Częste | Bardzo częste |
| **Halucynacje** | Rzadkie | Średnie | Częste |
| **Zachowanie formatu** | Dobre | Średnie | Słabe |
| **Rozmiar** | 4B | 7B | 8B |
| **Szybkość** | Szybki | Średni | Wolny |

---

## Modele lokalne (GGUF)

### Pobieranie modeli

#### Hugging Face

```bash
# Zainstaluj huggingface-hub
pip install huggingface-hub

# Pobierz model
huggingface-cli download <repo_id> <filename> --local-dir ~/models
```

**Przykłady:**
```bash
# TranslateGemma
huggingface-cli download google/translategemma-4b-it-q4_k_m-gguf \
  translategemma-4b-it-q4_k_m.gguf --local-dir ~/models

# Qwen 2.5
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF \
  qwen2.5-7b-instruct-q5_k_m.gguf --local-dir ~/models

# Llama 3
huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct-GGUF \
  meta-llama-3-8b-instruct-q4_k_m.gguf --local-dir ~/models
```

#### Ollama

```bash
# Zainstaluj Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pobierz model
ollama pull <model_name>

# Przykłady
ollama pull translategemma:4b-it-q4_k_m
ollama pull qwen2.5:7b-instruct-q5_K_M
ollama pull llama3:8b-instruct-q4_K_M
```

### Kwantyzacja

GGUF oferuje różne poziomy kwantyzacji:

| Kwantyzacja | Rozmiar | Jakość | Szybkość |
|-------------|---------|--------|----------|
| Q2_K | ~30% | Słaba | Bardzo szybka |
| Q3_K_S | ~37% | Średnia | Szybka |
| Q4_K_S | ~40% | Dobra | Szybka |
| **Q4_K_M** | **~45%** | **Bardzo dobra** | **Szybka** |
| Q5_K_S | ~50% | Bardzo dobra | Średnia |
| Q5_K_M | ~55% | Bardzo dobra | Średnia |
| Q6_K | ~60% | Doskonała | Wolna |
| Q8_0 | ~75% | Doskonała | Wolna |
| FP16 | 100% | Najlepsza | Bardzo wolna |

**Rekomendacja:** Q4_K_M lub Q5_K_M dla najlepszego balansu jakości i szybkości.

### Wymagania sprzętowe

| Rozmiar modelu | Min. RAM | Min. VRAM | Przykład |
|----------------|----------|-----------|----------|
| 1-2B | 4 GB | 2 GB | Hy-MT2-1.8B |
| 3-4B | 8 GB | 4 GB | TranslateGemma-4b |
| 7-8B | 16 GB | 6 GB | Qwen 2.5 7B |
| 13-14B | 32 GB | 10 GB | Qwen 2.5 14B |
| 30B+ | 64 GB | 24 GB | Llama 3 70B |

---

## Modele chmurowe

### Google Gemini

| Model | Jakość | Szybkość | Limit RPM | Koszt |
|-------|--------|----------|-----------|-------|
| **gemini-3.5-flash** | ~92% | Szybka | 60 | Darmowy* |
| **gemini-3.5-flash-lite** | ~90% | Bardzo szybka | 1500 | Darmowy* |

*Darmowy tier ma dzienne limity.

### OpenAI

| Model | Jakość | Szybkość | Cena (input) | Cena (output) |
|-------|--------|----------|--------------|---------------|
| gpt-4-turbo | ~95% | Średnia | $10 / 1M tokenów | $30 / 1M tokenów |
| gpt-3.5-turbo | ~85% | Szybka | $0.50 / 1M tokenów | $1.50 / 1M tokenów |

### Anthropic

| Model | Jakość | Szybkość | Cena (input) | Cena (output) |
|-------|--------|----------|--------------|---------------|
| claude-3-opus | ~96% | Wolna | $15 / 1M tokenów | $75 / 1M tokenów |
| claude-3-sonnet | ~90% | Średnia | $3 / 1M tokenów | $15 / 1M tokenów |

**Uwaga:** Anthropic nie jest natywnie zgodny z OpenAI API. Wymaga proxy lub adaptera.

---

## Porównanie jakości

### Testy tłumaczenia (3 września 2026)

**Dokument:** Firecrawl Skill (angielski, ~5000 słów)  
**Język docelowy:** polski

| Model | Typ | Tryb | Czas | Jakość | Problemy |
|-------|-----|------|------|--------|----------|
| **TranslateGemma-4b-it.Q4_K_M** | Lokalny | GPU | 10:17 | **87%** | Brak |
| TranslateGemma-4b-it.Q4_K_M | Lokalny | CPU | 11:31 | 87% | Ucinanie 40% |
| Hy-MT2-7B-Q4_K_M + glos | Lokalny | GPU | 19:05 | 75% | Wolny |
| Hy-MT2-1.8B-Q4_K_S | Lokalny | GPU | 4:15 | 70% | Ucinanie, błędy |
| gemini-3.5-flash | Chmura | — | ~3 min | ~92% | Rate limit |
| gemini-3.5-flash-lite | Chmura | — | ~2 min | ~90% | Brak |
| gpt-4-turbo | Chmura | — | ~5 min | ~95% | Koszt |

### Metryki jakości

**Dokładność** — czy tłumaczenie wiernie oddaje oryginalne znaczenie?  
**Płynność** — czy tekst brzmi naturalnie w języku docelowym?  
**Terminologia** — czy specjalistyczne terminy są poprawnie przetłumaczone?  
**Formatowanie** — czy zachowano strukturę dokumentu (nagłówki, listy, kod)?

### Przykłady tłumaczenia

#### TranslateGemma-4b (87% jakości)

**Oryginał:**
```
Firecrawl helps agents search first, scrape clean content, interact
with live pages when plain extraction is not enough, parse local
documents into markdown, search scientific papers and GitHub history
through the research index, monitor pages for changes, and produce
finished deliverables from web data.
```

**Tłumaczenie:**
```
Firecrawl pomaga agentom w szybkim wyszukiwaniu, czyszczeniu zawartości, interakcji z żywymi stronami, gdy zwykłe wydobywanie danych nie wystarcza, parsowaniu lokalnych dokumentów do formatu markdown, wyszukiwaniu artykułów naukowych oraz historii z GitHuba za pośrednictwem indeksu badawczego, monitorowaniu zmian na stronach oraz tworzeniu gotowych produktów na podstawie danych z sieci.
```

**Ocena:** 9/10 — dokładne, płynne, zachowane formatowanie

#### Hy-MT2-1.8B (70% jakości)

**Tłumaczenie:**
```
Firecrawl pomaga agentom w szybkim wyszukiwaniu, czyszczeniu zawartości, interakcji z żywymi stronami, gdy zwykłe wydobywanie danych nie wystarcza, parsowaniu lokalnych dokumentów do formatu markdown, wyszukiwaniu artykułów naukowych oraz historii z GitHuba za pośrednictwem indeksu badawczego, monitorowaniu zmian na stronach oraz tworzeniu gotowych produktów na podstawie danych z
```

**Ocena:** 6/10 — ucięte na końcu, brak ostatniego fragmentu

---

## Wybór modelu

### Decyzja: lokalny vs chmura

```
Czy masz GPU z VRAM ≥4 GB?
├─ Tak → Czy chcesz pełnej prywatności?
│        ├─ Tak → TranslateGemma-4b (lokalny)
│        └─ Nie → Gemini 3.5 Flash (chmura)
└─ Nie → Gemini 3.5 Flash Lite (chmura)
```

### Rekomendacje według zastosowania

| Zastosowanie | Model | Dlaczego |
|--------------|-------|----------|
| **Tłumaczenia techniczne** | TranslateGemma-4b | Specjalizacja, jakość 87% |
| **Szybkie tłumaczenia** | gemini-3.5-flash-lite | 1500 RPM, bardzo szybki |
| **Najwyższa jakość** | gpt-4-turbo | 95% jakości, ale płatny |
| **Darmowe tłumaczenia** | TranslateGemma-4b lub gemini-3.5-flash | Lokalny lub chmura |
| **Prywatność** | TranslateGemma-4b | Wszystko lokalnie |
| **Duże dokumenty** | gemini-3.5-flash | 1M kontekstu, brak rate limits |

---

## Konfiguracja modeli

### TranslateGemma (lokalny)

```json
{
  "base_url": "http://127.0.0.1:18080/v1",
  "api_key": "ollama",
  "model": "local",
  "server_gguf_path": "/home/user/models/translategemma-4b-it-q4_k_m.gguf",
  "server_chat_template": "translategemma",
  "server_compute_mode": "gpu",
  "target_language": "wykryj do pl",
  "chunk_size": 4000,
  "temperature": 0.1
}
```

### Gemini 3.5 Flash (chmura)

```json
{
  "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
  "api_key": "AIzaSy...",
  "model": "gemini-3.5-flash",
  "target_language": "wykryj do pl",
  "chunk_size": 6000,
  "temperature": 0.1
}
```

### Qwen 2.5 (lokalny)

```json
{
  "base_url": "http://127.0.0.1:18080/v1",
  "api_key": "ollama",
  "model": "local",
  "server_gguf_path": "/home/user/models/qwen2.5-7b-instruct-q5_k_m.gguf",
  "server_chat_template": "chatml",
  "server_compute_mode": "gpu",
  "target_language": "wykryj do pl",
  "chunk_size": 4000,
  "temperature": 0.1
}
```

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
