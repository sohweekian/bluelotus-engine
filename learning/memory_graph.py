"""Lean institutional memory graph (JSONL edges)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from learning.claim_store import read_claims
from learning.paths import memory_edges_path

MAX_EDGES_PER_CYCLE = 500


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_memory_edges(
    *,
    root: Path | None = None,
    cycle_id: str = "",
    persist: bool = True,
) -> Dict[str, Any]:
    claims = read_claims(root=root, status=None, limit=5000)
    edges: List[Dict[str, Any]] = []

    for claim in claims:
        cid = claim.get("claim_id")
        if not cid:
            continue
        cid_cycle = claim.get("cycle_id") or cycle_id
        module = claim.get("module")

        if claim.get("thesis_id"):
            edges.append({
                "from": cid,
                "to": claim["thesis_id"],
                "rel": "supports",
                "module": module,
                "cycle_id": cid_cycle,
            })

        for thesis in claim.get("linked_theses") or []:
            if isinstance(thesis, dict) and thesis.get("thesis_id"):
                edges.append({
                    "from": cid,
                    "to": thesis["thesis_id"],
                    "rel": "supports",
                    "module": module,
                    "cycle_id": cid_cycle,
                })

        if module:
            edges.append({
                "from": f"module:{module}",
                "to": cid,
                "rel": "registered",
                "cycle_id": cid_cycle,
            })

    edges = edges[:MAX_EDGES_PER_CYCLE]
    if persist and edges:
        path = memory_edges_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            for edge in edges:
                row = {**edge, "created_at": _utc_now()}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"edge_count": len(edges), "path": str(memory_edges_path(root))}
