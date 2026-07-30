# Text Language Rule

This is a pilot repository for MW, Inc., whose operators work in Japanese.
**Operator-facing UI copy may therefore be written in Japanese.** Everything
that is *development-facing*, however, **must still be written in English** so
the codebase stays maintainable and in sync with upstream.

## English is required for

1. **Code comments and docstrings** — every language (Python, TypeScript, YAML, shell, etc.).
2. **Documentation** — `README.md`, `CLAUDE.md`, files under `docs/`, ADRs, PR descriptions authored from this repo, and inline Markdown.
3. **Commit messages and PR titles/descriptions** authored via Claude Code.
4. **Log messages, exception messages, and CLI output** produced by application code.

## UI copy may be Japanese

Operator-facing frontend strings — labels, buttons, headings, placeholders,
tooltips, error messages, toast notifications, and any other strings rendered in
the product UI — **may be written in Japanese** (or English). Master-defined
values surfaced to the UI (e.g. metadata field labels in `config/*.yaml`) are
Japanese by design.

- **Stable identifiers stay ASCII.** Keys, enum / option `value`s, and other
  machine-facing tokens remain English/ASCII even when their display `label` is
  Japanese (e.g. `value: A000` with `label: "A000_フェイスタオル"`).

## What this means in practice

- When you add or modify a comment, write it in English. Do **not** preserve adjacent Japanese comments unchanged if you are editing the same block — translate them as part of the edit.
- When you generate documentation (new files under `docs/`, README updates, etc.), write it in English from the start.
- UI strings may be Japanese; match the language of the surrounding UI when adding or editing them.
- When the user provides instructions in Japanese, you may still respond to the user in Japanese — and operator-facing UI copy may be Japanese — but development-facing artifacts written **into the repository** (comments, docs, commit messages, logs) must be in English.

## Exceptions

- **User-provided content quoted verbatim** (e.g., a Japanese error message reproduced in a bug report) is allowed when accuracy of the quote matters.
- **Test fixtures and sample data** that intentionally contain non-English content for i18n / encoding testing.
- **Third-party content** (vendored files, generated code) that is not authored in this repo.
- **Existing Japanese content** outside the scope of the current edit. Do not perform drive-by translations of unrelated files; only translate within the diff you are already producing.
