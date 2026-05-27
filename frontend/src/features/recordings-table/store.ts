/** State management for the recordings-table filter and search.
 *
 * MCAP folders are always shown in descending date order (the default of `scan_dir`),
 * so no sort functionality is provided.
 */
import { create } from "zustand";
import { devtools } from "zustand/middleware";

/** Filter value by task_name.
 *
 * - `null`: all tasks (no filter)
 * - `""`: only recordings without task_name
 * - any other string: only recordings whose task_name matches exactly
 */
export type TaskFilterValue = string | null;

interface RecordingsTableStore {
  /** Search text */
  searchText: string;
  setSearchText: (text: string) => void;

  /** task_name filter */
  taskFilter: TaskFilterValue;
  setTaskFilter: (value: TaskFilterValue) => void;
}

export const useRecordingsTableStore = create<RecordingsTableStore>()(
  devtools(
    (set) => ({
      searchText: "",
      setSearchText: (text) => set({ searchText: text }, false, "setSearchText"),

      taskFilter: null,
      setTaskFilter: (value) => set({ taskFilter: value }, false, "setTaskFilter"),
    }),
    { name: "RecordingsTableStore" },
  ),
);
