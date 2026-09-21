"""Unit tests for the sector, division and district table extractors, on synthetic words."""

import pytest

from kisti.extract import sector_tables as s
from kisti.extract.pdf import Word


def w(text, x0, top, page=1):
    return Word(text, x0, x0 + 6 * len(text), top, page)


# --- sector tables ---------------------------------------------------------------------------


def coverage_line(label, values, top, page=1, label_x=100):
    words = [w(label, label_x, top, page)]
    words += [w(text, 200 + 60 * i, top, page) for i, text in enumerate(values)]
    return words


def test_extract_coverage_splits_divisions_and_districts():
    ten = [
        "1,572",
        "5.80",
        "2,452,658",
        "5.58",
        "1,897,977",
        "5.63",
        "90,419,468,125",
        "5.17",
        "50,706,630,818",
        "6.34",
    ]
    page = coverage_line("Barishal", ten, 100)
    page += coverage_line("All Divisions", ten, 120)
    page += coverage_line("Barguna", ten, 200)
    page += coverage_line("Total", ten, 220)
    page += coverage_line("All Districts", ten, 240)
    divisions, districts = s.extract_coverage({1: page})
    assert [r.division for r in divisions] == ["Barishal", "All Divisions"]
    assert [(r.division, r.district) for r in districts] == [
        ("Barishal", "Barguna"),
        ("Barishal", None),
        ("All Divisions", "All Districts"),
    ]
    assert divisions[0].values[0] == 1572


def test_extract_coverage_reads_a_district_name_wrapped_over_lines():
    ten = [
        "723",
        "2.67",
        "1,150,908",
        "2.62",
        "868,077",
        "2.58",
        "39,238,789,850",
        "2.24",
        "15,898,211,594",
        "1.99",
    ]
    page = coverage_line("All Divisions", ten, 50)
    page += [w("Chapai", 100, 191), w("Nababganj", 100, 209)]
    page += [w(text, 200 + 60 * i, 200) for i, text in enumerate(ten)]
    _, districts = s.extract_coverage({1: page})
    assert districts[0].district == "Chapai Nababganj"


def test_extract_trend_reads_the_rotated_table():
    words = []
    for i in range(10):
        year = f"{2024 - i}-{25 - i:02d}"
        top = 100 + 50 * i
        words.append(w(year[::-1], 117, top))
        for j, value in enumerate(["1,000", "2,000", "3.5", "4.5", "5.5", "6.5", "7.5"]):
            words.append(w(value[::-1], 200 + 40 * j, top + 3))
    rows = s.extract_trend(words)
    assert len(rows) == 70
    assert rows[0] == ("2024-25", "branches", "count", 1000)
    assert ("2015-16", "savings", "billion BDT", 7.5) in rows


def test_extract_trend_rejects_an_unexpected_table():
    with pytest.raises(ValueError):
        s.extract_trend([w("52-4202", 117, 100)])
