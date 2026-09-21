"""Unit tests for the per-MFI table extractors, on synthetic words shaped like the MRA pages.

The coordinates are made up; they reproduce the structure the parsers rely on: wrapped names, a
licence number under the name, cells on the serial number's line, ruled rows, and fund blocks
closed by a Total row."""

from kisti.extract import mfi_tables as m
from kisti.extract.pdf import Word


def w(text, x0, top, page=1):
    return Word(text, x0, x0 + 6 * len(text), top, page)


# --- grid tables -----------------------------------------------------------------------------

TABLE = m.GridTable(
    key="test",
    title="Test",
    columns=("a", "b"),
    ref_as=100,
    serial_max=100,
    name_lo=105,
    name_hi=200,
    numeric_lo=210,
    body_top=100,
    body_bottom=700,
)


def grid_page(shift=0.0, page=1):
    return [
        w("(As", 100 + shift, 50, page),
        # row 1: name wraps over two lines, licence beneath, cells on the serial line
        w("1", 80 + shift, 150, page),
        w("Alpha", 110 + shift, 140, page),
        w("Society", 140 + shift, 140, page),
        w("Foundation", 110 + shift, 150, page),
        w("00011-00022-00033", 110 + shift, 160, page),
        w("1.5", 215 + shift, 150, page),
        w("-", 260 + shift, 150, page),
        # row 2: the licence number is broken over two lines
        w("2", 80 + shift, 200, page),
        w("Beta", 110 + shift, 195, page),
        w("(B)00044-00055-", 110 + shift, 205, page),
        w("00066", 110 + shift, 213, page),
        w("2,500", 215 + shift, 200, page),
        w("3", 260 + shift, 200, page),
    ]


def test_extract_grid_reads_wrapped_names_licences_and_cells():
    rows = m.extract_grid({1: grid_page()}, TABLE)
    assert [(r.serial, r.name, r.license, r.values) for r in rows] == [
        (1, "Alpha Society Foundation", "00011-00022-00033", [1.5, None]),
        (2, "Beta (B)", "00044-00055-00066", [2500, 3]),
    ]
    assert all(not r.issues for r in rows)


def test_extract_grid_follows_the_page_shift():
    """Even and odd pages are printed at different horizontal offsets."""
    shifted = m.extract_grid({1: grid_page(shift=-11)}, TABLE)
    plain = m.extract_grid({1: grid_page()}, TABLE)
    assert [(r.name, r.license, r.values) for r in shifted] == [(r.name, r.license, r.values) for r in plain]


def test_extract_grid_flags_a_row_with_the_wrong_number_of_cells():
    page = [word for word in grid_page() if word.text != "3"]
    rows = m.extract_grid({1: page}, TABLE)
    assert rows[1].issues == ["expected 2 numeric cells, found 1"]


def test_extract_grid_uses_ruled_cells_when_the_table_has_them():
    """A name line closer to the next serial number still belongs to its own ruled row."""
    ruled = m.GridTable(**{**TABLE.__dict__, "use_separators": True})
    page = [
        w("(As", 100, 50),
        w("1", 80, 120),
        w("First", 110, 105),
        w("00011-00022-00033", 110, 150),  # far from row 1's serial line, but inside its cell
        w("1.5", 215, 120),
        w("2", 80, 160),
        w("Second", 110, 165),
        w("00044-00055-00066", 110, 175),
        w("2.5", 215, 160),
    ]
    rows = m.extract_grid({1: page}, ruled, separators={1: [155]})
    assert [(r.serial, r.name, r.license) for r in rows] == [
        (1, "First", "00011-00022-00033"),
        (2, "Second", "00044-00055-00066"),
    ]


def test_extract_grid_keeps_contact_words_out_of_the_name_column():
    """Words that start inside the name column but run into the next column are not name words."""
    bounded = m.GridTable(**{**TABLE.__dict__, "name_x1_max": 160})
    page = [word for word in grid_page() if word.text != "Society"]
    page.append(w("Address:", 150, 150))  # x0 inside the name column, x1 beyond its right edge
    page.append(w("Foundation", 110, 150))
    rows = m.extract_grid({1: page}, bounded)
    assert rows[0].name.startswith("Alpha")
    assert "Address:" not in rows[0].name


# --- fund composition ------------------------------------------------------------------------


def fund_row(label_words, values, top, page):
    label = [w(text, x, top, page) for text, x in label_words]
    numbers = [w(text, x, top, page) for text, x in zip(values, (374, 424, 473, 524))]
    return label + numbers


def test_extract_fund_closes_blocks_on_total_rows_across_a_page_break():
    page1 = [
        w("(As", 274, 50, 1),
        w("1", 96, 190, 1),
        w("Gamma", 117, 180, 1),
        w("00001-00002-00003", 117, 200, 1),
    ]
    page1 += fund_row([("Clients'", 262), ("Savings", 283)], ["100", "50%", "90", "45%"], 170, 1)
    page1 += fund_row([("Other", 262), ("Fund", 280)], ["100", "50%", "110", "55%"], 190, 1)
    page1 += fund_row([("Total", 262)], ["200", "100%", "200", "100%"], 210, 1)
    # the block for serial 2 starts at the bottom of page 1 and closes on page 2
    page1 += fund_row([("Cumulative", 262), ("Surplus", 294)], ["(30)", "10%", "-", "0%"], 300, 1)
    page2 = [
        w("(As", 274, 50, 2),
        w("2", 96, 150, 2),
        w("Delta", 117, 140, 2),
        w("00004-00005-00006", 117, 160, 2),
    ]
    page2 += fund_row([("Total", 262)], ["70", "100%", "200", "100%"], 170, 2)

    blocks = m.extract_fund({1: page1, 2: page2})
    assert len(blocks) == 2
    first = blocks[0]
    assert (first.serial, first.name, first.license) == (1, "Gamma", "00001-00002-00003")
    assert [t for t, _ in first.rows] == ["Clients' Savings", "Other Fund", "Total"]
    assert first.rows[0][1] == [100, 50, 90, 45]
    assert not first.issues
    second = blocks[1]
    assert [t for t, _ in second.rows] == ["Cumulative Surplus", "Total"]
    assert second.rows[0][1][0] == -30
    assert second.rows[0][1][2] is None
