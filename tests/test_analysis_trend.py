"""Tests for phase MF3: the ten-year trend and the printed two-year NPL comparison."""

import csv
from pathlib import Path

import pytest

from kisti.analysis import trend

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "real" / "processed"


def rows():
    with (PROCESSED / "sector_timeseries.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_ten_year_series_covers_exactly_the_ten_printed_fiscal_years():
    series = trend.ten_year_series()
    assert list(series.index) == [
        "2015-16",
        "2016-17",
        "2017-18",
        "2018-19",
        "2019-20",
        "2020-21",
        "2021-22",
        "2022-23",
        "2023-24",
        "2024-25",
    ]
    assert list(series.columns) == trend.TREND_METRICS


def test_ten_year_series_matches_the_committed_csv_exactly():
    series = trend.ten_year_series()
    for row in rows():
        assert series.loc[row["fiscal_year"], row["metric"]] == pytest.approx(float(row["value"]))


def test_cagr_matches_a_plain_python_calculation():
    series = trend.ten_year_series()
    for metric in trend.TREND_METRICS:
        first = float(
            [r["value"] for r in rows() if r["metric"] == metric and r["fiscal_year"] == "2015-16"][0]
        )
        last = float(
            [r["value"] for r in rows() if r["metric"] == metric and r["fiscal_year"] == "2024-25"][0]
        )
        expected = (last / first) ** (1 / 9) - 1
        assert trend.cagr(series[metric]) == pytest.approx(expected)


def test_cagr_of_a_flat_series_is_zero():
    import pandas as pd

    flat = pd.Series({"2015-16": 100.0, "2024-25": 100.0})
    assert trend.cagr(flat) == pytest.approx(0.0)


def test_growth_table_has_one_row_per_metric_with_the_printed_endpoints():
    table = trend.growth_table().set_index("metric")
    assert set(table.index) == set(trend.TREND_METRICS)
    assert table.loc["branches", "value_2015_16"] == 16_204
    assert table.loc["branches", "value_2024_25"] == 27_113
    assert table.loc["loan_outstanding", "cagr_pct"] == pytest.approx(16.3, abs=0.1)


def test_savings_and_loans_grew_faster_than_branches_and_borrowers():
    """The headline claim in RESULTS.md section 10, checked against the real numbers."""
    table = trend.growth_table().set_index("metric")["cagr_pct"]
    assert table["loan_outstanding"] > table["branches"]
    assert table["loan_outstanding"] > table["borrowers"]
    assert table["savings"] > table["branches"]
    assert table["savings"] > table["borrowers"]


def test_npl_two_year_matches_the_printed_quote_and_is_in_the_pdf_text():
    result = trend.npl_two_year()
    assert result["fy2023_24_pct"] == 8.09
    assert result["fy2024_25_pct"] == 8.52
    assert result["change_pp"] == pytest.approx(0.43)
    assert "8.09 percent" in result["quote"]
    assert "8.52 percent" in result["quote"]
    # The quote is a real sentence from the source PDF, not a paraphrase. It sits in a
    # two-column layout, so pdfplumber's plain reading order interleaves "8.52" and "percent"
    # onto different re-joined lines (confirmed by eye against `pdftotext -layout`, which does
    # preserve column geometry) — the check below uses substrings unaffected by that, on the
    # one page that should hold the whole passage.
    from kisti.extract.pdf import page_texts

    pdf = ROOT / "data" / "real" / "raw" / "mra_annual_statistics_2025-06.pdf"
    if not pdf.exists():
        pytest.skip("source PDF not fetched in this checkout")
    texts = page_texts(pdf)
    assert any(
        "8.09 percent" in t and "8.52" in t and "excluding" in t and "watchful category" in t for t in texts
    )
