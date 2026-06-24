"""Resolve open claims and write lean resolution scores."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from learning.claim_store import read_claims
from learning.outcome_tagger import tag_claim
from learning.paths import resolutions_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _brier_score(predicted: float, outcome: float) -> float:
    return (float(predicted) - float(outcome)) ** 2


def resolve_open_claims(
    dataset: Optional[Dict[str, Any]] = None,
    *,
    root: Path | None = None,
) -> Dict[str, Any]:
    """
    Resolution v2 (deterministic):
    1. Numeric outcome tagger (ground truth when data available)
    2. Snapshot proxy (v1) when tagger returns None
    3. EXPIRED past horizon
    """
    dataset = dataset or {}
    now = datetime.now(timezone.utc)
    open_claims = read_claims(root=root, status="OPEN")
    path = resolutions_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    resolved = 0
    expired = 0
    resolution_rows: List[Dict[str, Any]] = []

    for claim in open_claims:
        cid = claim.get("claim_id")
        horizon = _parse_dt(str(claim.get("horizon_end") or ""))
        module = claim.get("module")
        posterior = float(claim.get("posterior") or 0)
        status = "OPEN"
        outcome_value: Optional[float] = None
        brier: Optional[float] = None
        note = ""
        tag: Optional[Dict[str, Any]] = None

        tag = tag_claim(claim, dataset)
        if tag:
            status = "RESOLVED"
            outcome_value = float(tag.get("outcome_value") or 0)
            predicted = float(claim.get("posterior") or claim.get("confidence") or tag.get("predicted_probability") or 0.5)
            if claim.get("module") == "bgtm":
                brier = 0.0
            else:
                brier = _brier_score(predicted, outcome_value)
            note = f"ground_truth:{tag.get('tag_method')}"
        elif module == "nite_pei" and int(claim.get("events_applied") or 0) > 0:
            status = "RESOLVED"
            outcome_value = posterior
            brier = 0.0
            note = "nite_pei_event_applied_snapshot"
        elif module == "bgtm" and posterior > 0:
            status = "RESOLVED"
            outcome_value = posterior
            brier = 0.0
            note = "bgtm_probability_snapshot_v1"
        elif horizon and now >= horizon:
            status = "EXPIRED"
            expired += 1
            note = "horizon_passed_without_outcome_tag"
        else:
            continue

        if status == "RESOLVED":
            resolved += 1

        row = {
            "claim_id": cid,
            "cycle_id": claim.get("cycle_id"),
            "module": module,
            "resolution_status": status,
            "resolved_at": _utc_now(),
            "posterior_at_claim": posterior,
            "outcome_value": outcome_value,
            "brier_score": brier if brier is not None else _brier_score(posterior, outcome_value or 0),
            "note": note,
            "outcome_tag": tag,
            "manual_execution_required": True,
        }
        resolution_rows.append(row)

    if resolution_rows:
        with path.open("a", encoding="utf-8") as f:
            for row in resolution_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    _mark_claims_resolved(resolution_rows, root=root)

    return {
        "open_scanned": len(open_claims),
        "resolved": resolved,
        "expired": expired,
        "resolutions_path": str(path),
    }


def _mark_claims_resolved(rows: List[Dict[str, Any]], *, root: Path | None) -> None:
    """Rewrite claims file updating status for resolved/expired ids (lean file, typically < few MB)."""
    from learning.paths import claims_path

    path = claims_path(root)
    if not path.exists() or not rows:
        return
    status_map = {r["claim_id"]: r["resolution_status"] for r in rows}
    updated: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = row.get("claim_id")
            if cid in status_map:
                row["resolution_status"] = status_map[cid]
                row["resolved_at"] = _utc_now()
            updated.append(row)
    with path.open("w", encoding="utf-8") as f:
        for row in updated:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_resolutions(*, root: Path | None = None, limit: int = 5000) -> List[Dict[str, Any]]:
    path = resolutions_path(root)
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
