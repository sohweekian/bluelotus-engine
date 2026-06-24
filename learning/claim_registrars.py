"""Register T1 institutional claims from NITE-PEI and BGTM (anti-bloat)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from learning.claim_store import append_claims, count_claims_for_cycle, make_claim_id
from learning.constants import MAX_CLAIMS_PER_CYCLE, MAX_CIO_CLAIMS_PER_CYCLE, T1_MODULES
from learning.paths import project_root


def _horizon_end(days: int = 5) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(timespec="seconds")


def register_bgtm_claims(
    geo_lr_bridge: Dict[str, Any],
    *,
    cycle_id: str,
    root=None,
) -> Dict[str, Any]:
    if geo_lr_bridge.get("_status") not in (None, "OK") and not geo_lr_bridge.get("game_results"):
        return {"written": 0, "skipped": 0, "reason": "geo_lr_bridge not OK"}

    if count_claims_for_cycle(cycle_id, root=root) >= MAX_CLAIMS_PER_CYCLE:
        return {"written": 0, "skipped": 0, "reason": "cycle claim cap reached"}

    claims: List[Dict[str, Any]] = []
    for game_id, payload in (geo_lr_bridge.get("game_results") or {}).items():
        solution = (payload or {}).get("solution") or {}
        outcomes = solution.get("outcome_probabilities") or {}
        if not outcomes:
            continue
        top_key = max(outcomes, key=lambda k: float(outcomes[k] or 0))
        top_prob = float(outcomes[top_key] or 0)
        source_ref = f"bgtm:{game_id}:top_outcome:{top_key}"
        claims.append({
            "claim_id": make_claim_id("bgtm", cycle_id, source_ref),
            "tier": "T1",
            "module": "bgtm",
            "cycle_id": cycle_id,
            "thesis_id": None,
            "game_id": game_id,
            "source_ref": source_ref,
            "resolution_rule": "top_outcome_probability",
            "resolution_key": top_key,
            "prior": None,
            "posterior": round(top_prob, 6),
            "horizon_end": _horizon_end(7),
            "linked_theses": payload.get("linked_theses") or [],
        })
        # One secondary claim: talks probability when present
        if "w1_talks" in outcomes:
            talks_ref = f"bgtm:{game_id}:w1_talks"
            claims.append({
                "claim_id": make_claim_id("bgtm", cycle_id, talks_ref),
                "tier": "T1",
                "module": "bgtm",
                "cycle_id": cycle_id,
                "game_id": game_id,
                "source_ref": talks_ref,
                "resolution_rule": "outcome_probability",
                "resolution_key": "w1_talks",
                "prior": None,
                "posterior": round(float(outcomes["w1_talks"] or 0), 6),
                "horizon_end": _horizon_end(7),
            })

    remaining = MAX_CLAIMS_PER_CYCLE - count_claims_for_cycle(cycle_id, root=root)
    return append_claims(claims[: max(0, remaining)], root=root)


def register_nite_pei_claims(
    nite_block: Dict[str, Any],
    *,
    cycle_id: str,
    root=None,
) -> Dict[str, Any]:
    if not nite_block:
        return {"written": 0, "skipped": 0, "reason": "empty nite block"}

    if count_claims_for_cycle(cycle_id, root=root) >= MAX_CLAIMS_PER_CYCLE:
        return {"written": 0, "skipped": 0, "reason": "cycle claim cap reached"}

    claims: List[Dict[str, Any]] = []
    for snap in nite_block.get("thesis_snapshots") or nite_block.get("theses") or []:
        if not isinstance(snap, dict):
            continue
        thesis_id = snap.get("thesis_id") or snap.get("id")
        if not thesis_id:
            continue
        p_prior = float(snap.get("P_prior") or snap.get("p_prior_initial") or 0)
        p_post = float(snap.get("P_posterior") or snap.get("p_posterior_final") or 0)
        source_ref = f"nite_pei:thesis:{thesis_id}"
        claims.append({
            "claim_id": make_claim_id("nite_pei", cycle_id, source_ref),
            "tier": "T1",
            "module": "nite_pei",
            "cycle_id": cycle_id,
            "thesis_id": thesis_id,
            "source_ref": source_ref,
            "resolution_rule": "thesis_posterior_level",
            "prior": round(p_prior, 6),
            "posterior": round(p_post, 6),
            "horizon_end": _horizon_end(5),
            "events_applied": len(snap.get("events_applied") or []),
        })

    remaining = MAX_CLAIMS_PER_CYCLE - count_claims_for_cycle(cycle_id, root=root)
    return append_claims(claims[: max(0, remaining)], root=root)


def register_cio_prediction_claims(
    cio_manual: Dict[str, Any],
    *,
    cycle_id: str,
    root=None,
) -> Dict[str, Any]:
    """Register T2 CIO prediction claims from active manual report (capped)."""
    active = (cio_manual or {}).get("active") or cio_manual or {}
    if not active:
        return {"written": 0, "skipped": 0, "reason": "no active cio manual"}

    if count_claims_for_cycle(cycle_id, root=root) >= MAX_CLAIMS_PER_CYCLE:
        return {"written": 0, "skipped": 0, "reason": "cycle claim cap reached"}

    entry_type = str(active.get("entry_type") or "")
    claims: List[Dict[str, Any]] = []

    prediction = active.get("prediction") or {}
    if entry_type == "CIO_MARKET_PREDICTION" or prediction.get("prediction_id"):
        pid = prediction.get("prediction_id") or active.get("journal_id")
        included = prediction.get("included_tickers") or (active.get("evidence_refs") or {}).get("included") or []
        source_ref = f"cio_prediction:{pid}"
        claims.append({
            "claim_id": make_claim_id("cio_prediction", cycle_id, source_ref),
            "tier": "T2",
            "module": "cio_prediction",
            "cycle_id": cycle_id,
            "source_ref": source_ref,
            "prediction_id": pid,
            "resolution_rule": "relative_return_vs_benchmark",
            "prior": None,
            "posterior": float(active.get("confidence") or prediction.get("confidence") or 0.5),
            "confidence": active.get("confidence"),
            "horizon_end": _horizon_end(3),
            "included_tickers": included,
            "evidence_refs": active.get("evidence_refs") or {},
        })

    cio_cap = MAX_CIO_CLAIMS_PER_CYCLE
    remaining = min(
        cio_cap,
        MAX_CLAIMS_PER_CYCLE - count_claims_for_cycle(cycle_id, root=root),
    )
    return append_claims(claims[: max(0, remaining)], root=root)


def register_cio_prediction_files(*, cycle_id: str, root=None) -> Dict[str, Any]:
    """Register CIO prediction JSON files from data/cio/ (T2, capped)."""
    base = (root or project_root()) / "data" / "cio"
    if not base.exists():
        return {"written": 0, "skipped": 0}
    claims: List[Dict[str, Any]] = []
    for path in sorted(base.glob("manual_cio_prediction_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        prediction = data.get("prediction") or {}
        pid = prediction.get("prediction_id") or data.get("journal_id")
        if not pid:
            continue
        included = prediction.get("included_tickers") or (data.get("evidence_refs") or {}).get("included") or []
        source_ref = f"cio_prediction:{pid}"
        claims.append({
            "claim_id": make_claim_id("cio_prediction", cycle_id, source_ref),
            "tier": "T2",
            "module": "cio_prediction",
            "cycle_id": cycle_id,
            "source_ref": source_ref,
            "prediction_id": pid,
            "resolution_rule": "relative_return_vs_benchmark",
            "posterior": float(data.get("confidence") or prediction.get("confidence") or 0.5),
            "horizon_end": _horizon_end(3),
            "included_tickers": included,
            "evidence_refs": data.get("evidence_refs") or {},
        })
    remaining = min(
        MAX_CIO_CLAIMS_PER_CYCLE,
        MAX_CLAIMS_PER_CYCLE - count_claims_for_cycle(cycle_id, root=root),
    )
    return append_claims(claims[: max(0, remaining)], root=root)


def register_from_dataset(
    dataset: Dict[str, Any],
    *,
    cycle_id: Optional[str] = None,
    root=None,
) -> Dict[str, Any]:
    meta = dataset.get("meta") or {}
    cid = cycle_id or meta.get("cycle_id") or meta.get("generated_at") or "unknown_cycle"
    pl = dataset.get("prediction_layers") or {}
    results: Dict[str, Any] = {"cycle_id": cid, "modules": {}}

    geo = pl.get("geo_lr_bridge") or {}
    if geo:
        results["modules"]["bgtm"] = register_bgtm_claims(geo, cycle_id=str(cid), root=root)

    nite = dataset.get("nite_pei") or {}
    if nite:
        results["modules"]["nite_pei"] = register_nite_pei_claims(nite, cycle_id=str(cid), root=root)

    cio_manual = dataset.get("cio_manual_report") or {}
    if cio_manual:
        results["modules"]["cio_prediction"] = register_cio_prediction_claims(
            cio_manual, cycle_id=str(cid), root=root,
        )
    file_reg = register_cio_prediction_files(cycle_id=str(cid), root=root)
    if file_reg.get("written", 0):
        prev = results["modules"].get("cio_prediction") or {}
        results["modules"]["cio_prediction"] = {
            "written": prev.get("written", 0) + file_reg.get("written", 0),
            "skipped": prev.get("skipped", 0) + file_reg.get("skipped", 0),
        }

    results["total_written"] = sum(
        (m or {}).get("written", 0) for m in results["modules"].values()
    )
    return results
