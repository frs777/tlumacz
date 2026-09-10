# Treść pomocy GUI — Tłumacz

**Wersja:** 0.21.0-dev  
**Data ostatniej aktualizacji:** 2026-09-05

---

## Opis

Ten dokument zawiera treść wbudowanej pomocy wyświetlanej w zakładce **„Pomoc"** w GUI Tłumacza. Pomoc jest dostępna w dwóch językach: polskim i angielskim.

---

## Wersja polska

```html
<h2>Tłumacz — pomoc</h2>
<p>Tłumacz to narzędzie do tłumaczenia dokumentów (Markdown, TXT, HTML,
PDF, DOCX, ODT, EPUB) za pomocą modeli LLM zgodnych z API OpenAI.
Pliki EPUB, DOCX, ODT i PDF są tłumaczone z zachowaniem oryginalnego formatu.</p>

<h3>1. Konfiguracja modelu (zakładka „Ustawienia")</h3>
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
i port, a następnie zaznacz „Uruchamiaj serwer razem z programem".
Jeśli używasz własnego serwera, zostaw pole GGUF puste.</p>

<h3>3. Glosariusz</h3>
<p>Plik CSV dwukolumnowy <code>źródło,tłumaczenie</code>. Wpisy wymuszają
stałe tłumaczenia dla wybranych terminów. Nagłówek (<code>source,target</code>
lub <code>Pattern,Substitution</code>) oraz prefiks <code>#</code>
w tłumaczeniu są obsługiwane automatycznie. Wpisy można dodawać też
przyciskiem „Dodaj wpis".</p>

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
<p>Motyw „Systemowy" podąża za kolorem pulpitu; możesz też wymusić
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
</table>
```

---

## Wersja angielska

```html
<h2>Tłumacz — Help</h2>
<p>Tłumacz is a document translation tool (Markdown, TXT, HTML, PDF, DOCX, ODT, EPUB)
using LLM models compatible with OpenAI API. EPUB, DOCX, ODT and PDF files are
translated while preserving the original format.</p>

<h3>1. Model Configuration (Settings Tab)</h3>
<ul>
<li><b>Base URL</b> — OpenAI-compatible server address,
e.g. <code>http://127.0.0.1:8080/v1</code> for local llama.cpp/ollama.</li>
<li><b>API key</b> — authentication token sent as <code>Authorization: Bearer</code>.
Local servers usually ignore it (default placeholder <code>ollama</code>);
for remote services enter your key here.</li>
<li><b>Model</b> — model name available on the server.</li>
<li><b>Block size</b> — size of text chunk sent to the model.</li>
<li><b>Temperature</b> — randomness of responses (lower = more deterministic).</li>
<li><b>Target language</b> — language to translate text into.</li>
<li><b>Custom prompt</b> — optional prompt replacing the default
(style, terminology, tone); glossary and skills are added independently.</li>
</ul>

<h3>2. Local Server</h3>
<p>The program can run llama.cpp server itself: specify <code>.gguf</code> file
and port, then check "Run server with program". If using your own server,
leave GGUF field empty.</p>

<h3>3. Glossary</h3>
<p>Two-column CSV file <code>source,translation</code>. Entries force fixed
translations for selected terms. Header (<code>source,target</code> or
<code>Pattern,Substitution</code>) and <code>#</code> prefix in translation
are handled automatically. Entries can also be added with "Add entry" button.</p>

<h3>4. Skills</h3>
<p>Model instructions matched to file format (Markdown, TXT, HTML).
Enable skills you use — matching skill instructions will be injected into
the prompt during translation. You can add custom skills with
<b>"New skill..."</b> button (copies template) or as <code>.md</code> files
in <code>~/.config/tlumacz/skills/</code>. Frontmatter: <code>name</code>,
<code>formats</code> (comma-separated extensions), optional
<code>skip_patterns</code> (regexes of untranslated lines). User skill with
the same name overrides built-in one.</p>

<h3>5. Theme</h3>
<p>"System" theme follows desktop color; you can also force light or dark.</p>

<h3>6. Configuration File</h3>
<p>Settings are saved in <code>~/.config/tlumacz/config.json</code>. Fields:
<code>base_url</code>, <code>api_key</code>, <code>model</code>,
<code>chunk_size</code>, <code>temperature</code>, <code>target_language</code>,
<code>theme</code>, <code>glossary_path</code>, <code>system_prompt</code>,
<code>enabled_skills</code>, <code>skip_line_patterns</code>,
<code>server_port</code>, <code>server_gguf_path</code>,
<code>server_chat_template</code>, <code>server_parallel</code>,
<code>auto_start_server</code>, <code>model_profiles</code>, <code>last_input</code>,
<code>last_output</code>.</p>
<p>Corrupted file or wrong-typed fields are repaired with defaults, and the
program shows appropriate message. "Restore defaults" button saves backup
and returns to default settings (keeping file and glossary paths).</p>

<h3>7. Parameters Table</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Parameter</th><th>What it does</th><th>How to set</th><th>Why</th></tr>
<tr><td>Base URL</td><td>OpenAI-compatible API server address.</td>
<td>e.g. <code>http://127.0.0.1:18080/v1</code></td>
<td>Server must be reachable and speak OpenAI protocol.</td></tr>
<tr><td>API key</td><td><code>Authorization: Bearer</code> token.</td>
<td><code>ollama</code> for local server</td>
<td>Local servers ignore key; remote ones require real key.</td></tr>
<tr><td>Model</td><td>Model name on server.</td>
<td>e.g. <code>local</code> for own server</td>
<td>Must be available on specified server.</td></tr>
<tr><td>Block size</td><td>Text chunk size in one call (characters).</td>
<td><b>4000–6000</b></td>
<td>Smaller = better section context but more calls;
larger = fewer calls but risk of truncation and losing coherence.</td></tr>
<tr><td>Temperature</td><td>Model response randomness.</td>
<td><b>0.1–0.3</b></td>
<td>Low = faithful, deterministic translation; higher = free style.</td></tr>
</table>
```

