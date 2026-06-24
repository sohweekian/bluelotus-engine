"""CIO-reviewable learning proposals from calibration aggregates (advisory only)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from learning.constants import SLICDO_VERSION
from learning.outcome_engine import read_resolutions
from learning.paths import learning_proposals_path
from learning.retention import build_weekly_calibration


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_learning_proposals(*, root: Path | None = None) -> Dict[str, Any]:
    calibration = build_weekly_calibration(root=root)
    resolutions = read_resolutions(root=root)
    proposals: List[Dict[str, Any]] = []

    for mod, stats in (calibration.get("modules") or {}).items():
        count = int(stats.get("resolved_count") or 0)
        mean_brier = float(stats.get("mean_brier") or 0)
        if count < 5:
            proposals.append({
                "proposal_id": f"promote:{mod}:collecting",
                "module": mod,
                "action": "COLLECT_MORE_RESOLUTIONS",
                "reason": f"Only {count} resolved claims; need >=5 for promotion review",
                "cio_approval_required": False,
                "status": "WATCH",
            })
            continue
        if mean_brier <= 0.15:
            proposals.append({
                "proposal_id": f"promote:{mod}:calibration_ok",
                "module": mod,
                "action": "REVIEW_PARAMETER_PROMOTION",
                "reason": f"Mean Brier {mean_brier:.4f} over {count} resolutions",
                "cio_approval_required": True,
                "status": "PROPOSED",
            })
        else:
            proposals.append({
                "proposal_id": f"promote:{mod}:recalibrate",
                "module": mod,
                "action": "REVIEW_LR_OR_QRE_RECALIBRATION",
                "reason": f"Mean Brier {mean_brier:.4f} elevated over {count} resolutions",
                "cio_approval_required": True,
                "status": "PROPOSED",
            })

    payload = {
        "slicdo_version": SLICDO_VERSION,
        "generated_at": _utc_now(),
        "calibration": calibration,
        "total_resolutions": len(resolutions),
        "proposals": proposals,
        "execution_authority": "CIO_ONLY_MANUAL",
        "order_routing_enabled": False,
        "manual_execution_required": True,
    }

    out = learning_proposals_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
