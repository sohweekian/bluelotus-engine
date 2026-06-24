from __future__ import annotations

from typing import Any, Dict, List


READ_FIRST_TITLE = "CIO CONTEXT CAPSULE - READ FIRST"
READ_FIRST_TITLE_UNICODE = "CIO CONTEXT CAPSULE - READ FIRST"
MASTER_PROMPT_TITLE = "CHIEF CLERK / CONTRADICTION MAPPER MASTER PROMPT"
MASTER_PROMPT_TITLE_UNICODE = "CHIEF CLERK / CONTRADICTION MAPPER MASTER PROMPT"


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (list, tuple)):
        return "; ".join(_text(v) for v in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_text(v)}" for k, v in value.items())
    return str(value)


def get_capsule(dataset: Dict[str, Any]) -> Dict[str, Any]:
    capsule = dataset.get("cio_context_capsule") or {}
    return capsule if isinstance(capsule, dict) else {}


def get_master_prompt(dataset: Dict[str, Any]) -> Dict[str, Any]:
    prompt = dataset.get("chief_clerk_contradiction_mapper_master_prompt") or {}
    if not isinstance(prompt, dict) or not prompt:
        prompt = dataset.get("chief_strategist_master_prompt") or {}
    return prompt if isinstance(prompt, dict) else {}


def master_prompt_is_active(dataset: Dict[str, Any]) -> bool:
    prompt = get_master_prompt(dataset)
    return (
        prompt.get("status") == "ACTIVE"
        and prompt.get("role_name") == "Chief Clerk / Contradiction Mapper"
        and prompt.get("role_authority") == "CLERK_ONLY"
        and prompt.get("strategic_authority") is False
        and prompt.get("analyst_authority") is False
        and prompt.get("execution_authority") == "NONE"
        and prompt.get("order_routing_enabled") is False
        and int(prompt.get("system_orders_generated", -1)) == 0
        and prompt.get("mandatory_for_chief_clerk") is True
        and prompt.get("read_first") is True
        and int(prompt.get("priority", -1)) == 0
        and bool(prompt.get("prompt_hash"))
        and bool(prompt.get("master_prompt_text"))
    )


def capsule_is_active(dataset: Dict[str, Any]) -> bool:
    capsule = get_capsule(dataset)
    doctrine = capsule.get("core_doctrine") or {}
    return (
        capsule.get("status") == "ACTIVE"
        and capsule.get("active_llm_role") == "Chief Clerk / Contradiction Mapper"
        and doctrine.get("execution_authority") == "CIO_ONLY_MANUAL"
        and doctrine.get("order_routing_enabled") is False
        and int(doctrine.get("system_generated_orders") or 0) == 0
        and doctrine.get("llm_role_authority") == "CLERK_ONLY"
        and doctrine.get("llm_strategic_authority") is False
        and doctrine.get("llm_analyst_authority") is False
        and doctrine.get("llm_execution_authority") == "NONE"
        and bool(capsule.get("capsule_hash"))
    )


