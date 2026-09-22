# Data dictionary

Conventions that apply to every table in this project, and the fields of the source
manifest. Per-table column definitions are added in the phase that creates each table: real tables in
phase MF1, synthetic tables in phase MF4.

## Conventions

| Topic | Convention |
|---|---|
| Currency | Bangladeshi taka (BDT). Each column states whether the unit is taka, thousand, million, crore or billion; never mixed within a column |
| Ratios | Percent on a 0 to 100 scale, exactly as MRA prints them (for example OSS 134.80 means 134.8%), unless a column name ends in `_share` (0 to 1) |
| Missing values | MRA prints `-` for a missing or not-applicable value. Stored as an empty cell (null), never as 0 |
| Institution key | The MRA licence number (for example `00488-00186-00065`), stored as text so leading zeros are kept |
| As-of date | Each real table carries its report edition (`2025-06` or `2024-06`) and the page it was read from |
| Scope | Each aggregate carries its scope: `MFI`, `Grameen Bank`, `Government`, `Banks` or `All sector`. Scopes are never summed together |
| Synthetic rows | Every synthetic table has `is_synthetic = true` and lives under `data/synthetic/` |

## `data/source-manifest.json`

| Field | Type | Meaning |
|---|---|---|
| `path` | text | Where the file is stored, relative to the repository root |
| `url` | text | Where it was downloaded from |
| `sha256` | text | Checksum the download must match; a mismatch is rejected |
| `bytes` | integer | File size in bytes |
| `pages` | integer | Page count of the PDF |
| `description` | text | What the document contains and what it is used for |
| `publisher` | text | Who published it |
| `terms` | text | Copyright or licence statement and how the file is handled |
| `retrieved` | date | Day it was downloaded (`YYYY-MM-DD`) |

## Real tables (`data/real/processed/`)

Source, page ranges and known problems are in [extraction-notes.md](extraction-notes.md).
Every per-MFI table has the leading columns below, then its own measures.

