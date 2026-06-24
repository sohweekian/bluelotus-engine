from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from zoneinfo import ZoneInfo

from governance.contradiction_governance import collect_allowed_actions, collect_blocked_actions
from llm_clients.config_loader import env_required, load_dotenv, load_main_config, load_yaml_from_env, resolve_project_path
from llm_clients.model_router import get_default_model_role, get_model_config


def cycle_config(main_config: Dict[str, Any]) -> Dict[str, Any]:
    """Production clerk cycle paths (grand_cycle key retained for backward compatibility)."""
    cycle = main_config.get("deterministic_cycle")
    if isinstance(cycle, dict) and cycle:
        return cycle
    legacy = main_config.get("grand_cycle", {})
    return legacy if isinstance(legacy, dict) else {}


def load_operator_source_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def build_cycle_context(cycle_id: str | None = None) -> Dict[str, Any]:
    load_dotenv()
    main_config = load_main_config()
    cycle = cycle_config(main_config)
    active_cycle_id = cycle_id or make_cycle_id(str(cycle.get("default_cycle_prefix", "cycle")))
    dataset_path = resolve_project_path(str(cycle.get("dataset_snapshot_path", "")))
    live_news_path = resolve_project_path(str(cycle.get("live_news_brief_path", "")))
    operator_source_path = resolve_project_path(str(cycle.get("deterministic_operator_path", "")))
    brier_path = resolve_project_path(str(cycle.get("brier_observation_path", "")))
    model_role = get_default_model_role()
    model_config = get_model_config(model_role)
    operator_pack = wrap_operator_verdict_pack(active_cycle_id, operator_source_path)
    return {
        "cycle_id": active_cycle_id,
        "model_used": str(model_config.get("model_name", "")),
        "input_refs": {
            "dataset_snapshot_id": describe_path(dataset_path),
            "operator_pack_id": operator_pack["operator_pack_id"],
            "thesis_registry_version": str(load_yaml_from_env("THESIS_REGISTRY_PATH").get("registry_version", "")),
            "live_news_brief_timestamp": describe_path(live_news_path),
        },
        "dataset_summary": summarize_json_file(dataset_path),
        "live_news_summary": summarize_json_file(live_news_path),
        "brier_summary": summarize_json_file(brier_path),
        "thesis_registry": load_yaml_from_env("THESIS_REGISTRY_PATH"),
        "operator_verdict_pack": operator_pack,
    }


def wrap_operator_verdict_pack(cycle_id: str, source_path: Path) -> Dict[str, Any]:
    operator_full = load_operator_source_json(source_path)
    source_summary = summarize_json_file(source_path)
    pack_stub: Dict[str, Any] = {
        "blocked_actions": operator_full.get("blocked_actions", []) if isinstance(operator_full.get("blocked_actions"), list) else [],
        "allowed_actions": operator_full.get("allowed_actions", []) if isinstance(operator_full.get("allowed_actions"), list) else [],
    }
    blocked = sorted(collect_blocked_actions(pack_stub, operator_full))
    allowed = sorted(collect_allowed_actions(pack_stub, operator_full, []))
    return {
        "schema_version": "bluelotus_v3_operator_verdict_pack_v1.0",
        "cycle_id": cycle_id,
        "operator_pack_id": describe_path(source_path),
        "source_summary": source_summary,
        "blocked_actions": blocked,
        "allowed_actions": allowed,
        "manual_execution_required": True,
        "llm_order_generation": False,
    }


def build_operator_pack(cycle_id: str, source_path: Path) -> Dict[str, Any]:
    """Deprecated alias — use wrap_operator_verdict_pack."""
    return wrap_operator_verdict_pack(cycle_id, source_path)


def summarize_json_file(path: Path, max_chars: int = 800) -> Dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"exists": True, "path": str(path), "parse_error": str(exc)}
    text = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
    return {
        "exists": True,
        "path": str(path),
        "last_write": datetime.fromtimestamp(path.stat().st_mtime, ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds"),
        "excerpt": text[:max_chars],
    }


def describe_path(path: Path) -> str:
    if not path.exists():
        return f"missing:{path.name}"
    stamp = datetime.fromtimestamp(path.stat().st_mtime, ZoneInfo("Asia/Singapore")).strftime("%Y%m%dT%H%M%S")
    return f"{path.stem}:{stamp}"


def make_cycle_id(prefix: str) -> str:
    stamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}"


def cycle_output_root(cycle_id: str) -> Path:
    root = resolve_project_path(env_required("V3_CYCLE_OUTPUT_DIR"))
    return root / cycle_id
