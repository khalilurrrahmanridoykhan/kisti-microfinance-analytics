"""Q1: how concentrated is the sector?"""

from __future__ import annotations

import pandas as pd

from .stats import gini, hhi, lorenz, top_share

MEASURES = {
    "loan_outstanding_bdt": "Loan outstanding",
    "borrowers_total": "Borrowers",
    "savings_bdt": "Savings",
    "branches": "Branches",
    "employees_total": "Employees",
}


def concentration_table(active: pd.DataFrame) -> pd.DataFrame:
    """Top-1, top-4 and top-10 shares, HHI and Gini for each measure, over active MFIs."""
    rows = []
    for column, label in MEASURES.items():
        values = active[column].fillna(0)
        rows.append(
            {
                "measure": label,
                "n_mfis": int((values > 0).sum()),
                "top1_share_pct": 100 * top_share(values, 1),
                "top4_share_pct": 100 * top_share(values, 4),
                "top10_share_pct": 100 * top_share(values, 10),
                "hhi": hhi(values),
                "gini": gini(values),
            }
        )
    return pd.DataFrame(rows)


def largest(active: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    """The k largest MFIs by loan outstanding with their share of the sector."""
    total = active["loan_outstanding_bdt"].sum()
    top = active.nlargest(k, "loan_outstanding_bdt")
    return pd.DataFrame(
        {
            "name": top["name"],
            "loan_outstanding_bdt": top["loan_outstanding_bdt"],
            "loan_share_pct": 100 * top["loan_outstanding_bdt"] / total,
            "borrowers_total": top["borrowers_total"],
            "branches": top["branches"],
        }
    ).reset_index(drop=True)


def loan_lorenz(active: pd.DataFrame) -> pd.DataFrame:
    return lorenz(active["loan_outstanding_bdt"])
