/** Store managing severity filters for logs and health checks. */
import { create } from "zustand";
import { devtools } from "zustand/middleware";

export type Severity = "info" | "warning" | "danger";

interface LogStore {
  /** Severity filter for the log panel */
  severityFilter: Set<Severity>;
  /** Severity filter for the health-check panel */
  healthSeverityFilter: Set<Severity>;

  toggleSeverityFilter: (severity: Severity) => void;
  toggleHealthSeverityFilter: (severity: Severity) => void;
}

export const useLogStore = create<LogStore>()(
  devtools(
    (set) => ({
      severityFilter: new Set<Severity>(["info", "warning", "danger"]),
      healthSeverityFilter: new Set<Severity>(["info", "warning", "danger"]),

      toggleSeverityFilter: (severity) =>
        set(
          (state) => {
            const next = new Set(state.severityFilter);
            if (next.has(severity)) next.delete(severity);
            else next.add(severity);
            return { severityFilter: next };
          },
          false,
          "toggleSeverityFilter",
        ),

      toggleHealthSeverityFilter: (severity) =>
        set(
          (state) => {
            const next = new Set(state.healthSeverityFilter);
            if (next.has(severity)) next.delete(severity);
            else next.add(severity);
            return { healthSeverityFilter: next };
          },
          false,
          "toggleHealthSeverityFilter",
        ),
    }),
    { name: "LogStore" },
  ),
);
