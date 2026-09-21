"""Extract the per-MFI tables (chapters 5 to 9 of the MRA annual statistics).

Every table is a grid with one row per MFI. The x-thresholds below were measured on a
reference page of the June 2025 edition (`ref_as` is the x position of the "(As on ...)"
subtitle on that page). Pages alternate between two horizontal offsets, so each page is
shifted by how far its own subtitle sits from the reference one.
"""

from __future__ import annotations

from bisect import bisect
from dataclasses import dataclass, field

from .pdf import (
    LICENSE_RE,
    Word,
    by_page,
    complete_license,
    group_lines,
    is_number,
    join_name,
    nearest_anchor,
    split_license,
    to_number,
)


@dataclass(frozen=True)
class GridTable:
    key: str
    title: str
    columns: tuple[str, ...]
    ref_as: float
    serial_max: float
    name_lo: float
    name_hi: float
    numeric_lo: float
    body_top: float
    body_bottom: float
    short_license: bool = False
    numeric_hi: float = 750
    name_x1_max: float | None = None  # names end at this x; longer words belong to the next column
    use_separators: bool = False


@dataclass
class Row:
    serial: int
    name: str
    license: str | None
    page: int
    values: list = field(default_factory=list)
    short_license: int | None = None
    issues: list[str] = field(default_factory=list)


BASIC = GridTable(
    key="basic",
    title="Basic Information of MFIs",
    columns=(
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
    ),
    ref_as=361,
    serial_max=100,
    name_lo=120,
    name_hi=188,
    numeric_lo=270,
    body_top=143,
    body_bottom=600,
    short_license=True,
    use_separators=True,
    name_x1_max=186,
)

POSITIONS = GridTable(
    key="positions",
    title="Positions of MFIs",
    columns=("rank_loan_outstanding", "rank_loan_disbursement", "rank_branches", "rank_borrowers"),
    ref_as=272,
    serial_max=108,
    name_lo=110,
    name_hi=360,
    numeric_lo=375,
    body_top=144,
    body_bottom=740,
)

COST = GridTable(
    key="cost",
    title="Operating Cost Ratios of MFIs",
    columns=(
        "saving_cost_ratio",
        "borrowing_cost_ratio",
        "total_financial_cost_ratio",
        "general_admin_cost_ratio",
        "total_operating_cost_ratio",
    ),
    ref_as=274,
    serial_max=102,
    name_lo=105,
    name_hi=300,
    numeric_lo=300,
    body_top=150,
    body_bottom=740,
)

RISK = GridTable(
    key="risk",
    title="Risk Measuring Ratios of MFIs",
    columns=(
        "borrowing_to_loan_outstanding",
        "operating_cost_to_income",
        "capital_fund_to_loan_outstanding",
        "portfolio_yield",
        "return_on_assets",
        "operating_self_sufficiency",
        "operating_margin",
    ),
    ref_as=274,
    serial_max=100,
    name_lo=102,
    name_hi=245,
    numeric_lo=245,
    body_top=142,
    body_bottom=740,
)

GRID_TABLES = {t.key: t for t in (BASIC, POSITIONS, COST, RISK)}


def page_shift(words: list[Word], ref_as: float) -> float:
    """How far this page is shifted horizontally relative to the reference page."""
    for word in words:
        if word.text == "(As" and word.top < 130:
            return word.x0 - ref_as
    return 0.0


def extract_grid(
    pages: dict[int, list[Word]],
    table: GridTable,
    separators: dict[int, list[float]] | None = None,
) -> list[Row]:
    """One Row per anchor (serial number).

    A word belongs to the row whose cell (between two horizontal rules) contains it. Tables
    without usable rules fall back to the nearest serial number by vertical position.
    """
    rows: list[Row] = []
    for page_no in sorted(pages):
        words = pages[page_no]
        dx = page_shift(words, table.ref_as)
        body = [w for w in words if table.body_top < w.top < table.body_bottom and w.x0 > 60 + dx]
        anchors = [w for w in body if w.text.isdigit() and 60 + dx < w.x0 < table.serial_max + dx]
        anchors.sort(key=lambda w: w.top)
        if not anchors:
            continue
        bands: list[list[Word]] = [[] for _ in anchors]
        rules = (separators or {}).get(page_no) if table.use_separators else None
        cell_to_anchor = {bisect(rules, a.mid): i for i, a in enumerate(anchors)} if rules else {}
        for word in body:
            if word in anchors:
                continue
            if rules:
                index = cell_to_anchor.get(bisect(rules, word.mid))
                if index is not None:
                    bands[index].append(word)
            else:
                bands[nearest_anchor(word, anchors)].append(word)
        for anchor, band in zip(anchors, bands):
            rows.append(_build_row(anchor, band, table, dx))
    return rows


