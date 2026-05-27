/** State management for recording-list check status. */
import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface RecordingsStore {
  /** Set of checked folder names */
  checkedFolders: Set<string>;
  toggleCheck: (folder: string) => void;
  toggleCheckAll: (allFolders: string[]) => void;
  /** Replace the check state entirely with the given folders (used when switching filter tabs) */
  setCheckedFolders: (folders: string[]) => void;
  clearChecked: () => void;
}

export const useRecordingsStore = create<RecordingsStore>()(
  devtools(
    (set) => ({
      checkedFolders: new Set(),
      toggleCheck: (folder) =>
        set(
          (state) => {
            const next = new Set(state.checkedFolders);
            if (next.has(folder)) next.delete(folder);
            else next.add(folder);
            return { checkedFolders: next };
          },
          false,
          "toggleCheck",
        ),
      toggleCheckAll: (allFolders) =>
        set(
          (state) => {
            const allChecked = allFolders.length > 0 && allFolders.every((f) => state.checkedFolders.has(f));
            return { checkedFolders: allChecked ? new Set() : new Set(allFolders) };
          },
          false,
          "toggleCheckAll",
        ),
      setCheckedFolders: (folders) => set({ checkedFolders: new Set(folders) }, false, "setCheckedFolders"),
      clearChecked: () => set({ checkedFolders: new Set() }, false, "clearChecked"),
    }),
    { name: "RecordingsStore" },
  ),
);
