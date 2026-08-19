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

## Dokumentacja / pomoc

- [x] **Krótka pomoc w GUI (PL + EN)** — zakładka „Pomoc” opisująca: format
      i pola `config.json`, jak wybrać LLM (base_url, api_key, model), formaty
      obsługiwanych plików wejściowych (Markdown, TXT, HTML), serwer lokalny
      oraz regułę nazwy pliku wyjściowego. Przełączanie języka pomocy PL/EN.

## Tłumaczenie

- [x] **Wykrywanie języka wejściowego** — automatyczne rozpoznawanie, czy tekst
      jest już w języku docelowym (żeby nie tłumaczyć po raz drugi) —
      realizowane przez wewnętrzny prompt.
- [x] **Glosariusz / słownik** — opcja dodania **własnego pliku CSV** z parami
      źródło → tłumaczenie (wybór pliku w GUI) oraz dodawanie wpisów z poziomu
      GUI; wpisy stosowane podczas tłumaczenia.
- [x] **Motyw (theme)** — przełączanie motywów **dzień / noc / system** z
      poziomu GUI.

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
