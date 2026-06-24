"""90-day hot retention and weekly calibration aggregates."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from learning.constants import HOT_RETENTION_DAYS, WEEKLY_AGGREGATE_DAYS
from learning.outcome_engine import read_resolutions
from learning.paths import claims_path, weekly_calibration_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def apply_retention(*, root: Path | None = None) -> Dict[str, Any]:
    """Drop hot claim detail older than HOT_RETENTION_DAYS; keep weekly aggregates."""
    path = claims_path(root)
    if not path.exists():
        return {"pruned": 0, "kept": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=HOT_RETENTION_DAYS)
    kept: List[Dict[str, Any]] = []
    pruned = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            created = _parse_dt(str(row.get("created_at") or ""))
            if created < cutoff and row.get("resolution_status") in ("RESOLVED", "EXPIRED"):
                pruned += 1
                continue
            kept.append(row)

    with path.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    agg = build_weekly_calibration(root=root)
    return {"pruned": pruned, "kept": len(kept), "weekly_calibration": agg}


def build_weekly_calibration(*, root: Path | None = None) -> Dict[str, Any]:
    resolutions = read_resolutions(root=root)
    if not resolutions:
        return {"status": "NO_DATA", "modules": {}}

    by_module: Dict[str, List[float]] = defaultdict(list)
    for row in resolutions:
        if row.get("resolution_status") != "RESOLVED":
            continue
        mod = str(row.get("module") or "unknown")
        brier = row.get("brier_score")
        if brier is not None:
            by_module[mod].append(float(brier))

    summary: Dict[str, Any] = {"status": "OK", "generated_at": _utc_now(), "modules": {}}
    for mod, scores in by_module.items():
        if not scores:
            continue
        summary["modules"][mod] = {
            "resolved_count": len(scores),
            "mean_brier": round(sum(scores) / len(scores), 6),
            "window_days": WEEKLY_AGGREGATE_DAYS,
        }

    wpath = weekly_calibration_path(root)
    wpath.parent.mkdir(parents=True, exist_ok=True)
    with wpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")

    return summary
