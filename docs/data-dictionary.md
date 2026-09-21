# Data dictionary

Conventions that apply to every table in this project, and the fields of the source
manifest. Per-table column definitions are added in phase MF1 (real tables) and phase MF4
(synthetic tables), in the same phase that creates the table.

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

## Real tables (defined in MF1)

Institution-level tables come from chapters 5 to 9 of the MRA report, district and division
tables from chapter 3, and sector series from chapters 1 and 2. Their columns are defined
here when each table is extracted.

## Synthetic tables (defined in MF4)

`branches`, `officers`, `centers`, `clients`, `loans`, `schedule`, `payments`,
`savings_txn` and `products`, with every generator parameter and its source in
`docs/assumptions.md`.
