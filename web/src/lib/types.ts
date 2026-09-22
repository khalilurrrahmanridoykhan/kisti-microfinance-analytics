/** Shapes of the JSON files in public/data/, written by `python -m kisti.webdata`. */

export interface Meta {
  edition: string;
  generated_at: string;
  mfis_in_basic: number;
  mfis_active: number;
  loan_outstanding_active_bdt: number;
}

export interface Kpis {
  n_mfis: number;
  loan_outstanding_bdt: number;
  borrowers_total: number;
  clients_total: number;
  savings_bdt: number;
  branches_total: number;
}

export interface CoverageInfo {
  mfis_in_basic: number;
  mfis_active: number;
  mfis_without_data: number;
  active_with_ratios: number;
  active_with_cost_ratios: number;
  active_with_funds: number;
  loans_share_with_ratios_pct: number;
  loans_share_with_cost_ratios_pct: number;
  loans_share_with_funds_pct: number;
}

export interface ConcentrationRow {
  measure: string;
  n_mfis: number;
  top1_share_pct: number;
  top4_share_pct: number;
  top10_share_pct: number;
  hhi: number;
  gini: number;
}

export interface LorenzPoint {
  institutions: number;
  share: number;
}

export interface LargestMfi {
  name: string;
  loan_outstanding_bdt: number;
  loan_share_pct: number;
  borrowers_total: number;
  branches: number;
}

export interface OssBandRow {
  size_band: string;
  n_mfis: number;
  oss_p25: number;
  oss_median: number;
  oss_p75: number;
  roa_median: number;
  below_100_count: number;
  below_100_share_pct: number;
  negative_roa_share_pct: number;
}

export interface OssOverall {
  n_mfis: number;
  below_100_count: number;
  below_100_share_pct: number;
  share_of_loans_in_below_100_pct: number;
  oss_median: number;
  roa_median: number;
  negative_roa_count: number;
}

export interface SeparatesRow {
  factor: string;
  median_below_100: number;
  median_100_or_more: number;
  spearman_with_oss: number;
  n_pairs: number;
}

export interface EfficiencyBandRow {
  size_band: string;
  n_mfis: number;
  op_cost_ratio_median: number;
  op_cost_ratio_n: number;
  admin_cost_ratio_median: number;
  admin_cost_ratio_n: number;
  financial_cost_ratio_median: number;
  financial_cost_ratio_n: number;
  borrowers_per_employee_median: number;
  borrowers_per_employee_n: number;
  borrowers_per_branch_median: number;
  borrowers_per_branch_n: number;
  loan_per_employee_bdt_median: number;
  loan_per_employee_bdt_n: number;
  cost_per_borrower_bdt_median: number;
  cost_per_borrower_bdt_n: number;
}

export interface EfficiencyCorrRow {
  measure: string;
  spearman_with_size: number;
  n_pairs: number;
}

export interface YieldDistribution {
  n_mfis: number;
  p10: number;
  p25: number;
  median: number;
  p75: number;
  p90: number;
  max: number;
  above_reference_count: number;
  above_reference_share_pct: number;
  above_reference_loans_share_pct: number;
  weighted_average: number;
}

export interface YieldBandRow {
  size_band: string;
  n_mfis: number;
  yield_median: number;
  above_reference_share_pct: number;
}

export interface YieldVsOss {
  spearman_yield_oss: number;
  spearman_yield_cost_ratio: number;
  n_pairs: number;
}

export interface FundingChangeRow {
  source: string;
  share_2024_06_pct: number;
  share_2025_06_pct: number;
  change_pp: number;
  amount_2025_06_bdt: number;
  amount_change_pct: number;
}

export interface FundingBandRow {
  size_band: string;
  n_mfis: number;
  clients_savings_share_pct: number;
  bank_loans_share_pct: number;
  pksf_loans_share_pct: number;
  other_borrowing_share_pct: number;
  donor_funds_share_pct: number;
  surplus_and_other_share_pct: number;
}

export interface FundingTypical {
  n_mfis: number;
  median_savings_share_pct: number;
  mfis_with_bank_loans: number;
  mfis_bank_dependent: number;
  bank_dependent_share_pct: number;
  bank_dependent_loans_share_pct: number;
}

export interface OutreachSector {
  n_mfis: number;
  avg_loan_size_bdt: number;
  savings_per_client_bdt: number;
  female_client_share_pct: number;
  female_borrower_share_pct: number;
  third_gender_clients: number;
  third_gender_borrowers: number;
  borrowers_to_clients_pct: number;
  savings_to_loans_pct: number;
}

