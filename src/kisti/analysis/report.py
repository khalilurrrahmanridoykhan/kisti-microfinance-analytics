"""Run every analysis and write the tables, figures, summary numbers and RESULTS.md.

    python -m kisti.analysis

Every number in RESULTS.md is computed here from the committed CSVs, so the text cannot drift
from the data. Institutions are named only where the table itself is about the largest ones;
the screening rule and the data-quality checks report counts only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import concentration, data, efficiency, figures, funding, geography, outreach, peers, pricing, quality
from . import sustainability as sust
from .style import setup

ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = ROOT / "results"
RESULTS_MD = ROOT / "RESULTS.md"

DISTINCT_COLUMNS = {
    "portfolio_yield": "yield",
    "total_operating_cost_ratio": "operating cost per 100 taka",
    "borrowing_to_loan_outstanding": "borrowing to loans",
    "capital_fund_to_loan_outstanding": "capital fund to loans",
    "savings_share_of_funds_pct": "savings share of funds",
    "operating_self_sufficiency": "OSS",
    "avg_loan_size_bdt": "average loan (BDT)",
}


def n0(x) -> str:
    return f"{x:,.0f}"


def n1(x) -> str:
    return f"{x:,.1f}"


def p0(x) -> str:
    return f"{x:.0f}%"


def p1(x) -> str:
    return f"{x:.1f}%"


def bn(x) -> str:
    return f"{x / 1e9:,.1f} billion"


def mn(x) -> str:
    return f"{x / 1e6:,.0f} million"


def r2(x) -> str:
    """Two decimals, never a negative zero."""
    return f"{x + 0.0:.2f}".replace("-0.00", "0.00")


def distinctive(
    grouped: pd.DataFrame, features: dict[str, str], top: int = 2
) -> dict[int, list[tuple[str, float, float]]]:
    """For each group, the features whose group median is furthest from the all-MFI median, in units of the
    all-MFI interquartile range. Returns (label, group median, all-MFI median) for the `top` largest."""
    overall = {
        c: (grouped[c].median(), grouped[c].quantile(0.75) - grouped[c].quantile(0.25)) for c in features
    }
    result = {}
    for group, part in grouped.groupby("group"):
        scored = []
        for column, label in features.items():
            centre, spread = overall[column]
            value = part[column].median()
            scored.append((abs(value - centre) / spread if spread else 0.0, label, value, centre))
        scored.sort(reverse=True)
        result[int(group)] = [(label, value, centre) for _, label, value, centre in scored[:top]]
    return result


def md_table(
    frame: pd.DataFrame, formats: dict[str, str] | None = None, rename: dict[str, str] | None = None
) -> str:
    """A GitHub-flavoured markdown table. `formats` maps a column to a format spec such as ',.0f'."""
    formats = formats or {}
    columns = list(frame.columns)
    header = [(rename or {}).get(c, c) for c in columns]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---:" if c in formats else "---" for c in columns) + "|",
    ]
    for _, row in frame.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            spec = formats.get(column)
            cells.append(
                format(value, spec) if spec and pd.notna(value) else ("" if pd.isna(value) else str(value))
            )
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def compute() -> dict:
    frame = data.load()
    active = frame[frame["is_active"]].copy()
    ctx: dict = {"frame": frame, "active": active}
    ctx["coverage"] = quality.coverage(frame)
    ctx["concentration"] = concentration.concentration_table(active)
    ctx["largest"] = concentration.largest(active)
    ctx["oss_band"] = sust.by_band(active)
    ctx["oss_overall"] = sust.overall(active)
    ctx["separates"] = sust.what_separates(active)
    ctx["efficiency_band"] = efficiency.by_band(active)
    ctx["efficiency_corr"] = efficiency.scale_correlations(active)
    ctx["yield"] = pricing.distribution(active)
    ctx["yield_band"] = pricing.by_band(active)
    ctx["yield_oss"] = pricing.yield_vs_oss(active)
    ctx["funding_change"] = funding.change(active)
    ctx["funding_band"] = funding.by_band(active)
    ctx["funding_typical"] = funding.typical_mfi(active)
    ctx["funding_shift"] = funding.bank_dependence_shift(active)
    ctx["outreach_sector"] = outreach.sector_totals(active)
    ctx["outreach_typical"] = outreach.typical_mfi(active)
    ctx["outreach_band"] = outreach.by_band(active)
    ctx["quality_flags"] = quality.flags(active)
    grouped, profile, silhouettes = peers.cluster(active)
    ctx["grouped"], ctx["groups"], ctx["silhouettes"] = grouped, profile, silhouettes
    ctx["screening"] = peers.screening(active)
    districts = geography.districts()
    ctx["districts"] = districts
    ctx["divisions"] = geography.by_division(districts)
    ctx["geo"] = geography.summary(districts)
    return ctx


def write_tables(ctx: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    tables = {
        "01_concentration": ctx["concentration"],
        "01_largest_mfis": ctx["largest"],
        "02_sustainability_by_size": ctx["oss_band"],
        "02_what_separates": ctx["separates"],
        "03_efficiency_by_size": ctx["efficiency_band"],
        "03_efficiency_vs_size": ctx["efficiency_corr"],
        "04_yield_by_size": ctx["yield_band"],
        "05_funding_change": ctx["funding_change"],
        "05_funding_by_size": ctx["funding_band"],
        "06_outreach_by_size": ctx["outreach_band"],
        "07_data_quality_checks": ctx["quality_flags"],
        "08_peer_groups": ctx["groups"],
        "08_peer_group_silhouette": ctx["silhouettes"],
        "09_districts": ctx["districts"],
        "09_divisions": ctx["divisions"],
    }
    for name, table in tables.items():
        table.to_csv(outdir / f"{name}.csv", index=False, lineterminator="\n", float_format="%.4f")


def summary(ctx: dict) -> dict:
    """The headline numbers, written to results/summary.json and checked by tests."""
    conc = ctx["concentration"].set_index("measure")
    return {
        "mfis_in_basic": ctx["coverage"]["mfis_in_basic"],
        "mfis_active": ctx["coverage"]["mfis_active"],
        "loan_outstanding_active_bdt": float(ctx["active"]["loan_outstanding_bdt"].sum()),
        "top4_loan_share_pct": float(conc.loc["Loan outstanding", "top4_share_pct"]),
        "top4_borrower_share_pct": float(conc.loc["Borrowers", "top4_share_pct"]),
        "hhi_loan_outstanding": float(conc.loc["Loan outstanding", "hhi"]),
        "gini_loan_outstanding": float(conc.loc["Loan outstanding", "gini"]),
        "oss_below_100_count": ctx["oss_overall"]["below_100_count"],
        "oss_below_100_of": ctx["oss_overall"]["n_mfis"],
        "oss_below_100_loans_share_pct": float(ctx["oss_overall"]["share_of_loans_in_below_100_pct"]),
        "yield_median": float(ctx["yield"]["median"]),
        "yield_above_reference_count": ctx["yield"]["above_reference_count"],
        "female_client_share_pct": float(ctx["outreach_sector"]["female_client_share_pct"]),
        "avg_loan_size_bdt": float(ctx["outreach_sector"]["avg_loan_size_bdt"]),
        "bank_loan_share_change_pp": float(
            ctx["funding_change"].set_index("source").loc["Commercial-bank loans", "change_pp"]
        ),
        "national_borrowers_per_1000": float(ctx["geo"]["national_borrowers_per_1000"]),
        "n_groups": int(len(ctx["groups"])),
        "screening_flagged": ctx["screening"]["flagged"],
    }


def rho_word(rho: float) -> str:
    size = abs(rho)
    strength = "no" if size < 0.1 else "a weak" if size < 0.3 else "a moderate" if size < 0.6 else "a strong"
    if strength == "no":
        return "no relationship"
    return f"{strength} {'positive' if rho > 0 else 'negative'} relationship"


def render(ctx: dict, files: dict[str, str]) -> str:
    cov, conc, top = ctx["coverage"], ctx["concentration"].set_index("measure"), ctx["largest"]
    so, sep, yl = ctx["oss_overall"], ctx["separates"].set_index("factor"), ctx["yield"]
    ec = ctx["efficiency_corr"].set_index("measure")
    eb = ctx["efficiency_band"]
    ctx["funding_change"]["change_pp"] = ctx["funding_change"]["change_pp"].round(1) + 0.0
    fc = ctx["funding_change"].set_index("source")
    ft, fs = ctx["funding_typical"], ctx["funding_shift"]
    os_, ot = ctx["outreach_sector"], ctx["outreach_typical"]
    geo, dist, div = ctx["geo"], ctx["districts"], ctx["divisions"]
    groups, sil, scr = ctx["groups"], ctx["silhouettes"], ctx["screening"]
    band = ctx["oss_band"].set_index("size_band")
    lo = conc.loc["Loan outstanding"]
    names = ", ".join(top["name"].iloc[:-1]) + " and " + top["name"].iloc[-1]
    smallest = band.iloc[0]
    largest_band = band.iloc[-1]
    active = ctx["active"]
    curve = concentration.loan_lorenz(active)
    bottom90 = 100 * float(np.interp(0.9, curve["institutions"], curve["share"]))
    ranked = sil.set_index("k")["silhouette"]
    k = int(len(groups))
    flags = ctx["quality_flags"]
    fig = lambda key, alt: f"![{alt}](results/figures/{files[key]})"  # noqa: E731
    d_top, d_bottom = dist.head(5), dist.tail(5).iloc[::-1]
    dnames = lambda t: ", ".join(f"{r.district} ({r.borrowers_per_1000:.0f})" for r in t.itertuples())  # noqa: E731
    sunamganj = dist.reset_index(drop=True)
    sun_rank = int(sunamganj.index[sunamganj["district"] == "Sunamganj"][0]) + 1

    lines = [
        "# Results: the Bangladesh microfinance sector in June 2025",
        "",
        "Phase MF2. Every number below is computed by `make analyse` from the extracted MRA tables in",
        "`data/real/processed/` and the Census 2022 district populations. Nothing here uses synthetic",
        "data. The tables behind each figure are in [`results/tables/`](results/tables/).",
        "",
        "## Read this first: who is counted",
        "",
        f"The Basic table lists {cov['mfis_in_basic']} MFIs. {cov['mfis_without_data']} of them have no figures at all, and",
        f'{cov["mfis_in_basic"] - cov["mfis_without_data"] - cov["mfis_active"]} more report no loans or no borrowers, so **{cov["mfis_active"]} MFIs are analysed** ("active": loans',
        f"outstanding and borrowers both above zero). Together they hold {bn(active['loan_outstanding_bdt'].sum())} taka of loans (the report prints 1,748.8 billion for the sector; the per-MFI rows sum to slightly less, see the extraction notes).",
        "The ratio tables cover fewer of them, and each analysis says which:",
        "",
        "| Table | Active MFIs covered | Share of loan outstanding |",
        "|---|---:|---:|",
        f"| Basic (loans, borrowers, savings, staff) | {cov['mfis_active']} | 100% |",
        f"| Operating cost ratios | {cov['active_with_cost_ratios']} | {p1(cov['loans_share_with_cost_ratios_pct'])} |",
        f"| Risk ratios (yield, OSS, ROA, borrowing) | {cov['active_with_ratios']} | {p1(cov['loans_share_with_ratios_pct'])} |",
        f"| Fund composition | {cov['active_with_funds']} | {p1(cov['loans_share_with_funds_pct'])} |",
        "",
        'Amounts are taka. "Size" means loan outstanding. Medians describe a typical MFI (each counts once);',
        '"weighted" or "sector" figures add the numerators and denominators across MFIs, so large MFIs dominate.',
        "",
        "## 1. Concentration",
        "",
        fig("lorenz", "Lorenz curve of loan outstanding across MFIs"),
        "",
        md_table(
            ctx["concentration"],
            {
                "n_mfis": ",.0f",
                "top1_share_pct": ".1f",
                "top4_share_pct": ".1f",
                "top10_share_pct": ".1f",
                "hhi": ",.0f",
                "gini": ".2f",
            },
            {
                "measure": "Measure",
                "n_mfis": "MFIs",
                "top1_share_pct": "Top 1 %",
                "top4_share_pct": "Top 4 %",
                "top10_share_pct": "Top 10 %",
                "hhi": "HHI",
                "gini": "Gini",
            },
        ),
        "",
        f"{names} hold {p1(lo['top4_share_pct'])} of loan outstanding and {p1(conc.loc['Borrowers', 'top4_share_pct'])} of borrowers. {top['name'].iloc[0]} alone holds {p1(lo['top1_share_pct'])}",
        f"of the loan book. The Gini coefficient is {lo['gini']:.2f}: the smallest 90% of MFIs together hold {p0(bottom90)} of the loans. The HHI",
        f"({n0(lo['hhi'])}) looks low only because the rest of the sector is split across hundreds of small MFIs; the top-4 share and the Gini",
        "describe this sector better. Savings are more concentrated than loans "
        f"(top 4 hold {p1(conc.loc['Savings', 'top4_share_pct'])}), branches less ({p1(conc.loc['Branches', 'top4_share_pct'])}).",
        "",
        "## 2. Sustainability",
        "",
        fig("oss", "Share of MFIs with operating self-sufficiency below 100 percent, by size band"),
        "",
        md_table(
            ctx["oss_band"][
                [
                    "size_band",
                    "n_mfis",
                    "oss_median",
                    "roa_median",
                    "below_100_count",
                    "below_100_share_pct",
                    "negative_roa_share_pct",
                ]
            ],
            {
                "n_mfis": ",.0f",
                "oss_median": ".1f",
                "roa_median": ".1f",
                "below_100_count": ",.0f",
                "below_100_share_pct": ".1f",
                "negative_roa_share_pct": ".1f",
            },
            {
                "size_band": "Loan outstanding",
                "n_mfis": "MFIs",
                "oss_median": "Median OSS %",
                "roa_median": "Median ROA %",
                "below_100_count": "OSS < 100",
                "below_100_share_pct": "% OSS < 100",
                "negative_roa_share_pct": "% ROA < 0",
            },
        ),
        "",
        f"Operating self-sufficiency (OSS) below 100 means an MFI does not cover its costs from its own income. {so['below_100_count']} of {so['n_mfis']}",
        f"MFIs ({p1(so['below_100_share_pct'])}) are below 100, yet they hold only {p1(so['share_of_loans_in_below_100_pct'])} of the loans: the problem is",
        f"concentrated among small institutions. {p0(smallest['below_100_share_pct'])} of the smallest MFIs are below 100, against {p0(largest_band['below_100_share_pct'])}",
        f"of the {int(largest_band['n_mfis'])} largest. The median MFI has an OSS of {n1(so['oss_median'])} and a return on assets of {n1(so['roa_median'])}%",
        f"({so['negative_roa_count']} MFIs have negative ROA).",
        "",
        md_table(
            ctx["separates"],
            {
                "median_below_100": ",.1f",
                "median_100_or_more": ",.1f",
                "spearman_with_oss": ".2f",
                "n_pairs": ",.0f",
            },
            {
                "factor": "Factor",
                "median_below_100": "Median, OSS < 100",
                "median_100_or_more": "Median, OSS ≥ 100",
                "spearman_with_oss": "Rank corr. with OSS",
                "n_pairs": "MFIs",
            },
        ),
        "",
        f"MFIs below 100 are smaller (median loans {mn(sep.loc['Loan outstanding (BDT)', 'median_below_100'])} taka against {mn(sep.loc['Loan outstanding (BDT)', 'median_100_or_more'])}),",
        f"earn a lower yield ({n1(sep.loc['Portfolio yield (%)', 'median_below_100'])}% against {n1(sep.loc['Portfolio yield (%)', 'median_100_or_more'])}%), spend more per 100 taka lent",
        f"({n1(sep.loc['Operating cost per 100 taka of loans', 'median_below_100'])} against {n1(sep.loc['Operating cost per 100 taka of loans', 'median_100_or_more'])}), rely more on borrowing",
        f"({n1(sep.loc['Borrowing to loan outstanding (%)', 'median_below_100'])}% against {n1(sep.loc['Borrowing to loan outstanding (%)', 'median_100_or_more'])}% of loans) and hold a thinner capital cushion",
        f"({n1(sep.loc['Capital fund to loan outstanding (%)', 'median_below_100'])}% against {n1(sep.loc['Capital fund to loan outstanding (%)', 'median_100_or_more'])}%). The share of funds from clients' savings does not separate the two groups",
        f"(rank correlation {sep.loc['Clients' + chr(39) + ' savings share of funds (%)', 'spearman_with_oss']:.2f}). Two cautions: yield and operating cost are inputs to OSS, so their link to it is partly",
        "built in; and these are associations across institutions, not causes.",
        "",
        "## 3. Efficiency and scale",
        "",
        fig("cost", "Operating cost, financial cost and loans per employee by size band"),
        "",
        md_table(
            eb[
                [
                    "size_band",
                    "n_mfis",
                    "op_cost_ratio_median",
                    "financial_cost_ratio_median",
                    "borrowers_per_employee_median",
                    "borrowers_per_branch_median",
                    "loan_per_employee_bdt_median",
                    "cost_per_borrower_bdt_median",
                ]
            ],
            {
                "n_mfis": ",.0f",
                "op_cost_ratio_median": ".1f",
                "financial_cost_ratio_median": ".1f",
                "borrowers_per_employee_median": ",.0f",
                "borrowers_per_branch_median": ",.0f",
                "loan_per_employee_bdt_median": ",.0f",
                "cost_per_borrower_bdt_median": ",.0f",
            },
            {
                "size_band": "Loan outstanding",
                "n_mfis": "MFIs",
                "op_cost_ratio_median": "Op. cost /100 taka",
                "financial_cost_ratio_median": "Financial cost /100 taka",
                "borrowers_per_employee_median": "Borrowers per employee",
                "borrowers_per_branch_median": "Borrowers per branch",
                "loan_per_employee_bdt_median": "Loans per employee (BDT)",
                "cost_per_borrower_bdt_median": "Op. cost per borrower (BDT)",
            },
        ),
        "",
        f"Scale economies do not show up in cost per taka lent. The rank correlation between size and operating cost per 100 taka is {ec.loc['op_cost_ratio', 'spearman_with_size']:.2f} ({rho_word(ec.loc['op_cost_ratio', 'spearman_with_size'])}),",
        f"and the median sits between {n1(eb['op_cost_ratio_median'].min())} and {n1(eb['op_cost_ratio_median'].max())} in every band. Financial cost per 100 taka (interest on savings and on borrowing) rises with size ({r2(ec.loc['financial_cost_ratio', 'spearman_with_size'])}).",
        f"What does rise with size is lending per employee (correlation {ec.loc['loan_per_employee_bdt', 'spearman_with_size']:.2f}), because loans get larger, not because staff",
        f"serve more people: borrowers per employee show {rho_word(ec.loc['borrowers_per_employee', 'spearman_with_size'])} with size ({r2(ec.loc['borrowers_per_employee', 'spearman_with_size'])}). Cost per",
        "borrower rises with size for the same reason. These are ratios of published totals; staff counts are as reported by each MFI.",
        "",
        "## 4. Pricing",
        "",
        fig("yield", "Distribution of portfolio yield across MFIs with a 24 percent reference line"),
        "",
        f"Across {yl['n_mfis']} MFIs the median portfolio yield is {n1(yl['median'])}% (middle half {n1(yl['p25'])}% to {n1(yl['p75'])}%; loan-weighted average",
        f"{n1(yl['weighted_average'])}%). {yl['above_reference_count']} MFIs ({p1(yl['above_reference_share_pct'])}), holding {p1(yl['above_reference_loans_share_pct'])} of the loans, report a yield above",
        "24%. That figure is only a reference line: the press has reported a 24% ceiling since 2019 (see the caveats), MRA's own notification was not found, and",
        "portfolio yield is service-charge income over average loans, so it includes fees and is not the declining-balance rate a client pays. It cannot show",
        "whether any MFI breaches a limit.",
        "",
        md_table(
            ctx["yield_band"],
            {"n_mfis": ",.0f", "yield_median": ".1f", "above_reference_share_pct": ".1f"},
            {
                "size_band": "Loan outstanding",
                "n_mfis": "MFIs",
                "yield_median": "Median yield %",
                "above_reference_share_pct": "% above 24",
            },
        ),
        "",
        fig("yield_oss", "Operating self-sufficiency against portfolio yield, one point per MFI"),
        "",
        f"Yield and self-sufficiency move together (rank correlation {ctx['yield_oss']['spearman_yield_oss']:.2f}), and yield moves with the cost ratio too",
        f"({ctx['yield_oss']['spearman_yield_cost_ratio']:.2f}): MFIs with higher costs tend to charge more, and higher yields go with higher OSS, but the scatter is wide.",
        "",
        "## 5. Funding mix",
        "",
        fig("funding", "Funding mix by size band"),
        "",
        md_table(
            ctx["funding_change"],
            {
                "share_2024_06_pct": ".1f",
                "share_2025_06_pct": ".1f",
                "change_pp": "+.1f",
                "amount_2025_06_bdt": ",.0f",
                "amount_change_pct": "+.1f",
            },
            {
                "source": "Source of funds",
                "share_2024_06_pct": "Share Jun 2024 %",
                "share_2025_06_pct": "Share Jun 2025 %",
                "change_pp": "Change, points",
                "amount_2025_06_bdt": "Amount Jun 2025 (BDT)",
                "amount_change_pct": "Amount change %",
            },
        ),
        "",
        f"Over the {ft['n_mfis']} MFIs with a fund-composition row, clients' savings are {p1(fc.loc['Clients' + chr(39) + ' savings', 'share_2025_06_pct'])} of funds and surplus and other own funds",
        f"{p1(fc.loc['Surplus and other funds', 'share_2025_06_pct'])}; commercial-bank loans fell from {p1(fc.loc['Commercial-bank loans', 'share_2024_06_pct'])} to {p1(fc.loc['Commercial-bank loans', 'share_2025_06_pct'])} of funds",
        f"({fc.loc['Commercial-bank loans', 'amount_change_pct']:+.1f}% in taka) while savings grew {fc.loc['Clients' + chr(39) + ' savings', 'amount_change_pct']:.1f}% and PKSF loans {fc.loc['PKSF loans', 'amount_change_pct']:.1f}%.",
        f"A typical MFI draws {p0(ft['median_savings_share_pct'])} of its funds from clients' savings. {ft['mfis_with_bank_loans']} MFIs have commercial-bank loans and {ft['mfis_bank_dependent']} of them",
        f"({p1(ft['bank_dependent_share_pct'])} of the {ft['n_mfis']}) get a quarter or more of their funds from banks, together holding {p1(ft['bank_dependent_loans_share_pct'])} of loans. Between the two",
        f"years, {fs['bank_share_up_10pp']} MFIs raised their bank-loan share by 10 points or more and {fs['bank_share_down_10pp']} cut it by as much.",
        "",
        "## 6. Outreach",
        "",
        fig("outreach", "Average loan size and women's share of clients by size band"),
        "",
        md_table(
            ctx["outreach_band"][
                [
                    "size_band",
                    "n_mfis",
                    "avg_loan_size_median_bdt",
                    "savings_per_client_median_bdt",
                    "female_client_share_median_pct",
                    "borrowers_to_clients_median_pct",
                ]
            ],
            {
                "n_mfis": ",.0f",
                "avg_loan_size_median_bdt": ",.0f",
                "savings_per_client_median_bdt": ",.0f",
                "female_client_share_median_pct": ".1f",
                "borrowers_to_clients_median_pct": ".1f",
            },
            {
                "size_band": "Loan outstanding",
                "n_mfis": "MFIs",
                "avg_loan_size_median_bdt": "Avg loan (BDT)",
                "savings_per_client_median_bdt": "Savings per client (BDT)",
                "female_client_share_median_pct": "Women % of clients",
                "borrowers_to_clients_median_pct": "Borrowers % of clients",
            },
        ),
        "",
        f"The sector-wide average loan is {n0(os_['avg_loan_size_bdt'])} taka per borrower, but the typical MFI's is {n0(ot['median_avg_loan_size_bdt'])} (middle half",
        f"{n0(ot['p25_avg_loan_size_bdt'])} to {n0(ot['p75_avg_loan_size_bdt'])}); the large MFIs pull the average up. Clients hold {n0(os_['savings_per_client_bdt'])} taka of savings on average",
        f"({p1(os_['savings_to_loans_pct'])} of loans outstanding). Women are {p1(os_['female_client_share_pct'])} of clients and {p1(os_['female_borrower_share_pct'])} of borrowers;",
        f"{ot['mfis_female_share_90_plus']} MFIs are at least 90% women and {ot['mfis_female_share_below_50']} are under half. The report counts {n0(os_['third_gender_clients'])} third-gender clients and",
        f"{n0(os_['third_gender_borrowers'])} third-gender borrowers. {p1(os_['borrowers_to_clients_pct'])} of members have a loan.",
        "",
        "## 7. Data quality",
        "",
        "The published tables have gaps and inconsistencies, listed in full in [docs/extraction-notes.md](docs/extraction-notes.md). Beyond those, plausibility",
        "checks catch values that are probably entry errors. Counts only; no institution is named.",
        "",
        md_table(
            flags,
            {"mfis_checked": ",.0f", "mfis_flagged": ",.0f", "loans_share_of_flagged_pct": ".2f"},
            {
                "check": "Check",
                "mfis_checked": "MFIs checked",
                "mfis_flagged": "Flagged",
                "loans_share_of_flagged_pct": "Share of loans held by flagged %",
            },
        ),
        "",
        "Flagged MFIs hold a very small share of loans, so they matter little for sector totals but would distort averages, which is why the medians above",
        "are preferred and the peer groups below exclude them.",
        "",
        "## 8. Peer groups and a screening rule",
        "",
        fig("groups", "Peer groups by median ratios"),
        "",
        md_table(
            groups.drop(columns=["capital_ratio_median"]).rename(columns={}),
            {
                "group": ".0f",
                "n_mfis": ",.0f",
                "loans_share_pct": ".1f",
                "loan_outstanding_median_bdt": ",.0f",
                "avg_loan_size_median_bdt": ",.0f",
                "portfolio_yield_median": ".1f",
                "op_cost_ratio_median": ".1f",
                "borrowing_ratio_median": ".1f",
                "savings_share_median_pct": ".1f",
                "oss_median": ".1f",
                "below_100_share_pct": ".1f",
            },
            {
                "group": "Group",
                "n_mfis": "MFIs",
                "loans_share_pct": "% of loans",
                "loan_outstanding_median_bdt": "Median loans (BDT)",
                "avg_loan_size_median_bdt": "Median avg loan (BDT)",
                "portfolio_yield_median": "Yield %",
                "op_cost_ratio_median": "Op. cost /100",
                "borrowing_ratio_median": "Borrowing/loans %",
                "savings_share_median_pct": "Savings/funds %",
                "oss_median": "OSS %",
                "below_100_share_pct": "% OSS < 100",
            },
        )
        + "\n\n"
        + "Capital fund to loans, the seventh ratio, is in [`08_peer_groups.csv`](results/tables/08_peer_groups.csv) and the figure.",
        "",
        f"K-means on seven standardised ratios (size, loan size, yield, operating cost, borrowing, capital, savings share) over {int(groups['n_mfis'].sum())} MFIs with a complete",
        f"set and no implausible value gives {k} groups (best silhouette among 2 to 6 groups: {ranked.max():.2f}). A silhouette that low means the structure is weak: the groups",
        "are a convenient summary of how MFIs differ, not natural clusters. What sets each group apart (median against the median of all groups):",
        "",
        *[
            f"- **Group {g}** ({int(groups.set_index('group').loc[g, 'n_mfis'])} MFIs, {p1(groups.set_index('group').loc[g, 'loans_share_pct'])} of loans): "
            + "; ".join(f"{label} {value:,.1f} (all MFIs {centre:,.1f})" for label, value, centre in items)
            for g, items in distinctive(ctx["grouped"], DISTINCT_COLUMNS).items()
        ],
        "",
        f"**Screening rule.** MFIs with OSS below 100 and borrowing at or above {peers.WATCH_BORROWING_PCT:.0f}% of loans number {scr['flagged']} of {scr['n_mfis']}",
        f"({p1(scr['flagged_share_pct'])}); together they hold {p1(scr['flagged_loans_share_pct'])} of the loans, and their median loan book is {mn(scr['flagged_median_loan_outstanding_bdt'])}",
        "taka. This is a filter on financial-structure ratios. It says nothing about delinquency, which MRA publishes only for the sector as a whole, and it is not a",
        "finding about any named institution, so no list is published.",
        "",
        "## 9. Geography",
        "",
        fig("districts", "MFI borrowers per 1,000 people by district"),
        "",
        md_table(
            div[
                [
                    "division",
                    "population",
                    "borrowers",
                    "borrowers_per_1000",
                    "loan_outstanding_per_person_bdt",
                ]
            ],
            {
                "population": ",.0f",
                "borrowers": ",.0f",
                "borrowers_per_1000": ".0f",
                "loan_outstanding_per_person_bdt": ",.0f",
            },
            {
                "division": "Division",
                "population": "Population (Census 2022)",
                "borrowers": "MFI borrowers",
                "borrowers_per_1000": "Borrowers per 1,000",
                "loan_outstanding_per_person_bdt": "Loans per person (BDT)",
            },
        ),
        "",
        f"Nationally there are {n0(geo['national_borrowers_per_1000'])} MFI borrowers per 1,000 people, but districts range from {n0(geo['min_borrowers_per_1000'])} to {n0(geo['max_borrowers_per_1000'])}.",
        f"Highest: {dnames(d_top)}. Lowest: {dnames(d_bottom)}. By division, {div.iloc[0]['division']} is highest ({n0(div.iloc[0]['borrowers_per_1000'])}) and",
        f"{div.iloc[-1]['division']} lowest ({n0(div.iloc[-1]['borrowers_per_1000'])}). Sunamganj ranks {sun_rank} of {geo['n_districts']} from the top. Across districts, MFI borrowers per 1,000 people",
        f"have {rho_word(geo['spearman_borrowers_account'])} with the share of people holding a financial-institution account in the census (rank correlation",
        f"{geo['spearman_borrowers_account']:.2f}) and {rho_word(geo['spearman_borrowers_mobile'])} with mobile-banking accounts ({geo['spearman_borrowers_mobile']:.2f}). Borrowers are counts of loans",
        "held with MFIs, not distinct people, and the population is everyone, not adults; use the ranking, not the level.",
        "",
        "## Limits and caveats",
        "",
        "- **Real data only, and only what MRA publishes.** No per-MFI delinquency, no client-level data, nothing on Grameen Bank's own accounts beyond MRA's sector series.",
        "- **Denominators differ by table** (see the top). Findings on ratios describe the MFIs that report them.",
        "- **Associations, not causes.** Rank correlations and group medians describe how measures move together across institutions.",
        "- **The 24% reference.** The press has reported a 24% ceiling on microcredit interest since 2019, with later proposals to lower it "
        "([Financial Express, 2021](https://thefinancialexpress.com.bd/economy/bangladesh/microcredit-regulator-forms-committee-to-cut-microloan-interest-rates-1614393568)). "
        "MRA's own notification was not located and the current value is unconfirmed, so it is used only as a reference line.",
        "- **Census population** is the 2022 Census district table from BBS, as published on the Humanitarian Data Exchange under CC0. The report date is June 2025.",
        "- **Not yet done:** trends over time and the June 2024 comparison (phase MF3).",
        "",
        "Reproduce everything with `make analyse`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    setup()
    ctx = compute()
    write_tables(ctx, RESULTS_DIR / "tables")
    files = figures.all_figures(ctx, RESULTS_DIR / "figures")
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(summary(ctx), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    RESULTS_MD.write_text(render(ctx, files), encoding="utf-8")
    print(f"wrote {RESULTS_MD.name}, {len(files)} figures and the tables in {RESULTS_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
