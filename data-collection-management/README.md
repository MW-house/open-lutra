# data-collection-management

Web app that aggregates recorded data by metadata field: **how many recordings**
and **how much total time** exist for each value.

The recordings are the ones produced by the OpenLUTRA recorder — one directory
per recording under an `output/` tree:

```
output/
  20260801_060659/
    recording_meta.json   # metadata ids, e.g. {"object": "A001", ...}
    metadata.yaml         # rosbag2 info; duration is read from here
    quality_report.json   # duration fallback
```

`recording_meta.json` stores only stable ids (`A001`), so the app reads the
recording config (`config/<robot>.yaml`) declaring `metadata_fields:` and
resolves each id into `{id}_{label}` (e.g. `A001_バスタオル`) for display.

## Setup

Requires [uv](https://docs.astral.sh/uv/). Python only — no Node toolchain.

```bash
uv sync
cp config.example.yaml config.yaml   # then edit the two paths
```

### config.yaml

| Key | Meaning |
|-----|---------|
| `output_dir` | Directory holding one sub-directory per recording |
| `recording_config_path` | Recording config whose `metadata_fields:` is the label master |

Relative paths are resolved against the directory containing `config.yaml`.

## Run

```bash
uv run data-collection-management            # http://127.0.0.1:8080
uv run data-collection-management --port 9000 --config /path/to/config.yaml
```

Options: `--host`, `--port`, `--config`, `--reload`. `--config` can also be
given as the `DCM_CONFIG` environment variable.

## Using the app

- **集計** re-scans `output_dir` and refreshes every number. Nothing is cached,
  so recordings added since the last press are picked up.
- The **header** carries the date range, next to 集計. The page opens on
  **today**; the two date inputs set an arbitrary range (both ends inclusive,
  either end may be left empty for an open range), and the
  今日 / 過去7日 / 過去30日 / 全期間 buttons are shortcuts.
- The headline totals are split by task evaluation: 全体 / 成功 / 失敗, each with
  件数 and 合計時間. The split comes from the `task_evaluation` field; a master
  without that field shows the 全体 card only.
- **絞り込み** has one dropdown per metadata field; changing one re-aggregates
  immediately. Filters combine with AND (and with the date range), and
  `条件をクリア` resets them.
- Each field gets a breakdown table of 件数 / 合計時間 per value. Master options
  with **zero** recordings are listed too, so collection gaps stay visible.
- The **オペレータID** table additionally reports 成功 / 失敗 / 成功率 per operator.
  The rate is `成功 / (成功 + 失敗)`: recordings with no evaluation count toward
  件数 but stay out of the rate, and a group with nothing evaluated shows `-`.
- Values found in the data but missing from the master are shown as the raw id;
  recordings without a value for a field fall into `未設定`.
- **該当データ一覧** expands the individual recordings behind the current numbers.

## Daily CSV report

`GET /api/daily-summary.csv?date=YYYY-MM-DD` downloads one day's aggregate as CSV;
omitting `date` reports **today**. The file is UTF-8 with a BOM so Excel reads the
Japanese headers, and is named `summary_<YYYYmmdd>.csv`.

**The columns come from the master, not from this repo.** Between the date and the
metrics sits one column per field the recording config declares, in declaration order
and headed by that field's `key`:

```
日付  <field key>…  成功件数  成功時間  失敗件数  失敗時間
```

So a master declaring `operator_id` / `object` / `operation` / `task_evaluation` yields:

```
日付,operator_id,object,operation,成功件数,成功時間,失敗件数,失敗時間
2026/8/3,0005,Tシャツ,D000_端から持ち上げて中央に置く,741,1:04:02,3,0:00:15
```

Adding a field to `metadata_fields:` adds a column and splits the rows behind it. One
row per combination the data actually contains — unlike the UI tables, which also list
the master's zero-count options. Cells carry the master's `{id}_{label}` display
(`fields.display_for`), and a recording with no value for a field falls into `未設定`.

The one field held back is `task_evaluation` (`aggregate.EVALUATION_FIELD_KEY`): it
feeds the success / failure pairs rather than becoming a column, so both land on the
same row. A recording with no evaluation counts toward neither pair, and a master
without the field reports zeros across all four metric columns.

Durations use `H:MM:SS` and the date is unpadded (`2026/8/3`), matching the spreadsheet
this feeds. The columns that sheet derives itself — オペレーター氏名 (VLOOKUP),
1タスクあたり / 合計件数 / 合計時間 (formulas) — are deliberately not emitted.

## Duration and date sources

Per recording, duration comes from `metadata.yaml`
(`rosbag2_bagfile_information.duration.nanoseconds`), falling back to
`quality_report.json` (`duration_sec`), and finally `0` when neither exists.

The date used by the 期間 filter is the recording's start time from
`metadata.yaml` (`starting_time`), rendered in the **local** timezone of the
machine running this app. When that is missing, the directory name
(`<YYYYmmdd>_<HHMMSS>`) is parsed instead — note the recorder writes that name
using its own container clock, which may be UTC, so the two can differ by a day
around midnight. Recordings with neither are excluded whenever a date range is
set.

## Development

```bash
uv run pytest            # tests
uv run pytest --cov=src  # tests + coverage
uv run ruff check .      # lint
uv run ruff format .     # format
```

Layout:

| Module | Responsibility |
|--------|----------------|
| `config.py` | Load `config.yaml` (the two paths) |
| `fields.py` | Metadata field master from `metadata_fields:`, `{id}_{label}` display |
| `scanner.py` | Scan `output_dir` into per-recording metadata + duration |
| `aggregate.py` | Filtering, grouping, duration formatting |
| `csv_report.py` | Daily CSV report (master-driven columns, `H:MM:SS` / `Y/M/D` formatting) |
| `app.py` | FastAPI routes (`GET /api/config`, `POST /api/summary`, `GET /api/daily-summary.csv`) |
| `static/` | UI (plain HTML/CSS/JS, no build step) |
