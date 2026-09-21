import numpy as np
import pandas as pd

from kisti.analysis import data


def test_size_band_edges():
    values = pd.Series([9_999_999, 10e6, 99e6, 100e6, 1e9, 9.9e9, 10e9])
    assert list(data.size_band(values)) == [
        "< 10 million",
        "10-100 million",
        "10-100 million",
        "100 million-1 billion",
        "1-10 billion",
        "1-10 billion",
        "10 billion +",
    ]


def fund_rows(*rows):
    return pd.DataFrame(rows, columns=["license_no", "fund_type", "amount_2025_06_bdt", "amount_2024_06_bdt"])


def test_fund_amounts_group_sources_and_drop_the_total_row():
    fund = fund_rows(
        (1, "Clients' Savings", 100.0, 80.0),
        (1, "Loan from Other MFIs", 10.0, 10.0),
        (1, "Other loans", 5.0, 0.0),
        (1, "Cumulative Surplus", -20.0, 5.0),
        (1, "Total", 95.0, 95.0),
    )
    wide = data.fund_amounts(fund, "2025_06")
    assert wide.loc[1, "clients_savings"] == 100.0
    assert wide.loc[1, "other_borrowing"] == 15.0
    assert wide.loc[1, "surplus_and_other"] == -20.0
    assert wide.loc[1, "total_funds"] == 95.0


def test_fund_amounts_count_a_licence_printed_twice_once():
    row = (7, "Clients' Savings", 50.0, 40.0)
    wide = data.fund_amounts(fund_rows(row, row, (7, "Total", 50.0, 40.0)), "2025_06")
    assert wide.loc[7, "clients_savings"] == 50.0


def test_load_gives_one_row_per_mfi_in_the_basic_table():
    frame = data.load()
    assert len(frame) == 693
    assert frame["license_no"].is_unique
    assert frame["is_active"].sum() == 644
    active = frame[frame["is_active"]]
    assert active["size_band"].notna().all() and frame.loc[~frame["is_active"], "size_band"].isna().all()
    assert (active["loan_outstanding_bdt"] > 0).all() and (active["borrowers_total"] > 0).all()


def test_derived_measures_follow_their_definitions():
    frame = data.load()
    row = frame[(frame["is_active"]) & frame["total_operating_cost_ratio"].notna()].iloc[0]
    assert row["avg_loan_size_bdt"] == row["loan_outstanding_bdt"] / row["borrowers_total"]
    assert np.isclose(
        row["operating_cost_per_borrower_bdt"],
        row["total_operating_cost_ratio"] / 100 * row["avg_loan_size_bdt"],
    )
    assert np.isclose(row["female_client_share_pct"], 100 * row["clients_female"] / row["clients_total"])
