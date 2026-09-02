# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Add a **Restart serwera** button to GUI Settings. The managed `llama-server`
  will be stopped and started again using the current GUI/config parameters,
  without restarting the whole application. After restart, verify the API
  (`/v1/models`) and show success/error status to the user.
- Do not change the translation timer: the **stoper is already implemented**.
- Test newer 2B translation models and strengthen prompts for Markdown/HTML/
  DOCX/ODT/EPUB, especially for bilingual and multilingual documents.
- Improve translation performance and choose a final quality/speed model.

## [0.19.1] - 2026-08-23

### Added
- Test build with the current document translation pipeline and round-trip
  support for DOCX/ODT/EPUB.
- Translation timer (stoper) is implemented and retained as part of the GUI.
- Local Arch package `tlumacz-0.19.1-1-any.pkg.tar.zst` built successfully.

### Changed
- Local repository `/home/frs/RepoArch/x86_64/moje-repo.db` updated with the
  0.19.1 test package.
- Current test model is **Hy-MT2-1.8B-Q4_K_S**. It is fast enough for practical
  pipeline tests, but bilingual/multilingual documents still expose quality
  problems such as untranslated source-language fragments.

### Notes
- **0.19.1 is an early development/test version and is intentionally not
  published to the public AUR.**
- Snapshot/tag `snapshot-20260823-pre-aur` was created before further model and
  prompt experiments, so this state can be restored easily.
- Format tests indicate that DOCX/ODT/EPUB round-trip structure is preserved;
  remaining issues are primarily translation quality/model limitations rather
  than loss of the document format.

## [0.19.0] - 2026-08-20

### Added
- **DOCX and ODT now round-trip to their original format** instead of
  producing Markdown. Only text nodes (`w:t` for DOCX, `text:*` for ODT) are
  translated and written back in place; markup, styles, tables and non-content
  files are preserved.

### Changed
- XML/HTML tags are protected before URLs, including URLs inside attributes.
- XML/HTML content is chunked by characters without splitting protected
  placeholders.
- Text-less XML files are copied verbatim instead of being sent to the model.

## [0.18.2] - 2026-08-20

### Changed
- DOCX extraction uses **pandoc only**, removing the python-docx dependency
  and LibreOffice fallback chain.

## [0.18.1] - 2026-08-20

### Fixed
- EPUB no longer applies Markdown/YAML skip patterns to book content.
- Chat-template control tokens are stripped from translated output.

## [0.18.0] - 2026-08-20

### Added
- EPUB round-trip translation preserving XHTML structure and non-content files.

### Fixed
- EPUB rebuilding no longer reserializes XML or relies on fragile paragraph
  splitting, preventing namespace/XML corruption.

## [0.17.2] - 2026-08-19

### Fixed
- DOCX extraction works without python-docx in the application venv by using
  pandoc.

## [0.17.1] - 2026-08-19

### Fixed
- Bilingual/multilingual documents now explicitly instruct the model to
  translate every passage that is not already in the target language.

## [0.17.0] - 2026-08-19

### Added
- Binary document support for PDF, DOCX, ODT and EPUB.
- User skill template and `skip_patterns` in skill frontmatter.
- Model chat-template fallback and persistent `model_profiles`.
- Restore-defaults action with config backups.
- GUI tooltips and parameter help.

## [0.16.0] - 2026-08-19

### Added
- Code/URL protection, configurable skip patterns and section-aware chunking.
- `server_chat_template` support for jinja vs chatml.
- Chat-template EOS token cleanup.

## [0.15.0] - 2026-08-19

### Added
- Managed-server support for thinking models, `--jinja`, `--ctx-size 8192`,
  `enable_thinking: false` and `max_tokens` 6000.

## [0.14.0] - 2026-08-19

### Added
- Refresh and import actions for user skills; hidden files are available in
  file dialogs.

## [0.13.0] - 2026-08-19

### Added
- User skills from `~/.config/tlumacz/skills/`, overriding bundled skills by name.

## [0.12.0] - 2026-08-19

### Added
- Translation / Settings / Help tabs and built-in PL/EN help.

## [0.11.0] - 2026-08-19

### Added
- Format-specific skill injection and the initial test suite.

## [0.10.0] - 2026-08-19

### Added
- Local server settings in GUI and custom translation prompt.

## [0.9.0] - 2026-08-19

### Added
- Config validation with user-visible warnings.

## [0.8.0] - 2026-08-19

### Changed
- Prompt-based detection of text already written in the target language.

## [0.7.0] - 2026-08-19

### Added
- CSV glossary support and glossary management in GUI.

## [0.6.0] - 2026-08-19

### Added
- System/light/dark theme switching.

## [0.5.1] - 2026-08-19

### Added
- Managed local `llama-server` process and server configuration fields.

## [0.5.0] - 2026-08-18

### Added
- Initial Qt/PySide6 GUI, background translation worker, persistent config,
  reusable core translation engine and packaging files.

## [0.4.0] - 2025-06-20

### Added
- Tool-call status display and tool result messages in the CLI.

## [0.1.0] - 2025-06-20

### Added
- Initial Translator Agent CLI with React + Ink, message history, status line,
  exit commands and TypeScript/ESM project structure.
