"""Tests for the dashboard data contract: kisti.webdata.schema, the export, and the committed
files in web/public/data/. If a field is renamed on the Python side without updating the
TypeScript types in web/src/lib/schema.ts, this file will not catch that — see
web/src/lib/schema.test.ts for the other half of the contract."""

import json
from pathlib import Path

import pytest

from kisti.webdata import schema as s
from kisti.webdata.run import OUT, build, deep_clean, validate, with_percentiles_and_groups
from kisti.webdata.schema import check_record, check_records


def test_check_record_reports_missing_extra_and_wrong_type_fields():
    schema = {"a": int, "b": (float, type(None))}
    assert check_record({"a": 1, "b": 2.0}, schema, "x") == []
    assert check_record({"a": 1, "b": None}, schema, "x") == []  # matches the None alternative
    assert check_record({"a": 1}, schema, "x") == ["x: missing fields ['b']"]
    assert check_record({"a": 1, "b": 2.0, "c": 3}, schema, "x") == ["x: unexpected fields ['c']"]
    assert check_record({"a": "1", "b": 2.0}, schema, "x")[0].startswith("x.a: expected")


def test_check_record_treats_int_as_a_valid_float_but_not_bool_as_a_valid_float():
    assert check_record({"a": 1}, {"a": float}, "x") == []
    assert check_record({"a": True}, {"a": float}, "x") != []  # bool is an int subtype in Python
    assert check_record({"a": True}, {"a": bool}, "x") == []


def test_check_records_indexes_each_row():
    errors = check_records([{"a": 1}, {}], {"a": int}, "rows")
    assert errors == ["rows[1]: missing fields ['a']"]


@pytest.fixture(scope="module")
def datasets():
    return build()


def test_every_declared_dataset_passes_its_own_schema(datasets):
    for dataset in datasets:
        assert validate(dataset) == [], dataset.name


def test_mfi_count_and_licence_uniqueness(datasets):
    mfis = next(d for d in datasets if d.name == "mfis").payload
    assert len(mfis) == 644
    assert len({m["license_no"] for m in mfis}) == 644
    assert all(m["borrowers_total"] > 0 and m["loan_outstanding_bdt"] > 0 for m in mfis)


def test_district_count_matches_the_64_districts(datasets):
    districts = next(d for d in datasets if d.name == "districts").payload
    assert len(districts) == 64
    assert len({d["district"] for d in districts}) == 64


def test_meta_matches_the_mfi_and_district_datasets(datasets):
    meta = next(d for d in datasets if d.name == "meta").payload
    mfis = next(d for d in datasets if d.name == "mfis").payload
    assert meta["mfis_active"] == len(mfis) == 644
    assert meta["mfis_in_basic"] == 693


def test_deep_clean_turns_nan_and_pd_na_into_none_and_keeps_ordinary_values():
    import numpy as np
    import pandas as pd

    payload = {"a": float("nan"), "b": pd.NA, "c": np.float64(1.5), "d": [np.int64(3), None], "e": "text"}
    cleaned = deep_clean(payload)
    assert cleaned == {"a": None, "b": None, "c": 1.5, "d": [3, None], "e": "text"}
    assert isinstance(cleaned["c"], float) and isinstance(cleaned["d"][0], int)


def test_percentile_and_group_columns_are_within_range():
    from kisti.analysis.data import load

    active = load()
    active = active[active["is_active"]]
    frame = with_percentiles_and_groups(active)
    percentiles = frame[["yield_percentile_in_band", "oss_percentile_in_band", "cost_percentile_in_band"]]
    finite = percentiles.dropna()
    assert ((finite >= 0) & (finite <= 100)).all().all()
    assert frame["group"].dropna().isin([1, 2, 3, 4, 5, 6]).all()
    assert frame["flagged"].dtype == bool


def test_json_is_valid_and_matches_the_schemas(datasets):
    """Round-trips every payload through json.dumps/loads (catches non-serialisable values that
    `deep_clean` missed) and re-validates the parsed copy."""
    for dataset in datasets:
        cleaned = deep_clean(dataset.payload)
        parsed = json.loads(json.dumps(cleaned))
        dataset.payload = parsed
        assert validate(dataset) == [], dataset.name


# --- the committed files in web/public/data/ ------------------------------------------------


@pytest.fixture(scope="module")
def committed_manifest():
    manifest_path = OUT / "manifest.json"
    if not manifest_path.exists():
        pytest.skip("web/public/data/ not generated in this checkout; run `make webdata`")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def test_committed_manifest_lists_exactly_the_committed_files(committed_manifest):
    on_disk = sorted(p.name for p in OUT.glob("*.json") if p.name != "manifest.json")
    assert committed_manifest == on_disk


def assert_json_close(committed, fresh, path: str = "") -> None:
    """Recursive equality that tolerates the last-bit floating-point differences that k-means and
    silhouette_score can produce across BLAS backends (observed between macOS/Accelerate and the
    OpenBLAS used in CI): same clusters, numerically equivalent sums, different rounding."""
    if isinstance(committed, float) or isinstance(fresh, float):
        assert committed == pytest.approx(fresh, rel=1e-9, abs=1e-9), path
    elif isinstance(committed, dict):
        assert isinstance(fresh, dict) and committed.keys() == fresh.keys(), path
        for key in committed:
            assert_json_close(committed[key], fresh[key], f"{path}.{key}")
    elif isinstance(committed, list):
        assert isinstance(fresh, list) and len(committed) == len(fresh), path
        for i, (c, f) in enumerate(zip(committed, fresh)):
            assert_json_close(c, f, f"{path}[{i}]")
    else:
        assert committed == fresh, path


def test_committed_files_are_current(committed_manifest, datasets):
    """Every value except `generated_at` must match a fresh export, up to floating-point noise."""
    for dataset in datasets:
        committed = json.loads((OUT / f"{dataset.name}.json").read_text(encoding="utf-8"))
        fresh = json.loads(json.dumps(deep_clean(dataset.payload)))
        if isinstance(committed, dict) and "generated_at" in committed:
            committed = {**committed, "generated_at": None}
            fresh = {**fresh, "generated_at": None}
        assert_json_close(committed, fresh, dataset.name)


def test_schema_module_covers_every_top_level_field_used_by_the_export():
    """A change to MFI_COLUMNS or DISTRICT_COLUMNS that forgets to update the schema fails here,
    not only when the export runs."""
    from kisti.webdata.run import DISTRICT_COLUMNS, MFI_COLUMNS

    assert set(MFI_COLUMNS) == set(s.MFI_RECORD)
    assert set(DISTRICT_COLUMNS) == set(s.DISTRICT_RECORD)


def test_out_path_is_under_the_web_public_data_directory():
    assert OUT == Path(__file__).resolve().parents[1] / "web" / "public" / "data"
