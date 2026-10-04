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


def test_every_district_has_a_closed_path_inside_the_view_box():
    data = load(MAP)
    _, _, width, height = data["viewBox"]
    for shape in data["districts"]:
        assert shape["path"].startswith("M") and shape["path"].endswith("Z"), shape["district"]
        coordinates = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", shape["path"])]
        xs, ys = coordinates[0::2], coordinates[1::2]
        assert 0 <= min(xs) and max(xs) <= width, shape["district"]
        assert 0 <= min(ys) and max(ys) <= height, shape["district"]


def test_map_carries_its_attribution():
    data = load(MAP)
    assert "BBS" in data["source"] and "geoBoundaries" in data["source"]
    assert data["license"] == "CC BY 3.0 IGO"
