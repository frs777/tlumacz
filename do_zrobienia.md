# Do zrobienia — tlumacz

Lista pomysłów i niedokończonych usprawnień projektu **tlumacz**.

## Konfiguracja (config.json)

- [ ] **Pełna edycja config.json przez GUI** — obecnie ustawienia (model, base_url,
      api_key, chunk_size, temperature, target_language) są zapisywane do
      `~/.config/tlumacz/config.json` tylko przy kliknięciu *Tłumacz* i przy
      zamknięciu okna. Dodać jawny przycisk **Zapisz ustawienia** oraz autozapis
      przy zmianie pola (editingFinished), aby zmiany były trwałe natychmiast.
- [ ] **Lista modeli z serwera** — pobierać dostępne modele z
      `GET /v1/models` i podawać je jako rozwijaną listę zamiast pola tekstowego.
      Serwer lokalny (llama.cpp) ignoruje nazwę modelu i zawsze używa `local` —
      warto to pokazywać w UI (np. etykieta „serwer użyje modelu: local").
- [x] **Ścieżka do pliku GGUF** — możliwość podania bezpośredniej ścieżki do
      modelu `.gguf` w ustawieniach (np. do uruchomienia lokalnego llama.cpp
      bez osobnego serwera). Pola `server_gguf_path`, `server_port`,
      `auto_start_server` w config.json + `LlamaServer`
      (`tlumacz/server.py`) oraz grupa „Serwer lokalny" w GUI.
- [x] **Własny prompt użytkownika** — pole w ustawieniach na spersonalizowany
      prompt tłumaczenia (np. styl, terminologia, ton wypowiedzi).
- [x] **Walidacja config.json** — jeśli plik konfiguracji jest uszkodzony lub
      zawiera nieznane pola, GUI powinno wrócić do wartości domyślnych z
      komunikatem zamiast cichego błędu.
- [x] **Wstrzykiwanie skilli** — dodatkowe skille dotyczą tłumaczeń różnych
      formatów. Skille `.md` w pakiecie `tlumacz/skills/` (frontmatter:
      `name`, `formats`), wybór w GUI (grupa „Skille"), wstrzykiwane do
      promptu gdy rozszerzenie pliku wejściowego pasuje do włączonego skilla.
      Własne skille użytkownika: `~/.config/tlumacz/skills/` (skilla
      użytkownika zastępuje wbudowany o tej samej nazwie).
- [ ] **Przywracanie domyślnych opcji** — przycisk „Przywróć domyślne"
      w Ustawieniach: kopia aktualnego config.json do
      `config.backup-<data>.json`, potem zapis wartości domyślnych
      (z zachowaniem pól niekonfiguracyjnych: `last_input`, `last_output`,
      `glossary_path`). Przy naprawie uszkodzonego config.json zachować
      oryginał jako `.bak` (obecnie naprawa w miejscu gubi oryginał).
- [ ] **Odporność na zmianę modelu** — obecnie zmiana modelu GGUF wymaga
      zmian w kodzie (gemma → `--jinja` + `enable_thinking`, translategemma →
      `chatml` + czyszczenie EOS). Plan: (a) autofallback startu serwera —
      próba `--jinja`, w razie błędu parsowania szablonu retry z
      `--no-jinja --chat-template chatml`; (b) profil modelu zapamiętywany
      w config.json pod ścieżką GGUF (działające flagi używane automatycznie);
      (c) detekcja przez próbę — mikro-zapytanie sprawdza wyciek tokenu EOS
      i tryb „myślenia", parametry dostrajane samoczynnie.

## Dokumentacja / pomoc

- [x] **Krótka pomoc w GUI (PL + EN)** — zakładka „Pomoc” opisująca: format
      i pola `config.json`, jak wybrać LLM (base_url, api_key, model), formaty
      obsługiwanych plików wejściowych (Markdown, TXT, HTML), serwer lokalny
      oraz regułę nazwy pliku wyjściowego. Przełączanie języka pomocy PL/EN.
- [ ] **Szczegółowa pomoc dla każdej funkcji** — dwuwarstwowo: (a) tooltipy /
      dymki przy każdym polu („co to robi"), (b) rozbudowana tabela parametrów
      w zakładce Pomoc z kolumnami *co robi / ile ustawić / dlaczego* — np.
      chunk_size (mniejszy = lepszy kontekst sekcji, większy = mniej połączeń,
      ryzyko obcięcia; dla CPU zalecane 4000–6000), temperature (0.1–0.3 dla
      wiernego tłumaczenia), max_tokens, skip patterns, glosariusz, skille,
      serwer lokalny. Wyjaśnienia po ludzku, bez żargonu.

## Lokalizacja (i18n)

- [ ] **Struktura i18n** — wprowadzić mechanizm tłumaczeń aplikacji z
      gotowymi językami **polskim (pl)** i **angielskim (en)**, zaprojektowany
      tak, aby dodanie kolejnego języka wymagało tylko nowego pliku tłumaczeń
      (bez zmian w kodzie):
  - [ ] Pliki tłumaczeń (np. `tlumacz/i18n/pl.json`, `tlumacz/i18n/en.json`
        albo katalog `locale/` z formatem gettext/POT) z kluczami zamiast
        tekstu na sztywno w kodzie.
  - [ ] Wrapper/helper do odczytu kluczy (np. `tr("key")`), z fallbackiem do
        angielskiego, gdy klucza brakuje w wybranym języku.
  - [ ] Automatyczne wykrywanie języka systemu (locale) jako domyślnego
        z możliwością nadpisania w ustawieniach.
- [ ] **UI aplikacji** — przetłumaczyć wszystkie widoczne ciągi GUI
      (etykiety, przyciski, komunikaty, logi, tytuł okna) na pl i en —
      obecnie interfejs jest po polsku, część komunikatów po angielsku.
- [ ] **Pomoc w GUI** — przenieść treść zakładki „Pomoc” do systemu i18n
      zamiast dwóch sztywnych wariantów PL/EN, aby automatycznie obejmowała
      kolejne języki.
- [ ] **Dokumentacja** — zsynchronizować README (PL/EN) oraz `PODSUMOWANIE.md`
      z nowym mechanizmem tłumaczeń.
- [ ] **Format plików tłumaczeń** — rozważyć format łatwy do tłumaczenia
      przez LLM (JSON z płaskimi kluczami albo `.pot`/`.po`) oraz weryfikację
      kompletności kluczy (test: każdy klucz obecny we wszystkich językach).

## Tłumaczenie

- [x] **Wykrywanie języka wejściowego** — automatyczne rozpoznawanie, czy tekst
      jest już w języku docelowym (żeby nie tłumaczyć po raz drugi) —
      realizowane przez wewnętrzny prompt.
- [x] **Glosariusz / słownik** — opcja dodania **własnego pliku CSV** z parami
      źródło → tłumaczenie (wybór pliku w GUI) oraz dodawanie wpisów z poziomu
      GUI; wpisy stosowane podczas tłumaczenia.
- [x] **Motyw (theme)** — przełączanie motywów **dzień / noc / system** z
      poziomu GUI.
- [ ] **Wzorce pomijania per typ pliku** — obecnie `skip_line_patterns` to
      globalna lista regexów dopasowana do YAML frontmatteru Markdown, zbyt
      skomplikowana dla laika. Plan: (a) przenieść wzorce do skilla —
      opcjonalne pole `skip_patterns` w frontmatterze skilla używane
      automatycznie dla pasującego formatu; (b) uniwersalne „bezpieczne"
      wzorce zawsze aktywne; (c) pole regex w GUI zostaje jako sekcja
      „Zaawansowane (opcjonalnie)" dla zaawansowanych użytkowników.
- [ ] **Szablon skilla dla użytkowników** — dołączony `SKILL_TEMPLATE.md`
      z udokumentowanymi polami frontmatteru (`name`, `formats`, opcjonalnie
      `skip_patterns`) i przykładem; przycisk „Nowy skilla" kopiujący szablon
      do `~/.config/tlumacz/skills/`; dokumentacja w zakładce Pomoc.
- [ ] **Wbudowane skille PDF / DOCX / ODT / EPUB** — nowy moduł
      `tlumacz/extract.py` do ekstrakcji tekstu: PDF (`pdftotext`/pypdf),
      DOCX (python-docx/docx2txt), ODT (zipfile + content.xml, stdlib),
      EPUB (zipfile + strip HTML, stdlib) + 4 skille z regułami tłumaczenia
      (wzorce z `skillmarketplace/PDF-Translator/.../en-cap-translator` oraz
      `skillmarketplace/translate-doc`). Wyjście w 1. wersji jako Markdown
      (bez round-tripu do formatów binarnych — osobny, większy etap; OCR dla
      skanów również na później). Zależności opcjonalne z czytelnym komunikatem
      gdy brakuje biblioteki.

## Pakowanie / repo

- [ ] **Aktualizacja URL w PKGBUILD** — `url` wskazuje na
      `https://github.com/frs777/tlumacz`, zweryfikować przed publikacją w AUR.
- [ ] **Automatyczna synchronizacja moje-repo** — skrypt dodający nową paczkę
      do `/home/frs/RepoArch/x86_64` po każdym buildzie.
- [ ] **Paczki DEB / RPM / AppImage** — zbudowanie pakietów dla dystrybucji
      Debian/Ubuntu, Fedora/RHEL i AppImage (oprócz istniejącej paczki AUR).

## GitHub

- [x] **README domyślny po polsku** — ustawić `README.md` jako wersję polską,
      a wersję angielską (`README.en.md`) podlinkować na górze (link PL/EN).
- [ ] **Ikona repo / social preview** — dodać obrazek ogłoszeniowy (og-image).
