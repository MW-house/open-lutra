import { describe, expect, it } from "vitest";
import { sseKeys } from "../query-keys";

describe("sseKeys", () => {
  it("returns the topicStats key", () => {
    expect(sseKeys.topicStats()).toEqual(["sse", "topic-stats"]);
  });

  it("returns the logs key", () => {
    expect(sseKeys.logs()).toEqual(["sse", "logs"]);
  });

  it("returns the connectionStatus key", () => {
    expect(sseKeys.connectionStatus()).toEqual(["sse", "connection-status"]);
  });

  it("returns the jobs key", () => {
    expect(sseKeys.jobs()).toEqual(["sse", "jobs"]);
  });

  it("returns the same value on every call (references may differ)", () => {
    expect(sseKeys.topicStats()).toEqual(sseKeys.topicStats());
    expect(sseKeys.logs()).toEqual(sseKeys.logs());
  });
});
