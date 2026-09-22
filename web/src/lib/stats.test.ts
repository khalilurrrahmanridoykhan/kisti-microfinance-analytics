import { describe, expect, it } from "vitest";
import { groupBy, median, quantile, summariseRange } from "./stats";

describe("quantile", () => {
  it("matches pandas' default linear interpolation on a known example", () => {
    const sorted = [1, 2, 3, 4];
    expect(quantile(sorted, 0)).toBe(1);
    expect(quantile(sorted, 1)).toBe(4);
    expect(quantile(sorted, 0.5)).toBe(2.5);
    expect(quantile(sorted, 0.25)).toBeCloseTo(1.75);
  });

  it("handles a single value and an empty array", () => {
    expect(quantile([5], 0.5)).toBe(5);
    expect(Number.isNaN(quantile([], 0.5))).toBe(true);
  });
});

describe("median", () => {
  it("sorts before computing, so input order does not matter", () => {
    expect(median([5, 1, 3])).toBe(3);
    expect(median([4, 1, 3, 2])).toBe(2.5);
  });
});

describe("summariseRange", () => {
  it("drops null, undefined and non-finite values before summarising", () => {
    const result = summariseRange([1, 2, 3, null, undefined, NaN, Infinity, 4]);
    expect(result).toEqual({ n: 4, p25: 1.75, median: 2.5, p75: 3.25 });
  });

  it("returns n=0 and NaN quantiles for an all-missing input", () => {
    const result = summariseRange([null, undefined]);
    expect(result.n).toBe(0);
    expect(Number.isNaN(result.median)).toBe(true);
  });
});

describe("groupBy", () => {
  it("preserves each group's row order and groups by the key function", () => {
    const rows = [{ band: "a", v: 1 }, { band: "b", v: 2 }, { band: "a", v: 3 }];
    const groups = groupBy(rows, (r) => r.band);
    expect([...groups.keys()]).toEqual(["a", "b"]);
    expect(groups.get("a")).toEqual([{ band: "a", v: 1 }, { band: "a", v: 3 }]);
  });
});
