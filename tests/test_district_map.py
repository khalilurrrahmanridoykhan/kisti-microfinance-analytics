"""The committed district map must cover exactly the districts the dashboard reports on."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "web" / "public" / "geo" / "bd-districts.json"
DISTRICTS = ROOT / "web" / "public" / "data" / "districts.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_map_names_match_the_district_data():
    shapes = {d["district"] for d in load(MAP)["districts"]}
    assert shapes == {row["district"] for row in load(DISTRICTS)}
    assert len(shapes) == 64


def test_divisions_match_the_district_data_and_each_district_names_its_division():
    data = load(MAP)
    rows = {row["district"]: row["division"] for row in load(DISTRICTS)}
    assert {d["division"] for d in data["divisions"]} == set(rows.values())
    assert len(data["divisions"]) == 8
    for shape in data["districts"]:
        assert shape["division"] == rows[shape["district"]], shape["district"]


def test_every_shape_has_a_closed_path_and_a_bounding_box_inside_the_view_box():
    data = load(MAP)
    _, _, width, height = data["viewBox"]
    for shape in data["districts"] + data["divisions"]:
        name = shape.get("district", shape.get("division"))
        assert shape["path"].startswith("M") and shape["path"].endswith("Z"), name
        coordinates = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", shape["path"])]
        xs, ys = coordinates[0::2], coordinates[1::2]
        assert 0 <= min(xs) and max(xs) <= width, name
        assert 0 <= min(ys) and max(ys) <= height, name
        assert shape["bbox"] == [min(xs), min(ys), max(xs), max(ys)], name


def test_map_carries_its_attribution():
    data = load(MAP)
    assert "BBS" in data["source"] and "geoBoundaries" in data["source"]
    assert data["license"] == "CC BY 3.0 IGO"