export interface OutreachTypical {
  median_avg_loan_size_bdt: number;
  p25_avg_loan_size_bdt: number;
  p75_avg_loan_size_bdt: number;
  median_savings_per_client_bdt: number;
  median_female_client_share_pct: number;
  mfis_female_share_90_plus: number;
  mfis_female_share_below_50: number;
  median_borrowers_to_clients_pct: number;
}

export interface OutreachBandRow {
  size_band: string;
  n_mfis: number;
  avg_loan_size_median_bdt: number;
  avg_loan_size_p25_bdt: number;
  avg_loan_size_p75_bdt: number;
  savings_per_client_median_bdt: number;
  female_client_share_median_pct: number;
  borrowers_to_clients_median_pct: number;
}

export interface QualityFlagRow {
  check: string;
  mfis_checked: number;
  mfis_flagged: number;
  loans_share_of_flagged_pct: number;
}

export interface PeerGroupRow {
  group: number;
  n_mfis: number;
  loans_share_pct: number;
  loan_outstanding_median_bdt: number;
  avg_loan_size_median_bdt: number;
  portfolio_yield_median: number;
  op_cost_ratio_median: number;
  borrowing_ratio_median: number;
  capital_ratio_median: number;
  savings_share_median_pct: number;
  oss_median: number;
  below_100_share_pct: number;
}

export interface SilhouetteRow {
  k: number;
  silhouette: number;
}

export interface Screening {
  n_mfis: number;
  flagged: number;
  flagged_share_pct: number;
  flagged_loans_share_pct: number;
  flagged_median_loan_outstanding_bdt: number;
}

export interface GeoSummary {
  n_districts: number;
  national_borrowers_per_1000: number;
  median_borrowers_per_1000: number;
  max_borrowers_per_1000: number;
  min_borrowers_per_1000: number;
  spearman_borrowers_account: number;
  spearman_borrowers_mobile: number;
  n_pairs: number;
}

export interface SectorData {
  kpis: Kpis;
  coverage: CoverageInfo;
  concentration: ConcentrationRow[];
  lorenz: LorenzPoint[];
  largest_mfis: LargestMfi[];
  oss_by_band: OssBandRow[];
  oss_overall: OssOverall;
  what_separates: SeparatesRow[];
  efficiency_by_band: EfficiencyBandRow[];
  efficiency_correlations: EfficiencyCorrRow[];
  yield_distribution: YieldDistribution;
  yield_by_band: YieldBandRow[];
  yield_vs_oss: YieldVsOss;
  reference_ceiling_pct: number;
  funding_change: FundingChangeRow[];
  funding_by_band: FundingBandRow[];
  funding_typical: FundingTypical;
  outreach_sector: OutreachSector;
  outreach_typical: OutreachTypical;
  outreach_by_band: OutreachBandRow[];
  quality_flags: QualityFlagRow[];
  peer_groups: PeerGroupRow[];
  peer_silhouette: SilhouetteRow[];
  screening: Screening;
  geo_summary: GeoSummary;
}

export interface MfiRecord {
  license_no: number;
  name: string;
  size_band: string | null;
  branches: number | null;
  employees_total: number | null;
  clients_total: number | null;
  borrowers_total: number;
  female_client_share_pct: number | null;
  savings_bdt: number | null;
  loan_outstanding_bdt: number;
  avg_loan_size_bdt: number;
  has_ratios: boolean;
  portfolio_yield: number | null;
  operating_self_sufficiency: number | null;
  return_on_assets: number | null;
  total_operating_cost_ratio: number | null;
  borrowing_to_loan_outstanding: number | null;
  capital_fund_to_loan_outstanding: number | null;
  has_funds: boolean;
  savings_share_of_funds_pct: number | null;
  yield_percentile_in_band: number | null;
  oss_percentile_in_band: number | null;
  cost_percentile_in_band: number | null;
  group: number | null;
  flagged: boolean;
}

export interface DistrictRecord {
  division: string;
  district: string;
  population: number;
  households: number;
  branches: number;
  members: number;
  borrowers: number;
  loan_outstanding_bdt: number;
  members_per_1000: number;
  borrowers_per_1000: number;
  loan_outstanding_per_person_bdt: number;
  avg_loan_size_bdt: number;
  branches_per_100k: number;
  financial_account_pct: number;
  mobile_banking_pct: number;
}

export interface DivisionRecord {
  division: string;
  population: number;
  members: number;
  borrowers: number;
  loan_outstanding_bdt: number;
  borrowers_per_1000: number;
  loan_outstanding_per_person_bdt: number;
}

export interface SizeBandDef {
  label: string;
  min_bdt: number | null;
  max_bdt: number | null;
}

export interface MethodsData {
  reference_ceiling_pct: number;
  reference_ceiling_note: string;
  size_bands: SizeBandDef[];
  screening_rule: { borrowing_threshold_pct: number; note: string };
  coverage: CoverageInfo;
}
