/** Store that accumulates time-series quality metrics.
 *
 * Stores the topic_stats received once per second over SSE in a ring buffer,
 * and uses them as the source data for the Loss Rate graph and heatmap.
 */
import { create } from "zustand";
import { devtools } from "zustand/middleware";

/** Per-second snapshot (across all topics). */
export interface QualitySnapshot {
  /** Elapsed seconds (relative time, with the first push at 0). */
  elapsed: number;
  /** Map of topic name → loss_rate (0.0–1.0). */
  loss: Record<string, number>;
}

/** Marker for recording start/stop. */
export interface RecordingMarker {
  elapsed: number;
  type: "start" | "stop";
}

/** Maximum buffer size (5 minutes = 300 seconds). */
const MAX_BUFFER_SIZE = 300;

interface QualityHistoryStore {
  /** Time-series snapshots. */
  snapshots: QualitySnapshot[];
  /** Ordered list of detected topic names. */
  topicNames: string[];
  /** Time of the first push (monotonic clock reference). */
  startTime: number | null;
  /** Recording start/stop markers. */
  markers: RecordingMarker[];

  /** Append a new snapshot. */
  push: (topics: { name: string; loss_rate?: number }[]) => void;
  /** Append a recording marker. */
  addMarker: (type: "start" | "stop") => void;
}

export const useQualityHistoryStore = create<QualityHistoryStore>()(
  devtools(
    (set, get) => ({
      snapshots: [],
      topicNames: [],
      startTime: null,
      markers: [],

      push: (topics) => {
        const now = performance.now() / 1000;
        const state = get();
        const startTime = state.startTime ?? now;

        const loss: Record<string, number> = {};
        const knownNames = new Set(state.topicNames);
        const newNames: string[] = [];

        for (const t of topics) {
          loss[t.name] = t.loss_rate ?? 0;
          if (!knownNames.has(t.name)) {
            newNames.push(t.name);
          }
        }

        const snapshot: QualitySnapshot = {
          elapsed: now - startTime,
          loss,
        };

        const snapshots = [...state.snapshots, snapshot];
        if (snapshots.length > MAX_BUFFER_SIZE) {
          snapshots.splice(0, snapshots.length - MAX_BUFFER_SIZE);
        }

        set(
          {
            snapshots,
            topicNames: newNames.length > 0 ? [...state.topicNames, ...newNames] : state.topicNames,
            startTime,
          },
          false,
          "push",
        );
      },

      addMarker: (type) => {
        const state = get();
        if (state.startTime == null) return;
        const elapsed = performance.now() / 1000 - state.startTime;
        set({ markers: [...state.markers, { elapsed, type }] }, false, "addMarker");
      },
    }),
    { name: "QualityHistoryStore" },
  ),
);
