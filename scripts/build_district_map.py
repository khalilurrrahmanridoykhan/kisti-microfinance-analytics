"""Build the dashboard's district map from the official boundaries.

    python scripts/build_district_map.py     # writes web/public/geo/bd-districts.json

Reads the geoBoundaries ADM2 (district) and ADM1 (division) files listed in
data/source-manifest.json (fetch them with `make fetch`), projects both with the same
projection, simplifies each ring, and writes one SVG path, label point and bounding box per
district and per division under the names the dashboard uses, so the page draws and zooms the
map without a mapping library. Standard library only.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "real" / "raw" / "geoboundaries_bgd_adm2_simplified.geojson"
DIVISION_SOURCE = ROOT / "data" / "real" / "raw" / "geoboundaries_bgd_adm1_simplified.geojson"
DISTRICTS = ROOT / "web" / "public" / "data" / "districts.json"
OUT = ROOT / "web" / "public" / "geo" / "bd-districts.json"

# geoBoundaries keeps the pre-2018 English spellings; the census tables (and so the dashboard)
# use the current official ones.
RENAME = {
    "Brahamanbaria": "Brahmanbaria",
    "Chittagong": "Chattogram",
    "Comilla": "Cumilla",
    "Jessore": "Jashore",
    "Nawabganj": "Chapai Nababganj",
}
DIVISION_RENAME = {
    "Barisal": "Barishal",
    "Chittagong": "Chattogram",
    "Rajshani": "Rajshahi",  # misspelt in the geoBoundaries release
}

WIDTH = 600  # viewBox width in px; the height follows from the projection
PADDING = 8
TOLERANCE_PX = 0.6  # Douglas-Peucker tolerance in viewBox px: well under a screen pixel at the size shown
MIN_RING_AREA_PX = 1.5  # drop specks (tiny char islands) that would render as a dot


def rings_of(geometry: dict) -> list[list[list[float]]]:
    """Every outer and inner ring of a Polygon or MultiPolygon, as [lon, lat] lists."""
    if geometry["type"] == "Polygon":
        return list(geometry["coordinates"])
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    raise ValueError(f"unexpected geometry type {geometry['type']}")


def simplify(points: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    """Douglas-Peucker, iterative so long coastlines cannot hit the recursion limit."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        (x1, y1), (x2, y2) = points[start], points[end]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        worst, worst_index = -1.0, -1
        for i in range(start + 1, end):
            px, py = points[i]
            if length == 0:
                distance = math.hypot(px - x1, py - y1)
            else:
                distance = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / length
            if distance > worst:
                worst, worst_index = distance, i
        if worst > tolerance:
            keep[worst_index] = True
            stack.extend([(start, worst_index), (worst_index, end)])
    return [p for p, k in zip(points, keep) if k]


def ring_area(points: list[tuple[float, float]]) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]))) / 2


def shape(feature: dict, project, name: str) -> dict:
    """One feature as an SVG path, a label point, and a bounding box, all in viewBox px."""
    parts = []
    best_area, label_at = -1.0, (0.0, 0.0)
    xs: list[float] = []
    ys: list[float] = []
    for ring in rings_of(feature["geometry"]):
        points = simplify([project(lon, lat) for lon, lat in ring], TOLERANCE_PX)
        area = ring_area(points)
        if len(points) < 4 or area < MIN_RING_AREA_PX:
            continue
        parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points[:-1]) + "Z")
        xs.extend(x for x, _ in points)
        ys.extend(y for _, y in points)
        if area > best_area:  # label at the centre of the largest ring's vertices
            best_area = area
            label_at = (sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points))
    return {
        "name": name,
        "path": "".join(parts),
        "label": [round(label_at[0], 1), round(label_at[1], 1)],
        "bbox": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
    }


def check_names(kind: str, found: set[str], expected: set[str]) -> None:
    if found != expected:
        raise SystemExit(
            f"{kind} names differ from districts.json: "
            f"missing {sorted(expected - found)}, extra {sorted(found - expected)}"
        )


def build(source: dict, division_source: dict, districts_data: list[dict]) -> dict:
    features = source["features"]
    lons = [lon for f in features for ring in rings_of(f["geometry"]) for lon, _ in ring]
    lats = [lat for f in features for ring in rings_of(f["geometry"]) for _, lat in ring]
    # Equirectangular with the x axis shrunk by cos(mid-latitude): Bangladesh spans under 6
    # degrees of latitude, so this is visually indistinguishable from a conformal projection.
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))
    span_x = (max(lons) - min(lons)) * k
    span_y = max(lats) - min(lats)
    scale = (WIDTH - 2 * PADDING) / span_x
    height = math.ceil(span_y * scale + 2 * PADDING)

    def project(lon: float, lat: float) -> tuple[float, float]:
        return (PADDING + (lon - min(lons)) * k * scale, PADDING + (max(lats) - lat) * scale)

    division_of = {row["district"]: row["division"] for row in districts_data}
    districts = []
    for feature in features:
        name = RENAME.get(feature["properties"]["shapeName"], feature["properties"]["shapeName"])
        item = shape(feature, project, name)
        districts.append({"district": name, "division": division_of.get(name, ""), **_without_name(item)})
    check_names("district", {d["district"] for d in districts}, set(division_of))

    divisions = []
    for feature in division_source["features"]:
        raw = feature["properties"]["shapeName"]
        name = DIVISION_RENAME.get(raw, raw)
        divisions.append({"division": name, **_without_name(shape(feature, project, name))})
    check_names("division", {d["division"] for d in divisions}, set(division_of.values()))

    return {
        "source": (
            "Bangladesh Bureau of Statistics (BBS) and OCHA ROAP, "
            "via geoBoundaries (gbOpen BGD ADM1 and ADM2)"
        ),
        "license": "CC BY 3.0 IGO",
        "viewBox": [0, 0, WIDTH, height],
        "districts": sorted(districts, key=lambda d: d["district"]),
        "divisions": sorted(divisions, key=lambda d: d["division"]),
    }


def _without_name(item: dict) -> dict:
    return {key: value for key, value in item.items() if key != "name"}


def main() -> int:
    for path in (SOURCE, DIVISION_SOURCE):
        if not path.exists():
            print(f"{path.relative_to(ROOT)} is missing; run `make fetch` first.", file=sys.stderr)
            return 1
    result = build(
        json.loads(SOURCE.read_text(encoding="utf-8")),
        json.loads(DIVISION_SOURCE.read_text(encoding="utf-8")),
        json.loads(DISTRICTS.read_text(encoding="utf-8")),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    counts = f"{len(result['districts'])} districts, {len(result['divisions'])} divisions"
    print(f"wrote {OUT.relative_to(ROOT)} ({size_kb:.0f} KB, {counts})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
