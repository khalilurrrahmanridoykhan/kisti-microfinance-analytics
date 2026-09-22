import { describe, expect, it } from "vitest";
import { bandOrder, rangeByBand } from "./bands";
import type { MfiRecord, SizeBandDef } from "./types";

const SIZE_BANDS: SizeBandDef[] = [
  { label: "< 10 million", min_bdt: null, max_bdt: 10e6 },
  { label: "10-100 million", min_bdt: 10e6, max_bdt: 100e6 },
];

function mfi(size_band: string, value: number): MfiRecord {
  return {
    license_no: Math.random(),
    name: "x",
    size_band,
    branches: 1,
    employees_total: 1,
    clients_total: 1,
    borrowers_total: 1,
    female_client_share_pct: null,
    savings_bdt: null,
    loan_outstanding_bdt: 1,
    avg_loan_size_bdt: value,
    has_ratios: false,
    portfolio_yield: null,
    operating_self_sufficiency: null,
    return_on_assets: null,
    total_operating_cost_ratio: null,
    borrowing_to_loan_outstanding: null,
    capital_fund_to_loan_outstanding: null,
    has_funds: false,
    savings_share_of_funds_pct: null,
    yield_percentile_in_band: null,
    oss_percentile_in_band: null,
    cost_percentile_in_band: null,
    group: null,
    flagged: false,
  };
}

describe("bandOrder", () => {
  it("returns the labels in the order methods.json lists them", () => {
    expect(bandOrder(SIZE_BANDS)).toEqual(["< 10 million", "10-100 million"]);
  });
});

describe("rangeByBand", () => {
  it("summarises each band's values in the given order and drops empty bands", () => {
    const mfis = [mfi("10-100 million", 10), mfi("10-100 million", 30), mfi("10-100 million", 20)];
    const result = rangeByBand(mfis, bandOrder(SIZE_BANDS), (m) => m.avg_loan_size_bdt);
    expect(result).toEqual([{ label: "10-100 million", n: 3, p25: 15, median: 20, p75: 25 }]);
  });

  it("skips a value function that returns null for a given MFI", () => {
    const mfis = [mfi("< 10 million", 5)];
    const result = rangeByBand(mfis, bandOrder(SIZE_BANDS), () => null);
    expect(result).toEqual([]);
  });
});
