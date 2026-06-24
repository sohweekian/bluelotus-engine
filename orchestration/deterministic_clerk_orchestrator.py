from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from archive.learning_loop_archive import write_learning_loop_snapshot
from archive.strategist_archive import write_json, write_text
from chief_strategist.deterministic_clerk_digest import (
    build_deterministic_clerk_briefing,
    load_delivery,
    load_full_dataset,
    load_operating_truth,
    load_operator_full,
    render_clerk_digest_text,
)
from governance.contradiction_governance import (
    build_contradiction_governance,
    build_cio_decision_strip,
    collect_allowed_actions,
    collect_blocked_actions,
    write_contradiction_governance,
)
from llm_clients.config_loader import append_log, load_dotenv
from llm_clients.json_response_validator import validate_json_response
from orchestration.cycle_context_builder import build_cycle_context, cycle_output_root
from orchestration.publish_ready_pointer import write_publish_ready_pointer


class DeterministicClerkOrchestrator:
    """Zone A clerk cycle — no Qwen/LLM agents."""

    def run_cycle(self, cycle_id: str | None = None) -> Dict[str, Any]:
        load_dotenv()
        cycle_context = build_cycle_context(cycle_id)
        cycle_dir = cycle_output_root(str(cycle_context["cycle_id"]))
        cycle_dir.mkdir(parents=True, exist_ok=True)
        cycle_context["cycle_dir"] = str(cycle_dir)

        operator_pack = cycle_context["operator_verdict_pack"]
        validate_json_response(json.dumps(operator_pack), "OPERATOR_VERDICT_PACK_SCHEMA_PATH", save_failed=False)
        write_json(cycle_dir, "operator_verdict_pack.json", operator_pack)

        delivery = load_delivery()
        operating_truth = load_operating_truth(delivery)
        dataset = load_full_dataset(cycle_context)
        operator_full = load_operator_full(operator_pack)

        stub_briefing = {
            "cycle_id": cycle_context["cycle_id"],
            "summary": "",
            "recommended_posture": str(operating_truth.get("cio_action", "WAIT / HOLD")),
            "manual_execution_required": True,
            "llm_order_generation": False,
        }
        contradiction_governance = build_contradiction_governance(
            cycle_context,
            reports=[],
            briefing=stub_briefing,
            quality_summary={},
            agent_errors=[],
            full_dataset=dataset,
            operating_truth=operating_truth,
        )
        register = contradiction_governance["contradiction_register"]
        briefing = build_deterministic_clerk_briefing(
            cycle_context,
            operating_truth,
            operator_pack,
            operator_full,
            dataset,
            register,
        )
        validate_json_response(json.dumps(briefing), "CHIEF_STRATEGIST_BRIEFING_SCHEMA_PATH", save_failed=False)

        blocked = sorted(collect_blocked_actions(operator_pack, operator_full))
        allowed = sorted(collect_allowed_actions(operator_pack, operator_full, []))
        strip = build_cio_decision_strip(
            str(cycle_context["cycle_id"]),
            briefing,
            blocked,
            allowed,
            register.get("contradictions", []),
            register.get("created_at_sgt", ""),
        )
        contradiction_governance = {
            "contradiction_register": register,
            "cio_decision_strip": strip,
        }
        contradiction_paths = write_contradiction_governance(cycle_dir, contradiction_governance)

        digest_text = render_clerk_digest_text(
            briefing,
            contradiction_governance["contradiction_register"],
            operating_truth,
        )
        write_json(cycle_dir, "chief_strategist_briefing.json", briefing)
        write_json(cycle_dir, "chief_clerk_digest.json", {
            "schema_version": "bluelotus_v3_deterministic_clerk_digest_v1.0",
            "cycle_id": cycle_context["cycle_id"],
            "clerk_mode": "deterministic",
            "llm_council_enabled": False,
            "digest_layers": briefing.get("digest_layers", []),
            "operating_truth_excerpt": {
                key: operating_truth.get(key)
                for key in (
                    "regime", "cio_action", "causal_status",
                    "governance_gate_score", "governance_gate_failed_gates",
                    "brier_status", "report_readiness",
                )
                if key in operating_truth
            },
            "contradiction_count": register.get("contradiction_count", 0),
            "manual_execution_required": True,
            "llm_order_generation": False,
        })
        write_text(cycle_dir, "chief_clerk_digest.txt", digest_text)
        write_text(cycle_dir, "chief_strategist_report.txt", digest_text)

        learning_snapshot = {
            "mode": "deterministic_clerk",
            "cycle_id": cycle_context["cycle_id"],
            "validated_agent_reports": 0,
            "agent_errors": [],
            "quality_summary": {},
            "contradiction_governance": {
                "contradiction_count": register.get("contradiction_count", 0),
                "p1_count": register.get("p1_count", 0),
                "p2_count": register.get("p2_count", 0),
                "p3_count": register.get("p3_count", 0),
                "cio_decision_strip": contradiction_paths["cycle_cio_decision_strip"],
            },
            "llm_council_enabled": False,
            "prompt_architecture_enabled": False,
            "manual_execution_required": True,
            "llm_order_generation": False,
        }
        write_learning_loop_snapshot(cycle_dir, learning_snapshot)
        write_json(cycle_dir, "learning_loop_snapshot.json", learning_snapshot)

        try:
            from learning.cycle_report import build_learning_cycle_report

            learning_report = build_learning_cycle_report(learning_snapshot, run_proposals=False)
            write_json(cycle_dir, "learning_cycle_report.json", learning_report)
        except Exception as exc:
            append_log("v3_slicdo_learning.log", f"{cycle_context['cycle_id']}: learning report failed: {exc}")

        write_publish_ready_pointer(
            str(cycle_context["cycle_id"]),
            cycle_dir,
            mode="deterministic_clerk",
            extra={"publish_ready": True},
        )

        return {
            "ok": True,
            "mode": "deterministic_clerk",
            "cycle_id": cycle_context["cycle_id"],
            "cycle_dir": str(cycle_dir),
            "validated_agent_reports": 0,
            "llm_council_enabled": False,
            "chief_strategist_briefing": str(cycle_dir / "chief_strategist_briefing.json"),
            "chief_clerk_digest": str(cycle_dir / "chief_clerk_digest.txt"),
            "contradiction_register": contradiction_paths["cycle_contradiction_register"],
            "cio_decision_strip": contradiction_paths["cycle_cio_decision_strip"],
        }
