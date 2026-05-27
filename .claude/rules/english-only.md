# English-Only Rule

All human-readable text introduced into this repository **must be written in English**. This applies to:

1. **UI copy** — labels, buttons, headings, placeholders, tooltips, error messages, toast notifications, and any other strings rendered in the frontend.
2. **Code comments and docstrings** — every language (Python, TypeScript, YAML, shell, etc.).
3. **Documentation** — `README.md`, `CLAUDE.md`, files under `docs/`, ADRs, PR descriptions authored from this repo, and inline Markdown.
4. **Commit messages and PR titles/descriptions** authored via Claude Code.
5. **Log messages, exception messages, and CLI output** produced by application code.

## What this means in practice

- When you add or modify a comment, write it in English. Do **not** preserve adjacent Japanese comments unchanged if you are editing the same block — translate them as part of the edit.
- When you add or modify a UI string, write it in English. Do **not** introduce new Japanese strings even if surrounding strings are still Japanese.
- When you generate documentation (new files under `docs/`, README updates, etc.), write it in English from the start.
- When the user provides instructions in Japanese, you may still respond to the user in Japanese — but any artifact written **into the repository** must be in English.

## Exceptions

- **User-provided content quoted verbatim** (e.g., a Japanese error message reproduced in a bug report) is allowed when accuracy of the quote matters.
- **Test fixtures and sample data** that intentionally contain non-English content for i18n / encoding testing.
- **Third-party content** (vendored files, generated code) that is not authored in this repo.
- **Existing Japanese content** outside the scope of the current edit. Do not perform drive-by translations of unrelated files; only translate within the diff you are already producing.
