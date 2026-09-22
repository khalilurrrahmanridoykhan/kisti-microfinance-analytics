"""Build the JSON files the dashboard reads.

    python -m kisti.webdata            # writes web/public/data/*.json

Every file is checked against `kisti.webdata.schema` before being written, and every number in
it traces back to `kisti.analysis` (phase MF2) — this module only reshapes and validates.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis import peers, pricing, quality
from ..analysis.concentration import loan_lorenz
from ..analysis.data import BAND_EDGES, BAND_LABELS
from ..analysis.report import compute
from ..extract.run import EDITION
from . import schema as s

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "web" / "public" / "data"

# Ratios percentiled within each MFI's size band, for the benchmark page.
PERCENTILE_COLUMNS = {
    "portfolio_yield": "yield_percentile_in_band",
    "operating_self_sufficiency": "oss_percentile_in_band",
    "total_operating_cost_ratio": "cost_percentile_in_band",
}

MFI_COLUMNS = [
    "license_no",
    "name",
    "size_band",
    "branches",
    "employees_total",
    "clients_total",
    "borrowers_total",
    "female_client_share_pct",
    "savings_bdt",
    "loan_outstanding_bdt",
    "avg_loan_size_bdt",
    "has_ratios",
    "portfolio_yield",
    "operating_self_sufficiency",
    "return_on_assets",
    "total_operating_cost_ratio",
    "borrowing_to_loan_outstanding",
    "capital_fund_to_loan_outstanding",
    "has_funds",
    "savings_share_of_funds_pct",
    *PERCENTILE_COLUMNS.values(),
    "group",
    "flagged",
]

DISTRICT_COLUMNS = list(s.DISTRICT_RECORD)
DIVISION_COLUMNS = list(s.DIVISION_RECORD)


def clean(value):
    """A JSON-safe scalar: NaN/NaT/pd.NA become None, numpy and pandas scalars become plain
    Python ones (checked in this order, since pd.isna on some scalars raises for non-scalars)."""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and (pd.isna(value) or np.isinf(value)):
        return None
    if isinstance(value, np.generic):
        value = value.item()
    return value


def deep_clean(value):
    """Recursively apply `clean` through dicts and lists, so a numpy scalar or NaN nested inside
    a plain dict (as every summary dict from `kisti.analysis` is) still serialises safely."""
    if isinstance(value, dict):
        return {k: deep_clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [deep_clean(v) for v in value]
    return clean(value)


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    return [{c: clean(row[c]) for c in columns} for row in frame[columns].to_dict("records")]


def with_percentiles_and_groups(active: pd.DataFrame) -> pd.DataFrame:
    """Add each MFI's percentile rank within its size band, its peer group (where clustered),
    and whether it fails a data-quality plausibility check."""
    frame = active.copy()
    for column, out in PERCENTILE_COLUMNS.items():
        frame[out] = frame.groupby("size_band", observed=True)[column].rank(pct=True) * 100
    grouped, _, _ = peers.cluster(active)  # a subset: complete ratios, no implausible value
    frame["group"] = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    frame.loc[grouped.index, "group"] = grouped["group"].astype("Int64")
    frame["flagged"] = quality.implausible(frame)
    return frame


@dataclass
class Dataset:
    name: str
    payload: object
    schema: s.Schema | None = None
    is_list: bool = False


def kpis(frame: pd.DataFrame) -> dict:
    return {
        "n_mfis": int(len(frame)),
        "loan_outstanding_bdt": float(frame["loan_outstanding_bdt"].sum()),
        "borrowers_total": float(frame["borrowers_total"].sum()),
        "clients_total": float(frame["clients_total"].sum()),
        "savings_bdt": float(frame["savings_bdt"].sum()),
        "branches_total": float(frame["branches"].sum()),
    }


def build() -> list[Dataset]:
    ctx = compute()
    active = ctx["active"]
    now = datetime.now(UTC).isoformat(timespec="seconds")

    meta = {
        "edition": EDITION,
        "generated_at": now,
        "mfis_in_basic": ctx["coverage"]["mfis_in_basic"],
        "mfis_active": ctx["coverage"]["mfis_active"],
        "loan_outstanding_active_bdt": float(active["loan_outstanding_bdt"].sum()),
    }

    sector = {
        "kpis": kpis(active),
        "coverage": ctx["coverage"],
        "concentration": ctx["concentration"].to_dict("records"),
        "lorenz": loan_lorenz(active).to_dict("records"),
        "largest_mfis": ctx["largest"].to_dict("records"),
        "oss_by_band": ctx["oss_band"].to_dict("records"),
        "oss_overall": ctx["oss_overall"],
        "what_separates": ctx["separates"].to_dict("records"),
        "efficiency_by_band": ctx["efficiency_band"].to_dict("records"),
        "efficiency_correlations": ctx["efficiency_corr"].to_dict("records"),
        "yield_distribution": ctx["yield"],
        "yield_by_band": ctx["yield_band"].to_dict("records"),
        "yield_vs_oss": ctx["yield_oss"],
        "reference_ceiling_pct": pricing.REFERENCE_CEILING_PCT,
        "funding_change": ctx["funding_change"].to_dict("records"),
        "funding_by_band": ctx["funding_band"].to_dict("records"),
        "funding_typical": ctx["funding_typical"],
        "outreach_sector": ctx["outreach_sector"],
        "outreach_typical": ctx["outreach_typical"],
        "outreach_by_band": ctx["outreach_band"].to_dict("records"),
        "quality_flags": ctx["quality_flags"].to_dict("records"),
        "peer_groups": ctx["groups"].to_dict("records"),
        "peer_silhouette": ctx["silhouettes"].to_dict("records"),
        "screening": ctx["screening"],
        "geo_summary": ctx["geo"],
    }

    mfis = with_percentiles_and_groups(active)
    mfi_records = records(mfis, MFI_COLUMNS)

    districts = ctx["districts"]
    division_records = records(ctx["divisions"], DIVISION_COLUMNS)
    district_records = records(districts, DISTRICT_COLUMNS)

    methods = {
        "reference_ceiling_pct": pricing.REFERENCE_CEILING_PCT,
        "reference_ceiling_note": (
            "The press has reported a 24% ceiling on microcredit interest since 2019; MRA's own "
            "notification was not located, so the current value is unconfirmed. Used only as a "
            "reference line, never as a compliance check."
        ),
        "size_bands": [
            {
                "label": label,
                "min_bdt": (None if edge == 0 else edge),
                "max_bdt": (None if np.isinf(nxt) else nxt),
            }
            for label, edge, nxt in zip(BAND_LABELS, BAND_EDGES[:-1], BAND_EDGES[1:])
        ],
        "screening_rule": {
            "borrowing_threshold_pct": peers.WATCH_BORROWING_PCT,
            "note": (
                "MFIs with operating self-sufficiency below 100% and borrowing at or above "
                f"{peers.WATCH_BORROWING_PCT:.0f}% of loan outstanding. A filter on financial-structure "
                "ratios, not a measure of delinquency; reported as counts only, never as a named list."
            ),
        },
        "coverage": ctx["coverage"],
    }

    return [
        Dataset("meta", meta, s.META),
        Dataset("sector", sector, None),
        Dataset("mfis", mfi_records, s.MFI_RECORD, is_list=True),
        Dataset("districts", district_records, s.DISTRICT_RECORD, is_list=True),
        Dataset("divisions", division_records, s.DIVISION_RECORD, is_list=True),
        Dataset("methods", methods, None),
    ]


def validate(dataset: Dataset) -> list[str]:
    if dataset.schema is None:
        return []
    if dataset.is_list:
        return s.check_records(dataset.payload, dataset.schema, dataset.name)
    return s.check_record(dataset.payload, dataset.schema, dataset.name)


def write(datasets: list[Dataset], outdir: Path = OUT) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for dataset in datasets:
        dataset.payload = deep_clean(dataset.payload)
    errors = []
    for dataset in datasets:
        errors.extend(validate(dataset))
    if errors:
        raise ValueError("webdata contract violated:\n" + "\n".join(errors))
    manifest = []
    for dataset in datasets:
        filename = f"{dataset.name}.json"
        (outdir / filename).write_text(
            json.dumps(dataset.payload, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        manifest.append(filename)
    (outdir / "manifest.json").write_text(json.dumps(sorted(manifest), indent=2) + "\n", encoding="utf-8")


def main() -> int:
    datasets = build()
    write(datasets)
    for dataset in datasets:
        size = "list" if dataset.is_list else "object"
        print(f"  wrote {dataset.name}.json ({size})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
