import { formatCompactTaka, formatNumber } from "./format";
import type { DistrictRecord } from "./types";

export interface MapMetric {
  id: string;
  label: string;
  /** Short form for the metric switcher. */
  short: string;
  value: (d: DistrictRecord) => number;
  /** The figure for Bangladesh as a whole, from district totals (not a mean of district ratios). */
  national: (rows: DistrictRecord[]) => number;
  format: (v: number) => string;
}

const sum = (rows: DistrictRecord[], f: (d: DistrictRecord) => number) => rows.reduce((total, d) => total + f(d), 0);

export const MAP_METRICS: MapMetric[] = [
  {
    id: "borrowers",
    label: "MFI borrowers per 1,000 people",
    short: "Borrowers / 1,000",
    value: (d) => d.borrowers_per_1000,
    national: (rows) => (sum(rows, (d) => d.borrowers) / sum(rows, (d) => d.population)) * 1000,
    format: (v) => formatNumber(v, 0),
  },
  {
    id: "loans",
    label: "Loan outstanding per person",
    short: "Loans / person",
    value: (d) => d.loan_outstanding_per_person_bdt,
    national: (rows) => sum(rows, (d) => d.loan_outstanding_bdt) / sum(rows, (d) => d.population),
    format: formatCompactTaka,
  },
  {
    id: "branches",
    label: "MFI branches per 100,000 people",
    short: "Branches / 100K",
    value: (d) => d.branches_per_100k,
    national: (rows) => (sum(rows, (d) => d.branches) / sum(rows, (d) => d.population)) * 100_000,
    format: (v) => formatNumber(v, 1),
  },
  {
    id: "avg_loan",
    label: "Average loan per borrower",
    short: "Avg loan",
    value: (d) => d.avg_loan_size_bdt,
    national: (rows) => sum(rows, (d) => d.loan_outstanding_bdt) / sum(rows, (d) => d.borrowers),
    format: formatCompactTaka,
  },
  {
    id: "account",
    label: "People with a financial-institution account (Census 2022)",
    short: "Account %",
    value: (d) => d.financial_account_pct,
    national: (rows) => sum(rows, (d) => d.financial_account_pct * d.population) / sum(rows, (d) => d.population),
    format: (v) => `${formatNumber(v, 0)}%`,
  },
];

export const CLASS_COUNT = 5;

export interface ColorClass {
  min: number;
  max: number;
}

/** Splits the values into CLASS_COUNT quantile classes (about 13 districts each for 64), so
 * every colour step is used whatever the skew. Returns each class's actual min and max. */
export function quantileClasses(values: number[]): ColorClass[] {
  const sorted = [...values].sort((a, b) => a - b);
  const classes: ColorClass[] = [];
  for (let i = 0; i < CLASS_COUNT; i++) {
    const start = Math.floor((i * sorted.length) / CLASS_COUNT);
    const end = Math.floor(((i + 1) * sorted.length) / CLASS_COUNT) - 1;
    if (end < start) continue;
    classes.push({ min: sorted[start], max: sorted[end] });
  }
  return classes;
}

/** The class index (0 = lowest) for a value, against classes from `quantileClasses`. */
export function classOf(value: number, classes: ColorClass[]): number {
  for (let i = classes.length - 1; i > 0; i--) {
    if (value >= classes[i].min) return i;
  }
  return 0;
}
