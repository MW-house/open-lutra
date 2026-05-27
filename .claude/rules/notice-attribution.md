---
paths:
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
  - "frontend/src/**/*.css"
  - "NOTICE"
---

# NOTICE attribution check

When you add or modify code under `frontend/src/`, check whether `NOTICE` (at the repo root) needs an update. The third-party section of `NOTICE` lists every file in this repo that contains code copy-pasted (or substantially derived) from an outside project.

## When NOTICE must be updated

Update `NOTICE` if any of the following is happening in your current edit:

1. **You are copying code from a third-party project into `frontend/src/`** — even a single utility function. Examples: pulling another shadcn/ui component via `pnpm dlx shadcn@latest add ...`, copying a snippet from a Stack Overflow answer with a non-permissive license, vendoring a small library file.
2. **You are creating a new file under `frontend/src/features/*/ui/` that is shadcn-derived** — the existing `alert-dialog.tsx` is the precedent. New ones must be listed explicitly in `NOTICE` (the wildcard only covers `frontend/src/components/ui/*.tsx`).
3. **You are deleting all third-party-derived code from a path listed in `NOTICE`** — remove the now-obsolete entry so the attribution list reflects reality.
4. **You are introducing code under a license other than MIT or Apache-2.0** (e.g. BSD, ISC, MPL-2.0) — add a new third-party block to `NOTICE` with the relevant license text. Refuse to vendor code under GPL / AGPL / SSPL / BUSL / Commons Clause without confirming with the user, since those are not compatible with this repo's Apache-2.0 license.

## When NOTICE does NOT need to be updated

- Editing existing FastLabel-authored code under `frontend/src/`.
- Adding or modifying a file inside `frontend/src/components/ui/*.tsx` — already covered by the wildcard entry.
- Adding a new npm dependency to `package.json`. Build-time / runtime deps pulled by pnpm are not redistributed in the source release and are explicitly excluded from `NOTICE` by the trailing paragraph.
- Refactoring or renaming a file that's already listed in `NOTICE`, as long as the new path is still under a listed glob (`components/ui/*.tsx`). If the rename moves the file outside the listed glob, update the entry.

## How to apply

1. Before completing your task, scan your diff. If anything in the "must update" list above applies, edit `NOTICE` in the same change.
2. When the user explicitly says "don't update NOTICE" or "do it separately", surface the gap as a one-line warning in your end-of-turn summary but do not block.
3. The original license investigation lives in PR #75 / commit `8fc1ff3` ("Attribute shadcn/ui-derived UI code in NOTICE") — consult it for the rationale behind the current `NOTICE` structure if you need to extend it.
