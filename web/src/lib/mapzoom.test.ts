import { describe, expect, it } from "vitest";
import { IDENTITY, expandBox, fitBox, visibleBox } from "./mapzoom";

describe("fitBox", () => {
  it("centres and scales a box to fill the view less its margin", () => {
    const t = fitBox([40, 40, 60, 60], 100, 100, 0);
    expect(t.scale).toBe(5);
    // The box centre (50, 50) lands on the view centre.
    expect(t.scale * 50 + t.tx).toBe(50);
    expect(t.scale * 50 + t.ty).toBe(50);
  });

  it("never zooms out past the whole map and caps the zoom", () => {
    expect(fitBox([0, 0, 500, 500], 100, 100).scale).toBe(1);
    expect(fitBox([10, 10, 10.5, 10.5], 100, 100, 0, 6).scale).toBe(6);
  });
});

describe("visibleBox", () => {
  it("is the whole view with no zoom", () => {
    expect(visibleBox(IDENTITY, 100, 80)).toEqual([0, 0, 100, 80]);
  });

  it("inverts fitBox: the fitted box sits inside the visible window", () => {
    const t = fitBox([40, 40, 60, 60], 100, 100, 0.1);
    const [x0, y0, x1, y1] = visibleBox(t, 100, 100);
    expect(x0).toBeLessThanOrEqual(40);
    expect(y0).toBeLessThanOrEqual(40);
    expect(x1).toBeGreaterThanOrEqual(60);
    expect(y1).toBeGreaterThanOrEqual(60);
  });
});

describe("expandBox", () => {
  it("grows a box around its centre", () => {
    expect(expandBox([10, 10, 20, 30], 2)).toEqual([5, 0, 25, 40]);
  });
});