def _build_row(anchor: Word, band: list[Word], table: GridTable, dx: float) -> Row:
    name_words = [w for w in band if table.name_lo + dx <= w.x0 < table.name_hi + dx]
    if table.name_x1_max is not None:
        # Licence numbers are the widest words in the name column, so they are always kept.
        name_words = [w for w in name_words if w.x1 <= table.name_x1_max + dx or LICENSE_RE.search(w.text)]
    # The numeric cells sit on the same printed line as the serial number.
    numeric_words = sorted(
        (
            w
            for w in band
            if table.numeric_lo + dx <= w.x0 < table.numeric_hi + dx
            and is_number(w.text)
            and abs(w.top - anchor.top) <= 5
        ),
        key=lambda w: w.x0,
    )
    short = None
    if table.short_license:
        for word in band:
            if table.serial_max + dx <= word.x0 < table.name_lo + dx and word.text.isdigit():
                short = int(word.text)
                name_words = [w for w in name_words if w is not word]
    joined = join_name(name_words)
    name, licence = split_license(joined, short)
    row = Row(int(anchor.text), name, licence, anchor.page, short_license=short)
    if licence is None:
        licence = complete_license(joined, short)
        if licence:
            row.license = licence
            name = " ".join(joined.replace(licence[:-5], " ").split())
            row.name = name
            row.issues.append("info: licence rebuilt from the short licence number")
    elif short is not None and int(licence.rsplit("-", 1)[1]) != short:
        row.issues.append("licence number does not match the short licence number")
    row.values = [to_number(w.text) for w in numeric_words]
    if row.license is None:
        row.issues.append("licence number not found")
    if not row.name:
        row.issues.append("name not found")
    if len(row.values) != len(table.columns):
        row.issues.append(f"expected {len(table.columns)} numeric cells, found {len(row.values)}")
    if table.short_license and short is None:
        row.issues.append("short licence number not found")
    return row


# --- Fund composition (chapter 9): several rows per MFI, closed by a "Total" row -----------

FUND_REF_AS = 274
FUND_NAME_HI = 250
FUND_TYPE_LO = 255
FUND_TYPE_HI = 355
FUND_VALUE_LO = 360
FUND_BODY_TOP = 118
FUND_BODY_BOTTOM = 740
FUND_SERIAL_MAX = 104


@dataclass
class FundBlock:
    serial: int | None
    name: str
    license: str | None
    page: int
    rows: list[tuple[str, list]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def extract_fund(pages: dict[int, list[Word]]) -> list[FundBlock]:
    blocks: list[FundBlock] = []
    pending_words: list[Word] = []
    pending_rows: list[tuple[str, list]] = []
    first_page: int | None = None
    for page_no in sorted(pages):
        words = pages[page_no]
        dx = page_shift(words, FUND_REF_AS)
        body = [w for w in words if FUND_BODY_TOP < w.top < FUND_BODY_BOTTOM and w.x0 > 60 + dx]
        left = [w for w in body if w.x0 < FUND_NAME_HI + dx]
        right = [w for w in body if w.x0 >= FUND_TYPE_LO + dx]
        rows_on_page = []
        for line in group_lines(right):
            values = [w for w in line if is_number(w.text)]
            if len(values) < 3:
                continue
            fund_type = " ".join(w.text for w in line if not is_number(w.text)).replace("’", "'")
            rows_on_page.append((line[0].top, fund_type, [to_number(w.text) for w in values]))
        events = [(w.top, 0, w) for w in left] + [(top, 1, (t, v)) for top, t, v in rows_on_page]
        for _, kind, payload in sorted(events, key=lambda e: (round(e[0]), e[1])):
            if kind == 0:
                pending_words.append(payload)
                first_page = first_page or payload.page
                continue
            fund_type, values = payload
            pending_rows.append((fund_type, values))
            if fund_type == "Total":
                blocks.append(_build_block(pending_words, pending_rows, first_page or page_no, dx))
                pending_words, pending_rows, first_page = [], [], None
    return blocks


def _build_block(words: list[Word], rows: list[tuple[str, list]], page: int, dx: float) -> FundBlock:
    serial_words = [w for w in words if w.text.isdigit() and w.x0 < FUND_SERIAL_MAX + dx]
    if not serial_words:
        # A serial number printed slightly further right than usual sits among the name words.
        serial_words = [w for w in words if w.text.isdigit() and len(w.text) <= 3][:1]
    name_words = [w for w in words if w not in serial_words]
    name, licence = split_license(join_name(name_words))
    serial = int(serial_words[0].text) if serial_words else None
    block = FundBlock(serial, name, licence, page, rows)
    if len(serial_words) != 1:
        block.issues.append(f"expected 1 serial number, found {len(serial_words)}")
    if licence is None:
        block.issues.append("licence number not found")
    for fund_type, values in rows:
        if len(values) != 4:
            block.issues.append(f"{fund_type}: expected 4 values, found {len(values)}")
    return block


def group_pages(words: list[Word]) -> dict[int, list[Word]]:
    return dict(by_page(words))
