/** State management for the Quality Timeline (MCAP detail page).
 *
 * Centralizes topic selection, view range, playhead, and playback state.
 * Timeline Controller / heatmap / video / graphs all read from this store.
 */

import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface ViewRange {
  from: number;
  to: number;
}

/** Loss event currently hovered by the mouse. Used to highlight the corresponding gap in the timeline heatmap. */
export interface HoveredLossEvent {
  topicName: string;
  timestampSec: number;
}

interface QualityTimelineState {
  /** Currently selected topic name. null = show all topics */
  selectedTopic: string | null;
  setSelectedTopic: (topic: string | null) => void;

  /** Currently displayed time range (seconds) */
  viewRange: ViewRange;
  setViewRange: (range: ViewRange) => void;

  /** Playhead position (seconds) */
  playheadSec: number;
  setPlayheadSec: (sec: number) => void;

  /** Whether playback is active */
  isPlaying: boolean;
  setIsPlaying: (playing: boolean) => void;

  /** Whether a drag operation is in progress (minimap etc.). API requests are suppressed while true */
  isDragging: boolean;
  setIsDragging: (dragging: boolean) => void;

  /** Total recording length (seconds). Set when timeline data is fetched */
  durationSec: number;
  setDurationSec: (sec: number) => void;

  /** Loss event hovered in the quality detail panel. Used to highlight the same gap in the timeline heatmap */
  hoveredLossEvent: HoveredLossEvent | null;
  setHoveredLossEvent: (loss: HoveredLossEvent | null) => void;

  /** Reset all state (on page leave) */
  reset: () => void;
}

const initialState = {
  selectedTopic: null,
  viewRange: { from: 0, to: 0 },
  playheadSec: 0,
  isPlaying: false,
  isDragging: false,
  durationSec: 0,
  hoveredLossEvent: null as HoveredLossEvent | null,
};

export const useQualityTimelineStore = create<QualityTimelineState>()(
  devtools(
    (set) => ({
      ...initialState,
      setSelectedTopic: (topic) => set({ selectedTopic: topic }),
      setViewRange: (range) => set({ viewRange: range }),
      setPlayheadSec: (sec) => set({ playheadSec: sec }),
      setIsPlaying: (playing) => set({ isPlaying: playing }),
      setIsDragging: (dragging) => set({ isDragging: dragging }),
      setDurationSec: (sec) => set({ durationSec: sec, viewRange: { from: 0, to: sec } }),
      setHoveredLossEvent: (loss) => set({ hoveredLossEvent: loss }),
      reset: () => set(initialState),
    }),
    { name: "quality-timeline" },
  ),
);
