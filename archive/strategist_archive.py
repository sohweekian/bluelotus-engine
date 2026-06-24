from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_json(cycle_dir: Path, filename: str, payload: Dict[str, Any]) -> str:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    path = cycle_dir / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def write_text(cycle_dir: Path, filename: str, text: str) -> str:
    cycle_dir.mkdir(parents=True, exist_ok=True)
    path = cycle_dir / filename
    path.write_text(text, encoding="utf-8")
    return str(path)
