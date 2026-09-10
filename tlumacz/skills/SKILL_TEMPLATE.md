---
name: Mój skilla
formats: md, markdown
skip_patterns:
---

<!--
Wymagane pola frontmatteru:
- name: nazwa skilla (unikalna, widoczna w GUI).
- formats: rozszerzenia plików oddzielone przecinkiem, np. md, markdown.
  Rozszerzenie pliku wejściowego decyduje, czy skilla zostanie użyta.

Pole opcjonalne:
- skip_patterns: lista wyrażeń regularnych (regex) oddzielonych przecinkiem,
  opisująca linie, których NIE wolno tłumaczyć dla tego formatu
  (np. metadane YAML, znaczniki stron, nagłówki tabel).
  Przykład: ^\s*---\s*$, ^\s*(name|author|version)\s*:
  Puste pole = używane są tylko uniwersalne bezpieczne wzorce.

Treść poniżej to instrukcje dla modelu — są wstrzykiwane do promptu
tłumaczenia dla plików pasujących do tego skilla. Pisz wprost, co model
ma robić, a czego nie wolno mu tłumaczyć.
-->

Tłumaczysz dokument. Przestrzegaj tych zasad:
- Zachowaj dokładną strukturę dokumentu: nagłówki, listy, podkreślenia, linki,
  obrazy, tabele, cytaty blokowe i bloki kodu.
- Nie tłumacz zawartości w blokach kodu z obramowaniem (```), kodu inline (`),
  URL-i ani identyfikatorów używanych w linkach i ścieżkach obrazów.
- Zachowaj linie metadane bez zmian; tłumacz tylko wartości tekstowe.
- Nie zmieniaj liczby pustych linii między blokami.
- Zachowaj markery wyrównania tabel bez zmian; tłumacz tylko tekst komórek.
- Tłumacz wiernie i profesjonalnie; nie dodawaj komentarzy.
