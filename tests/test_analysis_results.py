"""Recompute headline numbers with plain Python (csv and statistics only) and compare them with
the pandas-based analysis, so a mistake in one implementation cannot pass unnoticed."""

import csv
import json
import statistics
from pathlib import Path

import pytest

from kisti.analysis import geography, peers, quality
from kisti.analysis.report import compute, summary

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "real" / "processed"


def rows(name):
    with (PROCESSED / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def num(value):
    return None if value == "" else float(value)


@pytest.fixture(scope="module")
def basic_active():
    return [
        r
        for r in rows("mfi_basic.csv")
        if (num(r["loan_outstanding_bdt"]) or 0) > 0 and (num(r["borrowers_total"]) or 0) > 0
    ]


@pytest.fixture(scope="module")
def context():
    return compute()


def test_active_set_and_total_loans(basic_active, context):
    assert len(basic_active) == 644
    total = sum(num(r["loan_outstanding_bdt"]) for r in basic_active)
    assert context["active"]["loan_outstanding_bdt"].sum() == pytest.approx(total)


def test_top4_share_hhi_and_gini_match_a_plain_python_calculation(basic_active, context):
    loans = sorted((num(r["loan_outstanding_bdt"]) for r in basic_active), reverse=True)
    total = sum(loans)
    figures = summary(context)
    assert figures["top4_loan_share_pct"] == pytest.approx(100 * sum(loans[:4]) / total)
    assert figures["hhi_loan_outstanding"] == pytest.approx(sum((100 * x / total) ** 2 for x in loans))
    mean = total / len(loans)
    gini = sum(abs(a - b) for a in loans for b in loans) / (2 * len(loans) ** 2 * mean)
    assert figures["gini_loan_outstanding"] == pytest.approx(gini)


def test_the_four_largest_are_the_expected_institutions(context):
    assert list(context["largest"]["name"]) == ["BRAC", "ASA", "BURO Bangladesh", "TMSS"]


def test_oss_below_100_matches_a_plain_python_count(basic_active, context):
    active_ids = {r["license_no"] for r in basic_active}
    oss = [
        num(r["operating_self_sufficiency"])
        for r in rows("mfi_risk_ratios.csv")
        if r["license_no"] in active_ids and r["operating_self_sufficiency"] != ""
    ]
    figures = summary(context)
    assert (figures["oss_below_100_count"], figures["oss_below_100_of"]) == (
        sum(v < 100 for v in oss),
        len(oss),
    )


def test_median_yield_and_reference_count(basic_active, context):
    active_ids = {r["license_no"] for r in basic_active}
    yields = [num(r["portfolio_yield"]) for r in rows("mfi_risk_ratios.csv") if r["license_no"] in active_ids]
    figures = summary(context)
    assert figures["yield_median"] == pytest.approx(statistics.median(yields))
    assert figures["yield_above_reference_count"] == sum(v > 24 for v in yields)


def test_female_share_and_average_loan(basic_active, context):
    figures = summary(context)
    female = sum(num(r["clients_female"]) or 0 for r in basic_active)
    clients = sum(num(r["clients_total"]) or 0 for r in basic_active)
    assert figures["female_client_share_pct"] == pytest.approx(100 * female / clients)
    loans = sum(num(r["loan_outstanding_bdt"]) for r in basic_active)
    borrowers = sum(num(r["borrowers_total"]) for r in basic_active)
    assert figures["avg_loan_size_bdt"] == pytest.approx(loans / borrowers)


def test_bank_loan_share_change_matches_a_plain_python_calculation(basic_active, context):
    active_ids = {r["license_no"] for r in basic_active}
    by_mfi = {}
    for r in rows("mfi_fund_composition.csv"):
        if r["license_no"] not in active_ids or r["fund_type"] == "Total":
            continue
        entry = by_mfi.setdefault(
            r["license_no"], {"seen": set(), "a25": 0.0, "a24": 0.0, "b25": 0.0, "b24": 0.0}
        )
        if r["fund_type"] in entry["seen"]:
            continue  # the block printed twice
        entry["seen"].add(r["fund_type"])
        for key, col in (("a25", "amount_2025_06_bdt"), ("a24", "amount_2024_06_bdt")):
            entry[key] += num(r[col]) or 0.0
        if r["fund_type"] == "Loan from Commercial Banks":
            entry["b25"] += num(r["amount_2025_06_bdt"]) or 0.0
            entry["b24"] += num(r["amount_2024_06_bdt"]) or 0.0
    both = [e for e in by_mfi.values() if e["a24"] > 0]
    share25 = 100 * sum(e["b25"] for e in both) / sum(e["a25"] for e in both)
    share24 = 100 * sum(e["b24"] for e in both) / sum(e["a24"] for e in both)
    assert summary(context)["bank_loan_share_change_pp"] == pytest.approx(share25 - share24)


def test_national_borrowers_per_1000_matches_the_census_total():
    borrowers = sum(num(r["borrowers"]) for r in rows("district_coverage.csv") if r["row_type"] == "district")
    population = sum(num(r["population"]) for r in rows("district_population.csv"))
    frame = geography.districts()
    assert geography.summary(frame)["national_borrowers_per_1000"] == pytest.approx(
        1000 * borrowers / population
    )
    assert len(frame) == 64 and frame["district"].is_unique


def test_committed_summary_is_current(context):
    committed = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    fresh = summary(context)
    # the peer-group count depends on clustering; every other number must match exactly
    for key in fresh:
        if key in ("n_groups", "screening_flagged"):
            continue
        assert committed[key] == pytest.approx(fresh[key]), key


def test_peer_groups_partition_the_clustered_mfis_and_exclude_implausible_values(context):
    grouped, profile = context["grouped"], context["groups"]
    assert 2 <= len(profile) <= 6
    assert grouped["group"].notna().all() and set(grouped["group"]) == set(profile["group"])
    assert profile["n_mfis"].sum() == len(grouped)
    assert not quality.implausible(grouped).any()
    # numbered from the smallest median loan book to the largest
    assert profile["loan_outstanding_median_bdt"].is_monotonic_increasing
    assert peers.SEED == 0


def test_every_mra_district_maps_to_exactly_one_census_district():
    from kisti.extract.census import census_district_name, normalise

    census = {normalise(r["district"]) for r in rows("district_population.csv")}
    mra = [r["district"] for r in rows("district_coverage.csv") if r["row_type"] == "district"]
    keys = [normalise(census_district_name(name)) for name in mra]
    assert len(mra) == 64 and set(keys) == census and len(set(keys)) == 64


def test_census_population_total():
    total = sum(int(r["population"]) for r in rows("district_population.csv"))
    assert total == 165_158_616  # Census 2022 national total, 165.2 million
