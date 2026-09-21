"""Q7: data-quality flags. Counts only: no institution is named."""

from __future__ import annotations

import pandas as pd

# Plausibility ranges chosen to catch entry errors, not to judge performance.
RULES = [
    ("portfolio_yield", "Portfolio yield outside 3% to 40%", lambda s: (s < 3) | (s > 40)),
    ("operating_self_sufficiency", "OSS outside 40% to 250%", lambda s: (s < 40) | (s > 250)),
    ("return_on_assets", "ROA outside -25% to 25%", lambda s: (s < -25) | (s > 25)),
    ("total_operating_cost_ratio", "Operating cost above 50 per 100 taka of loans", lambda s: s > 50),
    ("borrowers_per_employee", "More than 1,000 borrowers per employee", lambda s: s > 1000),
    (
        "avg_loan_size_bdt",
        "Average loan below 5,000 or above 250,000 taka",
        lambda s: (s < 5000) | (s > 250_000),
    ),
]


def flags(active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column, label, test in RULES:
        values = active[column].dropna()
        hit = test(values)
        rows.append(
            {
                "check": label,
                "mfis_checked": len(values),
                "mfis_flagged": int(hit.sum()),
                "loans_share_of_flagged_pct": 100
                * active.loc[hit[hit].index, "loan_outstanding_bdt"].sum()
                / active["loan_outstanding_bdt"].sum(),
            }
        )
    return pd.DataFrame(rows)


def coverage(frame: pd.DataFrame) -> dict[str, float]:
    """How much of the sector each table covers, and how many Basic rows carry no data at all."""
    active = frame[frame["is_active"]]
    total = active["loan_outstanding_bdt"].sum()
    return {
        "mfis_in_basic": len(frame),
        "mfis_active": len(active),
        "mfis_without_data": int(
            (
                frame[["branches", "clients_total", "borrowers_total", "savings_bdt", "loan_outstanding_bdt"]]
                .isna()
                .all(axis=1)
            ).sum()
        ),
        "active_with_ratios": int(active["has_ratios"].sum()),
        "active_with_cost_ratios": int(active["has_cost_ratios"].sum()),
        "active_with_funds": int(active["has_funds"].sum()),
        "loans_share_with_ratios_pct": 100
        * active.loc[active["has_ratios"], "loan_outstanding_bdt"].sum()
        / total,
        "loans_share_with_cost_ratios_pct": 100
        * active.loc[active["has_cost_ratios"], "loan_outstanding_bdt"].sum()
        / total,
        "loans_share_with_funds_pct": 100
        * active.loc[active["has_funds"], "loan_outstanding_bdt"].sum()
        / total,
    }


def implausible(frame: pd.DataFrame) -> pd.Series:
    """True for MFIs that fail at least one plausibility range above (missing values do not fail)."""
    failed = pd.Series(False, index=frame.index)
    for column, _, test in RULES:
        values = frame[column].dropna()
        failed.loc[values.index] |= test(values)
    return failed
