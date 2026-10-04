import { describe, expect, it } from "vitest";
import { MAP_METRICS, classOf, quantileClasses } from "./choropleth";
import type { DistrictRecord } from "./types";

describe("quantileClasses", () => {
  it("splits 10 values into 5 classes of 2, each with its actual min and max", () => {
    const classes = quantileClasses([10, 1, 9, 2, 8, 3, 7, 4, 6, 5]);
    expect(classes).toEqual([
      { min: 1, max: 2 },
      { min: 3, max: 4 },
      { min: 5, max: 6 },
      { min: 7, max: 8 },
      { min: 9, max: 10 },
    ]);
  });

  it("uses every class for 64 districts", () => {
    const classes = quantileClasses(Array.from({ length: 64 }, (_, i) => i));
    expect(classes).toHaveLength(5);
    expect(classes[0].min).toBe(0);
    expect(classes[4].max).toBe(63);
  });
});

describe("classOf", () => {
  const classes = quantileClasses([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  it("maps the extremes to the first and last class", () => {
    expect(classOf(1, classes)).toBe(0);
    expect(classOf(10, classes)).toBe(4);
  });
  it("puts a value between two classes in the lower one", () => {
    expect(classOf(4.5, classes)).toBe(1);
  });
});

describe("national figures", () => {
  const rows = [
    { population: 1000, borrowers: 100, branches: 1, loan_outstanding_bdt: 50_000, financial_account_pct: 20 },
    { population: 3000, borrowers: 900, branches: 5, loan_outstanding_bdt: 150_000, financial_account_pct: 40 },
  ] as DistrictRecord[];
  const byId = (id: string) => MAP_METRICS.find((m) => m.id === id)!;

  it("are ratios of totals, not means of district ratios", () => {
    expect(byId("borrowers").national(rows)).toBeCloseTo(250);
    expect(byId("loans").national(rows)).toBeCloseTo(50);
    expect(byId("branches").national(rows)).toBeCloseTo(150);
    expect(byId("avg_loan").national(rows)).toBeCloseTo(200);
  });

  it("weights the account share by population", () => {
    expect(byId("account").national(rows)).toBeCloseTo(35);
  });
});
