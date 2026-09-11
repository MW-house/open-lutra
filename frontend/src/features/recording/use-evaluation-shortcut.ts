/** Keyboard shortcut: E cycles the task-evaluation value through its options, so an operator can
 * label a finished take (success / failure) from the completion banner without the mouse.
 *
 * Mounted by RecordingCompletionBanner, which renders only while a finished recording is shown, so
 * the listener is scoped to that window and torn down when the banner clears. Uses a distinct key
 * from the Space record-toggle (use-record-shortcut) so the two coexist on the recorder page.
 */
import { useEffect, useRef } from "react";
import type { MetadataFieldOptionResponse } from "@/api/generated/schemas";
import { isInteractiveTarget } from "./keyboard";

interface EvaluationShortcutParams {
  /** Register the listener only while the banner can act (finished recording + field + entry). */
  enabled: boolean;
  /** The field's selectable options, in display order; cycled with wrap-around. */
  options: MetadataFieldOptionResponse[];
  /** The currently selected value; the next option after it is chosen (first if not found). */
  current: string;
  /** Persist the newly selected value. */
  onSelect: (value: string) => void;
}

export function useEvaluationShortcut({ enabled, options, current, onSelect }: EvaluationShortcutParams): void {
  // Keep the latest inputs in a ref so the handler reads fresh values without re-subscribing on
  // every selection change (mirrors use-record-shortcut reading getState() at fire time).
  const latest = useRef({ options, current, onSelect });
  latest.current = { options, current, onSelect };

  useEffect(() => {
    if (!enabled) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code !== "KeyE" || e.repeat) return;
      if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
      if (isInteractiveTarget(document.activeElement)) return;
      const { options: opts, current: cur, onSelect: select } = latest.current;
      if (opts.length === 0) return;
      e.preventDefault();
      // Advance to the next option, wrapping at the end; an unknown current (index -1) → first.
      const next = opts[(opts.findIndex((o) => o.value === cur) + 1) % opts.length];
      select(next.value);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [enabled]);
}
