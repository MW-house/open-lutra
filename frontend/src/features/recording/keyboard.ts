/** Shared helpers for the recorder-page keyboard shortcuts. */

/** True when focus is on an element that natively consumes Space or text input. */
export function isInteractiveTarget(el: Element | null): boolean {
  if (!el) return false;
  if (
    el instanceof HTMLInputElement ||
    el instanceof HTMLTextAreaElement ||
    el instanceof HTMLSelectElement ||
    el instanceof HTMLButtonElement
  ) {
    return true;
  }
  if (el instanceof HTMLElement && el.isContentEditable) return true;
  return el.closest('[role="button"], [role="textbox"]') !== null;
}
