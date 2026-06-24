#!/usr/bin/env python3
"""
SLICDO deterministic learning cycle — register, tag, resolve, graph, replay, propose.

Usage:
  python scripts/run_slicdo_learning_cycle.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.claim_registrars import register_from_dataset
from learning.constants import SLICDO_VERSION
from learning.memory_graph import build_memory_edges
from learning.outcome_engine import resolve_open_claims
from learning.promotion_ledger import create_proposal_ledger_entries
from learning.promotion_proposal import build_learning_proposals
from learning.retention import apply_retention
from replay.slicdo_replay import run_slicdo_calibration_replay


def main() -> int:
    parser = argparse.ArgumentParser(description="SLICDO deterministic learning cycle")
    parser.add_argument("--cycle-id", default="")
    parser.add_argument("--skip-retention", action="store_true")
    parser.add_argument("--skip-proposals", action="store_true")
    parser.add_argument("--skip-replay", action="store_true")
    args = parser.parse_args()

    dataset_path = ROOT / "data" / "frontend" / "dataset_raw.json"
    dataset = {}
    if dataset_path.exists():
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    cycle_id = args.cycle_id or (dataset.get("meta") or {}).get("cycle_id") or (dataset.get("meta") or {}).get("generated_at")

    print(f"SLICDO Learning Cycle ({SLICDO_VERSION})")
    print("=" * 44)

    reg = register_from_dataset(dataset, cycle_id=str(cycle_id), root=ROOT)
    print(f"Claims registered: {reg.get('total_written', 0)}")

    outcome = resolve_open_claims(dataset, root=ROOT)
    print(f"Resolved: {outcome.get('resolved', 0)} | Expired: {outcome.get('expired', 0)}")

    graph = build_memory_edges(root=ROOT, cycle_id=str(cycle_id))
    print(f"Memory edges: {graph.get('edge_count', 0)}")

    if not args.skip_retention:
        ret = apply_retention(root=ROOT)
        print(f"Retention pruned: {ret.get('pruned', 0)} | kept: {ret.get('kept', 0)}")

    if not args.skip_replay:
        replay = run_slicdo_calibration_replay(root=ROOT)
        print(f"Replay modules: {len((replay.get('modules') or {}))}")

    if not args.skip_proposals:
        props = build_learning_proposals(root=ROOT)
        ledger = create_proposal_ledger_entries(root=ROOT)
        print(f"Proposals: {len(props.get('proposals') or [])} | Ledger rows: {ledger.get('written', 0)}")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
