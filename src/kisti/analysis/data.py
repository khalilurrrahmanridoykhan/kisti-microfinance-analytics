"""Load the extracted MRA tables into one row per MFI.

The unit of analysis is an "active" MFI: a Basic-table row with both loan outstanding and
borrowers above zero. Every ratio states its own denominator, because the ratio tables cover
fewer MFIs than the Basic table (see docs/extraction-notes.md).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data" / "real" / "processed"

# Size bands by loan outstanding, in taka.
BAND_EDGES = [0, 10e6, 100e6, 1e9, 10e9, np.inf]
BAND_LABELS = ["< 10 million", "10-100 million", "100 million-1 billion", "1-10 billion", "10 billion +"]

# Fund composition types grouped into the five sources used in the funding analysis.
FUND_GROUPS = {
    "Clients' Savings": "clients_savings",
    "Loan from Commercial Banks": "bank_loans",
    "Loan from PKSF": "pksf_loans",
    "Loan from Other MFIs": "other_borrowing",
    "Loan from Govt.": "other_borrowing",
    "Other loans": "other_borrowing",
    "Donors' Fund": "donor_funds",
    "Cumulative Surplus": "surplus_and_other",
    "Other Fund": "surplus_and_other",
}
FUND_ORDER = [
    "clients_savings",
    "bank_loans",
    "pksf_loans",
    "other_borrowing",
    "donor_funds",
    "surplus_and_other",
]


def size_band(loan_outstanding: pd.Series) -> pd.Categorical:
    return pd.cut(loan_outstanding, bins=BAND_EDGES, labels=BAND_LABELS, right=False)


def fund_amounts(fund: pd.DataFrame, period: str) -> pd.DataFrame:
    """Funds per MFI by source in taka for one period (`2025_06` or `2024_06`), one row per licence."""
    fund = fund[fund["fund_type"] != "Total"].drop_duplicates(["license_no", "fund_type"]).copy()
    fund["source"] = fund["fund_type"].map(FUND_GROUPS)
    wide = fund.pivot_table(
        index="license_no", columns="source", values=f"amount_{period}_bdt", aggfunc="sum", fill_value=0.0
    )
    wide = wide.reindex(columns=FUND_ORDER, fill_value=0.0)
    wide["total_funds"] = wide.sum(axis=1)
    return wide


def load(processed: Path = PROCESSED) -> pd.DataFrame:
    """One row per MFI in the Basic table, with the ratio, position and fund tables joined on `license_no`."""
    basic = pd.read_csv(processed / "mfi_basic.csv")
    frame = basic.drop(columns=["edition", "serial", "license_printed", "page"])
    for filename, columns in (
        ("mfi_risk_ratios.csv", None),
        ("mfi_cost_ratios.csv", None),
        ("mfi_positions.csv", None),
    ):
        table = pd.read_csv(processed / filename).drop(
            columns=["edition", "serial", "license_printed", "name", "page"]
        )
        frame = frame.merge(table, on="license_no", how="left")

    fund = pd.read_csv(processed / "mfi_fund_composition.csv")
    now = fund_amounts(fund, "2025_06").add_suffix("_2025")
    before = fund_amounts(fund, "2024_06").add_suffix("_2024")
    frame = frame.merge(now, left_on="license_no", right_index=True, how="left")
    frame = frame.merge(before, left_on="license_no", right_index=True, how="left")

    frame["has_ratios"] = frame["operating_self_sufficiency"].notna()
    frame["has_cost_ratios"] = frame["total_operating_cost_ratio"].notna()
    frame["has_funds"] = frame["total_funds_2025"].notna()
    frame["is_active"] = (frame["loan_outstanding_bdt"] > 0) & (frame["borrowers_total"] > 0)
    frame["size_band"] = size_band(frame["loan_outstanding_bdt"]).astype(str)
    frame.loc[~frame["is_active"], "size_band"] = np.nan

    frame["avg_loan_size_bdt"] = frame["loan_outstanding_bdt"] / frame["borrowers_total"]
    frame["savings_per_client_bdt"] = frame["savings_bdt"] / frame["clients_total"]
    frame["female_client_share_pct"] = 100 * frame["clients_female"] / frame["clients_total"]
    frame["third_gender_clients"] = frame["clients_third_gender"]
    frame["borrowers_to_clients_pct"] = 100 * frame["borrowers_total"] / frame["clients_total"]
    with np.errstate(divide="ignore", invalid="ignore"):
        frame["borrowers_per_employee"] = frame["borrowers_total"] / frame["employees_total"].replace(
            0, np.nan
        )
        frame["borrowers_per_branch"] = frame["borrowers_total"] / frame["branches"].replace(0, np.nan)
    frame["loan_outstanding_per_employee_bdt"] = frame["loan_outstanding_bdt"] / frame[
        "employees_total"
    ].replace(0, np.nan)
    # The cost ratio is taka per 100 taka of loans, so cost per borrower follows from the loan size.
    frame["operating_cost_per_borrower_bdt"] = (
        frame["total_operating_cost_ratio"] / 100 * frame["avg_loan_size_bdt"]
    )
    frame["savings_share_of_funds_pct"] = 100 * frame["clients_savings_2025"] / frame["total_funds_2025"]
    frame["bank_loan_share_of_funds_pct"] = 100 * frame["bank_loans_2025"] / frame["total_funds_2025"]
    return frame
