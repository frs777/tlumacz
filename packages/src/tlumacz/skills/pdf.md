---
name: PDF
formats: pdf
skip_patterns: ^\s*\d+\s*$, ^\s*(page|strona|s\.)\s+\d+(\s+/\s+\d+)?\s*$, ^\s*[\|\s]*$
---
You are translating the extracted text of a PDF document. The text was
converted to Markdown-like form. Follow these rules:
- Preserve the document structure: headings, paragraphs, lists and tables.
- Do not translate page numbers, headers/footers of pages, or running heads
  repeated on every page; skip lines that contain only numbers or metadata.
- Keep URLs, file names, identifiers, code and email addresses unchanged.
- Preserve table alignment markers (|, :---, :---:) and translate only cell text.
- Translate captions, footnotes and references consistently with the glossary.
- Do not translate text inside inline code or fenced code blocks.
- Translate faithfully and professionally; do not add commentary.