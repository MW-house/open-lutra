import { beforeEach, describe, expect, it, vi } from "vitest";
import { useQualityHistoryStore } from "../quality-history-store";

describe("useQualityHistoryStore", () => {
  beforeEach(() => {
    useQualityHistoryStore.setState({ snapshots: [], topicNames: [], startTime: null, markers: [] });
    vi.restoreAllMocks();
  });

  describe("push", () => {
    it("appends a snapshot", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);

      useQualityHistoryStore.getState().push([
        { name: "/topic_a", loss_rate: 0.1 },
        { name: "/topic_b", loss_rate: 0.0 },
      ]);

      const state = useQualityHistoryStore.getState();
      expect(state.snapshots).toHaveLength(1);
      expect(state.snapshots[0].loss).toEqual({ "/topic_a": 0.1, "/topic_b": 0.0 });
    });

    it("sets startTime on the first push", () => {
      vi.spyOn(performance, "now").mockReturnValue(5000);

      useQualityHistoryStore.getState().push([{ name: "/a" }]);

      expect(useQualityHistoryStore.getState().startTime).toBe(5);
    });

    it("computes elapsed as seconds relative to the start time", () => {
      const mockNow = vi.spyOn(performance, "now");
      mockNow.mockReturnValue(1000);
      useQualityHistoryStore.getState().push([{ name: "/a", loss_rate: 0 }]);

      mockNow.mockReturnValue(3000);
      useQualityHistoryStore.getState().push([{ name: "/a", loss_rate: 0 }]);

      const snapshots = useQualityHistoryStore.getState().snapshots;
      expect(snapshots[0].elapsed).toBeCloseTo(0, 5);
      expect(snapshots[1].elapsed).toBeCloseTo(2, 5);
    });

    it("appends newly seen topic names to topicNames", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);

      useQualityHistoryStore.getState().push([{ name: "/a" }]);
      useQualityHistoryStore.getState().push([{ name: "/a" }, { name: "/b" }]);

      expect(useQualityHistoryStore.getState().topicNames).toEqual(["/a", "/b"]);
    });

    it("records 0 when loss_rate is undefined", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);

      useQualityHistoryStore.getState().push([{ name: "/a" }]);

      expect(useQualityHistoryStore.getState().snapshots[0].loss["/a"]).toBe(0);
    });

    it("drops the oldest snapshots once the count exceeds 300", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);

      for (let i = 0; i < 310; i++) {
        useQualityHistoryStore.getState().push([{ name: "/a", loss_rate: i / 1000 }]);
      }

      const snapshots = useQualityHistoryStore.getState().snapshots;
      expect(snapshots.length).toBe(300);
      expect(snapshots[snapshots.length - 1].loss["/a"]).toBeCloseTo(0.309, 3);
    });
  });

  describe("addMarker", () => {
    it("does not add a marker when startTime is unset", () => {
      useQualityHistoryStore.getState().addMarker("start");
      expect(useQualityHistoryStore.getState().markers).toHaveLength(0);
    });

    it("adds a recording-start marker", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);
      useQualityHistoryStore.getState().push([{ name: "/a" }]);

      vi.spyOn(performance, "now").mockReturnValue(3000);
      useQualityHistoryStore.getState().addMarker("start");

      const markers = useQualityHistoryStore.getState().markers;
      expect(markers).toHaveLength(1);
      expect(markers[0].type).toBe("start");
      expect(markers[0].elapsed).toBeCloseTo(2, 5);
    });

    it("adds a recording-stop marker", () => {
      vi.spyOn(performance, "now").mockReturnValue(1000);
      useQualityHistoryStore.getState().push([{ name: "/a" }]);

      vi.spyOn(performance, "now").mockReturnValue(5000);
      useQualityHistoryStore.getState().addMarker("stop");

      const markers = useQualityHistoryStore.getState().markers;
      expect(markers[0].type).toBe("stop");
    });
  });
});
