"""Append-only lean institutional claim store (JSONL)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from learning.constants import MAX_CLAIMS_PER_CYCLE
from learning.paths import claims_path, learning_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_claim_id(module: str, cycle_id: str, source_ref: str) -> str:
    raw = f"{module}|{cycle_id}|{source_ref}"
    return "clm:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def append_claims(
    claims: Iterable[Dict[str, Any]],
    *,
    root: Path | None = None,
    max_per_batch: int = MAX_CLAIMS_PER_CYCLE,
) -> Dict[str, Any]:
    """Append lean claim rows; skip duplicates already present for same claim_id."""
    learning_dir(root).mkdir(parents=True, exist_ok=True)
    path = claims_path(root)
    existing_ids = {r.get("claim_id") for r in read_claims(root=root, status=None)}

    written = 0
    skipped = 0
    batch = list(claims)[:max_per_batch]
    with path.open("a", encoding="utf-8") as f:
        for claim in batch:
            cid = claim.get("claim_id")
            if not cid or cid in existing_ids:
                skipped += 1
                continue
            try:
                from mid.narrative_firewall import reject_agent_claim
                if reject_agent_claim(claim):
                    skipped += 1
                    continue
            except Exception:
                pass
            row = dict(claim)
            row.setdefault("created_at", _utc_now())
            row.setdefault("resolution_status", "OPEN")
            row.setdefault("tier", "T1")
            row.setdefault("manual_execution_required", True)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing_ids.add(cid)
            written += 1

    return {"written": written, "skipped": skipped, "path": str(path)}


def read_claims(
    *,
    root: Path | None = None,
    status: Optional[str] = "OPEN",
    limit: int = 10_000,
) -> List[Dict[str, Any]]:
    path = claims_path(root)
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if status is not None and row.get("resolution_status") != status:
                continue
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def count_claims_for_cycle(cycle_id: str, *, root: Path | None = None) -> int:
    return sum(1 for r in read_claims(root=root, status=None) if r.get("cycle_id") == cycle_id)
