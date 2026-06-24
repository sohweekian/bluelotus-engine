from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_clients.config_loader import append_log, load_main_config, resolve_project_path
from orchestration.deterministic_clerk_orchestrator import DeterministicClerkOrchestrator


def pipeline_persist_db_enabled() -> bool:
    path = resolve_project_path("config/v3_pipeline.yaml")
    if not path.exists():
        return False
    try:
        import yaml

        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        pipeline = config.get("pipeline", {}) if isinstance(config.get("pipeline"), dict) else {}
        return bool(pipeline.get("persist_db"))
    except Exception:
        return False


def database_persistence_default_enabled() -> bool:
    config = load_main_config()
    return config.get("database_persistence", {}).get("enabled") is True


def database_persistence_fail_cycle_on_error() -> bool:
    config = load_main_config()
    return config.get("database_persistence", {}).get("fail_cycle_on_db_error") is True


def main() -> int:
    cycle_id = None
    persist_db = False
    for arg in sys.argv[1:]:
        if arg.startswith("--cycle-id="):
            cycle_id = arg.split("=", 1)[1].strip()
        if arg == "--persist-db":
            persist_db = True
    result = DeterministicClerkOrchestrator().run_cycle(cycle_id=cycle_id)
    if persist_db or pipeline_persist_db_enabled() or database_persistence_default_enabled():
        try:
            from orchestration.persist_v3_cycle_to_db import persist_cycle

            result["database_persistence"] = persist_cycle(result["cycle_dir"])
        except Exception as exc:
            result["database_persistence"] = {"ok": False, "error": str(exc)}
            append_log("v3_db_persistence_errors.log", f"{result.get('cycle_id')}: {exc}")
            if database_persistence_fail_cycle_on_error():
                result["ok"] = False
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
