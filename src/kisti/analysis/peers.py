"""Q8: peer groups from financial ratios, and a transparent screening rule.

The groups are descriptive summaries of how MFIs differ on published ratios. The screening
rule is a filter on financial-structure ratios, not a measure of delinquency, and its output is
reported as counts only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .quality import implausible

FEATURES = [
    "log_loan_outstanding",
    "log_avg_loan_size",
    "portfolio_yield",
    "total_operating_cost_ratio",
    "borrowing_to_loan_outstanding",
    "capital_fund_to_loan_outstanding",
    "savings_share_of_funds_pct",
]
SEED = 0
WATCH_BORROWING_PCT = 50.0


def complete_cases(active: pd.DataFrame) -> pd.DataFrame:
    """MFIs with every clustering feature and no implausible value (one outlier would form its own group)."""
    frame = active[~implausible(active)].copy()
    frame["log_loan_outstanding"] = np.log10(frame["loan_outstanding_bdt"])
    frame["log_avg_loan_size"] = np.log10(frame["avg_loan_size_bdt"])
    return frame.dropna(subset=FEATURES + ["operating_self_sufficiency"]).copy()


def choose_k(matrix: np.ndarray, candidates=range(2, 7)) -> tuple[int, pd.DataFrame]:
    scores = []
    for k in candidates:
        labels = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit_predict(matrix)
        scores.append({"k": k, "silhouette": float(silhouette_score(matrix, labels))})
    table = pd.DataFrame(scores)
    return int(table.loc[table["silhouette"].idxmax(), "k"]), table


def cluster(active: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (MFIs with a `group` column, group profiles, silhouette by k)."""
    frame = complete_cases(active)
    matrix = StandardScaler().fit_transform(frame[FEATURES])
    k, silhouettes = choose_k(matrix)
    raw = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit_predict(matrix)
    # Number the groups from smallest to largest median loan book so the labels are stable.
    order = frame.assign(raw=raw).groupby("raw")["loan_outstanding_bdt"].median().sort_values().index
    frame["group"] = pd.Series(raw, index=frame.index).map({old: new + 1 for new, old in enumerate(order)})
    total_loans = frame["loan_outstanding_bdt"].sum()
    rows = []
    for group, part in frame.groupby("group"):
        rows.append(
            {
                "group": int(group),
                "n_mfis": len(part),
                "loans_share_pct": 100 * part["loan_outstanding_bdt"].sum() / total_loans,
                "loan_outstanding_median_bdt": part["loan_outstanding_bdt"].median(),
                "avg_loan_size_median_bdt": part["avg_loan_size_bdt"].median(),
                "portfolio_yield_median": part["portfolio_yield"].median(),
                "op_cost_ratio_median": part["total_operating_cost_ratio"].median(),
                "borrowing_ratio_median": part["borrowing_to_loan_outstanding"].median(),
                "capital_ratio_median": part["capital_fund_to_loan_outstanding"].median(),
                "savings_share_median_pct": part["savings_share_of_funds_pct"].median(),
                "oss_median": part["operating_self_sufficiency"].median(),
                "below_100_share_pct": 100 * (part["operating_self_sufficiency"] < 100).mean(),
            }
        )
    return frame, pd.DataFrame(rows), silhouettes


def screening(active: pd.DataFrame) -> dict[str, float]:
    """MFIs that do not cover their costs (OSS < 100) and fund at least half their loans by borrowing."""
    frame = active[active["has_ratios"]]
    hit = (frame["operating_self_sufficiency"] < 100) & (
        frame["borrowing_to_loan_outstanding"] >= WATCH_BORROWING_PCT
    )
    return {
        "n_mfis": len(frame),
        "flagged": int(hit.sum()),
        "flagged_share_pct": 100 * hit.mean(),
        "flagged_loans_share_pct": 100
        * frame.loc[hit, "loan_outstanding_bdt"].sum()
        / frame["loan_outstanding_bdt"].sum(),
        "flagged_median_loan_outstanding_bdt": float(frame.loc[hit, "loan_outstanding_bdt"].median()),
    }
