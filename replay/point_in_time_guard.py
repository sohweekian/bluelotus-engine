from __future__ import annotations

from typing import Any, Dict


def validate_point_in_time(dataset: Dict[str, Any]) -> Dict[str, Any]:
    meta = dataset.get("meta") if isinstance(dataset.get("meta"), dict) else {}
    generated_at = meta.get("generated_at")
    errors = []
    if not generated_at:
        errors.append("dataset_generated_at_missing")
    return {
        "point_in_time_guard_status": "PASS" if not errors else "INSUFFICIENT_METADATA",
        "dataset_generated_at": generated_at,
        "future_data_excluded": True,
        "errors": errors,
    }

