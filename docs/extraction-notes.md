# Extraction notes: MRA annual statistics, June 2025

How the tables in `data/real/processed/` were read from the PDF, how they were checked, and
what the report itself gets wrong or leaves out. Regenerate everything with `make extract`
(about a minute); compare against a second method with `make crosscheck`.

`page` columns are **PDF page numbers**. The page printed on the sheet is one lower
(PDF page 84 is printed page 83).

## What was extracted

| File | Rows | Source | Grain |
|---|---:|---|---|
| `mfi_basic.csv` | 693 | Chapter 5, PDF pages 70 to 143 | One row per MFI |
| `mfi_positions.csv` | 626 | Chapter 6, pages 146 to 169 | One row per MFI |
| `mfi_cost_ratios.csv` | 600 | Chapter 7, pages 172 to 195 | One row per MFI |
| `mfi_risk_ratios.csv` | 540 | Chapter 8, pages 198 to 225 | One row per MFI |
| `mfi_fund_composition.csv` | 3,291 | Chapter 9, pages 228 to 307 | One row per MFI and fund type (569 MFIs) |
| `district_coverage.csv` | 73 | Table 3.2 | 64 districts, 8 division totals, 1 grand total |
| `division_summary.csv` | 9 | Table 3.1 | 8 divisions and the grand total |
| `sector_timeseries.csv` | 70 | Table 1.3 | 7 metrics for each of 10 fiscal years, MFIs only |
| `sector_llp.csv` | 6 | Table 2.1 | Consolidated loan classification, MFIs only |
| `district_population.csv` | 64 | Census 2022 district tables (HDX copy of BBS data) | 64 districts; `make extract` reads it from the Excel file |
| `extraction_issues.csv` | 2 | The extractors | Rows flagged while reading |

**Not extracted:** Chapter 10 (size-wise savings and disbursement, which can be recomputed
from the Basic table), Chapter 4 (social development expenditure), the sector charts that
compare MFIs, Grameen Bank, government bodies and banks, and the June 2024 edition (phase
MF3, which will confirm its layout first).

## Method

Plain text extraction cannot say which printed line belongs to which MFI, because names wrap
over up to five lines with the licence number beneath. The extractors therefore read
word coordinates with pdfplumber:

- Each row is anchored on its serial number. Numeric cells are the words on the serial
  number's line, read left to right into a fixed list of columns.
- The Basic table has ruled cells, so every word is assigned to the ruled row that contains
  it. The other tables have no rules and use the nearest serial number.
- Pages alternate between two horizontal offsets about 11 points apart. Each page is shifted
  by how far its own "(As on ...)" subtitle sits from the reference page.
- Fund composition has several rows per MFI, closed by a "Total" row, and a block can start
  on one page and finish on the next, so pages are read as one stream.
- The MFI key across tables is the last group of the licence number (`license_no`). The Basic
  table prints it in its own column, which is why it is used as the key.
- Names come from the ratio and fund tables where the MFI appears there, because the Basic
  table's name column is narrow and neighbours a contact-details column. The 42 MFIs that
  appear only in the Basic table use the name read from that column, limited to the column's
  ruled edges.

## How it was checked

1. **Every cell against a second method.** `scripts/crosscheck_pdftotext.py` re-reads the
   PDF as layout text with poppler's `pdftotext` and compares each numeric cell. Result on the
   committed tables: Basic 693 of 693 rows agree, cost ratios 600 of 600, risk ratios 540 of
   540, positions 626 of 626, with no row unread. The two methods share no code.
2. **Reconciliation tests** (`tests/test_processed_data.py`, run in CI): serial numbers are
   contiguous, licence numbers are unique, every table's MFIs exist in the Basic table, the
   same MFI has the same name everywhere, employees add up, division and district tables add
   up to their printed totals, loan classification shares add to 100, and the trend table ends
   on the printed 2024-25 figures.
3. **Page image.** The BRAC row in the Basic table was compared by eye with the rendered
   page. A 25-MFI spot-check fixture (`tests/fixtures/mfi_spot_check.csv`: the four largest by
   loan outstanding plus every 33rd serial) holds values taken from the second method, and the
   tests compare the CSVs against it.

## What the report itself gets wrong or leaves out

These are properties of the published figures, not extraction errors: the cells were
confirmed against the second method. They are kept as printed and listed in the tests, which
fail if a new one appears or a listed one disappears.

**Not every MFI is in every table.** The Basic table has 693 MFIs; the positions table has
626, cost ratios 600, risk ratios 540 and fund composition 569. The report does not say why.
Forty MFIs have a Basic row with every figure empty (`-`), and 48 have no loan outstanding.

**The per-MFI rows do not add up to the printed sector totals.** The shortfalls (per-MFI sum
minus the total printed in Table 3.1) are:

| Measure | Sum of MFI rows | Printed total | Difference |
|---|---:|---:|---:|
| Branches | 26,881 | 27,113 | -232 (-0.86%) |
| Employees | 228,577 | 234,380 | -5,803 (-2.48%) |
| Clients | 43,975,015 | 43,979,221 | -4,206 (-0.01%) |
| Borrowers | 33,676,820 | 33,682,069 | -5,249 (-0.02%) |
| Savings (BDT) | 799,309,408,696 | 799,324,421,991 | -15,013,295 (-0.002%) |
| Loan outstanding (BDT) | 1,748,726,085,968 | 1,748,802,083,320 | -75,997,352 (-0.004%) |

Money and client totals agree closely; branches and employees are further apart. Sector
totals in later analysis should be quoted from the report's totals, and shares computed from
the per-MFI rows should say that the base is the sum of MFI rows.

**Printed totals that differ from their printed parts.**

- Clients total differs from male + female + third gender on serials 61, 166 and 396.
- Borrowers total differs from its parts on serials 30, 63, 96, 263, 335, 520, 573, 592 and 631.
- Total operating cost ratio differs from financial cost + admin cost by more than rounding on
  serials 580, 594 and 599 of the cost table.
- Fund composition: components do not add to the total for serial 155 (both years), serial 380
  (June 2024) and serial 542 (June 2025); the shares for serial 155 add to about 121%.
- Several district amounts in taka differ from their division total by 1 to 3 taka (rounding).

**Duplicated identifiers.**

- Basic serial 600 (Society for Disadvantage Origins, licence no. 509) is printed with the
  full licence number of serial 361 (NEDA Society, licence no. 508). The short licence number,
  printed in its own column, tells them apart, and `license_printed` keeps the duplicate.
- Fund composition prints the block for Poribar Kallyan Sahayak Samittee (licence no. 578)
  twice, as serials 333 and 368. Both are kept; deduplicate on `license_no` in analysis.

**Outliers to check before using them.** One MFI has a portfolio yield of 129.88%. The value
matches the second method, so it is what the report prints.

**Units and conventions** are in [data-dictionary.md](data-dictionary.md).

## Census district populations (added in MF2)

`district_population.csv` comes from the Census 2022 district tables that UN in Bangladesh
published on the Humanitarian Data Exchange (a copy of BBS tables, listed as CC0). The 64
districts sum to 165,158,616 people, the national census total. MRA's spellings differ from
the census for three districts (Barisal, Bogra, Maulvibazar); the mapping is in
`kisti.extract.census` and a test checks that all 64 MRA districts match exactly one census
district. The workbook's tab names carry stray spaces, so sheets are found by their stripped names.
