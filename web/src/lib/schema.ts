/**
 * The TypeScript half of the data contract with the Python export
 * (src/kisti/webdata/schema.py). Field names and nullability here must match that file exactly;
 * schema.test.ts checks the committed JSON against this file, and
 * tests/test_webdata.py checks the same JSON against the Python one, so the two sides cannot
 * drift apart without a test failing on at least one of them.
 */

export type Kind = "string" | "number" | "boolean" | "int" | "string|null" | "number|null" | "int|null";

export type FieldSpec = Record<string, Kind>;

function matches(value: unknown, kind: Kind): boolean {
  switch (kind) {
    case "string":
      return typeof value === "string";
    case "number":
      return typeof value === "number" && Number.isFinite(value);
    case "int":
      return typeof value === "number" && Number.isInteger(value);
    case "boolean":
      return typeof value === "boolean";
    case "string|null":
      return value === null || typeof value === "string";
    case "number|null":
      return value === null || (typeof value === "number" && Number.isFinite(value));
    case "int|null":
      return value === null || (typeof value === "number" && Number.isInteger(value));
  }
}

/** Field-by-field errors for one record; empty means it matches the spec exactly. */
export function checkRecord(record: Record<string, unknown>, spec: FieldSpec, where: string): string[] {
  const errors: string[] = [];
  const specKeys = Object.keys(spec);
  const recordKeys = Object.keys(record);
  const missing = specKeys.filter((k) => !recordKeys.includes(k));
  const extra = recordKeys.filter((k) => !specKeys.includes(k));
  if (missing.length) errors.push(`${where}: missing fields ${JSON.stringify(missing)}`);
  if (extra.length) errors.push(`${where}: unexpected fields ${JSON.stringify(extra)}`);
  for (const [field, kind] of Object.entries(spec)) {
    if (!(field in record)) continue;
    if (!matches(record[field], kind)) {
      errors.push(`${where}.${field}: expected ${kind}, got ${JSON.stringify(record[field])}`);
    }
  }
  return errors;
}

export function checkRecords(records: Record<string, unknown>[], spec: FieldSpec, name: string): string[] {
  return records.flatMap((record, i) => checkRecord(record, spec, `${name}[${i}]`));
}

export const META: FieldSpec = {
  edition: "string",
  generated_at: "string",
  mfis_in_basic: "int",
  mfis_active: "int",
  loan_outstanding_active_bdt: "number",
};

export const CONCENTRATION_ROW: FieldSpec = {
  measure: "string",
  n_mfis: "int",
  top1_share_pct: "number",
  top4_share_pct: "number",
  top10_share_pct: "number",
  hhi: "number",
  gini: "number",
};

export const MFI_RECORD: FieldSpec = {
  license_no: "int",
  name: "string",
  size_band: "string|null",
  branches: "number|null",
  employees_total: "number|null",
  clients_total: "number|null",
  borrowers_total: "number",
  female_client_share_pct: "number|null",
  savings_bdt: "number|null",
  loan_outstanding_bdt: "number",
  avg_loan_size_bdt: "number",
  has_ratios: "boolean",
  portfolio_yield: "number|null",
  operating_self_sufficiency: "number|null",
  return_on_assets: "number|null",
  total_operating_cost_ratio: "number|null",
  borrowing_to_loan_outstanding: "number|null",
  capital_fund_to_loan_outstanding: "number|null",
  has_funds: "boolean",
  savings_share_of_funds_pct: "number|null",
  yield_percentile_in_band: "number|null",
  oss_percentile_in_band: "number|null",
  cost_percentile_in_band: "number|null",
  group: "int|null",
  flagged: "boolean",
};

export const DISTRICT_RECORD: FieldSpec = {
  division: "string",
  district: "string",
  population: "number",
  households: "number",
  branches: "number",
  members: "number",
  borrowers: "number",
  loan_outstanding_bdt: "number",
  members_per_1000: "number",
  borrowers_per_1000: "number",
  loan_outstanding_per_person_bdt: "number",
  avg_loan_size_bdt: "number",
  branches_per_100k: "number",
  financial_account_pct: "number",
  mobile_banking_pct: "number",
};

export const DIVISION_RECORD: FieldSpec = {
  division: "string",
  population: "number",
  members: "number",
  borrowers: "number",
  loan_outstanding_bdt: "number",
  borrowers_per_1000: "number",
  loan_outstanding_per_person_bdt: "number",
};
