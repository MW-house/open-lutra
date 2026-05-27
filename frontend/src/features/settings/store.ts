/** Application settings store.
 *
 * Persists task name and similar settings to localStorage.
 */
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface SettingsState {
  /** Task name (the leading part of the filename) */
  taskName: string;
}

interface SettingsActions {
  /** Update settings */
  update: (values: Partial<SettingsState>) => void;
  /** Reset settings (for testing) */
  reset: () => void;
}

type SettingsStore = SettingsState & SettingsActions;

const initialState: SettingsState = {
  taskName: "",
};

export const useSettingsStore = create<SettingsStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        update: (values) => set(values, false, "update"),

        reset: () => set(initialState, false, "reset"),
      }),
      {
        name: "app-settings",
        partialize: (state) => ({
          taskName: state.taskName,
        }),
      },
    ),
    { name: "SettingsStore" },
  ),
);
