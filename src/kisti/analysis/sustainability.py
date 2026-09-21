"""Q2: who covers their costs, and what separates those who do not?"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .data import BAND_LABELS
from .stats import spearman

SEPARATORS = [
    ("loan_outstanding_bdt", "Loan outstanding (BDT)"),
    ("portfolio_yield", "Portfolio yield (%)"),
    ("total_operating_cost_ratio", "Operating cost per 100 taka of loans"),
    ("borrowing_to_loan_outstanding", "Borrowing to loan outstanding (%)"),
    ("capital_fund_to_loan_outstanding", "Capital fund to loan outstanding (%)"),
    ("savings_share_of_funds_pct", "Clients' savings share of funds (%)"),
]


def with_ratios(active: pd.DataFrame) -> pd.DataFrame:
    return active[active["has_ratios"]].copy()


def by_band(active: pd.DataFrame) -> pd.DataFrame:
    """OSS and ROA by size band, and the share of MFIs that do not cover their costs (OSS < 100)."""
    frame = with_ratios(active)
    rows = []
    for band in BAND_LABELS:
        group = frame[frame["size_band"] == band]
        if group.empty:
            continue
        rows.append(
            {
                "size_band": band,
                "n_mfis": len(group),
                "oss_p25": group["operating_self_sufficiency"].quantile(0.25),
                "oss_median": group["operating_self_sufficiency"].median(),
                "oss_p75": group["operating_self_sufficiency"].quantile(0.75),
                "roa_median": group["return_on_assets"].median(),
                "below_100_count": int((group["operating_self_sufficiency"] < 100).sum()),
                "below_100_share_pct": 100 * (group["operating_self_sufficiency"] < 100).mean(),
                "negative_roa_share_pct": 100 * (group["return_on_assets"] < 0).mean(),
            }
        )
    return pd.DataFrame(rows)


def overall(active: pd.DataFrame) -> dict[str, float]:
    frame = with_ratios(active)
    below = frame["operating_self_sufficiency"] < 100
    return {
        "n_mfis": len(frame),
        "below_100_count": int(below.sum()),
        "below_100_share_pct": 100 * below.mean(),
        "share_of_loans_in_below_100_pct": 100
        * frame.loc[below, "loan_outstanding_bdt"].sum()
        / frame["loan_outstanding_bdt"].sum(),
        "oss_median": frame["operating_self_sufficiency"].median(),
        "roa_median": frame["return_on_assets"].median(),
        "negative_roa_count": int((frame["return_on_assets"] < 0).sum()),
    }


def what_separates(active: pd.DataFrame) -> pd.DataFrame:
    """Medians of candidate factors for MFIs below and at or above 100% OSS, with rank correlations.

    Descriptive only: a correlation here says which measures move together, not what causes what.
    """
    frame = with_ratios(active)
    below = frame["operating_self_sufficiency"] < 100
    rows = []
    for column, label in SEPARATORS:
        rho, n = spearman(frame[column], frame["operating_self_sufficiency"])
        rows.append(
            {
                "factor": label,
                "median_below_100": frame.loc[below, column].median(),
                "median_100_or_more": frame.loc[~below, column].median(),
                "spearman_with_oss": rho,
                "n_pairs": n,
            }
        )
    return pd.DataFrame(rows)


def log_size(frame: pd.DataFrame) -> pd.Series:
    return np.log10(frame["loan_outstanding_bdt"])
