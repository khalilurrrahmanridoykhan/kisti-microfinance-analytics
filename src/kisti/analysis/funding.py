"""Q5: how are MFIs funded, and how did the mix change from June 2024 to June 2025?"""

from __future__ import annotations

import pandas as pd

from .data import BAND_LABELS, FUND_ORDER

SOURCE_LABELS = {
    "clients_savings": "Clients' savings",
    "bank_loans": "Commercial-bank loans",
    "pksf_loans": "PKSF loans",
    "other_borrowing": "Other borrowing",
    "donor_funds": "Donors' funds",
    "surplus_and_other": "Surplus and other funds",
}
BANK_DEPENDENT_SHARE_PCT = 25.0


def with_funds(active: pd.DataFrame) -> pd.DataFrame:
    return active[active["has_funds"]].copy()


def mix(frame: pd.DataFrame, year: str) -> pd.Series:
    """Sector mix: each source's share of the summed funds of the given MFIs, in percent."""
    totals = frame[[f"{s}_{year}" for s in FUND_ORDER]].sum()
    totals.index = FUND_ORDER
    return 100 * totals / totals.sum()


def by_band(active: pd.DataFrame, year: str = "2025") -> pd.DataFrame:
    frame = with_funds(active)
    rows = []
    for band in BAND_LABELS:
        group = frame[frame["size_band"] == band]
        if group.empty:
            continue
        row = {"size_band": band, "n_mfis": len(group)}
        row.update({f"{s}_share_pct": v for s, v in mix(group, year).items()})
        rows.append(row)
    return pd.DataFrame(rows)


def change(active: pd.DataFrame) -> pd.DataFrame:
    """Sector mix in June 2024 and June 2025 over the MFIs that report funds in both years."""
    frame = with_funds(active)
    frame = frame[frame["total_funds_2024"].notna() & (frame["total_funds_2024"] > 0)]
    before, after = mix(frame, "2024"), mix(frame, "2025")
    return pd.DataFrame(
        {
            "source": [SOURCE_LABELS[s] for s in FUND_ORDER],
            "share_2024_06_pct": before.to_numpy(),
            "share_2025_06_pct": after.to_numpy(),
            "change_pp": (after - before).to_numpy(),
            "amount_2025_06_bdt": frame[[f"{s}_2025" for s in FUND_ORDER]].sum().to_numpy(),
            "amount_change_pct": (
                100
                * (
                    frame[[f"{s}_2025" for s in FUND_ORDER]].sum().to_numpy()
                    / frame[[f"{s}_2024" for s in FUND_ORDER]].sum().to_numpy()
                    - 1
                )
            ),
        }
    )


def typical_mfi(active: pd.DataFrame) -> dict[str, float]:
    """Medians across MFIs (each MFI counts once), as opposed to the amount-weighted sector mix."""
    frame = with_funds(active)
    bank = frame["bank_loan_share_of_funds_pct"]
    return {
        "n_mfis": len(frame),
        "median_savings_share_pct": frame["savings_share_of_funds_pct"].median(),
        "mfis_with_bank_loans": int((frame["bank_loans_2025"] > 0).sum()),
        "mfis_bank_dependent": int((bank >= BANK_DEPENDENT_SHARE_PCT).sum()),
        "bank_dependent_share_pct": 100 * (bank >= BANK_DEPENDENT_SHARE_PCT).mean(),
        "bank_dependent_loans_share_pct": 100
        * frame.loc[bank >= BANK_DEPENDENT_SHARE_PCT, "loan_outstanding_bdt"].sum()
        / frame["loan_outstanding_bdt"].sum(),
    }


def bank_dependence_shift(active: pd.DataFrame) -> dict[str, float]:
    """MFIs whose commercial-bank share of funds changed by at least 10 points between the two years."""
    frame = with_funds(active)
    frame = frame[frame["total_funds_2024"].notna() & (frame["total_funds_2024"] > 0)]
    before = 100 * frame["bank_loans_2024"] / frame["total_funds_2024"]
    delta = frame["bank_loan_share_of_funds_pct"] - before
    return {
        "n_mfis": len(frame),
        "bank_share_up_10pp": int((delta >= 10).sum()),
        "bank_share_down_10pp": int((delta <= -10).sum()),
    }
