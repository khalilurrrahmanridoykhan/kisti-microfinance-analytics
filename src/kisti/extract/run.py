"""Run every extractor on one MRA annual statistics PDF and write tidy CSVs.

    python -m kisti.extract

The PDF is fetched first with `make fetch`. Rows the extractors could not read cleanly, and
figures the publisher itself printed inconsistently, are written to `extraction_issues.csv`
instead of being silently repaired.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from . import mfi_tables as m
from . import sector_tables as s
from .pdf import page_texts, read_pages, read_separators

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PDF = ROOT / "data" / "real" / "raw" / "mra_annual_statistics_2025-06.pdf"
DEFAULT_OUT = ROOT / "data" / "real" / "processed"
EDITION = "2025-06"

# Fund composition amounts are printed for the report date and the year before.
FUND_COLUMNS = ("amount_2025_06_bdt", "share_2025_06_pct", "amount_2024_06_bdt", "share_2024_06_pct")


def license_no(licence: str | None) -> int | None:
    """The last group of a licence number, which identifies the MFI across tables."""
    if not licence:
        return None
    return int(licence.rsplit("-", 1)[1])


def contiguous(pages: list[int], label: str) -> list[int]:
    if pages != list(range(pages[0], pages[-1] + 1)):
        raise ValueError(f"{label}: table pages are not contiguous: {pages}")
    return pages


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if value is None else value for value in row])


def clean_contact_words(name: str) -> str:
    """Contact-detail labels from the neighbouring column can leak into a Basic table name."""
    words = [w for w in name.split() if w not in ("Address:", "Email:", "Phone:")]
    return " ".join(words)


def run(pdf_path: Path = DEFAULT_PDF, out_dir: Path = DEFAULT_OUT) -> dict[str, int]:
    texts = page_texts(pdf_path)

    def pages_with(*needles: str) -> list[int]:
        return [i + 1 for i, t in enumerate(texts) if all(n in t for n in needles)]

    issues: list[list] = []
    extracted: dict[str, list[m.Row]] = {}

    for key, table in m.GRID_TABLES.items():
        pages = contiguous(pages_with(table.title, "(As on"), key)
        separators = read_separators(pdf_path, pages) if table.use_separators else None
        rows = m.extract_grid(read_pages(pdf_path, pages), table, separators)
        if [r.serial for r in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"{key}: serial numbers are not contiguous")
        extracted[key] = rows

    fund_pages = contiguous(pages_with("Fund Composition of MFIs", "(As on"), "fund")
    fund_blocks = m.extract_fund(read_pages(pdf_path, fund_pages))
    if [b.serial for b in fund_blocks] != list(range(1, len(fund_blocks) + 1)):
        raise ValueError("fund: serial numbers are not contiguous")

    # Identity: the short licence number printed in the Basic table.
    basic_ids = {r.short_license for r in extracted["basic"]}
    names: dict[int, str] = {}
    for key in ("positions", "cost", "risk"):
        for row in extracted[key]:
            names.setdefault(license_no(row.license), row.name)
    for block in fund_blocks:
        names.setdefault(license_no(block.license), block.name)

    def note(table: str, serial, page, text: str) -> None:
        issues.append([EDITION, table, serial, page, text])

    for key, rows in extracted.items():
        seen: dict[int, int] = {}
        for row in rows:
            for text in row.issues:
                note(key, row.serial, row.page, text)
            mfi = row.short_license if key == "basic" else license_no(row.license)
            if mfi in seen:
                note(key, row.serial, row.page, f"licence no. {mfi} also on serial {seen[mfi]}")
            seen[mfi] = row.serial
            if key != "basic" and mfi not in basic_ids:
                note(key, row.serial, row.page, f"licence no. {mfi} is not in the Basic table")
    fund_seen: dict[int, int] = {}
    for block in fund_blocks:
        for text in block.issues:
            note("fund", block.serial, block.page, text)
        fund_id = license_no(block.license)
        if fund_id in fund_seen:
            note(
                "fund", block.serial, block.page, f"licence no. {fund_id} also on serial {fund_seen[fund_id]}"
            )
        fund_seen[fund_id] = block.serial
        if license_no(block.license) not in basic_ids:
            note(
                "fund",
                block.serial,
                block.page,
                f"licence no. {license_no(block.license)} is not in the Basic table",
            )

    # Grid tables: one row per MFI.
    counts: dict[str, int] = {}
    for key, rows in extracted.items():
        table = m.GRID_TABLES[key]
        out_rows = []
        for row in rows:
            mfi = row.short_license if key == "basic" else license_no(row.license)
            name = names.get(mfi) or clean_contact_words(row.name)
            out_rows.append([EDITION, row.serial, mfi, row.license, name, row.page, *row.values])
        header = ["edition", "serial", "license_no", "license_printed", "name", "page", *table.columns]
        filename = {
            "basic": "mfi_basic.csv",
            "positions": "mfi_positions.csv",
            "cost": "mfi_cost_ratios.csv",
            "risk": "mfi_risk_ratios.csv",
        }[key]
        write_csv(out_dir / filename, header, out_rows)
        counts[filename] = len(out_rows)

    # Fund composition: long format, one row per MFI and fund type.
    fund_rows = []
    for block in fund_blocks:
        mfi = license_no(block.license)
        name = names.get(mfi) or block.name
        for fund_type, values in block.rows:
            values = (values + [None] * 4)[:4]
            fund_rows.append(
                [EDITION, block.serial, mfi, block.license, name, block.page, fund_type, *values]
            )
    write_csv(
        out_dir / "mfi_fund_composition.csv",
        ["edition", "serial", "license_no", "license_printed", "name", "page", "fund_type", *FUND_COLUMNS],
        fund_rows,
    )
    counts["mfi_fund_composition.csv"] = len(fund_rows)

    # Sector tables.
    trend_page = pages_with("52-4202")
    llp_page = pages_with("Loans due between")
    division_page = pages_with("All Divisions")
    district_last = pages_with("All Districts")
    if not (trend_page and llp_page and division_page and district_last):
        raise ValueError("could not locate the sector tables")
    wanted = {trend_page[0], llp_page[0], *range(division_page[0], district_last[-1] + 1)}
    words = read_pages(pdf_path, sorted(wanted))

    trend = s.extract_trend(words[trend_page[0]])
    write_csv(
        out_dir / "sector_timeseries.csv",
        ["scope", "fiscal_year", "metric", "unit", "value"],
        [["MFIs", *row] for row in trend],
    )
    counts["sector_timeseries.csv"] = len(trend)

    llp = s.extract_llp(words[llp_page[0]])
    write_csv(
        out_dir / "sector_llp.csv",
        [
            "edition",
            "scope",
            "category",
            "specification",
            "amount_billion_bdt",
            "share_pct",
            "is_non_performing",
        ],
        [
            [
                EDITION,
                "MFIs",
                r["category"],
                r["specification"],
                r["amount_billion_bdt"],
                r["share_pct"],
                r["is_non_performing"],
            ]
            for r in llp
        ],
    )
    counts["sector_llp.csv"] = len(llp)

    divisions, districts = s.extract_coverage(
        {p: words[p] for p in range(division_page[0], district_last[-1] + 1)}
    )
    write_csv(
        out_dir / "division_summary.csv",
        ["edition", "division", *s.COVERAGE_COLUMNS],
        [[EDITION, r.division, *r.values] for r in divisions],
    )
    district_rows = []
    for r in districts:
        kind = (
            "all_districts"
            if r.district == "All Districts"
            else "division_total"
            if r.district is None
            else "district"
        )
        district_rows.append([EDITION, r.division, r.district or "", kind, *r.values])
    write_csv(
        out_dir / "district_coverage.csv",
        ["edition", "division", "district", "row_type", *s.COVERAGE_COLUMNS],
        district_rows,
    )
    counts["division_summary.csv"] = len(divisions)
    counts["district_coverage.csv"] = len(district_rows)

    write_csv(out_dir / "extraction_issues.csv", ["edition", "table", "serial", "page", "issue"], issues)
    counts["extraction_issues.csv"] = len(issues)
    return counts


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    for filename, count in run(pdf).items():
        print(f"{count:>6}  {filename}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
