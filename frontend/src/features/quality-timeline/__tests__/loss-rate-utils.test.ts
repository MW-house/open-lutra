import { describe, expect, it } from "vitest";
import type { TimelineGap, TimelineTopic } from "@/api/generated/schemas";
import {
  buildLossRateData,
  buildTopicLossRateSeries,
  LOSS_RATE_STEP_SEC,
  LOSS_RATE_WINDOW_SEC,
} from "../loss-rate-utils";

function gap(start: number, lostCount: number, durationSec = 0.05): TimelineGap {
  return {
    start_sec: start,
    end_sec: start + durationSec,
    duration_sec: durationSec,
    lost_count: lostCount,
    severity: lostCount >= 3 ? "major" : "minor",
  };
}

function topic(expectedHz: number, gaps: TimelineGap[]): TimelineTopic {
  return {
    name: "/test",
    msg_type: "std_msgs/msg/String",
    expected_hz: expectedHz,
    bins: [],
    gaps,
  };
}

const step = LOSS_RATE_STEP_SEC; // 0.1
const window = LOSS_RATE_WINDOW_SEC; // 0.5

describe("buildTopicLossRateSeries", () => {
  it("returns all zeros when there are no gaps", () => {
    const ys = buildTopicLossRateSeries(topic(30, []), 50);
    expect(Array.from(ys)).toEqual(new Array(50).fill(0));
  });

  it("returns all zeros when expected_hz is 0 (avoids division by zero)", () => {
    const ys = buildTopicLossRateSeries(topic(0, [gap(5.0, 3)]), 100);
    expect(Array.from(ys).every((v) => v === 0)).toBe(true);
  });

  it("places a loss at t=15.9s near 15.9s, not at 15.0s", () => {
    // 30 Hz topic, single 1-frame loss at 15.9s.
    // Expected per WINDOW_SEC window = 30 × WINDOW_SEC frames.
    // Plateau spans WINDOW_SEC centered on the gap (±WINDOW_SEC/2).
    const numPoints = 200; // covers up to 19.9s
    const ys = buildTopicLossRateSeries(topic(30, [gap(15.9, 1)]), numPoints);
    const expectedPct = (1 / (30 * window)) * 100;

    // The loss must appear at x=15.9 itself.
    expect(ys[Math.round(15.9 / step)]).toBeCloseTo(expectedPct, 5);

    // And in the neighboring points well inside the plateau.
    expect(ys[Math.round(15.8 / step)]).toBeCloseTo(expectedPct, 5);
    expect(ys[Math.round(16.0 / step)]).toBeCloseTo(expectedPct, 5);

    // The OLD 1-second-bin behavior placed the spike at x=15.0 — this must now be 0.
    expect(ys[Math.round(15.0 / step)]).toBe(0);

    // Points far outside the 0.5s plateau are 0.
    expect(ys[Math.round(15.0 / step)]).toBe(0);
    expect(ys[Math.round(17.0 / step)]).toBe(0);
  });

  it("sums lost_count across multiple gaps inside the same window", () => {
    // Two gaps very close together — both fall inside any window centered near them.
    const ys = buildTopicLossRateSeries(topic(30, [gap(10.0, 1), gap(10.05, 2)]), 200);
    const expectedPct = ((1 + 2) / (30 * window)) * 100;
    expect(ys[Math.round(10.0 / step)]).toBeCloseTo(expectedPct, 5);
  });

  it("caps the rate at 100%", () => {
    // 30 Hz topic, a huge burst of 100 lost frames at t=5s: 100/15 ≈ 666% → clamped to 100.
    const ys = buildTopicLossRateSeries(topic(30, [gap(5.0, 100)]), 100);
    expect(ys[Math.round(5.0 / step)]).toBe(100);
  });
});

describe("buildLossRateData", () => {
  it("returns an empty xs array when there are no topics", () => {
    const result = buildLossRateData([], null, 10);
    expect(result.length).toBe(1);
    expect((result[0] as Float64Array).length).toBe(0);
  });

  it("returns an empty xs array when durationSec is 0", () => {
    const result = buildLossRateData([topic(30, [gap(1, 1)])], null, 0);
    expect((result[0] as Float64Array).length).toBe(0);
  });

  it("emits xs at STEP_SEC intervals covering durationSec", () => {
    const result = buildLossRateData([topic(30, [])], null, 1.0);
    const xs = result[0] as Float64Array;
    // ceil(1.0 / 0.1) + 1 = 11 points: 0.0, 0.1, ..., 1.0
    expect(xs.length).toBe(11);
    expect(xs[0]).toBe(0);
    expect(xs[xs.length - 1]).toBeCloseTo(1.0, 5);
  });

  it("filters to the selected topic only", () => {
    const t1 = { ...topic(30, [gap(1, 1)]), name: "/a" };
    const t2 = { ...topic(30, [gap(2, 1)]), name: "/b" };
    const result = buildLossRateData([t1, t2], "/b", 5);
    // [xs, ys for /b only]
    expect(result.length).toBe(2);
  });

  it("includes one ys series per topic when no topic is selected", () => {
    const t1 = { ...topic(30, []), name: "/a" };
    const t2 = { ...topic(30, []), name: "/b" };
    const result = buildLossRateData([t1, t2], null, 5);
    expect(result.length).toBe(3); // xs + 2 topics
  });
});
