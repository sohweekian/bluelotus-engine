"""Deterministic Chief Clerk digest — Zone A only, no LLM council."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bluelotus_engine.timeutil import sgt_now
from governance.contradiction_governance import collect_allowed_actions, collect_blocked_actions, load_json_from_summary
from llm_clients.config_loader import resolve_project_path


DELIVERY_PATH = resolve_project_path("research/research_report_delivery_latest.json")


def load_delivery() -> Dict[str, Any]:
    if not DELIVERY_PATH.exists():
        return {}
    try:
        parsed = json.loads(DELIVERY_PATH.read_text(encoding="utf-8-sig"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def load_operating_truth(delivery: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    delivery = delivery if delivery is not None else load_delivery()
    op = delivery.get("operating_truth")
    if isinstance(op, dict) and op:
        return op
    contract = delivery.get("deterministic_contract")
    if isinstance(contract, dict):
        bundle = contract.get("operating_truth")
        if isinstance(bundle, dict):
            return bundle
    return {}


def load_full_dataset(cycle_context: Dict[str, Any]) -> Dict[str, Any]:
    summary = cycle_context.get("dataset_summary", {})
    if isinstance(summary, dict):
        path_text = str(summary.get("path", "")).strip()
        if path_text:
            path = Path(path_text)
            if path.exists():
                try:
                    parsed = json.loads(path.read_text(encoding="utf-8-sig"))
                    return parsed if isinstance(parsed, dict) else {}
                except Exception:
                    pass
    return load_json_from_summary(summary)


def load_operator_full(operator_pack: Dict[str, Any]) -> Dict[str, Any]:
    return load_json_from_summary(operator_pack.get("source_summary", {}))


def collect_stale_sources(dataset: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    health = dataset.get("source_health")
    if isinstance(health, list):
        for item in health:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or item.get("grade") or "").upper()
            name = str(item.get("source") or item.get("name") or item.get("feed") or "").strip()
            if name and any(tag in status for tag in ("STALE", "FAIL", "ERROR", "DOWN")):
                out.append(name)
    meta = dataset.get("meta", {}) if isinstance(dataset.get("meta"), dict) else {}
    for key in ("fear_greed_stale", "live_news_stale"):
        if meta.get(key):
            out.append(key.replace("_stale", ""))
    return sorted(set(out))


def source_coverage(dataset: Dict[str, Any]) -> Tuple[int, int]:
    meta = dataset.get("meta", {}) if isinstance(dataset.get("meta"), dict) else {}
    active = int(meta.get("sources_active") or meta.get("external_sources_active") or 0)
    expected = int(meta.get("sources_expected") or 0)
    return active, expected


def extract_cash_fortress_flags(operator_full: Dict[str, Any]) -> Tuple[bool, bool, bool]:
    operators = operator_full.get("operators", {}) if isinstance(operator_full.get("operators"), dict) else {}
    cfm = operators.get("cash_fortress_mode", {}) if isinstance(operators.get("cash_fortress_mode"), dict) else {}
    metrics = cfm.get("metrics", {}) if isinstance(cfm.get("metrics"), dict) else {}
    return (
        bool(metrics.get("cash_fortress_mode", False)),
        bool(metrics.get("scout_mode", False)),
        bool(metrics.get("second_tranche_blocked", False)),
    )


def choose_deterministic_posture(
    operating_truth: Dict[str, Any],
    p1_count: int,
    p2_count: int,
    cash_fortress_mode: bool,
    dataset: Optional[Dict[str, Any]] = None,
) -> str:
    if isinstance(dataset, dict):
        nite = dataset.get("nite_pei")
        if isinstance(nite, dict) and str(nite.get("ckri_zone", "")).upper() == "CRITICAL":
            return "REVIEW"
    if p1_count > 0:
        return "REVIEW"
    failed = operating_truth.get("governance_gate_failed_gates", [])
    if isinstance(failed, list) and failed:
        return "REVIEW"
    causal = str(operating_truth.get("causal_status", "")).upper()
    if "CRITICAL" in causal or causal == "INCOMPLETE":
        return "REVIEW"
    if p2_count > 0:
        return "REVIEW"
    cio_action = str(operating_truth.get("cio_action", "WAIT / HOLD")).upper()
    if "REDUCE" in cio_action or "RISK" in cio_action:
        return "REDUCE_RISK_REVIEW"
    if "HOLD" in cio_action:
        return "HOLD"
    if cash_fortress_mode:
        return "HOLD"
    return "WAIT"


def build_digest_layers(
    cycle_context: Dict[str, Any],
    dataset: Dict[str, Any],
    operating_truth: Dict[str, Any],
    operator_pack: Dict[str, Any],
    operator_full: Dict[str, Any],
) -> List[Dict[str, Any]]:
    active, expected = source_coverage(dataset)
    stale = collect_stale_sources(dataset)
    regime = str(operating_truth.get("regime") or dataset.get("regime", {}).get("regime_short", "UNKNOWN"))
    causal = str(operating_truth.get("causal_status", "UNKNOWN"))
    failed_gates = operating_truth.get("governance_gate_failed_gates", [])
    if not isinstance(failed_gates, list):
        failed_gates = []
    blocked = sorted(collect_blocked_actions(operator_pack, operator_full))
    allowed = sorted(collect_allowed_actions(operator_pack, operator_full, []))
    portfolio = dataset.get("portfolio", {}) if isinstance(dataset.get("portfolio"), dict) else {}
    cash = portfolio.get("cash", portfolio.get("cash_balance"))
    total_assets = portfolio.get("total_assets", portfolio.get("market_val"))
    brier = str(operating_truth.get("brier_status", "UNKNOWN"))
    readiness = str(operating_truth.get("report_readiness", "UNKNOWN"))

    layers: List[Dict[str, Any]] = [
        {
            "layer_id": "cycle_identity",
            "layer": "package_cycle_identity",
            "status": "DATA_CONFIRMED",
            "summary": f"Cycle {cycle_context.get('cycle_id')} · deterministic clerk · Zone A authority",
        },
        {
            "layer_id": "source_hierarchy",
            "layer": "source_health",
            "status": "WARN" if stale else "PASS",
            "summary": f"Sources {active}/{expected} active"
            + (f" · STALE: {', '.join(stale[:6])}" if stale else ""),
        },
        {
            "layer_id": "regime_operating_truth",
            "layer": "operating_truth",
            "status": "DATA_CONFIRMED",
            "summary": f"Regime {regime} · causal {causal} · CIO field {operating_truth.get('cio_action', 'N/A')}",
        },
        {
            "layer_id": "governance_readiness",
            "layer": "governance_gate",
            "status": "WARN" if failed_gates else "PASS",
            "summary": (
                f"Gate score {operating_truth.get('governance_gate_score', 'N/A')}"
                + (f" · failed: {', '.join(str(g) for g in failed_gates[:6])}" if failed_gates else " · all passed")
            ),
        },
        {
            "layer_id": "portfolio_execution",
            "layer": "broker_portfolio",
            "status": "PASS",
            "summary": (
                f"Assets {total_assets} · cash {cash} ({round(float(cash or 0) / float(total_assets or 1) * 100, 1)}%)"
                + " · broker P/L authoritative (snapshot)"
            ),
        },
        {
            "layer_id": "concentration_risk",
            "layer": "risk_metrics",
            "status": "DATA_CONFIRMED",
            "summary": _concentration_summary(dataset, operating_truth),
        },
        {
            "layer_id": "blind_spot_causal",
            "layer": "operating_truth",
            "status": "WARN" if str(operating_truth.get("blind_spot_status", "")).upper() == "WARNING" else "PASS",
            "summary": (
                f"Causal {operating_truth.get('causal_status', 'N/A')} · "
                f"blind spot {operating_truth.get('blind_spot_status', 'N/A')}"
                + (
                    f" · failed: {', '.join(str(x) for x in (operating_truth.get('blind_spot_failed_items') or [])[:4])}"
                    if operating_truth.get("blind_spot_failed_items") else ""
                )
            ),
        },
        {
            "layer_id": "deterministic_operators",
            "layer": "operator_blocks",
            "status": "DATA_CONFIRMED",
            "summary": f"Blocked {len(blocked)} · permitted {', '.join(str(a) for a in allowed[:5]) or 'WAIT'}",
        },
        {
            "layer_id": "forecast_brier",
            "layer": "brier_ledger",
            "status": "DATA_CONFIRMED",
            "summary": f"Brier {brier} · open forecasts {operating_truth.get('open_forecasts', 'N/A')}",
        },
        {
            "layer_id": "report_readiness",
            "layer": "report_bundle",
            "status": "DATA_CONFIRMED",
            "summary": f"Readiness {readiness} · release {operating_truth.get('_release_status', 'N/A')}",
        },
    ]
    return layers


def _concentration_summary(dataset: Dict[str, Any], operating_truth: Dict[str, Any]) -> str:
    risk = dataset.get("risk_metrics", {}) if isinstance(dataset.get("risk_metrics"), dict) else {}
    largest = risk.get("largest_position", {}) if isinstance(risk.get("largest_position"), dict) else {}
    ticker = largest.get("ticker") or operating_truth.get("largest_cluster", "?")
    wt = largest.get("weight_vs_equity_capital") or operating_truth.get("largest_cluster_weight")
    hhi = risk.get("concentration_hhi_equity_only", risk.get("hhi_equity_only"))
    conc = str(operating_truth.get("concentration_status", "N/A"))
    parts = [f"status {conc}", f"largest {ticker}"]
    if wt is not None:
        try:
            parts.append(f"wt {float(wt) * 100:.1f}%")
        except Exception:
            parts.append(f"wt {wt}")
    if hhi is not None:
        parts.append(f"HHI {hhi}")
    return " · ".join(parts)


def contradictions_to_map(contradictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(contradictions, start=1):
        severity = str(item.get("severity", "P3"))
        rows.append({
            "contradiction_id": item.get("contradiction_id") or f"DC-{idx:03d}",
            "severity": "WARNING" if severity in {"P1", "P2"} else "INFO",
            "layer_a": str(item.get("source_a", "")),
            "layer_a_claim": str(item.get("conflict_statement", ""))[:240],
            "layer_b": str(item.get("source_b", "")),
            "layer_b_claim": str(item.get("recommended_resolution_path", ""))[:240],
            "conflict_type": str(item.get("domain", "DETERMINISTIC")),
            "status": "OPEN",
            "clerk_note": "Deterministic contradiction rule. No advice.",
        })
    return rows


def build_cio_attention_items(
    contradictions: List[Dict[str, Any]],
    operating_truth: Dict[str, Any],
) -> List[str]:
    items: List[str] = []
    for item in contradictions:
        if item.get("cio_attention_required"):
            text = str(item.get("conflict_statement", "")).strip()
            if text:
                items.append(text[:240])
    failed = operating_truth.get("governance_gate_failed_gates", [])
    if isinstance(failed, list):
        for gate in failed[:4]:
            items.append(f"Governance gate failed: {gate}")
    return items[:8]


def build_deterministic_clerk_briefing(
    cycle_context: Dict[str, Any],
    operating_truth: Dict[str, Any],
    operator_pack: Dict[str, Any],
    operator_full: Dict[str, Any],
    dataset: Dict[str, Any],
    contradiction_register: Dict[str, Any],
) -> Dict[str, Any]:
    contradictions = contradiction_register.get("contradictions", [])
    if not isinstance(contradictions, list):
        contradictions = []
    p1_count = int(contradiction_register.get("p1_count", 0))
    p2_count = int(contradiction_register.get("p2_count", 0))
    cash_fortress, scout_mode, second_tranche_blocked = extract_cash_fortress_flags(operator_full)
    posture = choose_deterministic_posture(
        operating_truth, p1_count, p2_count, cash_fortress, dataset=dataset
    )
    digest_layers = build_digest_layers(
        cycle_context, dataset, operating_truth, operator_pack, operator_full
    )
    cio_items = build_cio_attention_items(contradictions, operating_truth)
    blocked = sorted(collect_blocked_actions(operator_pack, operator_full))

    summary = (
        f"Deterministic Chief Clerk mapped {len(digest_layers)} Zone A layers. "
        f"No LLM agent council. Report action field states: {posture}. "
        f"Contradictions: {contradiction_register.get('contradiction_count', 0)} "
        f"(P1 {p1_count}, P2 {p2_count})."
    )

    return {
        "schema_version": "bluelotus_v3_chief_strategist_briefing_v1.0",
        "clerk_mode": "deterministic",
        "llm_council_enabled": False,
        "active_llm_role": "Deterministic Chief Clerk (Zone A)",
        "role_authority": "CLERK_ONLY",
        "strategic_authority": False,
        "analyst_authority": False,
        "execution_authority": "NONE",
        "cycle_id": str(cycle_context.get("cycle_id", "")),
        "summary": summary,
        "report_action_field": posture,
        "recommended_posture": posture,
        "cash_fortress_mode": cash_fortress,
        "scout_mode": scout_mode,
        "second_tranche_blocked": second_tranche_blocked,
        "operator_blocks": blocked,
        "agent_consensus": [],
        "disagreements": [],
        "contradiction_map": contradictions_to_map(contradictions),
        "digest_layers": digest_layers,
        "readiness_change_log": [
            {
                "field": "clerk_mode",
                "status": "DETERMINISTIC",
                "layer": "zone_a_pipeline",
                "clerk_note": "LLM agent council disabled. Digest sourced from report bundle and governance only.",
            },
            {
                "field": "governance_readiness_change",
                "status": "REPORT_FIELD",
                "layer": "deterministic_operator_blocks",
                "clerk_note": f"Blocked actions: {blocked[:8]}",
            },
        ],
        "cio_attention_items": cio_items,
        "manual_execution_required": True,
        "llm_order_generation": False,
        "created_at_sgt": sgt_now(),
    }


def render_clerk_digest_text(
    briefing: Dict[str, Any],
    contradiction_register: Dict[str, Any],
    operating_truth: Dict[str, Any],
) -> str:
    lines = [
        "=" * 78,
        "DETERMINISTIC CHIEF CLERK DIGEST",
        "=" * 78,
        f"Cycle: {briefing.get('cycle_id', '')}",
        f"Mode: DETERMINISTIC · Zone A · NO LLM AGENTS",
        f"Generated: {briefing.get('created_at_sgt', '')}",
        "",
        "CORE POLICY:",
        "  This digest is computed entirely from deterministic pipeline outputs.",
        "  The legacy 9-agent Qwen council is DISABLED and NON-AUTHORITATIVE.",
        "",
        f"SUMMARY: {briefing.get('summary', '')}",
        f"POSTURE: {briefing.get('recommended_posture', 'WAIT')}",
        "",
        "DIGEST LAYERS:",
    ]
    for layer in briefing.get("digest_layers", []) or []:
        if not isinstance(layer, dict):
            continue
        lines.append(
            f"  [{layer.get('status', 'N/A')}] {layer.get('layer_id', '')}: {layer.get('summary', '')}"
        )
    lines.extend(["", "OPERATING TRUTH (excerpt):"])
    for key in (
        "regime", "cio_action", "causal_status", "governance_gate_score",
        "governance_gate_failed_gates", "brier_status", "report_readiness",
    ):
        if key in operating_truth:
            lines.append(f"  {key}: {operating_truth.get(key)}")
    lines.extend(["", "CONTRADICTION REGISTER:"])
    contradictions = contradiction_register.get("contradictions", [])
    if not contradictions:
        lines.append("  None detected.")
    else:
        for item in contradictions[:12]:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"  [{item.get('severity')}] {item.get('domain')}: {item.get('conflict_statement', '')}"
            )
    lines.extend([
        "",
        "CIO ATTENTION:",
    ])
    for item in briefing.get("cio_attention_items", []) or []:
        lines.append(f"  - {item}")
    if not briefing.get("cio_attention_items"):
        lines.append("  - No contradiction-triggered CIO attention items.")
    lines.extend([
        "",
        "EXECUTION: CIO_ONLY_MANUAL · order routing disabled · pipeline orders generated: 0",
        "=" * 78,
    ])
    return "\n".join(lines)
