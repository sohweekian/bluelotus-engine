"""Build enriched SLICDO learning cycle report for agent cycles."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from learning.claim_store import read_claims
from learning.constants import SLICDO_VERSION
from learning.outcome_engine import read_resolutions
from learning.paths import learning_cycle_latest_path, learning_proposals_path
from learning.promotion_proposal import build_learning_proposals


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_learning_cycle_report(
    base_snapshot: Dict[str, Any],
    *,
    root: Path | None = None,
    run_proposals: bool = False,
) -> Dict[str, Any]:
    open_claims = read_claims(root=root, status="OPEN")
    resolutions = read_resolutions(root=root, limit=200)
    proposals: Dict[str, Any] = {}
    if run_proposals:
        proposals = build_learning_proposals(root=root)
    elif learning_proposals_path(root).exists():
        try:
            proposals = json.loads(learning_proposals_path(root).read_text(encoding="utf-8"))
        except Exception:
            proposals = {}

    by_module: Dict[str, int] = {}
    for c in open_claims:
        m = str(c.get("module") or "unknown")
        by_module[m] = by_module.get(m, 0) + 1

    report = {
        **base_snapshot,
        "slicdo_version": SLICDO_VERSION,
        "learning_enriched_at": _utc_now(),
        "institutional_claims": {
            "open_count": len(open_claims),
            "open_by_module": by_module,
            "recent_resolutions": len(resolutions),
        },
        "learning_proposals_summary": {
            "proposal_count": len(proposals.get("proposals") or []),
            "pending_cio_approval": sum(
                1 for p in (proposals.get("proposals") or []) if p.get("cio_approval_required")
            ),
        },
        "slicdo_loop_status": "ACTIVE",
        "manual_execution_required": True,
    }

    out = learning_cycle_latest_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
