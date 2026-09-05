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

You are translating a document. Follow these rules:
- Preserve the exact document structure: headings, lists, emphasis, links,
  images, tables, blockquotes and code blocks.
- Do not translate content inside fenced code blocks (```), inline code (`),
  URLs, or identifiers used in links and image paths.
- Keep metadata lines unchanged; translate only prose values.
- Do not change the number of blank lines between blocks.
- Keep table alignment markers intact; translate only cell text.
- Translate faithfully and professionally; do not add commentary.