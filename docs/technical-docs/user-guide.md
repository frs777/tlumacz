# Podręcznik użytkownika — Tłumacz

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05

---

## Spis treści

1. [Wymagania systemowe](#wymagania-systemowe)
2. [Instalacja](#instalacja)
3. [Pierwsze uruchomienie](#pierwsze-uruchomienie)
4. [Interfejs użytkownika](#interfejs-użytkownika)
5. [Tłumaczenie dokumentów](#tłumaczenie-dokumentów)
6. [Konfiguracja API](#konfiguracja-api)
7. [Serwer lokalny](#serwer-lokalny)
8. [Tłumaczenie w chmurze](#tłumaczenie-w-chmurze)
9. [Glosariusz](#glosariusz)
10. [Skille](#skille)
11. [Zaawansowane funkcje](#zaawansowane-funkcje)
12. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Wymagania systemowe

### Minimalne

- **Python 3.10+**
- **System operacyjny:** Linux (testowano na Arch Linux/KDE Plasma), Windows, macOS
- **RAM:** 4 GB (8 GB zalecane dla modeli 7B+)
- **GPU:** opcjonalne, ale zalecane (Vulkan/CUDA)

### Opcjonalne zależności

- **llama-server** — dla wbudowanego zarządzanego serwera lokalnego
- **pandoc** — dla ekstrakcji DOCX (alternatywnie PyMuPDF)
- **poppler-utils** (`pdftotext`) — dla ekstrakcji PDF

---

## Instalacja

### Ze źródeł (rozwój)

```bash
# Sklonuj repozytorium
git clone https://github.com/frs777/tlumacz.git
cd tlumacz

# Zainstaluj w trybie deweloperskim
pip install -e .

# Uruchom aplikację
tlumacz
```

### Budowanie wheel

```bash
python -m build --wheel
```

### Arch Linux (AUR)

```bash
# Z lokalnego repozytorium
sudo pacman -S tlumacz

# Lub zbuduj z PKGBUILD
makepkg -si
```

---

## Pierwsze uruchomienie

Po uruchomieniu `tlumacz` zobaczysz główne okno z czterema zakładkami:

1. **Tłumaczenie** — wybór plików, przyciski tłumaczenia, log i podgląd
2. **API i serwer** — konfiguracja API, ustawienia serwera lokalnego
3. **Dodatki** — glosariusz, skille, pozostałe ustawienia
4. **Pomoc** — wbudowana pomoc w języku polskim i angielskim

### Szybki start (lokalny serwer)

1. Przejdź do zakładki **„API i serwer"**
2. W sekcji **„Serwer lokalny"** wskaż plik modelu GGUF
3. Zaznacz **„Uruchamiaj serwer razem z programem"**
4. Kliknij przycisk **„Uruchom serwer"** (lub zrestartuj aplikację)
5. Wróć do zakładki **„Tłumaczenie"**
6. Wybierz plik wejściowy i wyjściowy
7. Kliknij **„Tłumacz"**

### Szybki start (chmura)

1. Przejdź do zakładki **„API i serwer"**
2. W polu **„Model"** wybierz model chmurowy (np. `gemini-3.5-flash`)
3. Wprowadź klucz API w polu **„API key"**
4. Base URL zostanie ustawiony automatycznie
5. Wróć do zakładki **„Tłumaczenie"** i rozpocznij tłumaczenie

---

## Interfejs użytkownika

### Zakładka „Tłumaczenie"

#### Sekcja „Pliki"

- **Plik wejściowy** — ścieżka do dokumentu do przetłumaczenia
- **Plik wyjściowy** — ścieżka gdzie zostanie zapisane tłumaczenie (domyślnie `nazwa_pl.rozszerzenie`)
- **Przyciski „Przeglądaj..."** — otwierają dialog wyboru pliku

#### Przyciski tłumaczenia

- **Tłumacz** — rozpoczyna tłumaczenie w tle
- **Anuluj** — przerywa trwające tłumaczenie (kooperatywny cancel)

#### Pasek postępu i status

- **Pasek postępu** — pokazuje postęp tłumaczenia (bloki przetłumaczone / całkowite)
- **Stoper** — wyświetla czas trwania tłumaczenia
- **Spinner** — animowany wskaźnik aktywności

#### Log i podgląd

- **Log** — komunikaty statusu na żywo (postęp, błędy, statystyki cache)
- **Podgląd tłumaczenia** — podgląd przetłumaczonego tekstu (w przypadku niektórych rodzajów plików podgląd nie działa)

---

### Zakładka „API i serwer"

#### Sekcja „Ustawienia API"

| Pole | Opis | Przykład |
|------|------|----------|
| **Base URL** | Adres serwera API zgodnego z OpenAI | `http://127.0.0.1:18080/v1` |
| **API key** | Token uwierzytelniający | `ollama` (lokalny), klucz API (chmura) |
| **Model** | Nazwa modelu (combo box) | `LOCAL`, `gemini-3.5-flash`, własny |

#### Sekcja „Serwer lokalny"

| Pole | Opis | Przykład |
|------|------|----------|
| **Port** | Port serwera llama-server | `18080` |
| **Obliczenia serwera** | Tryb obliczeń | `gpu` (Vulkan), `cpu` |
| **Plik modelu (GGUF)** | Ścieżka do pliku modelu | `/home/user/models/model.gguf` |
| **Szablon czatu** | Format szablonu czatu | `jinja`, `chatml`, `translategemma` |
| **Wątki (parallel)** | Liczba równoległych slotów | `1` (zalecane dla lokalnego) |
| **Uruchamiaj serwer razem z programem** | Auto-start serwera | ✓ |

#### Przycisk multifunkcyjny „Restart serwera"

Przycisk zmienia etykietę i zachowanie w zależności od stanu serwera i checkboxa auto-start:

| Stan serwera | Auto-start | Etykieta przycisku | Akcja |
|--------------|------------|-------------------|-------|
| Działa | ✓ | **Restart serwera** | Zatrzymaj i uruchom ponownie |
| Działa | ✗ | **Zatrzymaj serwer** | Tylko zatrzymaj |
| Zatrzymany | ✓ | **Uruchom serwer** | Uruchom z aktualnymi ustawieniami |
| Zatrzymany | ✗ | **Zaznacz box 'Uruchamiaj serwer razem z programem'** | Pokaż informację |

**Uwaga:** Przycisk jest **zawsze aktywny** (nigdy nie zablokowany).

#### Sekcja „Pozostałe ustawienia"

| Pole | Opis | Zalecana wartość |
|------|------|------------------|
| **Rozmiar bloku** | Wielkość fragmentu tekstu (znaki) | `4000-6000` |
| **Temperatura** | Losowość odpowiedzi | `0.1-0.3` |
| **Język docelowy** | Język tłumaczenia | `wykryj do pl` |
| **Motyw** | Wygląd interfejsu | `Systemowy` |
| **Własny prompt** | Opcjonalny prompt systemowy | (puste) |
| **Pomijane linie (regex)** | Regexy linii nietłumaczonych | (domyślne) |
| **Czyść cache po tłumaczeniu** | Automatyczne czyszczenie cache | ✓ |

---

### Zakładka „Dodatki"

#### Sekcja „Glosariusz"

- **Plik glosariusza** — ścieżka do pliku CSV (`źródło,tłumaczenie`)
- **Dodaj wpis** — formularz do dodawania wpisów bezpośrednio z GUI
- **Licznik wpisów** — wyświetla liczbę załadowanych wpisów

#### Sekcja „Skille"

- **Skill** — to tak naprawde prompt dla modelu
- **Lista skilli** — checkboxy do włączania/wyłączania skilli
- **Odśwież** — przeładuj listę skilli z dysku
- **Importuj skilla...** — zaimportuj plik `.md` jako skill
- **Nowy skill...** — utwórz nowy plik szablonu skilla

#### Przycisk „Przywróć domyślne"

Zapisuje kopię zapasową `config.json` i przywraca ustawienia domyślne. Ścieżki plików (wejściowy, wyjściowy, glosariusz) są zachowywane.

---

### Zakładka „Pomoc"

Wbudowana pomoc w języku polskim i angielskim. Zawiera:

- Opis wszystkich parametrów
- Tabelę z zalecanymi wartościami
- Instrukcje konfiguracji serwera
- Opis glosariusza i skilli

**Przełączanie języka:** ComboBox „Język / Language" w prawym górnym rogu.

---

## Tłumaczenie dokumentów

### Obsługiwane formaty

| Format | Rozszerzenie | Tryb tłumaczenia | Zachowanie formatu |
|--------|--------------|------------------|-------------------|
| **Markdown** | `.md`, `.markdown` | Bezpośrednie | ✅ Zachowane |
| **Tekst** | `.txt` | Bezpośrednie | ✅ Zachowane |
| **HTML** | `.html`, `.htm` | Z ochroną tagów | ✅ Zachowane |
| **PDF** | `.pdf` | Tekstowe z zachowaniem układu | ⚠️ Częściowe (bez OCR) |
| **DOCX** | `.docx` | Round-trip XML | ✅ Zachowane |
| **ODT** | `.odt` | Round-trip XML | ✅ Zachowane |
| **EPUB** | `.epub` | Round-trip XHTML | ✅ Zachowane |

### Proces tłumaczenia

1. **Ekstrakcja tekstu** — dla formatów binarnych (PDF, DOCX, ODT, EPUB)
2. **Preprocessing** — ochrona kodu, URL-i, fragmentów nietłumaczonych
3. **Chunking** — podział tekstu na fragmenty (domyślnie 4000 znaków)
4. **Tłumaczenie** — wysłanie każdego fragmentu do API (równolegle jeśli `parallel > 1`)
5. **Postprocessing** — przywrócenie chronionych fragmentów
6. **Zapis** — zapisanie wyniku do pliku wyjściowego

### Round-trip dla formatów binarnych

Dla DOCX, ODT i EPUB tłumacz przetwarza **XML wewnątrz archiwum**, tłumacząc tylko węzły tekstowe. Struktura dokumentu (style, tabele, obrazy, czcionki) jest zachowywana 1:1.

**Proces:**
1. Rozpakowanie archiwum (ZIP)
2. Znalezienie plików treści (np. `word/document.xml` dla DOCX)
3. Tłumaczenie węzłów tekstowych in-place
4. Ponowne spakowanie archiwum

### Cache tłumaczeń

Tłumacz używa cache SQLite (`~/.config/tlumacz/cache.db`) do przechowywania przetłumaczonych fragmentów. Klucz cache to hash: `chunk + system_prompt + skill + model + temperature`.

**Zalety:**
- Przyspieszenie tłumaczenia dokumentów z powtarzającymi się fragmentami
- Oszczędność wywołań API (koszt, czas)

**Auto-cleanup:** Wpisy są automatycznie usuwane przy starcie aplikacji.

**Statystyki:** Po każdym tłumaczeniu w logach wyświetlane są statystyki cache (trafienia/pudła, skuteczność).

---

## Konfiguracja API

### Lokalne serwery

Tłumacz współpracuje z dowolnym serwerem zgodnym z API OpenAI:

#### llama.cpp (llama-server)

```bash
# Uruchom serwer ręcznie
llama-server \
  -m /ścieżka/do/model.gguf \
  --host 127.0.0.1 \
  --port 18080 \
  --ctx-size 8192 \
  --jinja

# Lub użyj wbudowanego zarządzanego serwera (zalecane)
```

**Konfiguracja w GUI:**
- Base URL: `http://127.0.0.1:18080/v1`
- API key: `ollama` (placeholder, ignorowany)
- Model: `local` (alias dla zarządzanego serwera)

#### Ollama

```bash
# Uruchom serwer
ollama serve

# Załaduj model
ollama pull qwen2.5-coder:7b-instruct-q5_K_M
```

**Konfiguracja w GUI:**
- Base URL: `http://127.0.0.1:11434/v1`
- API key: `ollama`
- Model: `qwen2.5-coder:7b-instruct-q5_K_M`

### Zdalne serwery (chmura)

Zobacz sekcję [Tłumaczenie w chmurze](#tłumaczenie-w-chmurze).

---

## Serwer lokalny

### Zarządzany serwer (zalecane)

Tłumacz może automatycznie zarządzać procesem `llama-server`:

1. **Wskaż plik GGUF** w zakładce „API i serwer" → „Plik modelu (GGUF)"
2. **Zaznacz** „Uruchamiaj serwer razem z programem"
3. **Uruchom aplikację** — serwer startuje automatycznie w tle
4. **Zamknij aplikację** — serwer jest zatrzymywany automatycznie

**Zalety:**
- Nie musisz ręcznie uruchamiać/zatrzymywać serwera
- Automatyczne czyszczenie osieroconych procesów
- Automatyczny restart przy błędach

### Ręczne zarządzanie serwerem

Jeśli wolisz kontrolować serwer ręcznie:

1. **Nie zaznaczaj** „Uruchamiaj serwer razem z programem"
2. **Uruchom serwer** w terminalu:
   ```bash
   llama-server -m model.gguf --port 18080 --jinja
   ```
3. **Użyj przycisku** „Uruchom serwer" / „Restart serwera" w GUI jeśli chcesz przejąć kontrolę

### Szablony czatu

| Szablon | Opis | Kiedy używać |
|---------|------|--------------|
| **jinja** | Natywny szablon modelu | Domyślny, większość modeli |
| **chatml** | Format ChatML | Modele z nieprawidłowym jinja |
| **translategemma** | Kody języków (en, pl, de) | Tylko TranslateGemma |

**Automatyczny fallback:** Jeśli serwer nie uruchomi się z wybranym szablonem, Tłumacz automatycznie próbuje alternatywne szablony.

### Tryb obliczeń

| Tryb | Opis | Kiedy używać |
|------|------|--------------|
| **gpu** | Vulkan/CUDA offload | Karta graficzna z VRAM |
| **cpu** | Tylko CPU | Brak GPU lub mały VRAM |

**Uwaga:** Tryb `gpu` z `--n-gpu-layers 999` próbuje offloadować wszystkie warstwy do GPU. Jeśli nie ma wystarczającej ilości VRAM, llama-server automatycznie dostosuje liczbę warstw.

---

## Tłumaczenie w chmurze

### Obsługiwane modele chmurowe

Tłumacz obsługuje modele chmurowe przez API zgodne z OpenAI:

#### Google Gemini

| Model | Opis | Limit |
|-------|------|-------|
| **gemini-3.5-flash** | Szybki model ogólnego przeznaczenia | 60 RPM |
| **gemini-3.5-flash-lite** | Najszybszy, prawie nieograniczony | 1500 RPM |

**Konfiguracja:**
1. Wybierz model z combo box „Model" (np. `gemini-3.5-flash`)
2. Base URL zostanie ustawiony automatycznie: `https://generativelanguage.googleapis.com/v1beta/openai/`
3. Wprowadź klucz API Google AI Studio w polu „API key"

**Uzyskanie klucza API:**
1. Przejdź do [Google AI Studio](https://aistudio.google.com/)
2. Zaloguj się kontem Google
3. Kliknij „Get API Key" → „Create API Key"
4. Skopiuj klucz i wklej do pola „API key" w Tłumaczu

#### Inne modele

Możesz użyć dowolnego modelu chmurowego zgodnego z OpenAI API:

1. Wybierz „(wprowadź ręcznie)" z combo box „Model"
2. Wpisz nazwę modelu w polu tekstowym
3. Ustaw odpowiedni Base URL i API key

### Przełączanie między lokalnym a chmurowym

**Combo box „Model"** zawiera:
- Modele chmurowe (z `cloud_models.json`)
- Separator
- **LOCAL** — przywraca ostatnie ustawienia lokalnego serwera
- **(wprowadź ręcznie)** — pole tekstowe dla własnego modelu

**Zachowanie:**
- Wybór modelu chmurowego → automatyczne ustawienie Base URL i API key
- Wybór LOCAL → przywrócenie `last_local_base_url`, `last_local_api_key`, `last_local_model`
- Własny model → ręczna konfiguracja

### Pamięć ustawień lokalnych

Tłumacz zapamiętuje ostatnie ustawienia lokalnego serwera:
- `last_local_base_url` — ostatni Base URL
- `last_local_api_key` — ostatni API key
- `last_local_model` — ostatni model

Dzięki temu przełączanie między chmurą a lokalnym serwerem jest szybkie i bezbolesne.

---

## Glosariusz

### Format pliku CSV

Glosariusz to plik CSV dwukolumnowy:

```csv
source,target
API,API
backend,backend
frontend,frontend
machine learning,uczenie maszynowe
```

**Zasady:**
- Pierwsza kolumna: termin źródłowy
- Druga kolumna: tłumaczenie
- Nagłówek (`source,target` lub `Pattern,Substitution`) jest opcjonalny
- Linie zaczynające się od `#` są traktowane jako komentarze
- Maksymalnie 5000 wpisów (ograniczenie promptu)

### Jak działa glosariusz

1. **Ładowanie** — przy wskazaniu pliku CSV w GUI
2. **Filtrowanie** — przed każdym tłumaczeniem fragmentu Tłumacz wybiera tylko te wpisy, które występują w tekście źródłowym
3. **Wstrzykiwanie** — wybrane wpisy są dodawane do promptu systemowego
4. **Wymuszanie** — model jest instruowany, aby używać dokładnie tych tłumaczeń

**Przykład promptu z glosariuszem:**
```
Use the following glossary terms exactly, do not translate them differently.
Apply them ONLY to words that actually appear in the source text:
- API => API
- backend => backend
```

### Zarządzanie glosariuszem z GUI

- **Przeglądaj...** — wybierz plik CSV
- **Dodaj wpis** — formularz do dodawania wpisów bez edycji pliku
- **Licznik** — wyświetla liczbę załadowanych wpisów

---

## Skille

### Czym są skille?

Skille to pliki Markdown z instrukcjami dla modelu, dopasowane do konkretnych formatów plików. Kiedy tłumaczysz plik `.md`, Tłumacz automatycznie wstrzykuje skill Markdown do promptu systemowego.

### Format skilla

```markdown
---
name: Markdown
formats: md, markdown
skip_patterns: ^```$,^---$
---

You are translating a Markdown document. Preserve all formatting:
- Headings (#, ##, ###)
- Lists (-, *, 1.)
- Code blocks (```)
- Links [text](url)
- Tables
```

**Pola frontmatter:**
- `name` — nazwa skilla (wyświetlana w GUI)
- `formats` — rozszerzenia plików (oddzielone przecinkami)
- `skip_patterns` — opcjonalne regexy linii nietłumaczonych

### Wbudowane skille

Tłumacz zawiera wbudowane skille dla:
- **Markdown** — ochrona składni Markdown
- **HTML** — ochrona tagów HTML
- **DOCX** — instrukcje dla tłumaczenia XML w DOCX
- **ODT** — instrukcje dla tłumaczenia XML w ODT
- **EPUB** — instrukcje dla tłumaczenia XHTML w EPUB
- **PDF** — instrukcje dla tłumaczenia PDF
- **Plaintext** — podstawowe instrukcje

### Własne skille

**Lokalizacja:** `~/.config/tlumacz/skills/`

**Tworzenie:**
1. Kliknij **„Nowy skilla..."** w zakładce „Dodatki"
2. Edytuj plik szablonu (nazwa, formaty, instrukcje)
3. Zaznacz skill w liście
4. Kliknij **„Odśwież"**

**Importowanie:**
1. Kliknij **„Importuj skilla..."**
2. Wybierz plik `.md` z frontmatter
3. Skill zostanie skopiowany do katalogu użytkownika

**Nadpisywanie:** Skill użytkownika o tej samej nazwie zastępuje wbudowany skill.

### Auto-select skill

Kiedy zmieniasz plik wejściowy, Tłumacz automatycznie:
1. Odznacza wszystkie skille
2. Zaznacza skill pasujący do rozszerzenia pliku

**Przykład:** Wybierasz `dokument.md` → automatycznie zaznacza się skill „Markdown".

---

## Zaawansowane funkcje

### Równoległe tłumaczenie

Tłumacz może tłumaczyć wiele fragmentów równolegle:

**Konfiguracja:**
- `parallel` w `config.json` (domyślnie `2`)
- Dla lokalnego serwera zalecane `parallel=1` (ograniczenia `llama-server`)
- Dla chmury możesz zwiększyć `parallel` do 4-8 (uwaga na rate limits)

**Jak to działa:**
- `ThreadPoolExecutor` z `max_workers=parallel`
- Każdy fragment tłumaczony w osobnym wątku
- Wyniki zbierane i zapisywane w oryginalnej kolejności

### Ochrona fragmentów technicznych

Tłumacz automatycznie chroni:
- **Bloki kodu** (```code```)
- **URL-e** (http://, https://)
- **Adresy email**
- **Zmienne kodu** (`$variable`, `${variable}`)
- **Tagi HTML** (w trybie HTML)

**Mechanizm:**
1. **Protect** — zastępuje chronione fragmenty placeholderami (`@@PROTECTED_0@@`)
2. **Tłumaczenie** — model tłumaczy tylko tekst
3. **Restore** — przywraca oryginalne fragmenty

### Własny prompt systemowy

Możesz nadpisać domyślny prompt systemowy:

**Zastosowania:**
- Zmiana stylu tłumaczenia (formalny, nieformalny)
- Dodanie kontekstu domenowego (techniczny, medyczny, prawny)
- Wymuszenie terminologii

**Uwaga:** Glosariusz i skille są dodawane **niezależnie** od własnego promptu.

### Pomijanie linii (regex)

Możesz zdefiniować regexy linii, które nie będą tłumaczone:

**Domyślne wzorce:**
```
^---$          # YAML frontmatter separator
^```.*$        # Code block delimiters
^#[\s]         # Markdown headings (opcjonalnie)
```

**Konfiguracja:** Pole „Pomijane linie (regex)" w zakładce „API i serwer" → „Pozostałe ustawienia"

### Motywy interfejsu

| Motyw | Opis |
|-------|------|
| **Systemowy** | Podąża za kolorem pulpitu (zalecane) |
| **Jasny** | Wymusza jasny motyw |
| **Ciemny** | Wymusza ciemny motyw |

**Zmiana:** ComboBox „Motyw" w zakładce „API i serwer" → „Pozostałe ustawienia"

---

## Rozwiązywanie problemów

### Serwer nie uruchamia się

**Objawy:** Błąd „Serwer nie uruchomił się" lub timeout po 60s.

**Przyczyny i rozwiązania:**

1. **Brak llama-server w PATH**
   ```bash
   # Sprawdź czy llama-server jest zainstalowany
   which llama-server
   
   # Jeśli nie, zainstaluj (Arch Linux)
   sudo pacman -S llama.cpp-cuda  # lub llama.cpp dla CPU
   ```

2. **Port zajęty przez inny proces**
   ```bash
   # Sprawdź co zajmuje port
   ss -tlnp | grep 18080
   
   # Zabij proces
   kill <PID>
   ```

3. **Nieprawidłowa ścieżka GGUF**
   - Sprawdź czy plik istnieje: `ls /ścieżka/do/model.gguf`
   - Sprawdź czy plik nie jest uszkodzony (porównaj hash)

4. **Za mało RAM/VRAM**
   - Zmniejsz `ctx_size` w ustawieniach serwera
   - Zmień tryb obliczeń na `cpu`
   - Użyj mniejszego modelu (np. 1.8B zamiast 7B)

### Tłumaczenie się zacina

**Objawy:** Pasek postępu nie postępuje się, spinner się kręci.

**Rozwiązania:**

1. **Anuluj tłumaczenie** — kliknij „Anuluj" i spróbuj ponownie
2. **Zmniejsz rozmiar bloku** — np. z 6000 na 3000 znaków
3. **Zmniejsz max_tokens** — proporcjonalnie do `chunk_size`
4. **Sprawdź log serwera** — czy nie ma błędów OOM

### Słaba jakość tłumaczenia

**Objawy:** Błędy gramatyczne, ucinanie tekstu, halucynacje.

**Rozwiązania:**

1. **Użyj lepszego modelu** — TranslateGemma-4b (87% jakości) lub Gemini-3.5-flash (chmura)
2. **Dodaj glosariusz** — wymuś tłumaczenie kluczowych terminów
3. **Zmniejsz temperaturę** — np. z 0.3 na 0.1 (bardziej deterministyczne)
4. **Zwiększ rozmiar bloku** — lepszy kontekst, ale ryzyko obcięcia
5. **Włącz skill** — dopasowany do formatu pliku

### Crash przy anulowaniu

**Objawy:** `QThread: Destroyed while thread is still running`

**Status:** ✅ Naprawione w v0.21.0-dev

Jeśli nadal występuje:
1. Zaktualizuj do najnowszej wersji
2. Zgłoś bug na GitHub z logami

### Uszkodzony plik konfiguracyjny

**Objawy:** Komunikat „Wykryto problemy w konfiguracji"

**Rozwiązanie:**
1. Tłumacz automatycznie naprawia uszkodzone pola
2. Kopia zapasowa jest zapisywana jako `config.backup-YYYYMMDD-HHMMSS.json`
3. Możesz ręcznie przywrócić z kopii zapasowej
4. Lub kliknij „Przywróć domyślne" w zakładce „Dodatki"

---

## Pliki konfiguracyjne

| Plik | Lokalizacja | Opis |
|------|-------------|------|
| **config.json** | `~/.config/tlumacz/config.json` | Ustawienia aplikacji |
| **cache.db** | `~/.config/tlumacz/cache.db` | Cache tłumaczeń (SQLite) |
| **debug.log** | `~/.config/tlumacz/debug.log` | Logi diagnostyczne (slow chunks) |
| **skills/** | `~/.config/tlumacz/skills/` | Własne skille użytkownika |

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