---

## Struktura pomocy

### Zakładki

Pomoc w GUI jest zorganizowana w sekcje:

1. **Konfiguracja modelu** — opis pól API (Base URL, API key, Model, itp.)
2. **Serwer lokalny** — instrukcje konfiguracji llama.cpp
3. **Glosariusz** — format CSV, dodawanie wpisów
4. **Skille** — format frontmatter, tworzenie własnych skilli
5. **Motyw** — wybór motywu interfejsu
6. **Plik konfiguracji** — opis pól config.json
7. **Tabela parametrów** — zalecane wartości i wyjaśnienia

### Przełączanie języka

ComboBox „Język / Language" w prawym górnym rogu zakładki „Pomoc":
- **Polski** — wyświetla pomoc w języku polskim
- **English** — wyświetla pomoc w języku angielskim

Zmiana języka pomocy **nie zmienia** języka interfejsu (tylko zakładka Pomoc).

---

## Implementacja

### Metody w MainWindow

```python
def _build_help_tab(self) -> QWidget:
    """Zbuduj zakładkę Pomoc."""
    tab = QWidget()
    layout = QVBoxLayout(tab)
    
    # ComboBox języka
    language_row = QHBoxLayout()
    language_row.addWidget(QLabel("Język / Language:"))
    self.help_language = QComboBox()
    self.help_language.addItem("Polski", "pl")
    self.help_language.addItem("English", "en")
    self.help_language.currentIndexChanged.connect(self._update_help)
    language_row.addWidget(self.help_language)
    language_row.addStretch(1)
    layout.addLayout(language_row)
    
    # QTextBrowser z pomocą
    self.help_view = QTextBrowser()
    self.help_view.setOpenExternalLinks(True)
    layout.addWidget(self.help_view, 1)
    
    self._update_help()
    return tab

def _update_help(self) -> None:
    """Zaktualizuj treść pomocy po zmianie języka."""
    lang = self.help_language.currentData()
    set_language(lang)
    self._refresh_ui_texts()
    if lang == "en":
        content = self._help_text_en()
    else:
        content = self._help_text_pl()
    self.help_view.setHtml(content)
```

### Lokalizacja

Treść pomocy jest **hardcoded** w metodach `_help_text_pl()` i `_help_text_en()`.

**Plan na przyszłość:** Przenieść treść pomocy do systemu i18n (`i18n.py`) aby ułatwić tłumaczenie na inne języki.

---

## Rozszerzanie pomocy

### Dodawanie nowych sekcji

Aby dodać nową sekcję do pomocy:

1. Otwórz `tlumacz/qt_gui/main_window.py`
2. Znajdź metodę `_help_text_pl()` lub `_help_text_en()`
3. Dodaj nową sekcję HTML:
   ```html
   <h3>8. Nowa sekcja</h3>
   <p>Opis nowej funkcjonalności...</p>
   ```
4. Zapisz plik i zrestartuj aplikację

### Zmiana istniejącej treści

1. Otwórz `tlumacz/qt_gui/main_window.py`
2. Znajdź odpowiednią sekcję w `_help_text_pl()` lub `_help_text_en()`
3. Edytuj treść HTML
4. Zapisz i zrestartuj

### Dodawanie nowego języka

1. Dodaj nowy język do ComboBox w `_build_help_tab()`:
   ```python
   self.help_language.addItem("Deutsch", "de")
   ```
2. Utwórz metodę `_help_text_de()` z treścią po niemiecku
3. Zaktualizuj `_update_help()`:
   ```python
   if lang == "en":
       content = self._help_text_en()
   elif lang == "de":
       content = self._help_text_de()
   else:
       content = self._help_text_pl()
   ```

---

## Licencja

MIT — zobacz [LICENSE.txt](../../LICENSE.txt)

## Autor

frs — https://github.com/frs777/tlumacz
