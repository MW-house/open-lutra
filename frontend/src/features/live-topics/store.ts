/** Store managing topic selection state. */
import { create } from "zustand";
import { devtools } from "zustand/middleware";

/** Maximum number of topics that can be previewed at once */
export const MAX_PREVIEWED_TOPICS = 4;

interface TopicStore {
  /** Set of topic names selected for recording */
  selectedTopics: Set<string>;
  /** Topics shown in the preview (in selection order). Up to MAX_PREVIEWED_TOPICS. */
  previewedTopics: string[];
  /** Whether live mode is on */
  isLive: boolean;

  toggleTopic: (topic: string) => void;
  selectAllTopics: (topics: string[]) => void;
  deselectAllTopics: () => void;
  /** Toggle a preview tile add/remove. Adding past MAX_PREVIEWED_TOPICS is ignored. */
  togglePreviewedTopic: (topic: string) => void;
  /** Remove the given topic from the preview (X button). */
  removePreviewedTopic: (topic: string) => void;
  /** Clear the entire preview (click on empty list area). */
  clearPreviewedTopics: () => void;
  setIsLive: (live: boolean) => void;
  initializeTopics: (defaultTopics: string[]) => void;
}

export const useLiveTopicsStore = create<TopicStore>()(
  devtools(
    (set) => ({
      selectedTopics: new Set<string>(),
      previewedTopics: [],
      isLive: false,

      toggleTopic: (topic) =>
        set(
          (state) => {
            const next = new Set(state.selectedTopics);
            if (next.has(topic)) next.delete(topic);
            else next.add(topic);
            return { selectedTopics: next };
          },
          false,
          "toggleTopic",
        ),

      selectAllTopics: (topics) => set({ selectedTopics: new Set(topics) }, false, "selectAllTopics"),
      deselectAllTopics: () => set({ selectedTopics: new Set() }, false, "deselectAllTopics"),

      togglePreviewedTopic: (topic) =>
        set(
          (state) => {
            if (state.previewedTopics.includes(topic)) {
              return { previewedTopics: state.previewedTopics.filter((t) => t !== topic) };
            }
            // At the limit — silently no-op
            if (state.previewedTopics.length >= MAX_PREVIEWED_TOPICS) return state;
            return { previewedTopics: [...state.previewedTopics, topic] };
          },
          false,
          "togglePreviewedTopic",
        ),

      removePreviewedTopic: (topic) =>
        set(
          (state) => {
            if (!state.previewedTopics.includes(topic)) return state;
            return { previewedTopics: state.previewedTopics.filter((t) => t !== topic) };
          },
          false,
          "removePreviewedTopic",
        ),

      clearPreviewedTopics: () => set({ previewedTopics: [] }, false, "clearPreviewedTopics"),

      setIsLive: (live) => set({ isLive: live }, false, "setIsLive"),
      initializeTopics: (defaultTopics) => set({ selectedTopics: new Set(defaultTopics) }, false, "initializeTopics"),
    }),
    { name: "TopicStore" },
  ),
);
