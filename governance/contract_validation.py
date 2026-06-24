"""Lightweight JSON contract validation (no external jsonschema dependency)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def project_root() -> Path:
    import os
    env = os.environ.get("BLUELOTUS_PROJECT_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


DATASET_REQUIRED_TOP = (
    "meta",
    "regime",
    "portfolio",
    "execution",
    "cio_decisions",
)

DATASET_META_REQUIRED = ("generated_at", "market_session")

EXECUTION_REQUIRED = (
    "execution_authority",
    "order_routing_enabled",
)

DELIVERY_REQUIRED_TOP = (
    "delivery_status",
    "generator_version",
    "operating_truth",
    "consistency_discipline",
)

DELIVERY_OT_REQUIRED = (
    "cio_action",
    "report_readiness",
    "execution_authority",
    "order_routing_enabled",
    "orders_generated_by_pipeline",
)


def _check_keys(obj: Dict[str, Any], required: Tuple[str, ...], prefix: str) -> List[str]:
    errors: List[str] = []
    for key in required:
        if key not in obj:
            errors.append(f"{prefix} missing required key: {key}")
    return errors


def validate_dataset_contract(path: Path) -> Dict[str, Any]:
    errors: List[str] = []
    if not path.exists():
        return {"ok": False, "path": str(path), "errors": ["file not found"]}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(path), "errors": [f"json parse error: {exc}"]}
    if not isinstance(data, dict):
        return {"ok": False, "path": str(path), "errors": ["root must be object"]}

    errors.extend(_check_keys(data, DATASET_REQUIRED_TOP, "dataset"))
    meta = data.get("meta") or {}
    if isinstance(meta, dict):
        errors.extend(_check_keys(meta, DATASET_META_REQUIRED, "dataset.meta"))
    execution = data.get("execution") or {}
    if isinstance(execution, dict):
        errors.extend(_check_keys(execution, EXECUTION_REQUIRED, "dataset.execution"))
        if execution.get("execution_authority") not in (None, "CIO_ONLY_MANUAL"):
            errors.append("dataset.execution.execution_authority must be CIO_ONLY_MANUAL")
        if execution.get("order_routing_enabled") is True:
            errors.append("dataset.execution.order_routing_enabled must be False")

    return {"ok": not errors, "path": str(path), "errors": errors}


def validate_delivery_contract(path: Path) -> Dict[str, Any]:
    errors: List[str] = []
    if not path.exists():
        return {"ok": False, "path": str(path), "errors": ["file not found"]}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "path": str(path), "errors": [f"json parse error: {exc}"]}
    if not isinstance(data, dict):
        return {"ok": False, "path": str(path), "errors": ["root must be object"]}

    errors.extend(_check_keys(data, DELIVERY_REQUIRED_TOP, "delivery"))
    ot = data.get("operating_truth") or {}
    if isinstance(ot, dict):
        errors.extend(_check_keys(ot, DELIVERY_OT_REQUIRED, "delivery.operating_truth"))
        if ot.get("execution_authority") != "CIO_ONLY_MANUAL":
            errors.append("delivery.operating_truth.execution_authority must be CIO_ONLY_MANUAL")
        if ot.get("order_routing_enabled") is True:
            errors.append("delivery.operating_truth.order_routing_enabled must be False")
        if int(ot.get("orders_generated_by_pipeline") or 0) != 0:
            errors.append("delivery.operating_truth.orders_generated_by_pipeline must be 0")

    cd = data.get("consistency_discipline") or {}
    if isinstance(cd, dict) and "live_truth_consistency" not in cd:
        errors.append("delivery.consistency_discipline missing live_truth_consistency")

    return {"ok": not errors, "path": str(path), "errors": errors}


def run_all_contract_validations(root: Path | None = None) -> Dict[str, Any]:
    root = root or project_root()
    dataset_result = validate_dataset_contract(root / "data" / "frontend" / "dataset_raw.json")
    delivery_result = validate_delivery_contract(root / "research" / "research_report_delivery_latest.json")
    ok = dataset_result["ok"] and delivery_result["ok"]
    return {
        "ok": ok,
        "dataset": dataset_result,
        "delivery": delivery_result,
        "errors": (dataset_result.get("errors") or []) + (delivery_result.get("errors") or []),
    }
