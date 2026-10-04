"""Build the dashboard's district map from the official boundaries.

    python scripts/build_district_map.py     # writes web/public/geo/bd-districts.json

Reads the geoBoundaries ADM2 file listed in data/source-manifest.json (fetch it with
`make fetch`), projects it, simplifies each ring, and writes one SVG path per district under
the district names the dashboard uses, so the page draws the map without a mapping library.
Standard library only.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "real" / "raw" / "geoboundaries_bgd_adm2_simplified.geojson"
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


def build(source: dict, names: set[str]) -> dict:
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

    districts = []
    for feature in features:
        name = RENAME.get(feature["properties"]["shapeName"], feature["properties"]["shapeName"])
        parts = []
        best_area, label_at = -1.0, (0.0, 0.0)
        for ring in rings_of(feature["geometry"]):
            points = simplify([project(lon, lat) for lon, lat in ring], TOLERANCE_PX)
            area = ring_area(points)
            if len(points) < 4 or area < MIN_RING_AREA_PX:
                continue
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points[:-1]) + "Z")
            if area > best_area:  # label at the centre of the largest ring's vertices
                best_area = area
                label_at = (sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points))
        label = [round(label_at[0], 1), round(label_at[1], 1)]
        districts.append({"district": name, "path": "".join(parts), "label": label})

    found = {d["district"] for d in districts}
    if found != names:
        raise SystemExit(
            "district names differ from districts.json: "
            f"missing {sorted(names - found)}, extra {sorted(found - names)}"
        )

    return {
        "source": "Bangladesh Bureau of Statistics (BBS) and OCHA ROAP, via geoBoundaries (gbOpen BGD ADM2)",
        "license": "CC BY 3.0 IGO",
        "viewBox": [0, 0, WIDTH, height],
        "districts": sorted(districts, key=lambda d: d["district"]),
    }


def main() -> int:
    if not SOURCE.exists():
        print(f"{SOURCE.relative_to(ROOT)} is missing; run `make fetch` first.", file=sys.stderr)
        return 1
    names = {row["district"] for row in json.loads(DISTRICTS.read_text(encoding="utf-8"))}
    result = build(json.loads(SOURCE.read_text(encoding="utf-8")), names)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} ({size_kb:.0f} KB, {len(result['districts'])} districts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