def build_master_prompt_rows(dataset: Dict[str, Any]) -> List[List[Any]]:
    prompt = get_master_prompt(dataset)
    return [
        ["Field", "Value", "Certainty", "Source Layer"],
        ["Version", prompt.get("version", ""), "DATA_CONFIRMED", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Status", prompt.get("status", ""), "DATA_CONFIRMED", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Role Name", prompt.get("role_name", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Role Authority", prompt.get("role_authority", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Strategic Authority", prompt.get("strategic_authority", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Analyst Authority", prompt.get("analyst_authority", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Execution Authority", prompt.get("execution_authority", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Order Routing Enabled", prompt.get("order_routing_enabled", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["System Orders Generated", prompt.get("system_orders_generated", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Mandatory for Chief Clerk", prompt.get("mandatory_for_chief_clerk", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Read First", prompt.get("read_first", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Priority", prompt.get("priority", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Prompt Hash", prompt.get("prompt_hash", ""), "DATA_CONFIRMED", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Core Instruction", prompt.get("core_instruction", ""), "GOVERNANCE_RULE", "chief_clerk_contradiction_mapper_master_prompt"],
        ["Source Priority", _text(prompt.get("source_priority") or []), "GOVERNANCE_RULE", "source_priority"],
        ["Required Response Sequence", _text(prompt.get("required_response_sequence") or []), "GOVERNANCE_RULE", "required_response_sequence"],
        ["Contradiction Map Schema", _text(prompt.get("contradiction_map_schema") or {}), "GOVERNANCE_RULE", "contradiction_map_schema"],
        ["Readiness Change Fields", _text(prompt.get("readiness_change_fields") or []), "GOVERNANCE_RULE", "readiness_change_fields"],
        ["Allowed Functions", _text(prompt.get("allowed_functions") or []), "GOVERNANCE_RULE", "allowed_functions"],
        ["Forbidden Functions", _text(prompt.get("forbidden_functions") or []), "GOVERNANCE_RULE", "forbidden_functions"],
        ["Forbidden Behaviors", _text(prompt.get("forbidden_behaviors") or []), "GOVERNANCE_RULE", "forbidden_behaviors"],
        ["Full Master Prompt Text", prompt.get("master_prompt_text", ""), "GOVERNANCE_RULE", "master_prompt_text"],
    ]


def render_master_prompt_text_section(dataset: Dict[str, Any], unicode_title: bool = False) -> str:
    prompt = get_master_prompt(dataset)
    title = MASTER_PROMPT_TITLE_UNICODE if unicode_title else MASTER_PROMPT_TITLE
    line = "=" * 78
    short = "=" * 60
    lines = [
        line,
        title,
        short,
        f"Version: {prompt.get('version', 'MISSING')}",
        f"Status: {prompt.get('status', 'MISSING')}",
        f"Role Name: {prompt.get('role_name', 'MISSING')}",
        f"Role Authority: {prompt.get('role_authority', 'MISSING')}",
        f"Strategic Authority: {_text(prompt.get('strategic_authority'))}",
        f"Analyst Authority: {_text(prompt.get('analyst_authority'))}",
        f"Clerk Execution Authority: {prompt.get('execution_authority', 'MISSING')}",
        f"Mandatory for Chief Clerk: {_text(prompt.get('mandatory_for_chief_clerk'))}",
        f"Read First: {_text(prompt.get('read_first'))}",
        f"Priority: {prompt.get('priority', '')}",
        f"Prompt Hash: {prompt.get('prompt_hash', '')}",
        "",
        "Chief Clerk / Contradiction Mapper Master Prompt: ACTIVE / MANDATORY / READ FIRST",
        f"Prompt Version: {prompt.get('version', '')}",
        f"Prompt Hash: {prompt.get('prompt_hash', '')}",
        "CIO Context Capsule Status: ACTIVE",
        "Pipeline Execution Authority: CIO_ONLY_MANUAL",
        "Clerk Execution Authority: NONE",
        "Order Routing Enabled: FALSE",
        "System Orders Generated: 0",
        "",
        "Core Instruction:",
        prompt.get("core_instruction", ""),
        "",
        "Source Priority:",
    ]
    for idx, item in enumerate(prompt.get("source_priority") or [], start=1):
        lines.append(f"{idx}. {item}")
    lines.extend(["", "Required Response Sequence:"])
    for idx, item in enumerate(prompt.get("required_response_sequence") or [], start=1):
        lines.append(f"{idx}. {item}")
    lines.extend(["", "CONTRADICTION MAP:"])
    for key, value in (prompt.get("contradiction_map_schema") or {}).items():
        lines.append(f"- {key}: {_text(value)}")
    lines.extend(["", "READINESS CHANGE LOG:"])
    for item in prompt.get("readiness_change_fields") or []:
        lines.append(f"- {item}")
    lines.extend(["", "Forbidden Behaviors:"])
    for item in prompt.get("forbidden_behaviors") or []:
        lines.append(f"- {item}")
    lines.extend(["", "Full Master Prompt Text:", prompt.get("master_prompt_text", ""), line])
    return "\n".join(lines).strip() + "\n"


def build_cio_context_rows(dataset: Dict[str, Any]) -> List[List[Any]]:
    capsule = get_capsule(dataset)
    doctrine = capsule.get("core_doctrine") or {}
    decision = capsule.get("latest_cio_layer_decision") or {}
    record = capsule.get("cio_three_step_record") or {}
    sleeves = capsule.get("active_sleeve_rules") or {}
    return [
        ["section_title", READ_FIRST_TITLE, "DATA_CONFIRMED", "cio_context_capsule"],
        ["version", capsule.get("version", ""), "DATA_CONFIRMED", "cio_context_capsule"],
        ["active_llm_role", capsule.get("active_llm_role", ""), "GOVERNANCE_RULE", "cio_context_capsule"],
        ["mandatory_for_chief_clerk", capsule.get("mandatory_for_all_chief_clerk_replies", ""), "DATA_CONFIRMED", "cio_context_capsule"],
        ["latest_cio_decision", _text(decision), "CIO_RECORD", "latest_cio_layer_decision"],
        ["strategic_thinking", _text(record.get("strategic_thinking")), "CIO_RECORD", "cio_three_step_record"],
        ["strategic_planning", _text(record.get("strategic_planning")), "CIO_RECORD", "cio_three_step_record"],
        ["strategic_execution", _text(record.get("strategic_execution")), "CIO_RECORD", "cio_three_step_record"],
        ["execution_authority", doctrine.get("execution_authority", ""), "GOVERNANCE_RULE", "core_doctrine"],
        ["order_routing_enabled", doctrine.get("order_routing_enabled", ""), "GOVERNANCE_RULE", "core_doctrine"],
        ["system_orders_generated", doctrine.get("system_generated_orders", ""), "GOVERNANCE_RULE", "core_doctrine"],
        ["llm_subordination_rule", doctrine.get("llm_subordination_rule", ""), "GOVERNANCE_RULE", "core_doctrine"],
        ["second_tranche_authorized", "FALSE", "GOVERNANCE_RULE", "core_doctrine"],
        ["dca_rule", doctrine.get("dca_rule", ""), "GOVERNANCE_RULE", "core_doctrine"],
        ["cash_fortress", _text(sleeves.get("cash_fortress")), "CIO_RULE", "active_sleeve_rules"],
        ["gold_miners_policy", _text(sleeves.get("gold_miners")), "CIO_RULE", "active_sleeve_rules"],
        ["banks_policy", _text(sleeves.get("banks_bac_wfc")), "CIO_RULE", "active_sleeve_rules"],
        ["high_beta_policy", _text(sleeves.get("high_beta_satellites")), "CIO_RULE", "active_sleeve_rules"],
        ["pl_asts_policy", _text(sleeves.get("foundational_tactical_cash_engine")), "CIO_RULE", "active_sleeve_rules"],
        ["kill_conditions", _text(capsule.get("kill_conditions") or []), "GOVERNANCE_RULE", "kill_conditions"],
        ["bootstrap_prompt", ((capsule.get("conversation_bootstrap_prompt") or {}).get("text") or ""), "GOVERNANCE_RULE", "conversation_bootstrap_prompt"],
        ["capsule_hash", capsule.get("capsule_hash", ""), "DATA_CONFIRMED", "cio_context_capsule"],
    ]


def render_cio_context_text_section(dataset: Dict[str, Any], unicode_title: bool = False) -> str:
    capsule = get_capsule(dataset)
    doctrine = capsule.get("core_doctrine") or {}
    decision = capsule.get("latest_cio_layer_decision") or {}
    record = capsule.get("cio_three_step_record") or {}
    thinking = record.get("strategic_thinking") or {}
    planning = record.get("strategic_planning") or {}
    execution = record.get("strategic_execution") or {}
    sleeves = capsule.get("active_sleeve_rules") or {}
    title = READ_FIRST_TITLE_UNICODE if unicode_title else READ_FIRST_TITLE
    line = "=" * 78
    lines = [
        line,
        f"  {title}",
        line,
        f"Version: {capsule.get('version', 'MISSING')}",
        f"Active LLM Role: {capsule.get('active_llm_role', 'Chief Clerk / Contradiction Mapper')}",
        f"Mandatory for Chief Clerk: {_text(capsule.get('mandatory_for_all_chief_clerk_replies'))}",
        f"Capsule Hash: {capsule.get('capsule_hash', '')}",
        "",
        "Latest CIO Decision Record:",
        f"CIO manual event-scout record. Classification: {decision.get('classification', '')}. Not full risk-on: {_text(decision.get('not_full_risk_on'))}. Not second tranche: {_text(decision.get('not_second_tranche'))}.",
        "",
        "CIO Strategic Thinking Record:",
        thinking.get("summary", ""),
        f"Core Interpretation: {thinking.get('core_interpretation', '')}",
        f"Market Read: {thinking.get('market_read', '')}",
        "",
        "CIO Strategic Planning Record:",
        f"Gold miners: {planning.get('gold_miners', '')}",
        f"Banks: {planning.get('banks', '')}",
        f"High beta satellites: {planning.get('high_beta', '')}",
        f"PL/ASTS tactical cash engine: {planning.get('foundational_tactical_cash_engine', '')}",
        f"DCA: {planning.get('dca_rule', '')}",
        "",
        "Strategic Execution:",
        f"{execution.get('positioning_status', '')} Execution mode: {execution.get('execution_mode', doctrine.get('execution_authority', ''))}. No system orders. No routing. Scout positioning only, not second tranche.",
        f"LLM Subordination Rule: {doctrine.get('llm_subordination_rule', '')}",
        "",
        "Active Sleeve Rules:",
    ]
    for key, sleeve in sleeves.items():
        if isinstance(sleeve, dict):
            lines.append(f"- {key}: {sleeve.get('current_policy', '')} | {sleeve.get('allowed', '')} | Forbidden: {sleeve.get('forbidden', '')}")
    lines.extend([
        "",
        "Kill Conditions:",
        "- " + "\n- ".join(capsule.get("kill_conditions") or []),
        "",
        "Bootstrap Instruction:",
        (capsule.get("conversation_bootstrap_prompt") or {}).get("text", ""),
        "",
        "Hard Rule:",
        doctrine.get("tactical_score_rule", ""),
        line,
    ])
    return "\n".join(lines).strip() + "\n"


def prepend_cio_context_text_section(report_text: str, dataset: Dict[str, Any]) -> str:
    if READ_FIRST_TITLE in report_text or READ_FIRST_TITLE_UNICODE in report_text:
        return report_text
    return render_cio_context_text_section(dataset).rstrip() + "\n\n" + report_text.lstrip()


def prepend_master_prompt_and_cio_context(report_text: str, dataset: Dict[str, Any]) -> str:
    text = prepend_cio_context_text_section(report_text, dataset)
    if MASTER_PROMPT_TITLE in text or MASTER_PROMPT_TITLE_UNICODE in text:
        return text
    return render_master_prompt_text_section(dataset).rstrip() + "\n\n" + text.lstrip()
