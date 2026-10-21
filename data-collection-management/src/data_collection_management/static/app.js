// UI for the aggregation API: pick filters, press 集計, render the breakdown.

// The breakdown that also reports success / failure counts and a success rate.
const RATE_FIELD_KEY = "operator_id";

const filters = {};
let recordingsVisible = false;

function formatRate(rate) {
  return rate === null ? "-" : `${(rate * 100).toFixed(1)}%`;
}

const el = (id) => document.getElementById(id);

// Local calendar date as YYYY-MM-DD (toISOString would shift by the UTC offset).
function isoDate(date) {
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function daysAgo(days) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return isoDate(date);
}

function applyPreset(preset) {
  const today = isoDate(new Date());
  el("date-from").value = preset === "all" ? "" : preset === "today" ? today : daysAgo(Number(preset) - 1);
  el("date-to").value = preset === "all" ? "" : today;
}

async function aggregate() {
  const button = el("aggregate");
  button.disabled = true;
  button.textContent = "集計中…";
  try {
    const response = await fetch("/api/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filters,
        date_from: el("date-from").value || null,
        date_to: el("date-to").value || null,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      const detail = typeof payload.detail === "string" ? payload.detail : null;
      throw new Error(detail || `集計に失敗しました (HTTP ${response.status})`);
    }
    render(payload);
    el("error").hidden = true;
  } catch (error) {
    el("error").textContent = error.message;
    el("error").hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "集計";
  }
}

function render(summary) {
  el("aggregated-at").textContent = `最終集計: ${summary.aggregated_at.replace("T", " ")}`;
  el("paths").textContent = `対象: ${summary.output_dir} / 定義: ${summary.recording_config_path}`;

  renderTotals(summary);
  renderFilters(summary.fields);
  renderSummaries(summary.field_summaries);
  renderRecordings(summary.fields, summary.recordings);
}

function renderTotals(summary) {
  const container = el("totals");
  container.replaceChildren();
  container.append(createTotalCard("全体", summary.total_count, summary.total_duration_text, true));
  for (const total of summary.evaluation_totals) {
    container.append(createTotalCard(total.display, total.count, total.duration_text, false));
  }
}

function createTotalCard(label, count, durationText, isOverall) {
  const card = document.createElement("div");
  card.className = isOverall ? "total-card overall" : "total-card";

  const labelEl = document.createElement("span");
  labelEl.className = "total-label";
  labelEl.textContent = label;

  const countEl = document.createElement("span");
  countEl.className = "total-value";
  countEl.textContent = `${count} 件`;

  const durationEl = document.createElement("span");
  durationEl.className = "total-duration";
  durationEl.textContent = durationText;

  card.append(labelEl, countEl, durationEl);
  return card;
}

function renderFilters(fields) {
  const container = el("filters");
  container.replaceChildren();
  if (fields.length === 0) {
    container.append(createEmpty("metadata_fields が定義されていません。"));
    return;
  }

  for (const field of fields) {
    const wrapper = document.createElement("div");
    wrapper.className = "filter";

    const label = document.createElement("label");
    label.textContent = field.label;
    label.htmlFor = `filter-${field.key}`;

    const select = document.createElement("select");
    select.id = `filter-${field.key}`;
    select.append(new Option("すべて", ""));
    for (const option of field.options) {
      select.append(new Option(option.display, option.value));
    }
    select.value = filters[field.key] ?? "";
    // Changing a filter re-aggregates immediately so the numbers always match the controls.
    select.addEventListener("change", () => {
      filters[field.key] = select.value;
      aggregate();
    });

    wrapper.append(label, select);
    container.append(wrapper);
  }
}

function renderSummaries(fieldSummaries) {
  const container = el("summaries");
  container.replaceChildren();

  for (const summary of fieldSummaries) {
    const panel = document.createElement("section");
    panel.className = "panel";

    const head = document.createElement("div");
    head.className = "panel-head";
    const heading = document.createElement("h2");
    heading.textContent = summary.label;
    head.append(heading);

    // Success / failure per value only earns its columns where the operator is the
    // subject being compared; elsewhere it would just widen the table.
    const withRate = summary.key === RATE_FIELD_KEY;
    const classNames = withRate
      ? ["", "num", "num", "num", "num", "num", "bar-cell"]
      : ["", "num", "num", "bar-cell"];

    const maxCount = Math.max(1, ...summary.groups.map((group) => group.count));
    const table = document.createElement("table");
    const headers = withRate
      ? ["値", "件数", "成功", "失敗", "成功率", "合計時間", ""]
      : ["値", "件数", "合計時間", ""];
    table.append(createRow("th", headers, classNames));
    for (const group of summary.groups) {
      const values = withRate
        ? [
            group.display,
            `${group.count}`,
            `${group.success_count}`,
            `${group.failure_count}`,
            formatRate(group.success_rate),
            group.duration_text,
            "",
          ]
        : [group.display, `${group.count}`, group.duration_text, ""];
      const row = createRow("td", values, classNames);
      if (group.count === 0) {
        row.className = "zero";
      } else {
        const bar = document.createElement("span");
        bar.className = "bar";
        bar.style.width = `${(group.count / maxCount) * 100}%`;
        row.lastElementChild.append(bar);
      }
      table.append(row);
    }

    const scroll = document.createElement("div");
    scroll.className = "table-scroll";
    scroll.append(table);
    panel.append(head, scroll);
    container.append(panel);
  }
}

function renderRecordings(fields, recordings) {
  const container = el("recordings");
  container.replaceChildren();
  container.hidden = !recordingsVisible;
  el("toggle-recordings").textContent = recordingsVisible ? "隠す" : "表示";

  if (recordings.length === 0) {
    container.append(createEmpty("該当するデータがありません。"));
    return;
  }

  const table = document.createElement("table");
  const headers = ["データ", "開始", "時間", ...fields.map((field) => field.label)];
  table.append(createRow("th", headers, ["", "", "num"]));

  for (const recording of recordings) {
    const values = [
      recording.name,
      recording.started_at ? recording.started_at.replace("T", " ") : "-",
      recording.duration_text,
      ...fields.map((field) => displayValue(field, recording.metadata[field.key])),
    ];
    table.append(createRow("td", values, ["", "", "num"]));
  }

  const scroll = document.createElement("div");
  scroll.className = "table-scroll";
  scroll.append(table);
  container.append(scroll);
}

function displayValue(field, value) {
  if (!value) return "-";
  const option = field.options.find((candidate) => candidate.value === value);
  return option ? option.display : value;
}

function createRow(cellTag, values, classNames = []) {
  const row = document.createElement("tr");
  values.forEach((value, index) => {
    const cell = document.createElement(cellTag);
    cell.textContent = value;
    if (classNames[index]) cell.className = classNames[index];
    row.append(cell);
  });
  return row;
}

function createEmpty(message) {
  const paragraph = document.createElement("p");
  paragraph.className = "empty";
  paragraph.textContent = message;
  return paragraph;
}

el("aggregate").addEventListener("click", aggregate);
el("reset-filters").addEventListener("click", () => {
  for (const key of Object.keys(filters)) delete filters[key];
  aggregate();
});
for (const button of document.querySelectorAll("[data-preset]")) {
  button.addEventListener("click", () => {
    applyPreset(button.dataset.preset);
    aggregate();
  });
}
for (const id of ["date-from", "date-to"]) {
  el(id).addEventListener("change", aggregate);
}
el("toggle-recordings").addEventListener("click", () => {
  recordingsVisible = !recordingsVisible;
  aggregate();
});

// The page opens on today's collection; widen the range from there.
applyPreset("today");
aggregate();
