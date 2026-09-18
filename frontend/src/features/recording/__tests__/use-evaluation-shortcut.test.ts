import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { MetadataFieldOptionResponse } from "@/api/generated/schemas";
import { useEvaluationShortcut } from "../use-evaluation-shortcut";

const OPTIONS: MetadataFieldOptionResponse[] = [
  { value: "success", label: "成功" },
  { value: "failure", label: "失敗" },
];

function dispatchE(): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { code: "KeyE", cancelable: true });
  document.dispatchEvent(event);
  return event;
}

function mount(props: Partial<Parameters<typeof useEvaluationShortcut>[0]> = {}) {
  const onSelect = vi.fn();
  const result = renderHook(() =>
    useEvaluationShortcut({ enabled: true, options: OPTIONS, current: "success", onSelect, ...props }),
  );
  return { onSelect, ...result };
}

/** The shared listener and focus rule are covered by use-page-shortcut / keyboard; this is the cycle. */
describe("useEvaluationShortcut", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("advances to the next option and prevents default", () => {
    const { onSelect } = mount({ current: "success" });

    const event = dispatchE();

    expect(onSelect).toHaveBeenCalledWith("failure");
    expect(event.defaultPrevented).toBe(true);
  });

  it("wraps from the last option back to the first", () => {
    const { onSelect } = mount({ current: "failure" });

    dispatchE();

    expect(onSelect).toHaveBeenCalledWith("success");
  });

  it("falls back to the first option when the current value is unknown", () => {
    const { onSelect } = mount({ current: "???" });

    dispatchE();

    expect(onSelect).toHaveBeenCalledWith("success");
  });

  it("cycles from the latest value, so a second press advances again", () => {
    const onSelect = vi.fn();
    const { rerender } = renderHook(
      ({ current }: { current: string }) =>
        useEvaluationShortcut({ enabled: true, options: OPTIONS, current, onSelect }),
      { initialProps: { current: "success" } },
    );

    rerender({ current: "failure" });
    dispatchE();

    // Reads the fresh "failure" and wraps to "success" rather than the stale "success" → "failure".
    expect(onSelect).toHaveBeenCalledWith("success");
  });

  it("does nothing when disabled", () => {
    const { onSelect } = mount({ enabled: false });

    dispatchE();

    expect(onSelect).not.toHaveBeenCalled();
  });

  it("does nothing when there are no options, leaving the default action intact", () => {
    const { onSelect } = mount({ options: [] });

    const event = dispatchE();

    expect(onSelect).not.toHaveBeenCalled();
    expect(event.defaultPrevented).toBe(false);
  });
});
