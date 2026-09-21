"""Q3: do larger MFIs run more cheaply, and how productive are staff and branches?"""

from __future__ import annotations

import pandas as pd

from .data import BAND_LABELS
from .stats import spearman

MEASURES = [
    ("total_operating_cost_ratio", "op_cost_ratio"),
    ("general_admin_cost_ratio", "admin_cost_ratio"),
    ("total_financial_cost_ratio", "financial_cost_ratio"),
    ("borrowers_per_employee", "borrowers_per_employee"),
    ("borrowers_per_branch", "borrowers_per_branch"),
    ("loan_outstanding_per_employee_bdt", "loan_per_employee_bdt"),
    ("operating_cost_per_borrower_bdt", "cost_per_borrower_bdt"),
]


def by_band(active: pd.DataFrame) -> pd.DataFrame:
    """Median of each efficiency measure by size band (each measure over the MFIs that report it)."""
    rows = []
    for band in BAND_LABELS:
        group = active[active["size_band"] == band]
        row = {"size_band": band, "n_mfis": len(group)}
        for column, name in MEASURES:
            row[f"{name}_median"] = group[column].median()
            row[f"{name}_n"] = int(group[column].notna().sum())
        rows.append(row)
    return pd.DataFrame(rows)


def scale_correlations(active: pd.DataFrame) -> pd.DataFrame:
    """Rank correlation of each measure with loan outstanding across MFIs."""
    rows = []
    for column, name in MEASURES:
        rho, n = spearman(active["loan_outstanding_bdt"], active[column])
        rows.append({"measure": name, "spearman_with_size": rho, "n_pairs": n})
    return pd.DataFrame(rows)
