"""Unit tests for the number, licence and line helpers, on synthetic input."""

import pytest

from kisti.extract.pdf import (
    Word,
    complete_license,
    group_lines,
    is_number,
    join_name,
    split_license,
    to_number,
)


def w(text, x0, top, page=1):
    return Word(text, x0, x0 + 6 * len(text), top, page)


# --- numbers and licences ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("-", None),
        ("1,234", 1234),
        ("1,10,781", 110781),
        ("12.50", 12.5),
        ("53.81%", 53.81),
        ("100%", 100),
        ("(4,187,481)", -4187481),
        ("-3.5", -3.5),
    ],
)
def test_to_number(token, expected):
    assert to_number(token) == expected
    assert is_number(token)


@pytest.mark.parametrize("token", ["Foundation", "(ALWO)", "01713000210,", "Jun-25", ""])
def test_is_number_rejects_text(token):
    assert not is_number(token)


def test_split_license_removes_it_from_the_name():
    assert split_license("Abalamban 21112-01012-00792") == ("Abalamban", "21112-01012-00792")


def test_split_license_joins_a_licence_broken_across_lines():
    name, licence = split_license("Access Toward (ALWO)00584-01897- 00244")
    assert (name, licence) == ("Access Toward (ALWO)", "00584-01897-00244")


def test_split_license_accepts_a_four_digit_middle_group_and_a_bracket_letter():
    assert split_license("A 21112-0174-00839")[1] == "21112-0174-00839"
    assert split_license("Sajida 00251-00155(K)-155")[1] == "00251-00155(K)-155"


def test_split_license_prefers_the_one_matching_the_short_number():
    text = "Neighbour 01666-00838-00508 Own name 01111-02222-00509"
    assert split_license(text, short_number=509)[1] == "01111-02222-00509"


def test_split_license_without_a_licence():
    assert split_license("Just a name") == ("Just a name", None)


def test_complete_license_from_short_number():
    assert complete_license("YWCA 04978-00711- Email:", 551) == "04978-00711-00551"
    assert complete_license("no prefix here", 551) is None
    assert complete_license("04978-00711-", None) is None


def test_group_lines_and_join_name_follow_reading_order():
    words = [w("Society", 140, 100), w("Alpha", 110, 101), w("Foundation", 110, 112)]
    assert [len(line) for line in group_lines(words)] == [2, 1]
    assert join_name(words) == "Alpha Society Foundation"
