"""Reconciliation tests on the committed tables in data/real/processed/.

These run in CI without the PDFs. Where the publisher printed figures that do not add up,
the exact rows are listed here as known exceptions: a new discrepancy fails the test, and a
listed one that disappears also fails, so the list can never go stale.
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

import pytest

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "real" / "processed"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read(name, folder=PROCESSED):
    with (folder / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def num(value):
    return None if value == "" else float(value)


def total(rows, column):
    return sum(num(r[column]) or 0 for r in rows)


@pytest.fixture(scope="module")
def basic():
    return read("mfi_basic.csv")


@pytest.fixture(scope="module")
def divisions():
    return {r["division"]: r for r in read("division_summary.csv")}


@pytest.fixture(scope="module")
def districts():
    return read("district_coverage.csv")


# --- shape --------------------------------------------------------------------------------

EXPECTED_ROWS = {
    "mfi_basic.csv": 693,
    "mfi_positions.csv": 626,
    "mfi_cost_ratios.csv": 600,
    "mfi_risk_ratios.csv": 540,
}


@pytest.mark.parametrize(("filename", "count"), EXPECTED_ROWS.items())
def test_row_counts_and_contiguous_serials(filename, count):
    rows = read(filename)
    assert len(rows) == count
    assert [int(r["serial"]) for r in rows] == list(range(1, count + 1))


def test_every_row_has_a_name_and_a_clean_licence_number():
    for filename in EXPECTED_ROWS:
        for row in read(filename):
            assert row["name"], (filename, row["serial"])
            assert "Address:" not in row["name"] and "Email:" not in row["name"], row["name"]
            assert int(row["license_no"]) > 0


def test_licence_numbers_are_unique_within_each_table(basic):
    for filename in EXPECTED_ROWS:
        ids = [r["license_no"] for r in read(filename)]
        assert len(ids) == len(set(ids)), filename


def test_ratio_tables_only_contain_mfis_from_the_basic_table(basic):
    known = {r["license_no"] for r in basic}
    for filename in (
        "mfi_positions.csv",
        "mfi_cost_ratios.csv",
        "mfi_risk_ratios.csv",
        "mfi_fund_composition.csv",
    ):
        assert {r["license_no"] for r in read(filename)} <= known, filename


def test_the_same_mfi_has_the_same_name_in_every_table(basic):
    names = {r["license_no"]: r["name"] for r in basic}
    for filename in (
        "mfi_positions.csv",
        "mfi_cost_ratios.csv",
        "mfi_risk_ratios.csv",
        "mfi_fund_composition.csv",
    ):
        for row in read(filename):
            assert row["name"] == names[row["license_no"]], (filename, row["license_no"])


def test_the_one_licence_printed_twice_is_recorded_as_an_issue(basic):
    """Serial 600 is printed with the licence of serial 361; the short number tells them apart."""
    by_serial = {int(r["serial"]): r for r in basic}
    assert by_serial[600]["license_printed"] == by_serial[361]["license_printed"]
    assert by_serial[600]["license_no"] != by_serial[361]["license_no"]
    issues = read("extraction_issues.csv")
    assert any(r["table"] == "basic" and r["serial"] == "600" for r in issues)


# --- internal identities in the Basic table ----------------------------------------------------

# Rows where the printed total is not the sum of its printed parts (checked against the page).
CLIENT_TOTAL_EXCEPTIONS = {61, 166, 396}
BORROWER_TOTAL_EXCEPTIONS = {30, 63, 96, 263, 335, 520, 573, 592, 631}


def violations(rows, parts, whole):
    return {int(r["serial"]) for r in rows if sum(num(r[p]) or 0 for p in parts) != (num(r[whole]) or 0)}


def test_employees_add_up(basic):
    assert violations(basic, ["employees_male", "employees_female"], "employees_total") == set()


def test_clients_add_up_except_for_the_printed_exceptions(basic):
    parts = ["clients_male", "clients_female", "clients_third_gender"]
    assert violations(basic, parts, "clients_total") == CLIENT_TOTAL_EXCEPTIONS


def test_borrowers_add_up_except_for_the_printed_exceptions(basic):
    parts = ["borrowers_male", "borrowers_female", "borrowers_third_gender"]
    assert violations(basic, parts, "borrowers_total") == BORROWER_TOTAL_EXCEPTIONS


def test_no_mfi_has_more_borrowers_than_clients(basic):
    for row in basic:
        assert (num(row["borrowers_total"]) or 0) <= (num(row["clients_total"]) or 0), row["serial"]


# --- reconciliation with the printed sector totals --------------------------------------------

# (column, total printed in Table 3.1 / Table 1.3, tolerance as a share of the printed total).
# The per-MFI rows fall short of the printed totals by the amounts below. The report does not
# explain the gap; the tolerances document how large it is and fail if it grows.
PRINTED_TOTALS = [
    ("branches", 27_113, 0.009),
    ("employees_total", 234_380, 0.025),
    ("clients_total", 43_979_221, 0.0002),
    ("borrowers_total", 33_682_069, 0.0002),
    ("savings_bdt", 799_324_421_991, 0.0001),
    ("loan_outstanding_bdt", 1_748_802_083_320, 0.0001),
]


@pytest.mark.parametrize(("column", "printed", "tolerance"), PRINTED_TOTALS)
def test_per_mfi_sums_are_close_to_the_printed_sector_totals(basic, column, printed, tolerance):
    difference = total(basic, column) - printed
    assert abs(difference) / printed <= tolerance, difference
    assert difference <= 0, "the per-MFI rows should never exceed the printed total"


def test_division_table_adds_up_to_all_divisions(divisions):
    parts = [row for name, row in divisions.items() if name != "All Divisions"]
    assert len(parts) == 8
    for column in ("branches", "members", "borrowers"):
        assert total(parts, column) == num(divisions["All Divisions"][column])
    for column in ("loan_outstanding_bdt", "savings_bdt"):  # taka, rounded to the unit
        assert abs(total(parts, column) - num(divisions["All Divisions"][column])) <= 2


def test_district_table_has_64_districts_and_matches_the_division_table(districts, divisions):
    kinds = Counter(r["row_type"] for r in districts)
    assert kinds == {"district": 64, "division_total": 8, "all_districts": 1}
    for name, division in divisions.items():
        if name == "All Divisions":
            continue
        rows = [r for r in districts if r["division"] == name]
        total_row = next(r for r in rows if r["row_type"] == "division_total")
        members = [r for r in rows if r["row_type"] == "district"]
        for column in ("branches", "members", "borrowers"):
            assert total(members, column) == num(total_row[column]) == num(division[column]), (name, column)
        for column in ("loan_outstanding_bdt", "savings_bdt"):
            assert abs(total(members, column) - num(total_row[column])) <= 3, (name, column)
            assert num(total_row[column]) == num(division[column]), (name, column)


def test_district_names_are_clean_and_unique(districts):
    names = [r["district"] for r in districts if r["row_type"] == "district"]
    assert len(names) == len(set(names))
    # A division label printed beside a district must not leak into the district name
    # (districts that share a division's name, such as Dhaka, are single words).
    divisions = {"Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh", "Rajshahi", "Rangpur", "Sylhet"}
    assert not [n for n in names if len(n.split()) > 1 and n.split()[0] in divisions]


def test_loan_classification_matches_table_2_1():
    rows = {r["category"]: r for r in read("sector_llp.csv")}
    shares = {k: float(v["share_pct"]) for k, v in rows.items()}
    assert shares == {
        "good": 82.63,
        "watchful": 8.85,
        "sub_standard": 1.83,
        "doubtful": 1.99,
        "bad": 4.70,
        "total": 100.0,
    }
    parts = ("good", "watchful", "sub_standard", "doubtful", "bad")
    assert sum(shares[k] for k in parts) == pytest.approx(100.0, abs=0.01)
    assert sum(float(rows[k]["amount_billion_bdt"]) for k in parts) == pytest.approx(
        float(rows["total"]["amount_billion_bdt"]), abs=0.02
    )
    npl = sum(shares[k] for k in ("sub_standard", "doubtful", "bad"))
    assert npl == pytest.approx(8.52, abs=0.005)
    assert {k for k, v in rows.items() if v["is_non_performing"] == "True"} == {
        "sub_standard",
        "doubtful",
        "bad",
    }


def test_trend_table_ends_at_the_printed_2024_25_totals(divisions):
    series = defaultdict(dict)
    for row in read("sector_timeseries.csv"):
        series[row["metric"]][row["fiscal_year"]] = float(row["value"])
    assert sorted(next(iter(series.values()))) == [f"{y}-{str(y + 1)[2:]}" for y in range(2015, 2025)]
    last = {metric: values["2024-25"] for metric, values in series.items()}
    assert last["branches"] == 27_113
    assert last["employees"] == 234_380
    assert last["members"] == pytest.approx(43.98, abs=0.005)
    assert last["borrowers"] == pytest.approx(33.68, abs=0.005)
    assert last["loan_outstanding"] == pytest.approx(
        num(divisions["All Divisions"]["loan_outstanding_bdt"]) / 1e9, abs=0.005
    )
    assert last["savings"] == pytest.approx(num(divisions["All Divisions"]["savings_bdt"]) / 1e9, abs=0.005)
    assert last["branches"] == num(divisions["All Divisions"]["branches"])


# --- cost, risk, positions and fund composition ----------------------------------------------


# Rows where the printed total operating cost differs from financial cost plus admin cost
# by more than rounding (checked against the page).
COST_TOTAL_EXCEPTIONS = {580, 594, 599}


def test_operating_cost_ratios_add_up_where_all_parts_are_printed():
    found = set()
    for row in read("mfi_cost_ratios.csv"):
        a, b, c, d, e = (
            num(row[k])
            for k in (
                "saving_cost_ratio",
                "borrowing_cost_ratio",
                "total_financial_cost_ratio",
                "general_admin_cost_ratio",
                "total_operating_cost_ratio",
            )
        )
        if None in (a, b, c):
            continue
        assert a + b == pytest.approx(c, abs=0.02), row["serial"]
        if d is not None and e is not None and abs(c + d - e) > 0.02:
            found.add(int(row["serial"]))
    assert found == COST_TOTAL_EXCEPTIONS


def test_positions_are_ranks_within_the_basic_table():
    for row in read("mfi_positions.csv"):
        for column in ("rank_loan_outstanding", "rank_loan_disbursement", "rank_branches", "rank_borrowers"):
            assert 1 <= num(row[column]) <= 693


def test_the_largest_mfis_are_ranked_first(basic):
    ranks = {r["license_no"]: r for r in read("mfi_positions.csv")}
    by_loans = sorted(basic, key=lambda r: -(num(r["loan_outstanding_bdt"]) or 0))[:4]
    assert [ranks[r["license_no"]]["rank_loan_outstanding"] for r in by_loans] == ["1", "2", "3", "4"]
    assert [r["name"] for r in by_loans][:2] == ["BRAC", "ASA"]


# Blocks where the printed components do not add up to the printed total, or the same block
# is printed twice (checked against the page).
FUND_AMOUNT_EXCEPTIONS = {(155, "2025_06"), (155, "2024_06"), (380, "2024_06"), (542, "2025_06")}
FUND_SHARE_EXCEPTIONS = {(155, "2025_06"), (155, "2024_06")}
FUND_DUPLICATE_BLOCKS = {(333, 368)}


def fund_blocks():
    blocks = defaultdict(list)
    for row in read("mfi_fund_composition.csv"):
        blocks[int(row["serial"])].append(row)
    return blocks


def test_fund_components_add_up_to_the_total_except_for_the_printed_exceptions():
    found = set()
    for serial, rows in fund_blocks().items():
        for period in ("2025_06", "2024_06"):
            column = f"amount_{period}_bdt"
            components = sum(num(r[column]) or 0 for r in rows if r["fund_type"] != "Total")
            printed = next(num(r[column]) for r in rows if r["fund_type"] == "Total")
            if abs(components - (printed or 0)) > 2:
                found.add((serial, period))
    assert found == FUND_AMOUNT_EXCEPTIONS


def test_fund_shares_add_up_to_100_except_for_the_printed_exceptions():
    found = set()
    for serial, rows in fund_blocks().items():
        for period in ("2025_06", "2024_06"):
            shares = sum(num(r[f"share_{period}_pct"]) or 0 for r in rows if r["fund_type"] != "Total")
            printed = next(num(r[f"amount_{period}_bdt"]) for r in rows if r["fund_type"] == "Total")
            if printed and abs(shares - 100) > 0.1:
                found.add((serial, period))
    assert found == FUND_SHARE_EXCEPTIONS


def test_fund_table_has_one_total_per_block_and_only_known_duplicates():
    blocks = fund_blocks()
    assert len(blocks) == 569
    assert all(sum(r["fund_type"] == "Total" for r in rows) == 1 for rows in blocks.values())
    by_licence = defaultdict(list)
    for serial, rows in blocks.items():
        by_licence[rows[0]["license_no"]].append(serial)
    assert {tuple(v) for v in by_licence.values() if len(v) > 1} == FUND_DUPLICATE_BLOCKS


# --- spot check against an independent extraction ------------------------------------------------


def test_spot_checked_mfis_match_an_independent_extraction(basic):
    """25 MFIs (the four largest plus every 33rd serial) compared with values read by a second,
    unrelated method (pdftotext layout text), and BRAC also read off the page image."""
    by_id = {r["license_no"]: r for r in basic}
    risk = {r["license_no"]: r for r in read("mfi_risk_ratios.csv")}
    fixture = read("mfi_spot_check.csv", FIXTURES)
    assert len(fixture) == 25
    for expected in fixture:
        row = by_id[expected["license_no"]]
        for column in ("branches", "borrowers_total", "savings_bdt", "loan_outstanding_bdt"):
            assert num(row[column]) == num(expected[column]), (expected["name"], column)
        if expected["operating_self_sufficiency"]:
            got = num(risk[expected["license_no"]]["operating_self_sufficiency"])
            assert got == num(expected["operating_self_sufficiency"]), expected["name"]
