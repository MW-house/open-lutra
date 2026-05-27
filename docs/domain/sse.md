# SSE (Server-Sent Events) Stream

> Specifies how the backend streams real-time data to the frontend.

## Overview

`GET /api/topics/stream` delivers real-time data over Server-Sent Events. SSE falls outside the OpenAPI standard, so the spec is documented here.

For the REST API endpoint spec, see the Swagger UI that FastAPI generates automatically (`http://localhost:8000/docs`).

## Event list

| Event name | Frequency | Contents |
|---|---|---|
| `topic_stats` | Every 1s | Statistics for all topics (Hz, status, loss_rate, etc.) |
| `log` | On occurrence | New log entry (severity, message, timestamp) |

## Connection example

```javascript
const es = new EventSource("/api/topics/stream");

es.addEventListener("topic_stats", (e) => {
  const stats = JSON.parse(e.data);
  // { "/topic_name": { actual_hz, status, loss_rate, ... }, ... }
});

es.addEventListener("log", (e) => {
  const log = JSON.parse(e.data);
  // { severity, message, timestamp }
});
```

## How it's used on the frontend

The `use-topics-stream.ts` hook manages the SSE connection and writes received data directly into the TanStack Query cache. Components then read the data through the regular Query hooks (`useTopicStats()`, etc.).
