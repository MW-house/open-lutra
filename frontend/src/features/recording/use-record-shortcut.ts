/** Keyboard shortcut: Space toggles recording start/stop, mirroring the Record button.
 *
 * Mounted by RecordButton, which renders only on the recorder page, so the shortcut is
 * scoped to that page and torn down on navigation. Targets hands-free operation (e.g. a
 * foot pedal that emits Space) per issue #34.
 */
import { useEffect } from "react";
import { isInteractiveTarget } from "./keyboard";
import { useRecordingStore } from "./store";

export function useRecordShortcut(): void {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code !== "Space" || e.repeat) return;
      if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return;
      // Skip while typing or when an element already handles Space (also avoids a double-toggle
      // when the Record button itself is focused — its native Space click handles that case).
      if (isInteractiveTarget(document.activeElement)) return;
      // Space owns the recorder page; suppress the default page scroll.
      e.preventDefault();
      useRecordingStore.getState().toggle();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);
}
