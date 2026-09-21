"""Cross-check the extracted per-MFI tables against a second, unrelated extraction method.

The extractors in `kisti.extract` read word coordinates with pdfplumber. This script reads
the same PDF as plain layout text with poppler's `pdftotext -layout`, takes the numbers at
the end of each serial-numbered line, and compares them with the CSVs cell by cell. The two
methods share no code, so agreement is evidence that no cell was misread or shifted.

    make crosscheck        # needs `pdftotext` (poppler) on the PATH
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "real" / "raw" / "mra_annual_statistics_2025-06.pdf"
PROCESSED = ROOT / "data" / "real" / "processed"

NUMBER = re.compile(r"^-?\d[\d,]*(\.\d+)?$|^-$")

# csv file, table title, trailing numeric columns, whether the second column is the short licence no.
TABLES = [
    (
        "mfi_basic.csv",
        "Basic Information of MFIs",
        [
            "branches",
            "employees_male",
            "employees_female",
            "employees_total",
            "clients_male",
            "clients_female",
            "clients_third_gender",
            "clients_total",
            "borrowers_male",
            "borrowers_female",
            "borrowers_third_gender",
            "borrowers_total",
            "savings_bdt",
            "loan_disbursement_bdt",
            "loan_outstanding_bdt",
        ],
        True,
    ),
    (
        "mfi_cost_ratios.csv",
        "Operating Cost Ratios of MFIs",
        [
            "saving_cost_ratio",
            "borrowing_cost_ratio",
            "total_financial_cost_ratio",
            "general_admin_cost_ratio",
            "total_operating_cost_ratio",
        ],
        False,
    ),
    (
        "mfi_risk_ratios.csv",
        "Risk Measuring Ratios of MFIs",
        [
            "borrowing_to_loan_outstanding",
            "operating_cost_to_income",
            "capital_fund_to_loan_outstanding",
            "portfolio_yield",
            "return_on_assets",
            "operating_self_sufficiency",
            "operating_margin",
        ],
        False,
    ),
    (
        "mfi_positions.csv",
        "Positions of MFIs",
        ["rank_loan_outstanding", "rank_loan_disbursement", "rank_branches", "rank_borrowers"],
        False,
    ),
]


def layout_pages(pdf: Path) -> list[str]:
    text = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout
    return text.split("\f")


def second_method(pages: list[str], title: str, columns: list[str], has_short: bool) -> dict[int, tuple]:
    parsed: dict[int, tuple] = {}
    width = len(columns)
    for page in pages:
        if title not in page or "(As on" not in page:
            continue
        for line in page.split("\n"):
            tokens = line.split()
            if len(tokens) < width + 1 or not tokens[0].isdigit():
                continue
            if not all(NUMBER.match(t) for t in tokens[-width:]):
                continue
            values = [None if t == "-" else float(t.replace(",", "")) for t in tokens[-width:]]
            short = int(tokens[1]) if has_short and tokens[1].isdigit() else None
            parsed[int(tokens[0])] = (short, values)
    return parsed


def main() -> int:
    pages = layout_pages(PDF)
    failed = False
    for filename, title, columns, has_short in TABLES:
        expected = second_method(pages, title, columns, has_short)
        agree = disagree = missing = 0
        for row in csv.DictReader((PROCESSED / filename).open(encoding="utf-8")):
            serial = int(row["serial"])
            if serial not in expected:
                missing += 1
                continue
            short, values = expected[serial]
            mine = [None if row[c] == "" else float(row[c]) for c in columns]
            same_id = short is None or short == int(row["license_no"])
            if mine == values and same_id:
                agree += 1
            else:
                disagree += 1
        print(
            f"{filename:<22} agree {agree:>4}  disagree {disagree:>3}  not read by second method {missing:>3}"
        )
        failed = failed or disagree or missing
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
