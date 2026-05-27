/** Pure helpers for Loss Rate chart series construction.
 *
 * Each sample point at x = i * STEP is the loss% inside a WINDOW-wide window centered on x.
 * A loss event at timestamp t shows up near t (within STEP/2) instead of being snapped to a
 * fixed bin's left edge, eliminating the visual offset that 1-second bins previously had.
 */

import type uPlot from "uplot";
import type { TimelineTopic } from "@/api/generated/schemas";

/** Sliding-window length in seconds. Matches the original fixed-bin width so the
 * denominator (expected_hz × WINDOW_SEC) — and therefore the 2% / 5% warn/danger
 * threshold semantics — is unchanged from the pre-sliding-window implementation. */
export const LOSS_RATE_WINDOW_SEC = 1.0;

/** Distance between successive sample points in seconds. */
export const LOSS_RATE_STEP_SEC = 0.1;

/** Builds per-point loss_rate (%) for a single topic.
 *
 * Window i is centered on x = i * STEP_SEC and spans [x - WINDOW/2, x + WINDOW/2).
 * A gap that overlaps the window contributes its full lost_count to that point — the same
 * gap therefore appears in up to ceil(WINDOW/STEP) consecutive points, forming a plateau.
 */
export function buildTopicLossRateSeries(topic: TimelineTopic, numPoints: number): Float64Array {
  const ys = new Float64Array(numPoints);
  const expectedPerWindow = topic.expected_hz * LOSS_RATE_WINDOW_SEC;
  if (expectedPerWindow <= 0) return ys;

  const half = LOSS_RATE_WINDOW_SEC / 2;
  const gaps = topic.gaps;
  for (let i = 0; i < numPoints; i++) {
    const center = i * LOSS_RATE_STEP_SEC;
    const windowStart = center - half;
    const windowEnd = center + half;
    let lostInWindow = 0;
    for (const gap of gaps) {
      if (gap.end_sec > windowStart && gap.start_sec < windowEnd) {
        lostInWindow += gap.lost_count;
      }
    }
    ys[i] = Math.min(100, (lostInWindow / expectedPerWindow) * 100);
  }
  return ys;
}

/** Builds aligned uPlot data (xs followed by one ys per topic) for the Loss Rate chart. */
export function buildLossRateData(
  topics: TimelineTopic[],
  selectedTopic: string | null,
  durationSec: number,
): uPlot.AlignedData {
  const filtered = selectedTopic ? topics.filter((t) => t.name === selectedTopic) : topics;
  if (filtered.length === 0 || durationSec <= 0) return [new Float64Array(0)];

  const numPoints = Math.max(1, Math.ceil(durationSec / LOSS_RATE_STEP_SEC) + 1);
  const xs = new Float64Array(numPoints);
  for (let i = 0; i < numPoints; i++) {
    xs[i] = i * LOSS_RATE_STEP_SEC;
  }

  const series: (Float64Array | number[])[] = [xs];
  for (const topic of filtered) {
    series.push(buildTopicLossRateSeries(topic, numPoints));
  }
  return series as uPlot.AlignedData;
}
