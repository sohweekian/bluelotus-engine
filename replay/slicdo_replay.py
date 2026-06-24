"""SLICDO calibration replay — numeric layers only, no LLM."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REPLAY_VERSION = "slicdo_replay_v1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_slicdo_calibration_replay(
    *,
    root: Path | None = None,
    brier_threshold: float = 0.15,
) -> Dict[str, Any]:
    from learning.outcome_engine import read_resolutions

    resolutions = read_resolutions(root=root)
    by_module: Dict[str, List[float]] = defaultdict(list)
    ground_truth = 0
    snapshot_proxy = 0

    for row in resolutions:
        if row.get("resolution_status") != "RESOLVED":
            continue
        mod = str(row.get("module") or "unknown")
        brier = row.get("brier_score")
        if brier is not None:
            by_module[mod].append(float(brier))
        note = str(row.get("note") or "")
        if "ground_truth" in note or "relative_return" in note or "tag_method" in note:
            ground_truth += 1
        elif "snapshot" in note:
            snapshot_proxy += 1

    module_summary: Dict[str, Any] = {}
    for mod, scores in by_module.items():
        mean_brier = sum(scores) / len(scores) if scores else 0.0
        module_summary[mod] = {
            "resolved_count": len(scores),
            "mean_brier": round(mean_brier, 6),
            "passes_threshold": mean_brier <= brier_threshold,
            "replay_recommendation": (
                "REVIEW_PARAMETER_PROMOTION" if mean_brier <= brier_threshold and len(scores) >= 5
                else "COLLECT_MORE_RESOLUTIONS"
            ),
        }

    out = {
        "version": REPLAY_VERSION,
        "generated_at": _utc_now(),
        "brier_threshold": brier_threshold,
        "total_resolutions": len(resolutions),
        "ground_truth_tags": ground_truth,
        "snapshot_proxy_tags": snapshot_proxy,
        "modules": module_summary,
        "execution_authority": "CIO_ONLY_MANUAL",
        "advisory_only": True,
    }

    if root:
        out_path = root / "data" / "learning" / "slicdo_replay_latest.json"
    else:
        out_path = Path(__file__).resolve().parent.parent / "data" / "learning" / "slicdo_replay_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["output_path"] = str(out_path)
    return out
