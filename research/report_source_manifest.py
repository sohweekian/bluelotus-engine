"""Deterministic report source manifest — section hashes and dataset lineage."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

MANIFEST_VERSION = "slicdo_d1_v1.0"

# Bundle keys → (compute function id, primary dataset keys)
AUTHORITATIVE_SECTIONS: Dict[str, Dict[str, Any]] = {
    "operating_truth": {
        "compute_fn": "research.report_bundle.build_operating_truth",
        "source_keys": ["regime", "portfolio", "cross_market_confirmation", "meta"],
    },
    "causal_explanation": {
        "compute_fn": "research.report_bundle.build_causal_explanation",
        "bundle_key": "causal",
        "source_keys": ["cross_market_confirmation", "regime", "portfolio"],
    },
    "blind_spot": {
        "compute_fn": "research.report_bundle.build_blind_spot_checklist",
        "bundle_key": "blind",
        "source_keys": ["regime", "portfolio", "source_health"],
    },
    "concentration_risk": {
        "compute_fn": "research.report_bundle.build_concentration_risk",
        "bundle_key": "conc",
        "source_keys": ["portfolio", "portfolio_readonly"],
    },
    "consistency_audit": {
        "compute_fn": "research.report_bundle.build_consistency_audit",
        "bundle_key": "audit",
        "source_keys": ["meta", "regime", "portfolio"],
    },
    "gold_thesis_tracker": {
        "compute_fn": "research.report_bundle.build_gold_thesis_tracker",
        "bundle_key": "gold_thesis",
        "source_keys": ["portfolio", "cross_market_confirmation"],
    },
    "live_truth_reconciliation": {
        "compute_fn": "research.report_bundle.build_hygiene_truth_bundle",
        "bundle_key": "live_truth",
        "source_keys": ["portfolio", "portfolio_readonly", "execution"],
    },
    "cio_manual_strategy": {
        "compute_fn": "mid.cio_manual_reports.build_cio_manual_report_layer",
        "source_keys": ["cio_manual_report"],
    },
    "slicdo_summary": {
        "compute_fn": "learning.claim_registrars.register_from_dataset",
        "source_keys": ["slicdo", "prediction_layers", "nite_pei"],
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_payload(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle_section_payload(bundle: Dict[str, Any], spec: Dict[str, Any]) -> Any:
    key = spec.get("bundle_key") or spec.get("section_id")
    if key == "cio_manual_strategy":
        return bundle.get("cio_manual_report") or {}
    if key == "slicdo_summary":
        return bundle.get("slicdo_summary") or {}
    if key == "live_truth_reconciliation":
        return bundle.get("live_truth") or {}
    return bundle.get(key) or {}


def build_report_source_manifest(
    bundle: Dict[str, Any],
    *,
    dataset: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    dataset = dataset or {}
    sections: List[Dict[str, Any]] = []

    for section_id, spec in AUTHORITATIVE_SECTIONS.items():
        payload = _bundle_section_payload(bundle, {**spec, "section_id": section_id})
        if section_id == "cio_manual_strategy":
            payload = (dataset.get("cio_manual_report") or payload) if not payload else payload
        if section_id == "slicdo_summary":
            payload = dataset.get("slicdo") or payload

        sections.append({
            "section_id": section_id,
            "zone": "AUTHORITATIVE",
            "compute_fn": spec["compute_fn"],
            "source_keys": list(spec["source_keys"]),
            "content_sha256": _sha256_payload(payload),
            "non_empty": bool(payload),
        })

    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": _utc_now(),
        "section_count": len(sections),
        "sections": sections,
        "dataset_meta": {
            "cycle_id": (dataset.get("meta") or {}).get("cycle_id"),
            "generated_at": (dataset.get("meta") or {}).get("generated_at"),
            "dataset_sha256_hint": _sha256_payload({
                "meta": dataset.get("meta"),
                "regime": (dataset.get("regime") or {}).get("regime"),
            })[:16],
        },
    }


def build_deterministic_contract(
    bundle: Dict[str, Any],
    *,
    dataset: Optional[Dict[str, Any]] = None,
    narrative_quarantine: bool = True,
) -> Dict[str, Any]:
    from mid.narrative_firewall import narrative_quarantine_enabled

    quarantine = narrative_quarantine if narrative_quarantine is not None else narrative_quarantine_enabled()
    manifest = build_report_source_manifest(bundle, dataset=dataset)
    op = bundle.get("operating_truth") or {}
    return {
        "contract_version": MANIFEST_VERSION,
        "generated_at": _utc_now(),
        "zone_a_authority": "report_bundle",
        "zone_b_status": "QUARANTINED" if quarantine else "OBSERVATION",
        "narrative_quarantine": quarantine,
        "execution_authority": op.get("execution_authority", "CIO_ONLY_MANUAL"),
        "order_routing_enabled": bool(op.get("order_routing_enabled", False)),
        "orders_generated_by_pipeline": int(op.get("orders_generated_by_pipeline") or 0),
        "report_source_manifest": manifest,
        "authoritative_causal_status": (bundle.get("causal") or {}).get("causal_status"),
        "authoritative_blind_spot_status": (bundle.get("blind") or {}).get("blind_spot_status"),
    }


def validate_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    sections = manifest.get("sections") or []
    required = set(AUTHORITATIVE_SECTIONS.keys())
    present = {s.get("section_id") for s in sections if isinstance(s, dict)}
    missing = sorted(required - present)
    empty_required = [
        s.get("section_id")
        for s in sections
        if isinstance(s, dict)
        and s.get("section_id") in {"operating_truth", "causal_explanation", "blind_spot", "concentration_risk"}
        and not s.get("non_empty")
    ]
    ok = not missing and not empty_required
    return {
        "ok": ok,
        "missing_sections": missing,
        "empty_required_sections": empty_required,
        "section_count": len(sections),
    }
