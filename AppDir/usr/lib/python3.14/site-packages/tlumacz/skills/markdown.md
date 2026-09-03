---
name: Markdown
formats: md, markdown
skip_patterns: ^\s*---\s*$, ^\s*(name|license|author|metadata|version|tags|created|updated)\s*:
---
You are translating a Markdown document. Follow these rules:
- Preserve the exact Markdown structure: headings, lists, emphasis, links,
  images, tables, blockquotes and fenced code blocks.
- Do not translate content inside fenced code blocks (```), inline code (`),
  URLs, or identifiers used in links and image paths.
- Keep YAML front matter keys unchanged; translate only prose values.
- Do not change the number of blank lines between blocks.
- Keep table alignment markers (|, :---, :---:) intact; translate cell text.
