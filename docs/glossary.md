# Glossary

Every metric used in this project, with its formula. Ratios in the first two sections are
**as defined by MRA** in *Microfinance in Bangladesh (Annual Statistics), June 2025*
(chapters 7 and 8), so per-MFI figures here match the published tables. The third section
lists the standard portfolio measures computed later on the synthetic loan book, where the
choice of definition is stated explicitly.

## MRA operating cost ratios (per 100 BDT of loan outstanding)

| Term | Meaning |
|---|---|
| Saving cost ratio (a) | Cost of client savings, per 100 BDT of loan outstanding (LO) |
| Borrowing cost ratio (b) | Cost of borrowed funds, per 100 BDT LO |
| Total financial cost ratio (c) | a + b |
| General and admin cost ratio (d) | Operating overhead, per 100 BDT LO |
| Total operating cost ratio (e) | c + d |

## MRA risk-measuring ratios

These are financial-structure and performance ratios. **None of them measures
delinquency.**

| Ratio | Formula |
|---|---|
| Borrowing to loan outstanding | Total borrowing / loan outstanding × 100 |
| Total operating cost to total income | Total operating cost / total income × 100 |
| Capital fund to loan outstanding | Capital fund / loan outstanding × 100 |
| Portfolio yield (PY) | Total service charge income / average loan outstanding × 100 |
| Return on assets (ROA) | Net surplus / average total assets × 100 |
| Operating self-sufficiency (OSS) | Financial income / (financial expenses + loan loss provision + operating expenses) × 100 |
| Operating margin | Net surplus / service charge × 100 |

OSS below 100 means the institution does not cover its costs from its own income.

## MRA loan classification

Loans are classified by days overdue. Sector-level shares are published for June 2025
(Table 2.1); per-MFI shares are not.

| Class | Days overdue |
|---|---|
| Good | Regular (not overdue) |
| Watchful | Due 1 to 30 days |
| Sub-standard | Due 31 to 180 days |
| Doubtful | Due 181 to 365 days |
| Bad | Due above 365 days |

These are the specifications printed in Table 2.1 of the June 2025 report. Non-performing
loans (NPL) are sub-standard, doubtful and bad together; the report excludes "watchful"
from its NPL figure. Table 2.1 gives no provisioning rates, so the rate for each class
must be taken from the MRA rule itself and cited before it is used in phase MF5.

## Standard portfolio measures (phase MF5, computed on synthetic data)

| Measure | Definition used here |
|---|---|
| PAR30 / PAR90 | Outstanding principal of loans with any installment more than 30 / 90 days late, divided by total outstanding principal |
| Write-off ratio | Principal written off in the period / average gross loan portfolio |
| Collection efficiency | Amount collected in the period / amount due in the period (advance payments reported separately) |
| Roll rate | Share of loans in one delinquency class that move to another class in the next month |
| Vintage curve | Cumulative delinquency or default share, by disbursement month, against loan age |
| Client retention / dropout | Share of clients with an active loan or savings account at the start of a period who still have one at the end |
| Average loan size | Loan outstanding / number of borrowers |
| Effective interest rate (EIR) | Annualised internal rate of return of the client's cash flows, including fees, insurance and compulsory savings held back |
| Herfindahl-Hirschman index (HHI) | Sum of squared market shares, on a 0 to 10,000 scale |
| Gini coefficient | Inequality of a measure (for example loan outstanding) across institutions |

## Terms used in the sector analysis (phase MF2)

| Term | Definition used here |
|---|---|
| Active MFI | Loan outstanding and borrowers both above zero in the Basic table |
| Size band | Loan outstanding: below 10 million, 10-100 million, 100 million-1 billion, 1-10 billion, 10 billion and above taka |
| OSS below 100 | The MFI's income does not cover its financial cost, loan-loss provision and operating cost |
| Operating cost per 100 taka | MRA's total operating cost ratio: cost per 100 taka of loan outstanding |
| Loans per employee | Loan outstanding divided by total employees |
| Cost per borrower | Operating cost ratio / 100 x average loan size |
| Average loan size | Loan outstanding divided by borrowers |
| Women's share of clients | Female clients divided by total clients |
| Borrowers per 1,000 people | MFI borrowers in a district divided by its Census 2022 population, times 1,000 |
| Spearman correlation | Rank correlation between two measures across MFIs; describes association, not cause |
| Silhouette | How well separated k-means groups are, from -1 to 1; below about 0.25 means weak structure |

## Scopes in the MRA report

| Scope | Includes |
|---|---|
| MFIs | The 693 MRA-licensed microfinance institutions |
| Grameen Bank | Reported separately |
| Government departments and institutions | Reported separately |
| Banks | Scheduled banks with microfinance windows |
| All sector | All four groups together |

Always state the scope next to a number. The report quotes all-sector totals in some places
and MFI-only totals in others, and they differ by hundreds of billions of taka.
