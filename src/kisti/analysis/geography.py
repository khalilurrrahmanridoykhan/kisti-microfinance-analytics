"""Q9: where do MFIs reach people, by district?

Members and borrowers are counts of MFI clients, not of distinct people: someone can hold
loans from several MFIs, and Grameen Bank, government schemes and banks are outside these
figures. The measures are coverage of the MFI sector, not financial inclusion as a whole.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..extract.census import census_district_name, normalise
from .data import PROCESSED
from .stats import spearman


def districts(processed: Path = PROCESSED) -> pd.DataFrame:
    coverage = pd.read_csv(processed / "district_coverage.csv")
    coverage = coverage[coverage["row_type"] == "district"].copy()
    coverage["census_key"] = coverage["district"].map(lambda name: normalise(census_district_name(name)))
    population = pd.read_csv(processed / "district_population.csv").rename(
        columns={"division": "census_division"}
    )
    population["census_key"] = population["district"].map(normalise)
    frame = coverage.merge(population, on="census_key", how="left", suffixes=("", "_census"))
    if frame["population"].isna().any():
        raise ValueError(
            "districts without a census match: "
            + ", ".join(frame.loc[frame["population"].isna(), "district"])
        )
    frame["members_per_1000"] = 1000 * frame["members"] / frame["population"]
    frame["borrowers_per_1000"] = 1000 * frame["borrowers"] / frame["population"]
    frame["loan_outstanding_per_person_bdt"] = frame["loan_outstanding_bdt"] / frame["population"]
    frame["avg_loan_size_bdt"] = frame["loan_outstanding_bdt"] / frame["borrowers"]
    frame["branches_per_100k"] = 100_000 * frame["branches"] / frame["population"]
    return (
        frame[
            [
                "division",
                "district",
                "population",
                "households",
                "branches",
                "members",
                "borrowers",
                "loan_outstanding_bdt",
                "members_per_1000",
                "borrowers_per_1000",
                "loan_outstanding_per_person_bdt",
                "avg_loan_size_bdt",
                "branches_per_100k",
                "financial_account_pct",
                "mobile_banking_pct",
            ]
        ]
        .sort_values("borrowers_per_1000", ascending=False)
        .reset_index(drop=True)
    )


def by_division(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby("division").agg(
        population=("population", "sum"),
        members=("members", "sum"),
        borrowers=("borrowers", "sum"),
        loan_outstanding_bdt=("loan_outstanding_bdt", "sum"),
    )
    grouped["borrowers_per_1000"] = 1000 * grouped["borrowers"] / grouped["population"]
    grouped["loan_outstanding_per_person_bdt"] = grouped["loan_outstanding_bdt"] / grouped["population"]
    return grouped.sort_values("borrowers_per_1000", ascending=False).reset_index()


def summary(frame: pd.DataFrame) -> dict[str, float]:
    rho_account, n = spearman(frame["borrowers_per_1000"], frame["financial_account_pct"])
    rho_mobile, _ = spearman(frame["borrowers_per_1000"], frame["mobile_banking_pct"])
    return {
        "n_districts": len(frame),
        "national_borrowers_per_1000": 1000 * frame["borrowers"].sum() / frame["population"].sum(),
        "median_borrowers_per_1000": frame["borrowers_per_1000"].median(),
        "max_borrowers_per_1000": frame["borrowers_per_1000"].max(),
        "min_borrowers_per_1000": frame["borrowers_per_1000"].min(),
        "spearman_borrowers_account": rho_account,
        "spearman_borrowers_mobile": rho_mobile,
        "n_pairs": n,
    }
