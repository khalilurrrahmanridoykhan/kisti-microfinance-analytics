import { describe, expect, it } from "vitest";
import { roundedBarPath, roundedColumnPath } from "./svg";

describe("roundedBarPath", () => {
  it("starts and ends at the baseline x for a zero-width bar", () => {
    const path = roundedBarPath(10, 0, 0, 20);
    expect(path).toContain("M 10 0");
  });

  it("draws a path that reaches the bar's far edge", () => {
    const path = roundedBarPath(0, 0, 100, 20, 4);
    expect(path).toContain("H 96"); // far edge minus the corner radius
    expect(path.startsWith("M 0 0")).toBe(true);
  });

  it("caps the radius so it never exceeds half the height or the width", () => {
    const path = roundedBarPath(0, 0, 3, 40, 10);
    // radius is capped at width (3), so the horizontal run to the corner is at x=0
    expect(path).toContain("H 0");
  });
});

describe("roundedColumnPath", () => {
  it("closes at the baseline (yTop + height)", () => {
    const path = roundedColumnPath(0, 0, 20, 50, 4);
    expect(path).toContain("M 0 50");
  });

  it("handles a zero-height column without throwing", () => {
    expect(() => roundedColumnPath(0, 100, 20, 0)).not.toThrow();
  });
});
