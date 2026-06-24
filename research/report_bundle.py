"""Single compute pass for all BlueLotus V3 report renderers (Phase 1 trust upgrade)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


GOV_CONTRACT_FIELDS = (
    "cio_action",
    "confidence",
    "confidence_label",
    "causal_status",
    "blind_spot_status",
    "concentration_status",
    "_release_status",
    "governance_gate_score",
    "governance_gate_failed_gates",
    "governance_gate_passed_gates",
    "governance_gate_deductions",
    "sentiment_hygiene_gate",
)

# Live-computed in report_bundle — never overwrite from governance gate snapshot (prevents Check 2 drift).
LIVE_COMPUTE_FIELDS = frozenset({"causal_status", "blind_spot_status", "concentration_status"})


def merge_governance_contract(op_truth: Dict[str, Any]) -> Dict[str, Any]:
    from research.research_report_generator import _load_approved_truth_for_renderer

    approved = _load_approved_truth_for_renderer() or {}
    mirror: Dict[str, Any] = {}
    for field in GOV_CONTRACT_FIELDS:
        if field in LIVE_COMPUTE_FIELDS:
            if field in approved:
                mirror[field] = approved[field]
            continue
        if field in approved:
            op_truth[field] = approved[field]
    if mirror:
        op_truth["governance_mirror"] = mirror
    return op_truth


def build_consistency_discipline_payload(
    dataset: Dict[str, Any],
    archive: Dict[str, Any],
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    from research.research_report_generator import (
        CANONICAL_SECTION_ORDER,
        build_snapshot_hierarchy,
    )

    causal = bundle["causal"]
    blind = bundle["blind"]
    conc = bundle["conc"]
    audit = bundle["audit"]
    op_truth = bundle["operating_truth"]
    remediations = bundle["remediations"]
    action = bundle["action_logic"]
    chain = bundle["causal_chain"]
    risk_gov = bundle["risk_governor"]
    forecast = bundle["forecast_maturity"]
    freshness = bundle["freshness"]
    news = bundle["news_priority"]
    readiness = bundle["readiness"]
    gold_thesis = bundle["gold_thesis"]
    portfolio_truth = bundle["portfolio_truth"]
    live_truth = bundle["live_truth"]
    cio_certainty = bundle["cio_decisions_certainty"]

    rf_data = dataset.get("research_forecasting") or {}
    acc_data = rf_data.get("accuracy_summary") or []
    resolved = sum(int(r.get("resolved_count") or 0) for r in acc_data if isinstance(r, dict))
    brier_mat = (
        "MATURE" if resolved >= 100 else "NOT_MATURE" if resolved >= 30 else "COLLECTING"
    )

    rc_iq = dataset.get("institutional_quant") or {}
    rc_db = archive.get("database_row") or {}
    rc_qri = float(
        rc_db.get("quant_readiness_index")
        or rc_db.get("quant_readiness_score")
        or rc_iq.get("readiness_score")
        or 0
    )
    rc_qrl = (
        rc_db.get("quant_readiness_label")
        or rc_iq.get("readiness_label")
        or (
            "INSTITUTIONAL_READY"
            if rc_qri >= 90
            else "REVIEW_REQUIRED"
            if rc_qri >= 75
            else "NOT_READY"
        )
    )
    rc_gm_cluster = (gold_thesis.get("thesis_action") or {}).get("gold_miner_cluster_weight", 0.0) or 0.0
    rc_causal_pass = causal.get("pass_count", 0)
    rc_causal_total = causal.get("pass_count", 0) + causal.get("fail_count", 0)
    rc_blind_pass = blind.get("pass_count", 0)
    rc_blind_fail = blind.get("fail_count", 0)

    consistency_discipline: Dict[str, Any] = {
        "causal_explanation": {
            "status": causal["causal_status"],
            "confidence": causal["causal_confidence"],
            "pass_count": causal["pass_count"],
            "fail_count": causal["fail_count"],
            "critical_checks": causal["critical_checks"],
            "primary_driver": causal["primary_driver"],
            "missing_inputs": causal["missing_inputs"],
        },
        "blind_spot": {
            "status": blind["blind_spot_status"],
            "pass_count": blind["pass_count"],
            "fail_count": blind["fail_count"],
            "cio_penalty": blind["cio_penalty"],
            "failed_items": blind["failed_items"],
            "remediations": remediations,
        },
        "concentration_risk": {
            "status": conc["concentration_status"],
            "hhi": conc["hhi"],
            "top3_weight": conc["top3_weight"],
            "largest_ticker": conc["largest_ticker"],
            "largest_weight": conc["largest_weight"],
            "clusters": conc["clusters"],
            "thresholds": {
                "NORMAL": "<0.35 HHI/<35% top1",
                "ELEVATED": "<0.50/<50%",
                "HIGH": "<0.65/<65%",
                "CRITICAL": ">=0.65/>=65%",
            },
        },
        "consistency_audit": {
            "status": audit["audit_status"],
            "report_status": audit.get("report_status", ""),
            "score": audit["audit_score"],
            "pass_count": audit["pass_count"],
            "warn_count": audit["warn_count"],
            "fail_count": audit["fail_count"],
            "check_results": {r[0]: r[1] for r in audit["check_rows"]},
        },
        "brier_accountability": {
            "maturity": brier_mat,
            "resolved_total": resolved,
            "required_for_reporting": 30,
            "required_for_significance": 100,
            "note": (
                "COLLECTING: no meaningful Brier signal yet — insufficient resolved forecasts."
                if brier_mat == "COLLECTING"
                else (
                    "NOT_MATURE: some signal but insufficient for full statistical accountability."
                    if brier_mat == "NOT_MATURE"
                    else "MATURE: statistically meaningful Brier accountability established."
                )
            ),
        },
        "cio_action_logic": action,
        "causal_chain": chain[:5],
        "portfolio_risk_governor": risk_gov,
        "forecast_maturity": forecast,
        "freshness_governor": {
            "freshness_status": freshness.get("freshness_status"),
            "stale_sections": freshness.get("stale_sections"),
            "critical_stale_sections": freshness.get("critical_stale_sections"),
            "non_critical_stale_sections": freshness.get("non_critical_stale_sections"),
            "confidence_penalty": freshness.get("confidence_penalty"),
        },
        "news_priority": news,
        "report_readiness": readiness,
        "gold_thesis_tracker": gold_thesis,
        "portfolio_truth_resolver": {
            "source_name": portfolio_truth.get("source_name"),
            "source_age_minutes": portfolio_truth.get("source_age_minutes"),
            "freshness": portfolio_truth.get("freshness"),
            "confidence": portfolio_truth.get("confidence"),
            "cio_action_cap": portfolio_truth.get("cio_action_cap"),
            "mismatch_detail": portfolio_truth.get("mismatch_detail"),
            "label": portfolio_truth.get("label"),
        },
        "live_truth_consistency": live_truth,
        "cio_decisions_certainty": cio_certainty,
    }
    consistency_discipline["report_control"] = {
        "canonical_version": "v2r6",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_hierarchy": build_snapshot_hierarchy(dataset),
        "operating_truth": {
            "regime": op_truth.get("regime", ""),
            "regime_score": op_truth.get("regime_score", 0),
            "cio_action": op_truth.get("cio_action", "WAIT / HOLD"),
            "report_status": op_truth.get("report_readiness", "PENDING"),
            "quant_process_readiness": rc_qrl,
            "quant_process_score": round(rc_qri, 1),
            "causal_status": op_truth.get("causal_status", "UNKNOWN"),
            "causal_pass": rc_causal_pass,
            "causal_total": rc_causal_total,
            "blind_spot_status": op_truth.get("blind_spot_status", "UNKNOWN"),
            "blind_spot_pass": rc_blind_pass,
            "blind_spot_fail": rc_blind_fail,
            "gold_thesis_status": op_truth.get("gold_thesis_status", "UNKNOWN"),
            "gold_thesis_score": round(float(op_truth.get("gold_thesis_score", 0.0) or 0), 3),
            "gold_thesis_confidence": gold_thesis.get("confidence", "UNKNOWN"),
            "gold_add_allowed": op_truth.get("gold_add_allowed", False),
            "concentration_status": op_truth.get("concentration_status", "UNKNOWN"),
            "gold_miner_cluster_pct": (
                round(float(rc_gm_cluster) * 100, 1)
                if rc_gm_cluster <= 1.0
                else round(float(rc_gm_cluster), 1)
            ),
            "execution_authority": op_truth.get("execution_authority", "CIO_ONLY_MANUAL"),
            "order_routing_enabled": op_truth.get("order_routing_enabled", False),
            "orders_generated_by_pipeline": op_truth.get("orders_generated_by_pipeline", 0),
            "live_truth_consistency": (live_truth or {}).get("live_truth_consistency", "NOT_RUN"),
        },
    }
    consistency_discipline["cross_asset_floor_tracker"] = {
        "status": "NOT_YET_IMPLEMENTED",
        "gold_floor_status": "WATCH",
        "beta_floor_status": "WATCH",
        "liquidity_stress_status": "STABLE",
        "synchronized_floor_score": None,
        "cio_action": "WAIT",
        "reload_allowed": False,
        "reason": "Requires floor defense confirmation. Module not yet implemented.",
    }
    consistency_discipline["certainty_labels"] = {
        "DATA_CONFIRMED": "Direct from live data sources (DB, broker, market feed)",
        "MODEL_INFERRED": "Computed by internal model from confirmed inputs",
        "PROVISIONAL": "Best-estimate with known uncertainty or partial inputs",
        "CIO_THESIS": "CIO-authored non-negotiable doctrine or standing rule",
        "UNVERIFIED": "Claimed by model but not from a primary data source",
        "MISSING": "Known data gap — data that should exist is absent",
    }
    consistency_discipline["canonical_section_order"] = CANONICAL_SECTION_ORDER
    consistency_discipline["operating_truth"] = op_truth
    return consistency_discipline


def build_report_bundle(dataset: Dict[str, Any], archive: Dict[str, Any]) -> Dict[str, Any]:
    """Canonical single-pass report computation for TXT, Excel, Word, and delivery JSON."""
    from research.research_report_generator import (
        CERTAINTY_LABELS,
        _build_section_a_reconciliation,
        _cio_decisions_certainty_label,
        _load_approved_truth_for_renderer,
        build_blind_spot_checklist,
        build_blind_spot_remediations,
        build_causal_chain,
        build_causal_explanation,
        build_cio_action_logic,
        build_cio_briefing_model,
        build_consistency_audit,
        build_concentration_risk,
        build_forecast_maturity_schedule,
        build_freshness_governor,
        build_gold_thesis_tracker,
        build_hygiene_truth_bundle,
        build_news_priority_engine,
        build_operating_truth,
        build_portfolio_risk_governor,
        build_report_readiness,
        detect_archive_live_mismatches,
    )

    causal = build_causal_explanation(dataset)
    blind = build_blind_spot_checklist(dataset)
    conc = build_concentration_risk(dataset)
    op_pre = build_operating_truth(dataset, archive, causal, blind, conc)
    audit = build_consistency_audit(
        dataset, archive, causal_data=causal, blind_data=blind, operating_truth=op_pre,
    )
    op_truth = build_operating_truth(dataset, archive, causal, blind, conc, audit)
    approved_truth = _load_approved_truth_for_renderer() or {}
    op_truth = merge_governance_contract(op_truth)

    action_logic = build_cio_action_logic(op_truth, dataset)
    remediations = build_blind_spot_remediations(blind)
    causal_chain = build_causal_chain(dataset, causal)
    risk_governor = build_portfolio_risk_governor(dataset, conc)
    forecast_maturity = build_forecast_maturity_schedule(dataset)
    freshness = build_freshness_governor(dataset)
    news_priority = build_news_priority_engine(dataset, op_truth)
    readiness = build_report_readiness(op_truth, freshness)
    op_truth["report_readiness"] = readiness["classification"]
    mismatches = detect_archive_live_mismatches(op_truth, archive)

    hygiene = build_hygiene_truth_bundle(dataset, op_truth)
    portfolio_truth = hygiene["portfolio_truth"]
    live_truth = hygiene["live_truth"]

    gold_thesis = build_gold_thesis_tracker(dataset)
    op_truth["gold_thesis_status"] = gold_thesis.get("status", "UNKNOWN")
    op_truth["gold_thesis_score"] = gold_thesis.get("score", 0.0)
    op_truth["gold_add_allowed"] = gold_thesis.get("thesis_action", {}).get("add_allowed", False)

    briefing_model = build_cio_briefing_model(
        dataset,
        archive,
        causal_data=causal,
        blind_data=blind,
        operating_truth=op_truth,
        action_logic=action_logic,
        freshness_data=freshness,
        news_data=news_priority,
        conc_data=conc,
        audit_data=audit,
    )

    cio_certainty = _cio_decisions_certainty_label(dataset)
    cio_certainty_tag = CERTAINTY_LABELS.get(cio_certainty, f"[{cio_certainty}]")

    section_a_text = _build_section_a_reconciliation(
        portfolio_truth=portfolio_truth or {},
        live_truth=live_truth or {},
        dataset=dataset,
        op_truth=op_truth,
    )

    partial = {
        "causal": causal,
        "blind": blind,
        "conc": conc,
        "audit": audit,
        "operating_truth": op_truth,
        "approved_truth": approved_truth,
        "action_logic": action_logic,
        "remediations": remediations,
        "causal_chain": causal_chain,
        "risk_governor": risk_governor,
        "forecast_maturity": forecast_maturity,
        "freshness": freshness,
        "news_priority": news_priority,
        "readiness": readiness,
        "mismatches": mismatches,
        "hygiene": hygiene,
        "portfolio_truth": portfolio_truth,
        "live_truth": live_truth,
        "gold_thesis": gold_thesis,
        "briefing_model": briefing_model,
        "cio_decisions_certainty": cio_certainty,
        "cio_decisions_certainty_tag": cio_certainty_tag,
        "section_a_text": section_a_text,
    }
    partial["consistency_discipline"] = build_consistency_discipline_payload(
        dataset, archive, partial,
    )
    return partial


def live_truth_blocks_readiness(bundle: Dict[str, Any]) -> bool:
    """True when live truth reconciliation must cap report readiness."""
    status = (bundle.get("live_truth") or {}).get("live_truth_consistency", "NOT_RUN")
    return status in ("NOT_RUN", "FAIL")
