"""Append-only pipeline run ledger for BlueLotus V3 production observability."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def project_root() -> Path:
    env = __import__("os").environ.get("BLUELOTUS_PROJECT_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


LEDGER_PATH = project_root() / "data" / "audit" / "pipeline_run_ledger.jsonl"
LATEST_PATH = project_root() / "data" / "audit" / "pipeline_run_latest.json"


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_run_record(
    *,
    run_kind: str,
    started_at: str,
    completed_at: str,
    ok: bool,
    steps: Optional[List[Dict[str, Any]]] = None,
    failures: Optional[List[Dict[str, Any]]] = None,
    dry_run: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    root = project_root()
    dataset = root / "data" / "frontend" / "dataset_raw.json"
    delivery = root / "research" / "research_report_delivery_latest.json"
    record: Dict[str, Any] = {
        "run_id": f"{run_kind}_{completed_at.replace(':', '').replace('+', '')}",
        "run_kind": run_kind,
        "started_at": started_at,
        "completed_at": completed_at,
        "ok": ok,
        "dry_run": dry_run,
        "step_count": len(steps or []),
        "failure_count": len(failures or []),
        "failures": failures or [],
        "artifact_hashes": {
            "dataset_raw_sha256": _sha256_file(dataset),
            "delivery_json_sha256": _sha256_file(delivery),
            "report_txt_sha256": _sha256_file(root / "research" / "Bluelotus_V3_Report.txt"),
            "report_xlsx_sha256": _sha256_file(root / "research" / "Bluelotus_V3_Report.xlsx"),
            "report_docx_sha256": _sha256_file(root / "research" / "Bluelotus_V3_Report.docx"),
        },
        "execution_authority": "CIO_ONLY_MANUAL",
        "order_routing_enabled": False,
    }
    if steps is not None:
        record["steps"] = steps
    if extra:
        record.update(extra)
    return record


def append_run_record(record: Dict[str, Any]) -> Path:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    LATEST_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return LEDGER_PATH


def record_pipeline_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    record = build_run_record(
        run_kind="v3_intelligence_pipeline",
        started_at=summary.get("started_at_sgt", _utc_now()),
        completed_at=summary.get("completed_at_sgt", _utc_now()),
        ok=bool(summary.get("ok")),
        steps=summary.get("step_results"),
        failures=summary.get("failures"),
        dry_run=bool(summary.get("dry_run")),
    )
    append_run_record(record)
    return record
