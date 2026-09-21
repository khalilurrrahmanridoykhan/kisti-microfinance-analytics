"""Extract the sector-level tables: the ten-year trend (1.3), loan classification (2.1) and
the division and district coverage tables (3.1, 3.2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .pdf import Word, group_lines, is_number, to_number

DIVISIONS = ("Barishal", "Chattogram", "Dhaka", "Khulna", "Mymensingh", "Rajshahi", "Rangpur", "Sylhet")

COVERAGE_COLUMNS = (
    "branches",
    "branches_share_pct",
    "members",
    "members_share_pct",
    "borrowers",
    "borrowers_share_pct",
    "loan_outstanding_bdt",
    "loan_outstanding_share_pct",
    "savings_bdt",
    "savings_share_pct",
)

# (metric, unit) in the order the rows are printed in Table 1.3
TREND_METRICS = (
    ("branches", "count"),
    ("employees", "count"),
    ("members", "million"),
    ("borrowers", "million"),
    ("loan_disbursement", "billion BDT"),
    ("loan_outstanding", "billion BDT"),
    ("savings", "billion BDT"),
)


@dataclass
class CoverageRow:
    division: str
    district: str | None  # None for a division total row
    values: list
    page: int
    issues: list[str] = field(default_factory=list)


def _numeric_split(line: list[Word]) -> tuple[list[Word], list[Word]]:
    """Split a line into its leading label words and the numeric tokens that follow."""
    first = next((i for i, w in enumerate(line) if is_number(w.text) and w.text != "-"), len(line))
    return line[:first], line[first:]


def _label(words: list[Word], gap: float = 30.0) -> list[str]:
    """Group label words into clusters separated by wide horizontal gaps."""
    clusters: list[list[Word]] = []
    for word in words:
        if clusters and word.x0 - clusters[-1][-1].x1 <= gap:
            clusters[-1].append(word)
        else:
            clusters.append([word])
    return [" ".join(w.text for w in cluster).replace("’", "'") for cluster in clusters]


def _wrapped_label(line: list[Word], lines: list[list[Word]], reach: float = 14.0) -> list[Word]:
    """Label words for a numbers-only line: a long name is wrapped over the lines above and below."""
    top = line[0].top
    near = [
        other
        for other in lines
        if other is not line
        and abs(other[0].top - top) <= reach
        and not any(is_number(w.text) for w in other)
        and all(w.x0 < line[0].x0 for w in other)
    ]
    return [w for other in sorted(near, key=lambda o: o[0].top) for w in other]


def extract_coverage(pages: dict[int, list[Word]]) -> tuple[list[CoverageRow], list[CoverageRow]]:
    """Return (division rows, district rows). District rows include each division's Total row."""
    divisions: list[CoverageRow] = []
    districts: list[CoverageRow] = []
    seen_all_divisions = False
    division_index = 0
    for page_no in sorted(pages):
        lines = group_lines(pages[page_no])
        for line in lines:
            label_words, numbers = _numeric_split(line)
            if len(numbers) != len(COVERAGE_COLUMNS):
                continue
            if not all(is_number(w.text) for w in numbers):
                continue
            if not label_words:
                label_words = _wrapped_label(line, lines)
                if not label_words:
                    continue
            labels = _label(label_words)
            # A division label printed in its own column can sit within the merge gap of the district.
            head = labels[0].split(" ", 1)
            is_prefixed = len(head) == 2 and head[0] in DIVISIONS and len(labels) == 1
            if is_prefixed and division_index < len(DIVISIONS):
                labels = [head[1]]
            values = [to_number(w.text) for w in numbers]
            if not seen_all_divisions:
                name = labels[-1]
                if name == "All Divisions":
                    seen_all_divisions = True
                    divisions.append(CoverageRow("All Divisions", None, values, page_no))
                elif name in DIVISIONS:
                    divisions.append(CoverageRow(name, None, values, page_no))
                continue
            name = labels[-1]
            if name == "All Districts":
                districts.append(CoverageRow("All Divisions", "All Districts", values, page_no))
            elif name == "Total":
                districts.append(CoverageRow(DIVISIONS[division_index], None, values, page_no))
                division_index += 1
            elif division_index < len(DIVISIONS):
                districts.append(CoverageRow(DIVISIONS[division_index], name, values, page_no))
    return divisions, districts


def extract_trend(words: list[Word]) -> list[tuple[str, str, str, float]]:
    """Table 1.3 as (fiscal_year, metric, unit, value) rows.

    The table is printed rotated by 90 degrees, so every string comes out reversed
    ("52-4202" is "2024-25") and each year is a horizontal row of seven metric values.
    """
    year_words = [
        w for w in words if len(w.text) == 7 and w.text[::-1][4] == "-" and w.text[::-1][:4].isdigit()
    ]
    if len(year_words) != 10:
        raise ValueError(f"expected 10 fiscal years in the trend table, found {len(year_words)}")
    rows = []
    for year_word in sorted(year_words, key=lambda w: w.top):
        cells = sorted(
            (w for w in words if abs(w.top - year_word.top) <= 12 and w.x0 > year_word.x1 + 5),
            key=lambda w: w.x0,
        )
        cells = [w for w in cells if is_number(w.text[::-1])]
        if len(cells) != len(TREND_METRICS):
            raise ValueError(
                f"{year_word.text[::-1]}: expected {len(TREND_METRICS)} values, found {len(cells)}"
            )
        for (metric, unit), cell in zip(TREND_METRICS, cells):
            rows.append((year_word.text[::-1], metric, unit, to_number(cell.text[::-1])))
    return rows


LLP_KEYS = (
    ("Regular", "good"),
    ("1 to 30", "watchful"),
    ("31 to 180", "sub_standard"),
    ("181 to 365", "doubtful"),
    ("Above 365", "bad"),
    ("Existing loan", "total"),
)


def extract_llp(words: list[Word]) -> list[dict]:
    """Table 2.1: consolidated loan classification, amounts in billion BDT and shares in percent."""
    rows = []
    for line in group_lines(words):
        text = " ".join(w.text for w in line)
        numbers = [w for w in line if is_number(w.text) and w.text != "-"]
        if len(numbers) < 2:
            continue
        for key, category in LLP_KEYS:
            if key in text:
                specification = " ".join(w.text for w in line if w not in numbers[-2:])
                rows.append(
                    {
                        "category": category,
                        "specification": specification.replace("*", "").strip(),
                        "amount_billion_bdt": to_number(numbers[-2].text),
                        "share_pct": to_number(numbers[-1].text),
                        "is_non_performing": category in ("sub_standard", "doubtful", "bad"),
                    }
                )
                break
    return rows
