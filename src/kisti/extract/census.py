"""District population from the Census 2022 district tables (Humanitarian Data Exchange copy).

    python -m kisti.extract.census

Writes `data/real/processed/district_population.csv`, one row per district, and defines the
mapping from the district spellings MRA prints to the census spellings.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_XLSX = ROOT / "data" / "real" / "raw" / "bbs_census_2022_admin2.xlsx"
DEFAULT_OUT = ROOT / "data" / "real" / "processed" / "district_population.csv"

# MRA spellings that differ from the census spelling once punctuation and case are ignored.
MRA_TO_CENSUS = {"Barisal": "Barishal", "Bogra": "Bogura", "Maulvibazar": "Moulvibazar"}

ACCOUNT_SHEET = "Having Account in Financial"
ACCOUNT_COLUMN = "Have financial account_Overall"
MOBILE_SHEET = "Having Mobile Banking Account"
MOBILE_COLUMN = "Mobile Bank Account_Overall"


def normalise(name: str) -> str:
    """Lower-case letters only, so `Cox’s Bazar` and `Cox's Bazar` compare equal."""
    return "".join(ch for ch in name.lower() if ch.isalpha())


def census_district_name(mra_name: str) -> str:
    return MRA_TO_CENSUS.get(mra_name, mra_name)


def sheet(book: pd.ExcelFile, name: str) -> pd.DataFrame:
    """A sheet by name, ignoring the stray leading and trailing spaces in the workbook's tab names."""
    for candidate in book.sheet_names:
        if candidate.strip() == name:
            return book.parse(candidate)
    raise ValueError(f"worksheet {name!r} not found")


def read_population(xlsx: Path = DEFAULT_XLSX) -> pd.DataFrame:
    book = pd.ExcelFile(xlsx)
    merged = sheet(book, "Merged_All_Table")
    frame = merged[
        [
            "Division",
            "District",
            "Division_Geocode",
            "District_Geocode",
            "Household_Total",
            "Population_Total",
        ]
    ].rename(
        columns={
            "Division": "division",
            "District": "district",
            "Division_Geocode": "division_geocode",
            "District_Geocode": "district_geocode",
            "Household_Total": "households",
            "Population_Total": "population",
        }
    )
    accounts = sheet(book, ACCOUNT_SHEET)[["District", ACCOUNT_COLUMN]]
    mobile = sheet(book, MOBILE_SHEET)[["District", MOBILE_COLUMN]]
    frame = frame.merge(
        accounts.rename(columns={"District": "district", ACCOUNT_COLUMN: "financial_account_pct"})
    )
    frame = frame.merge(mobile.rename(columns={"District": "district", MOBILE_COLUMN: "mobile_banking_pct"}))
    return frame.sort_values(["division", "district"]).reset_index(drop=True)


def main() -> int:
    frame = read_population(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX)
    frame.insert(0, "edition", "census-2022")
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DEFAULT_OUT, index=False, lineterminator="\n")
    print(f"{len(frame):>6}  {DEFAULT_OUT.name}  (total population {int(frame['population'].sum()):,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
