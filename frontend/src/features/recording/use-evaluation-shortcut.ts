/** Keyboard shortcut: E cycles the task-evaluation value through its options, so an operator can
 * label a finished take (success / failure) from the completion banner without the mouse.
 *
 * Mounted by RecordingCompletionBanner, which renders only while a finished recording is shown, so
 * the listener is scoped to that window and torn down when the banner clears. Uses a distinct key
 * from the Space record-toggle (use-record-shortcut) so the two coexist on the recorder page.
 *
 * The focus rule and the listener setup come from usePageShortcut, so E follows the same rule as
 * Space. No per-key exception is needed: none of the recorder page's <select> options start with
 * "e", so cancelling the native typeahead costs nothing.
 */

import type { MetadataFieldOptionResponse } from "@/api/generated/schemas";
import { usePageShortcut } from "./use-page-shortcut";

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
  usePageShortcut({
    code: "KeyE",
    // An empty list has nothing to cycle. Gating registration rather than returning from onFire
    // leaves the key to the rest of the page instead of cancelling its default for nothing.
    enabled: enabled && options.length > 0,
    // Advance to the next option, wrapping at the end; an unknown current (index -1) → first.
    onFire: () => onSelect(options[(options.findIndex((o) => o.value === current) + 1) % options.length].value),
  });
}
