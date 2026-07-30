# Pre-registered metadata

Operators often need to tag every recording with the same few attributes — who
operated the robot, which object was manipulated, and so on. Instead of typing
those after each recording, they are **pre-registered** once from a master and
then attached to every subsequent recording until changed — exactly like the
[task name](../../README.md#task-name).

## What gets stored

Each recording folder's `recording_meta.json` holds a `metadata` map alongside
`task_name` / `recording_config_name` / `tags`:

```json
{
  "task_name": "pick-and-place",
  "recording_config_name": "simulator",
  "tags": [],
  "metadata": { "operator_id": "007", "target_object": "box" }
}
```

`metadata` is a plain **`key -> value` string map**, separate from the free-form
`tags` list. **Values are always strings**, so a numeric field keeps its leading
zeros (`"007"` stays `"007"`, never parsed to `7`).

## Defining the master fields

The available fields are declared in the active recording config's
`metadata_fields:` section (`config/<recording>.yaml`, selected via
`RECORDING_CONFIG`) and served to the UI through `GET /api/config`. Omit the
section (or leave it empty) to hide the feature entirely.

```yaml
metadata_fields:
  - key: operator_id          # stable key stored in recording_meta.json
    label: "Operator ID"      # display label
    type: number              # digits only, stored as a string ("007" stays "007")
    pattern: '^[0-9]+$'       # optional: regex the value must match
    placeholder: "e.g. 007"   # optional: input hint
  - key: target_object
    label: "Target Object"
    type: select              # pick from the options below
    options:
      - value: box
        label: "Box"          # optional; falls back to `value`
      - value: cup
      - value: bottle
```

| Field | Required | Description |
|---|---|---|
| `key` | yes | Stable identifier used as the map key in `recording_meta.json` |
| `label` | yes | Display label shown in the UI |
| `type` | no (default `select`) | `select` = pick from `options`; `number` = digits-only text input; `text` = free text |
| `pattern` | no | Regex the value must match; a mismatch is flagged in the UI |
| `placeholder` | no | Input hint for `number` / `text` fields |
| `options` | for `select` | Allowed values; each is `{ value, label? }` (label falls back to `value`) |

## How operators set values

- A **Metadata** popover in the recording bar (next to the task-name editor)
  renders one control per field. Selections are sticky across recordings
  (persisted in the browser's `localStorage`), like the task name.
- **`task_evaluation` is a special case**: it is a post-recording judgement, so
  it is *not* offered in the pre-recording panel. Instead the
  recording-completion banner shows a success / failure selector once the
  recording stops, defaulting to `success`; the banner persists the value
  (including the default) to `recording_meta.json`. The selector can also be
  cycled through its options with the `E` key, so a take can be labeled
  hands-free. The frontend keys this off
  the field's `key` (`task_evaluation`) — it is a deliberate MW-specific
  behaviour rather than a general config flag. The field still appears in the
  master `metadata_fields` so its label and options are master-defined.
- Values can also be edited after the fact from the metadata dialog on the
  recordings page (which shows every field, `task_evaluation` included), and
  appear as badges in the recordings list.

## Validation

Constraints are enforced **in the UI**: `number` fields accept digits only, and
a `pattern` mismatch is flagged. The **backend stays lenient** — it stores
whatever is submitted and never blocks a recording, consistent with the
"recording is never interrupted" principle. If a field is later removed from the
master, any stale value on older recordings is simply ignored by the UI.

## Extending

- **Required fields** are intentionally not enforced yet. A soft, opt-in
  `required` flag (warn but never block) fits the same config-driven design and
  could be added without breaking the lenient backend.
- **Rules beyond a regex** (cross-field logic, external lookups) are better
  expressed in code — the [custom validators](custom_validators.md) mechanism is
  the precedent for plugging in per-recording checks, and a validator can read
  the parsed `metadata` from `ValidationContext.recording_meta`.
