"""Q4: what do MFIs earn on their loans, relative to the interest-rate ceiling reported by the press?

Portfolio yield is service-charge income divided by average loan outstanding, so it includes
fees and is not the declining-balance rate charged to a client. It is compared with the ceiling
only as a reference line, never as a test of compliance.
"""

from __future__ import annotations

import pandas as pd

from .data import BAND_LABELS
from .stats import spearman

# The ceiling the press has reported since 2019 (24% a year). MRA's own notification was not
# found, and later proposals to lower it are reported, so the current value must be confirmed.
REFERENCE_CEILING_PCT = 24.0


def yields(active: pd.DataFrame) -> pd.DataFrame:
    return active[active["has_ratios"]].copy()


def distribution(active: pd.DataFrame) -> dict[str, float]:
    frame = yields(active)
    yield_ = frame["portfolio_yield"]
    above = yield_ > REFERENCE_CEILING_PCT
    return {
        "n_mfis": len(frame),
        "p10": yield_.quantile(0.10),
        "p25": yield_.quantile(0.25),
        "median": yield_.median(),
        "p75": yield_.quantile(0.75),
        "p90": yield_.quantile(0.90),
        "max": yield_.max(),
        "above_reference_count": int(above.sum()),
        "above_reference_share_pct": 100 * above.mean(),
        "above_reference_loans_share_pct": 100
        * frame.loc[above, "loan_outstanding_bdt"].sum()
        / frame["loan_outstanding_bdt"].sum(),
        "weighted_average": (frame["portfolio_yield"] * frame["loan_outstanding_bdt"]).sum()
        / frame["loan_outstanding_bdt"].sum(),
    }


def by_band(active: pd.DataFrame) -> pd.DataFrame:
    frame = yields(active)
    rows = []
    for band in BAND_LABELS:
        group = frame[frame["size_band"] == band]
        if group.empty:
            continue
        rows.append(
            {
                "size_band": band,
                "n_mfis": len(group),
                "yield_median": group["portfolio_yield"].median(),
                "above_reference_share_pct": 100 * (group["portfolio_yield"] > REFERENCE_CEILING_PCT).mean(),
            }
        )
    return pd.DataFrame(rows)


def yield_vs_oss(active: pd.DataFrame) -> dict[str, float]:
    frame = yields(active)
    rho, n = spearman(frame["portfolio_yield"], frame["operating_self_sufficiency"])
    rho_cost, _ = spearman(frame["portfolio_yield"], frame["total_operating_cost_ratio"])
    return {"spearman_yield_oss": rho, "spearman_yield_cost_ratio": rho_cost, "n_pairs": n}
