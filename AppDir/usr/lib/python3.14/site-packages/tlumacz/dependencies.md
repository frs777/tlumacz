# Zależności niezbędne do obsługi formatów dokumentów w tłumaczu

Aplikacja dzieli formaty na dwa rodzaje:
* **Formaty tekstowe** – pliki otwierane bezpośrednio jako zwykły tekst (`.txt`, `.md` itp.).
* **Formaty binarne** – wymagają wcześniejszego ekstrakcji tekstu przed tłumaczeniem.
  PDF, DOCX, ODT, EPUB.

Poniższa tabela przedstawia narzędzia i pakiety Pythona niezbędne do obsługi każdego formatu.
Zależności są **wykrywane lazli** – jeśli nie są obecne, aplikacja stosuje fallback (często na pandoc lub inne narzędzie systemowe).

| Format | Wymagane narzędzia / pakiety | Fallback / alternatywa |
|--------|-----------------------------|------------------------|
| **PDF** | * `pdftotext` (z pakietu **poppler-utils**)<br>* lub pakiet Pythona **pypdf** | Jeśli żadne z powyższych nie jest dostępne, ekstrakcja tekstu zostanie pominięta (plik traktowany jest jako niewyciągalny). |
| **DOCX** | * **pandoc** (do konwersji docx → markdown) | Jeśli pandoc jest niedostępny, ekstrakcja tekstu zostanie pominięta (plik traktowany jako niewyciągalny). |
| **ODT** | **Tylko Python** –standardowa biblioteka biblioteka `zipfile` do rozpakowania archiwum ODT oraz parser XML/HTML (moduły `xml.etree.ElementTree`, `html.parser.HTMLParser`).<br>*Nie wymaga żadnych zewnętrznych narzędzi.* | Brak – ekstrakcja opiera się wyłącznie na wbudowanych modułach Pythona. |
| **EPUB** | **Tylko Python** –standardowa biblioteka `zipfile` do rozpakowania archiwum EPUB (które jest w rzeczywistości ZIP) oraz obsługa XML/HTML wewnątrz (podobnie jak w ODT).<br>*Nie wymaga żadnych zewnętrznych narzędzi.* | Brak – struktura EPUB (mimetype, META-INF/container.xml, OEBPS/) jest analizowana wyłącznie za pomocą wbudowanych modułów Pythona. |

### Podsumowanie

* **PDF** – najbardziej zależny od zewnętrznych narzędzi systemowych (poppler, pypdf).
* **DOCX** – obsługiwany przez **pandoc** (docx → markdown), który jest jednocześnie używany do konwersji zwrotnej do DOCX/ODT/PDF.
* **ODT i EPUB** – obsługiwane wyłącznie przez Pythona – nie wymagają instalowania żadnych dodatkowych pakietów systemowych ani narzędzi zewnętrznych. Jest to ułatwienie dla użytkowników, którzy nie mogą lub nie chcą instalować dodatkowego oprogramowania.

> **Uwaga:** Aplikacja `tlumacz` jest zaprojektowana tak, aby działała nawet wtedy, gdy niektóre z tych zależności nie będą zainstalowane – w takich przypadkach stosowane są fallbacki, a użytkownik otrzymuje odpowiednie komunikaty o braku możliwości ekstrakcji.