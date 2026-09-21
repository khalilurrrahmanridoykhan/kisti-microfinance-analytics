"""Q6: how deep does credit reach: loan sizes, savings, women, borrowers among members?"""

from __future__ import annotations

import pandas as pd

from .data import BAND_LABELS


def sector_totals(active: pd.DataFrame) -> dict[str, float]:
    """Amount-weighted figures over active MFIs (sum of numerators over sum of denominators)."""
    return {
        "n_mfis": len(active),
        "avg_loan_size_bdt": active["loan_outstanding_bdt"].sum() / active["borrowers_total"].sum(),
        "savings_per_client_bdt": active["savings_bdt"].sum() / active["clients_total"].sum(),
        "female_client_share_pct": 100 * active["clients_female"].sum() / active["clients_total"].sum(),
        "female_borrower_share_pct": 100 * active["borrowers_female"].sum() / active["borrowers_total"].sum(),
        "third_gender_clients": float(active["clients_third_gender"].sum()),
        "third_gender_borrowers": float(active["borrowers_third_gender"].sum()),
        "borrowers_to_clients_pct": 100 * active["borrowers_total"].sum() / active["clients_total"].sum(),
        "savings_to_loans_pct": 100 * active["savings_bdt"].sum() / active["loan_outstanding_bdt"].sum(),
    }


def typical_mfi(active: pd.DataFrame) -> dict[str, float]:
    """Medians across MFIs, each MFI counting once."""
    return {
        "median_avg_loan_size_bdt": active["avg_loan_size_bdt"].median(),
        "p25_avg_loan_size_bdt": active["avg_loan_size_bdt"].quantile(0.25),
        "p75_avg_loan_size_bdt": active["avg_loan_size_bdt"].quantile(0.75),
        "median_savings_per_client_bdt": active["savings_per_client_bdt"].median(),
        "median_female_client_share_pct": active["female_client_share_pct"].median(),
        "mfis_female_share_90_plus": int((active["female_client_share_pct"] >= 90).sum()),
        "mfis_female_share_below_50": int((active["female_client_share_pct"] < 50).sum()),
        "median_borrowers_to_clients_pct": active["borrowers_to_clients_pct"].median(),
    }


def by_band(active: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for band in BAND_LABELS:
        group = active[active["size_band"] == band]
        rows.append(
            {
                "size_band": band,
                "n_mfis": len(group),
                "avg_loan_size_median_bdt": group["avg_loan_size_bdt"].median(),
                "avg_loan_size_p25_bdt": group["avg_loan_size_bdt"].quantile(0.25),
                "avg_loan_size_p75_bdt": group["avg_loan_size_bdt"].quantile(0.75),
                "savings_per_client_median_bdt": group["savings_per_client_bdt"].median(),
                "female_client_share_median_pct": group["female_client_share_pct"].median(),
                "borrowers_to_clients_median_pct": group["borrowers_to_clients_pct"].median(),
            }
        )
    return pd.DataFrame(rows)
