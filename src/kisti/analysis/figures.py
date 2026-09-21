"""The figures for RESULTS.md. Each takes tables from the analysis modules and writes one PNG."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import concentration, funding, peers, pricing
from .data import BAND_LABELS
from .style import BLUE, GRID, INK, INK_2, ORANGE, SERIES, SURFACE, caption, plt, rounded_bars, save

BAND_LABELS_TALL = list(reversed(BAND_LABELS))


def _band_axis(ax, labels=BAND_LABELS_TALL):
    ax.set_yticks(range(len(labels)), labels)
    ax.grid(axis="y", visible=False)


def lorenz(active: pd.DataFrame, out: Path) -> None:
    curve = concentration.loan_lorenz(active)
    table = concentration.concentration_table(active).iloc[0]
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.plot([0, 1], [0, 1], color=INK_2, linewidth=1, linestyle="-", alpha=0.5)
    ax.plot(curve["institutions"], curve["share"], color=BLUE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Cumulative share of MFIs, smallest first")
    ax.set_ylabel("Cumulative share of loan outstanding")
    ax.set_title("A few MFIs hold most of the loan book")
    ax.text(0.5, 0.42, "Equal shares", color=INK_2, fontsize=8, rotation=38, ha="center")
    ax.annotate(
        f"Smallest 90% of MFIs hold {100 * float(np.interp(0.9, curve['institutions'], curve['share'])):.0f}%\n"
        f"Largest 4 hold {table['top4_share_pct']:.0f}%  (Gini {table['gini']:.2f})",
        xy=(0.93, float(np.interp(0.93, curve["institutions"], curve["share"]))),
        xytext=(0.05, 0.8),
        fontsize=9,
        color=INK,
    )
    caption(fig, f"June 2025, {len(active)} MFIs with loans outstanding. Source: MRA annual statistics.")
    save(fig, out)


def oss_by_band(table: pd.DataFrame, out: Path) -> None:
    rows = table.set_index("size_band").reindex(BAND_LABELS_TALL)
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    y = range(len(rows))
    rounded_bars(ax, y, rows["below_100_share_pct"])
    for i, (share, count, n) in enumerate(
        zip(rows["below_100_share_pct"], rows["below_100_count"], rows["n_mfis"])
    ):
        ax.text(share + 1.2, i, f"{share:.0f}%  ({count} of {n})", va="center", fontsize=8.5, color=INK)
    _band_axis(ax)
    ax.set_xlim(0, 65)
    ax.set_xlabel("Share of MFIs with operating self-sufficiency below 100%")
    ax.set_title("Smaller MFIs are more likely not to cover their costs")
    ax.set_ylabel("Loan outstanding")
    caption(
        fig, "June 2025, MFIs in the risk-ratio table with loans outstanding. Source: MRA annual statistics."
    )
    save(fig, out)


def _range(ax, frame, column, scale=1.0):
    for i, band in enumerate(BAND_LABELS_TALL):
        values = frame.loc[frame["size_band"] == band, column].dropna() / scale
        if values.empty:
            continue
        lo, med, hi = values.quantile([0.25, 0.5, 0.75])
        ax.plot([lo, hi], [i, i], color=BLUE, linewidth=2, solid_capstyle="round")
        ax.plot(med, i, "o", color=BLUE, markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
        ax.text(med, i + 0.28, f"{med:.1f}", ha="center", fontsize=8, color=INK)


def cost_scale(active: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.3), sharey=True)
    panels = [
        ("total_operating_cost_ratio", "Operating cost per 100 taka of loans", 1.0),
        ("total_financial_cost_ratio", "Financial cost per 100 taka of loans", 1.0),
        ("loan_outstanding_per_employee_bdt", "Loans per employee, million taka", 1e6),
    ]
    for ax, (column, title, scale) in zip(axes, panels):
        _range(ax, active, column, scale)
        ax.set_title(title, fontsize=9.5)
        ax.set_ylim(-0.6, len(BAND_LABELS) - 0.3)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(BAND_LABELS_TALL)), BAND_LABELS_TALL)
    axes[0].set_ylabel("Loan outstanding")
    fig.suptitle(
        "Larger MFIs lend more per employee, but do not run more cheaply per taka lent",
        x=0.01,
        y=1.06,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    caption(
        fig,
        "Dot is the median, line the middle half of MFIs in each size band. June 2025. Source: MRA annual statistics.",
    )
    save(fig, out)


def yield_hist(active: pd.DataFrame, out: Path) -> None:
    values = active.loc[active["has_ratios"], "portfolio_yield"]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    shown = values.clip(upper=40)
    ax.hist(shown, bins=np.arange(0, 41, 1), color=BLUE, edgecolor=SURFACE, linewidth=1.2)
    ax.axvline(pricing.REFERENCE_CEILING_PCT, color=INK, linewidth=1.4)
    ax.text(
        pricing.REFERENCE_CEILING_PCT + 0.4,
        ax.get_ylim()[1] * 0.92,
        "24%: ceiling reported by the press\nsince 2019 (unverified)",
        fontsize=8,
        color=INK,
        va="top",
    )
    ax.set_xlabel("Portfolio yield, % of average loan outstanding (values above 40% shown at 40)")
    ax.set_ylabel("Number of MFIs")
    ax.set_title("Most MFIs earn 16-24% on their loans")
    ax.grid(axis="x", visible=False)
    caption(
        fig,
        "Yield is service-charge income over average loans, so it includes fees. It is not the rate charged to a client.",
    )
    save(fig, out)


def yield_vs_oss(active: pd.DataFrame, out: Path) -> None:
    frame = active[active["has_ratios"] & (active["portfolio_yield"] <= 40)]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(
        frame["portfolio_yield"],
        frame["operating_self_sufficiency"],
        s=16,
        color=BLUE,
        alpha=0.55,
        linewidths=0,
    )
    ax.axhline(100, color=INK, linewidth=1.2)
    ax.text(0.5, 101.5, "Costs just covered (OSS 100%)", fontsize=8, color=INK)
    ax.set_ylim(40, 250)
    ax.set_xlim(0, 40)
    ax.set_xlabel("Portfolio yield, %")
    ax.set_ylabel("Operating self-sufficiency, %")
    ax.set_title("Higher yields go with higher self-sufficiency, with wide scatter")
    caption(
        fig,
        "One point per MFI, June 2025. Points outside the axes (7 MFIs with implausible values) are not drawn.",
    )
    save(fig, out)


BAND_TALL_SOURCES = funding.SOURCE_LABELS


def funding_by_band(table: pd.DataFrame, out: Path) -> None:
    rows = table.set_index("size_band").reindex(BAND_LABELS_TALL)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    left = np.zeros(len(rows))
    dark = {SERIES[0], SERIES[5]}
    for slot, (source, label) in enumerate(funding.SOURCE_LABELS.items()):
        widths = rows[f"{source}_share_pct"].to_numpy()
        ax.barh(
            range(len(rows)),
            widths,
            left=left,
            height=0.5,
            color=SERIES[slot],
            edgecolor=SURFACE,
            linewidth=1.5,
            label=label,
        )
        for i, (w, base) in enumerate(zip(widths, left)):
            if w >= 9:
                ax.text(
                    base + w / 2,
                    i,
                    f"{w:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if SERIES[slot] in dark else INK,
                )
        left += widths
    _band_axis(ax)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of the MFIs' funds, %")
    ax.set_ylabel("Loan outstanding")
    ax.set_title("PKSF loans matter most to mid-sized MFIs; the largest fund from savings and surplus")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=8)
    caption(
        fig,
        "Amount-weighted mix within each band, June 2025, MFIs with a fund-composition row. Labels shown where they fit.",
    )
    save(fig, out)


def outreach(active: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.3), sharey=True)
    _range(axes[0], active, "avg_loan_size_bdt", 1000)
    axes[0].set_title("Average loan per borrower, thousand taka", fontsize=9.5)
    _range(axes[1], active, "female_client_share_pct", 1.0)
    axes[1].set_title("Women's share of clients, %", fontsize=9.5)
    for ax in axes:
        ax.set_ylim(-0.6, len(BAND_LABELS) - 0.3)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(BAND_LABELS_TALL)), BAND_LABELS_TALL)
    axes[0].set_ylabel("Loan outstanding")
    fig.suptitle(
        "Larger MFIs lend larger sums; women are the large majority of clients at every size",
        x=0.01,
        y=1.06,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    caption(
        fig,
        "Dot is the median, line the middle half of MFIs in each size band. June 2025. Source: MRA annual statistics.",
    )
    save(fig, out)


def districts(frame: pd.DataFrame, national: float, out: Path) -> None:
    ordered = frame.sort_values("borrowers_per_1000")
    fig, ax = plt.subplots(figsize=(7.4, 11.4))
    y = np.arange(len(ordered))
    rounded_bars(ax, y, ordered["borrowers_per_1000"], height=0.62)
    ax.set_yticks(y, ordered["district"], fontsize=7.5)
    ax.axvline(national, color=INK, linewidth=1.2)
    ax.text(national + 4, 1.0, f"National\n{national:.0f}", fontsize=8, color=INK, va="bottom")
    for idx in (0, 1, 2, len(ordered) - 3, len(ordered) - 2, len(ordered) - 1):
        value = ordered["borrowers_per_1000"].iloc[idx]
        ax.text(value + 4, idx, f"{value:.0f}", va="center", fontsize=7.5, color=INK)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 520)
    ax.set_ylim(-0.8, len(ordered) - 0.2)
    ax.set_xlabel("MFI borrowers per 1,000 people (Census 2022 population)")
    ax.set_title("MFI borrowers per 1,000 people, by district")
    fig.subplots_adjust(left=0.2, right=0.97, top=0.97, bottom=0.06)
    caption(
        fig,
        "June 2025. Counts borrowers of MFIs, not distinct people; Grameen Bank, government schemes and banks are excluded.",
        y=0.015,
    )
    save(fig, out)


def groups(profile: pd.DataFrame, out: Path) -> None:
    columns = [
        ("portfolio_yield_median", "Yield, %"),
        ("op_cost_ratio_median", "Op. cost /100"),
        ("borrowing_ratio_median", "Borrowing/loans, %"),
        ("capital_ratio_median", "Capital/loans, %"),
        ("savings_share_median_pct", "Savings/funds, %"),
        ("oss_median", "OSS, %"),
    ]
    fig, axes = plt.subplots(1, len(columns), figsize=(11.5, 2.8), sharey=True)
    labels = [f"Group {int(g)}  (n={int(n)})" for g, n in zip(profile["group"], profile["n_mfis"])]
    for ax, (column, title) in zip(axes, columns):
        ax.plot(
            profile[column],
            range(len(profile)),
            "o",
            color=BLUE,
            markersize=8,
            markeredgecolor=SURFACE,
            markeredgewidth=2,
        )
        for i, value in enumerate(profile[column]):
            ax.text(value, i + 0.3, f"{value:.0f}", ha="center", fontsize=8, color=INK)
        ax.set_title(title, fontsize=8.5)
        ax.grid(axis="y", visible=False)
        ax.set_ylim(-0.6, len(profile) - 0.2)
    axes[0].set_yticks(range(len(profile)), labels)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Four peer groups, numbered from smallest to largest loan book (medians)",
        x=0.01,
        y=1.08,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    caption(
        fig,
        f"Groups from k-means on seven ratios, {int(profile['n_mfis'].sum())} MFIs. Silhouette is low: the groups are a summary, not natural clusters.",
    )
    save(fig, out)


def all_figures(context: dict, outdir: Path) -> dict[str, str]:
    """Write every figure and return {name: filename}."""
    active = context["active"]
    files = {
        "lorenz": "01_concentration_lorenz.png",
        "oss": "02_oss_by_size.png",
        "cost": "03_cost_by_size.png",
        "yield": "04_portfolio_yield.png",
        "yield_oss": "05_yield_vs_oss.png",
        "funding": "06_funding_mix_by_size.png",
        "outreach": "07_outreach_by_size.png",
        "districts": "08_districts_borrowers_per_1000.png",
        "groups": "09_peer_groups.png",
    }
    lorenz(active, outdir / files["lorenz"])
    oss_by_band(context["oss_band"], outdir / files["oss"])
    cost_scale(active, outdir / files["cost"])
    yield_hist(active, outdir / files["yield"])
    yield_vs_oss(active, outdir / files["yield_oss"])
    funding_by_band(context["funding_band"], outdir / files["funding"])
    outreach(active, outdir / files["outreach"])
    districts(
        context["districts"], context["geo"]["national_borrowers_per_1000"], outdir / files["districts"]
    )
    groups(context["groups"], outdir / files["groups"])
    return files


__all__ = ["all_figures", "GRID", "ORANGE", "peers"]
