"""Low-level helpers for reading positioned words out of the MRA report PDFs.

The per-MFI tables are laid out as a grid: a serial number, a name that wraps over several
lines with the licence number beneath it, and numeric columns. Plain text extraction loses
which line belongs to which row, so the extractors work from word coordinates instead.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

LICENSE_RE = re.compile(r"\d{5}\s*-\s*\d{4,5}(?:\([A-Za-z]+\))?\s*-\s*\d{2,5}")
NUMBER_RE = re.compile(r"^(?:-?\d+(?:,\d+)*(?:\.\d+)?%?|\(\d+(?:,\d+)*(?:\.\d+)?%?\))$")
MISSING = "-"


@dataclass(frozen=True)
class Word:
    text: str
    x0: float
    x1: float
    top: float
    page: int  # 1-based PDF page number

    @property
    def mid(self) -> float:
        return self.top + 4.5


def read_pages(pdf_path: Path, page_numbers: list[int]) -> dict[int, list[Word]]:
    """Positioned words for the given 1-based pages."""
    pages: dict[int, list[Word]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for number in page_numbers:
            words = pdf.pages[number - 1].extract_words()
            pages[number] = [Word(w["text"], w["x0"], w["x1"], w["top"], number) for w in words]
    return pages


def read_separators(
    pdf_path: Path, page_numbers: list[int], min_width: float = 450.0
) -> dict[int, list[float]]:
    """Vertical positions of the horizontal rules that separate table rows.

    The rules are drawn as one short segment per column, so segments at the same height are
    added up and only heights whose segments span most of the page count as a row separator.
    """
    separators: dict[int, list[float]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for number in page_numbers:
            span: dict[int, float] = defaultdict(float)
            for line in pdf.pages[number - 1].lines:
                if abs(line["bottom"] - line["top"]) < 1.5:
                    span[round(line["top"])] += abs(line["x1"] - line["x0"])
            separators[number] = sorted(top for top, width in span.items() if width > min_width)
    return separators


def page_texts(pdf_path: Path) -> list[str]:
    """Plain text of every page, used only to locate tables."""
    with pdfplumber.open(pdf_path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def is_number(token: str) -> bool:
    return token == MISSING or bool(NUMBER_RE.match(token))


def to_number(token: str) -> int | float | None:
    """Parse a printed number. `-` is a missing value, `%` is dropped, commas are removed and
    a number in brackets is negative."""
    token = token.strip()
    if token == MISSING or token == "":
        return None
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()").rstrip("%").replace(",", "")
    value = float(token) if "." in token else int(token)
    return -value if negative else value


def group_lines(words: list[Word], tolerance: float = 3.0) -> list[list[Word]]:
    """Group words into visual lines by their top coordinate, each line sorted left to right."""
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (w.top, w.x0)):
        if lines and abs(lines[-1][0].top - word.top) <= tolerance:
            lines[-1].append(word)
        else:
            lines.append([word])
    return [sorted(line, key=lambda w: w.x0) for line in lines]


def join_name(words: list[Word]) -> str:
    """Join the words of a wrapped name in reading order."""
    lines = group_lines(words)
    return " ".join(" ".join(w.text for w in line) for line in lines)


def split_license(text: str, short_number: int | None = None) -> tuple[str, str | None]:
    """Split a joined name-and-licence string into (name, licence).

    The licence number is sometimes broken across two printed lines, so whitespace after a
    hyphen is tolerated and then removed. If several licence numbers are present (a
    neighbouring row's leaks in), the one whose last group equals `short_number` wins.
    """
    matches = list(LICENSE_RE.finditer(text))
    if not matches:
        return " ".join(text.split()), None
    match = matches[0]
    if short_number is not None:
        for candidate in matches:
            if int(re.sub(r"\s+", "", candidate.group(0)).rsplit("-", 1)[1]) == short_number:
                match = candidate
                break
    licence = re.sub(r"\s+", "", match.group(0))
    name = (text[: match.start()] + " " + text[match.end() :]).strip()
    return " ".join(name.split()), licence


LICENSE_PREFIX_RE = re.compile(r"\d{5}\s*-\s*\d{4,5}(?:\([A-Za-z]+\))?\s*-")


def complete_license(text: str, short_number: int | None) -> str | None:
    """Rebuild a licence whose last group was printed on a different line, far from its prefix.

    The last group of a licence number is the same as the short licence number printed next
    to the serial number, so the two together identify the full licence.
    """
    match = LICENSE_PREFIX_RE.search(text)
    if not match or short_number is None:
        return None
    return re.sub(r"\s+", "", match.group(0)) + f"{short_number:05d}"


def nearest_anchor(word: Word, anchors: list[Word]) -> int:
    """Index of the anchor whose vertical position is closest to the word."""
    return min(range(len(anchors)), key=lambda i: abs(anchors[i].mid - word.mid))


def by_page(words: list[Word]) -> dict[int, list[Word]]:
    grouped: dict[int, list[Word]] = defaultdict(list)
    for word in words:
        grouped[word.page].append(word)
    return grouped
