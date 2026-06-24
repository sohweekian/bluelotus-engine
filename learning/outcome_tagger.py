"""Numeric ground-truth outcome tagger — no LLM judgment."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from learning.paths import outcome_tags_path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ticker_chg_pct(dataset: Dict[str, Any], ticker: str) -> Optional[float]:
    t = str(ticker).upper()
    live = dataset.get("live_prices") or {}
    row = live.get(t)
    if isinstance(row, dict) and row.get("chg_pct") is not None:
        try:
            return float(row["chg_pct"])
        except (TypeError, ValueError):
            return None
    portfolio = dataset.get("portfolio") or {}
    pos = (portfolio.get("positions") or {}).get(t)
    if isinstance(pos, dict) and pos.get("chg_pct") is not None:
        try:
            val = float(pos["chg_pct"])
            return val if val != 0.0 else None
        except (TypeError, ValueError):
            return None
    return None


def _append_tag(row: Dict[str, Any], *, root: Path | None) -> None:
    path = outcome_tags_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def tag_cio_prediction_claim(claim: Dict[str, Any], dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Resolve CIO prediction: sleeve avg return vs SPY/QQQ benchmark (binary)."""
    tickers = claim.get("included_tickers") or []
    if not tickers:
        refs = claim.get("evidence_refs") or {}
        tickers = refs.get("included") or refs.get("included_tickers") or []
    if not tickers:
        return None

    returns: List[float] = []
    details: Dict[str, Any] = {}
    for t in tickers:
        chg = _ticker_chg_pct(dataset, str(t))
        if chg is not None:
            returns.append(chg)
            details[str(t).upper()] = chg
    bench = _ticker_chg_pct(dataset, "SPY")
    bench_name = "SPY"
    if bench is None:
        bench = _ticker_chg_pct(dataset, "QQQ")
        bench_name = "QQQ"
    if not returns or bench is None:
        return None

    sleeve_avg = sum(returns) / len(returns)
    outperformed = sleeve_avg > bench
    outcome_value = 1.0 if outperformed else 0.0
    predicted = float(claim.get("posterior") or claim.get("confidence") or 0.5)

    return {
        "claim_id": claim.get("claim_id"),
        "module": "cio_prediction",
        "tag_method": "relative_return_vs_benchmark",
        "benchmark": bench_name,
        "benchmark_return_pct": round(bench, 4),
        "sleeve_avg_return_pct": round(sleeve_avg, 4),
        "ticker_returns": details,
        "outcome_value": outcome_value,
        "outcome_label": "OUTPERFORM" if outperformed else "UNDERPERFORM",
        "predicted_probability": round(predicted, 6),
        "tagged_at": _utc_now(),
        "manual_execution_required": True,
    }


def tag_nite_pei_claim(claim: Dict[str, Any], dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """NITE-PEI: posterior move magnitude as calibration proxy when events applied."""
    if int(claim.get("events_applied") or 0) <= 0:
        return None
    prior = float(claim.get("prior") or 0)
    posterior = float(claim.get("posterior") or 0)
    delta = abs(posterior - prior)
    outcome_value = 1.0 if delta >= 0.05 else 0.0
    return {
        "claim_id": claim.get("claim_id"),
        "module": "nite_pei",
        "tag_method": "posterior_move_threshold",
        "prior": prior,
        "posterior": posterior,
        "delta": round(delta, 6),
        "outcome_value": outcome_value,
        "outcome_label": "MATERIAL_MOVE" if outcome_value else "IMMEDIATE_MOVE",
        "tagged_at": _utc_now(),
        "manual_execution_required": True,
    }


def tag_bgtm_claim(claim: Dict[str, Any], dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """BGTM: keep probability registration; tag as registered snapshot."""
    posterior = float(claim.get("posterior") or 0)
    if posterior <= 0:
        return None
    return {
        "claim_id": claim.get("claim_id"),
        "module": "bgtm",
        "tag_method": "probability_registration",
        "outcome_value": posterior,
        "outcome_label": "REGISTERED",
        "resolution_key": claim.get("resolution_key"),
        "tagged_at": _utc_now(),
        "manual_execution_required": True,
    }


def tag_claim(claim: Dict[str, Any], dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    module = str(claim.get("module") or "")
    if module == "cio_prediction":
        return tag_cio_prediction_claim(claim, dataset)
    if module == "nite_pei":
        return tag_nite_pei_claim(claim, dataset)
    if module == "bgtm":
        return tag_bgtm_claim(claim, dataset)
    return None


def tag_open_claims(
    claims: List[Dict[str, Any]],
    dataset: Dict[str, Any],
    *,
    root: Path | None = None,
    persist: bool = True,
) -> List[Dict[str, Any]]:
    tags: List[Dict[str, Any]] = []
    for claim in claims:
        tag = tag_claim(claim, dataset)
        if tag:
            tags.append(tag)
            if persist:
                _append_tag(tag, root=root)
    return tags
