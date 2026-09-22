"""The data contract between the Python pipeline and the dashboard.

Each entry maps a dataset name to the Python type each of its top-level fields (or, for a
list dataset, each record's fields) must have. `kisti.webdata.run` checks every file it writes
against this before writing it, and `web/src/lib/schema.ts` lists the same fields by hand — if
one side changes without the other, the dashboard breaks visibly (a missing field) rather than
silently, and `tests/test_webdata.py` fails first.
"""

from __future__ import annotations

# Field name -> the Python type it must have. `float | None` fields serialise to `number | null`.
Schema = dict[str, type | tuple]

META: Schema = {
    "edition": str,
    "generated_at": str,
    "mfis_in_basic": int,
    "mfis_active": int,
    "loan_outstanding_active_bdt": float,
}

KPI: Schema = {
    "n_mfis": int,
    "loan_outstanding_bdt": float,
    "borrowers_total": float,
    "clients_total": float,
    "savings_bdt": float,
    "branches_total": float,
}

CONCENTRATION_ROW: Schema = {
    "measure": str,
    "n_mfis": int,
    "top1_share_pct": float,
    "top4_share_pct": float,
    "top10_share_pct": float,
    "hhi": float,
    "gini": float,
}

LORENZ_POINT: Schema = {"institutions": float, "share": float}

BAND_ROW: Schema = {"size_band": str, "n_mfis": int}  # each dataset adds its own numeric columns

MFI_RECORD: Schema = {
    "license_no": int,
    "name": str,
    "size_band": (str, type(None)),
    "branches": (float, type(None)),
    "employees_total": (float, type(None)),
    "clients_total": (float, type(None)),
    "borrowers_total": float,
    "female_client_share_pct": (float, type(None)),
    "savings_bdt": (float, type(None)),
    "loan_outstanding_bdt": float,
    "avg_loan_size_bdt": float,
    "has_ratios": bool,
    "portfolio_yield": (float, type(None)),
    "operating_self_sufficiency": (float, type(None)),
    "return_on_assets": (float, type(None)),
    "total_operating_cost_ratio": (float, type(None)),
    "borrowing_to_loan_outstanding": (float, type(None)),
    "capital_fund_to_loan_outstanding": (float, type(None)),
    "has_funds": bool,
    "savings_share_of_funds_pct": (float, type(None)),
    "yield_percentile_in_band": (float, type(None)),
    "oss_percentile_in_band": (float, type(None)),
    "cost_percentile_in_band": (float, type(None)),
    "group": (int, type(None)),
    "flagged": bool,
}

DISTRICT_RECORD: Schema = {
    "division": str,
    "district": str,
    "population": float,
    "households": float,
    "branches": float,
    "members": float,
    "borrowers": float,
    "loan_outstanding_bdt": float,
    "members_per_1000": float,
    "borrowers_per_1000": float,
    "loan_outstanding_per_person_bdt": float,
    "avg_loan_size_bdt": float,
    "branches_per_100k": float,
    "financial_account_pct": float,
    "mobile_banking_pct": float,
}

DIVISION_RECORD: Schema = {
    "division": str,
    "population": float,
    "members": float,
    "borrowers": float,
    "loan_outstanding_bdt": float,
    "borrowers_per_1000": float,
    "loan_outstanding_per_person_bdt": float,
}


def check_record(record: dict, schema: Schema, where: str) -> list[str]:
    """Field-by-field type errors, empty if the record matches the schema exactly (no extra,
    no missing, no wrong type; bool is checked separately since it is a subtype of int)."""
    errors = []
    missing = schema.keys() - record.keys()
    extra = record.keys() - schema.keys()
    if missing:
        errors.append(f"{where}: missing fields {sorted(missing)}")
    if extra:
        errors.append(f"{where}: unexpected fields {sorted(extra)}")
    for field, expected in schema.items():
        if field not in record:
            continue
        value = record[field]
        types = expected if isinstance(expected, tuple) else (expected,)
        ok = any(
            (t is bool and isinstance(value, bool))
            or (t is float and isinstance(value, (int, float)) and not isinstance(value, bool))
            or (t not in (bool, float) and isinstance(value, t))
            for t in types
        )
        if not ok:
            errors.append(f"{where}.{field}: expected {expected}, got {type(value).__name__} ({value!r})")
    return errors


def check_records(records: list[dict], schema: Schema, name: str) -> list[str]:
    errors = []
    for i, record in enumerate(records):
        errors.extend(check_record(record, schema, f"{name}[{i}]"))
    return errors
