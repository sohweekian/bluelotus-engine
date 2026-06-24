"""Publish-ready cycle pointer for O(1) publisher lookup."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from llm_clients.config_loader import resolve_project_path

POINTER_NAME = "latest_publish_ready.json"


def pointer_path() -> Path:
    return resolve_project_path("data/v3_cycles") / POINTER_NAME


def write_publish_ready_pointer(
    cycle_id: str,
    cycle_dir: Path | str,
    *,
    mode: str = "deterministic_clerk",
    extra: Optional[Dict[str, Any]] = None,
) -> Path:
    path = pointer_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "schema_version": "bluelotus_v3_publish_ready_pointer_v1.0",
        "cycle_id": cycle_id,
        "cycle_dir": str(cycle_dir),
        "mode": mode,
        "written_at_sgt": datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds"),
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_publish_ready_pointer() -> Dict[str, Any]:
    path = pointer_path()
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
