import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createTimer } from "../create-timer";

describe("createTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("invokes the callback after the specified delay", () => {
    const timer = createTimer();
    const callback = vi.fn();

    timer.set(callback, 1000);
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalledOnce();
  });

  it("cancels the previous timer when set is called again", () => {
    const timer = createTimer();
    const first = vi.fn();
    const second = vi.fn();

    timer.set(first, 1000);
    timer.set(second, 1000);

    vi.advanceTimersByTime(1000);
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledOnce();
  });

  it("cancels the timer with clear", () => {
    const timer = createTimer();
    const callback = vi.fn();

    timer.set(callback, 1000);
    timer.clear();

    vi.advanceTimersByTime(1000);
    expect(callback).not.toHaveBeenCalled();
  });

  it("can call set again after clear", () => {
    const timer = createTimer();
    const callback = vi.fn();

    timer.set(callback, 1000);
    timer.clear();
    timer.set(callback, 500);

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledOnce();
  });

  it("does not throw when clear is called with no timer set", () => {
    const timer = createTimer();
    expect(() => timer.clear()).not.toThrow();
  });

  it("does not throw when clear is called after the callback ran", () => {
    const timer = createTimer();
    const callback = vi.fn();

    timer.set(callback, 100);
    vi.advanceTimersByTime(100);
    expect(() => timer.clear()).not.toThrow();
  });
});
