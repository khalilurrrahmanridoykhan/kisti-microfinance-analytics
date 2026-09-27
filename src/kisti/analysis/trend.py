"""Q10 (phase MF3): the ten-year sector trend and the two-year movement from June 2024 to
June 2025.

Everything here comes from tables already extracted from the single June 2025 report in
phase MF1 — `sector_timeseries.csv` (Table 1.3, ten fiscal years) and the fund-composition
Jun-24/Jun-25 columns (Table 2.1's cousin, chapter 9) already used in `funding.change()`. The
loan-quality two-year comparison is a direct quote of MRA's own printed sentence, not something
computed from a table: see `NPL_TWO_YEAR_QUOTE` for the citation.

**Scoping note, not extracted:** the standalone June 2024 report has per-MFI Basic, Positions,
Cost and Risk tables of its own, which would allow an independent per-MFI year-over-year
comparison beyond funding. Its Basic Information table is printed rotated 90 degrees (unlike
June 2025's), and Positions/Cost/Risk use different column pixel positions, so none of the
extractors calibrated in phase MF1 transfer directly — each would need its own fresh
calibration, the same scale of work phase MF1 did for the June 2025 report. Given that the
June 2025 report's own ten-year series and Jun-24/Jun-25 fund composition already deliver this
phase's sector-level and funding-mix findings, that recalibration was not done for phase MF3;
`data/real/raw/mra_annual_statistics_2024-06.pdf` is fetched and available for a future phase
that wants a full per-MFI two-year comparison.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .data import PROCESSED

# MRA's own printed comparison (chapter 2.2, PDF page 29 of the June 2025 report, printed page
# 28): "In the previous year, non-performing loans accounted for 8.09 percent of total
# outstanding, whereas in FY2024-25, classified loans alone reached 8.52 percent, excluding the
# watchful category." Both figures use the same definition (classified/NPL, excluding watchful).
NPL_TWO_YEAR_QUOTE = (
    "In the previous year, non-performing loans accounted for 8.09 percent of total "
    "outstanding, whereas in FY2024-25, classified loans alone reached 8.52 percent, "
    "excluding the watchful category."
)
NPL_FY2023_24_PCT = 8.09
NPL_FY2024_25_PCT = 8.52
NPL_SOURCE = "MRA, Microfinance in Bangladesh (Annual Statistics) June-2025, chapter 2.2, printed page 28"

TREND_METRICS = [
    "branches",
    "employees",
    "members",
    "borrowers",
    "loan_disbursement",
    "loan_outstanding",
    "savings",
]
FIRST_YEAR = "2015-16"
LAST_YEAR = "2024-25"


def ten_year_series(processed: Path = PROCESSED) -> pd.DataFrame:
    """Table 1.3 as one row per fiscal year, one column per metric."""
    long = pd.read_csv(processed / "sector_timeseries.csv")
    wide = long.pivot(index="fiscal_year", columns="metric", values="value")
    order = sorted(wide.index, key=lambda year: int(year[:4]))
    return wide.loc[order, TREND_METRICS]


def cagr(series: pd.Series, first: str = FIRST_YEAR, last: str = LAST_YEAR) -> float:
    """Compound annual growth rate between two fiscal years in a ten_year_series column."""
    years = sorted(series.index, key=lambda year: int(year[:4]))
    n = years.index(last) - years.index(first)
    return (series[last] / series[first]) ** (1 / n) - 1


def growth_table(processed: Path = PROCESSED) -> pd.DataFrame:
    """CAGR and the first/last values for each trend metric, 2015-16 to 2024-25."""
    series = ten_year_series(processed)
    rows = []
    for metric in TREND_METRICS:
        rows.append(
            {
                "metric": metric,
                "value_2015_16": series.loc[FIRST_YEAR, metric],
                "value_2024_25": series.loc[LAST_YEAR, metric],
                "cagr_pct": 100 * cagr(series[metric]),
            }
        )
    return pd.DataFrame(rows)


def npl_two_year() -> dict:
    return {
        "fy2023_24_pct": NPL_FY2023_24_PCT,
        "fy2024_25_pct": NPL_FY2024_25_PCT,
        "change_pp": round(NPL_FY2024_25_PCT - NPL_FY2023_24_PCT, 2),
        "quote": NPL_TWO_YEAR_QUOTE,
        "source": NPL_SOURCE,
    }
