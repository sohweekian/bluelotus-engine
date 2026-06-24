"""CIO-governed promotion ledger (advisory + rollback metadata)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from learning.paths import learning_proposals_path, promotion_ledger_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_ledger(*, root: Path | None = None, limit: int = 200) -> List[Dict[str, Any]]:
    path = promotion_ledger_path(root)
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(rows) >= limit:
                break
    return rows


def append_promotion_record(record: Dict[str, Any], *, root: Path | None = None) -> Dict[str, Any]:
    path = promotion_ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        **record,
        "recorded_at": _utc_now(),
        "execution_authority": "CIO_ONLY_MANUAL",
        "order_routing_enabled": False,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def create_proposal_ledger_entries(*, root: Path | None = None) -> Dict[str, Any]:
    """Mirror learning proposals into promotion ledger as PROPOSED (no auto-apply)."""
    props_path = learning_proposals_path(root)
    if not props_path.exists():
        return {"written": 0}
    payload = json.loads(props_path.read_text(encoding="utf-8"))
    written = 0
    for prop in payload.get("proposals") or []:
        if not isinstance(prop, dict):
            continue
        record = {
            "promotion_id": prop.get("proposal_id"),
            "module": prop.get("module"),
            "action": prop.get("action"),
            "status": prop.get("status", "PROPOSED"),
            "reason": prop.get("reason"),
            "cio_approval_required": prop.get("cio_approval_required", True),
            "replay_evidence": None,
            "rollback_to": None,
        }
        append_promotion_record(record, root=root)
        written += 1
    return {"written": written}


def approve_promotion(
    promotion_id: str,
    *,
    approved_by: str = "CIO",
    replay_evidence: Optional[str] = None,
    root: Path | None = None,
) -> Dict[str, Any]:
    return append_promotion_record({
        "promotion_id": promotion_id,
        "status": "APPROVED",
        "approved_by": approved_by,
        "replay_evidence": replay_evidence,
        "note": "Approval recorded; parameter apply remains manual.",
    }, root=root)


def rollback_promotion(
    promotion_id: str,
    *,
    rolled_back_by: str = "CIO",
    reason: str = "",
    root: Path | None = None,
) -> Dict[str, Any]:
    return append_promotion_record({
        "promotion_id": promotion_id,
        "status": "ROLLED_BACK",
        "rolled_back_by": rolled_back_by,
        "reason": reason,
    }, root=root)