| Column | Type | Meaning |
|---|---|---|
| `edition` | text | Report edition, `2025-06` |
| `serial` | integer | Row number as printed in that table |
| `license_no` | integer | Last group of the licence number, the key that joins tables |
| `license_printed` | text | Full licence number as printed (serial 600 of the Basic table repeats another MFI's) |
| `name` | text | MFI name, taken from the ratio and fund tables where the MFI appears there |
| `page` | integer | PDF page the row was read from (printed page is one lower) |

**`mfi_basic.csv`** (693 rows). Counts are people; money is in taka.
`branches`; `employees_male`, `employees_female`, `employees_total`; `clients_male`,
`clients_female`, `clients_third_gender`, `clients_total`; `borrowers_male`, `borrowers_female`,
`borrowers_third_gender`, `borrowers_total`; `savings_bdt`, `loan_disbursement_bdt`,
`loan_outstanding_bdt`. Clients are members; borrowers are members with a loan.

**`mfi_positions.csv`** (626 rows). Rank of the MFI among all MFIs, 1 is the largest:
`rank_loan_outstanding`, `rank_loan_disbursement`, `rank_branches`, `rank_borrowers`.

**`mfi_cost_ratios.csv`** (600 rows). Taka per 100 taka of loan outstanding:
`saving_cost_ratio`, `borrowing_cost_ratio`, `total_financial_cost_ratio` (sum of the two),
`general_admin_cost_ratio`, `total_operating_cost_ratio`.

**`mfi_risk_ratios.csv`** (540 rows). Percent, as in the [glossary](glossary.md):
`borrowing_to_loan_outstanding`, `operating_cost_to_income`, `capital_fund_to_loan_outstanding`,
`portfolio_yield`, `return_on_assets`, `operating_self_sufficiency`, `operating_margin`.

**`mfi_fund_composition.csv`** (3,291 rows, 569 MFIs). One row per MFI and fund type.
`fund_type` is Clients' Savings, Loan from Commercial Banks, Loan from PKSF, Loan from Other
MFIs, Loan from Govt., Other loans, Donors' Fund, Cumulative Surplus, Other Fund or Total.
`amount_2025_06_bdt` and `amount_2024_06_bdt` are taka; `share_2025_06_pct` and
`share_2024_06_pct` are the share of that MFI's total funds, in percent.

**`district_coverage.csv`** (73 rows) and **`division_summary.csv`** (9 rows). `row_type` is
`district`, `division_total` or `all_districts` (districts only). Measures, all MFIs, June 2025:
`branches`, `members`, `borrowers`, `loan_outstanding_bdt`, `savings_bdt`, each followed by its
`_share_pct` of the national total. Some district names follow the report's spelling
(for example Bogra, Barisal, Chapai Nababganj).

**`sector_timeseries.csv`** (70 rows). Long format: `scope` (MFIs), `fiscal_year`
(`2015-16` to `2024-25`), `metric`, `unit`, `value`. Metrics: branches and employees (count),
members and borrowers (million), loan disbursement, loan outstanding and savings (billion BDT).

**`sector_llp.csv`** (6 rows). Consolidated loan classification, MFIs, June 2025: `category`
(good, watchful, sub_standard, doubtful, bad, total), `specification` as printed,
`amount_billion_bdt`, `share_pct`, `is_non_performing`.

**`district_population.csv`** (64 rows). Census 2022, from BBS via the Humanitarian Data Exchange:
`district`, `division`, BBS geocodes (`division_geocode`, `district_geocode`), `households`,
`population` (everyone, all ages), `financial_account_pct` and `mobile_banking_pct` (percent of
people with a financial-institution or mobile-banking account, as labeled by BBS). MRA spells
three districts differently (Barisal, Bogra, Maulvibazar); `kisti.extract.census` maps them.

**`extraction_issues.csv`.** Rows flagged while reading: `table`, `serial`, `page`, `issue`.

## Synthetic tables (defined in MF4)

`branches`, `officers`, `centers`, `clients`, `loans`, `schedule`, `payments`,
`savings_txn` and `products`, with every generator parameter and its source in
`docs/assumptions.md`.

## Analysis outputs (`results/`)

Written by `make analyse` (phase MF2). Every figure in `RESULTS.md` has its table in
`results/tables/`, named `NN_topic.csv` after the section it belongs to. Conventions:

| Term | Meaning |
|---|---|
| Active MFI | A Basic-table row with loan outstanding and borrowers both above zero (644 of 693) |
| Size band | Loan outstanding: below 10 million, 10-100 million, 100 million-1 billion, 1-10 billion, 10 billion and above (taka) |
| `*_median` | Median across MFIs, each MFI counting once |
| `*_share_pct` (sector) | Sum of the numerators over the sum of the denominators, so large MFIs dominate |
| `*_n` | Number of MFIs behind a median (a ratio is computed only for MFIs that report it) |
| `borrowers_per_1000` | MFI borrowers per 1,000 people in the district (Census 2022 population) |

`results/summary.json` holds the headline numbers that the tests recompute independently.

## Dashboard data (`web/public/data/`)

Written by `make webdata` (`src/kisti/webdata`), reshaping the same MF2 analysis into JSON
for the dashboard in `web/`. `meta.json`, `mfis.json` and `districts.json` are checked
against a field-by-field schema on both the Python side (`src/kisti/webdata/schema.py`,
tested in `tests/test_webdata.py`) and the TypeScript side (`web/src/lib/schema.ts`, tested
in `web/src/lib/schema.test.ts` and re-checked at runtime by `loadAppData`). `sector.json`
carries the same tables as `results/tables/`, reshaped for the dashboard's charts, and
`methods.json` carries the size-band definitions, the screening-rule note and the interest-
rate reference note shown on the dashboard's Methods tab.
