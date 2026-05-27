import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ValidationBadge } from "../validation-badge";

describe("ValidationBadge", () => {
  it.each([null, "unknown"] as const)("reserves an empty icon slot for status=%s", (status) => {
    const { container } = render(<ValidationBadge status={status} />);
    const slot = container.firstChild as HTMLElement | null;
    expect(slot).not.toBeNull();
    expect(slot?.getAttribute("data-status")).toBeNull();
    expect(slot?.querySelector("svg")).toBeNull();
  });

  it.each(["pass", "warn", "fail", "error"] as const)("renders an icon for status=%s", (status) => {
    const { container } = render(<ValidationBadge status={status} />);
    const slot = container.querySelector(`[data-status="${status}"]`);
    expect(slot).not.toBeNull();
    expect(slot?.querySelector("svg")).not.toBeNull();
  });
});
