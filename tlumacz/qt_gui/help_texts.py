"""Teksty pomocy HTML dla zakładek Help w GUI.

Wyekstrahowane z main_window.py aby zmniejszyć rozmiar pliku.
"""


def help_text_pl() -> str:
    """Polska wersja pomocy."""
    return """
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


def help_text_en() -> str:
    """English version of help content."""
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
file and a port, then tick "start the server with the app".
Leave the GGUF field empty when using your own server.</p>

<h3>3. Glossary</h3>
<p>A two-column CSV file <code>source,translation</code>. Entries enforce
fixed translations for chosen terms. A header row
(<code>source,target</code> or <code>Pattern,Substitution</code>) and a
<code>#</code> prefix in the translation are handled automatically.
Entries can also be added with the "Add entry" button.</p>

<h3>4. Skills</h3>
<p>Model instructions matched to the file format (Markdown, TXT, HTML).
Enable the skills you use — the instructions of a matching skill are
injected into the prompt during translation. You can add your own skills
with the <b>"New skill..."</b> button (copies a template) or as
<code>.md</code> files in <code>~/.config/tlumacz/skills/</code>.
Frontmatter: <code>name</code> (name), <code>formats</code>
(extensions separated by commas), optionally <code>skip_patterns</code>
(regexes of lines not to translate for this format). A user skill with
the same name as a bundled one replaces it.</p>

<h3>5. Theme</h3>
<p>"System" follows the desktop color scheme; you can force light or dark.</p>

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
app shows a message about it. The "Restore defaults" button saves a backup
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
<td>Preference; "system" follows the desktop.</td></tr>
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
