"""Post-generation publish gate — fail-closed on core safety and P1 trust checks."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def project_root() -> Path:
    import os
    env = os.environ.get("BLUELOTUS_PROJECT_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


HARD_FAIL_PREFIXES = ("P1",)
HARD_FAIL_CORE_RANGE = range(1, 11)  # checks 1-10


def _is_hard_fail(check_id: Any) -> bool:
    if isinstance(check_id, int) and check_id in HARD_FAIL_CORE_RANGE:
        return True
    label = str(check_id)
    return any(label.startswith(p) for p in HARD_FAIL_PREFIXES)


def run_publish_gate(
    *,
    txt_path: Optional[Path] = None,
    word_path: Optional[Path] = None,
    excel_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
    skip_contracts: bool = False,
    emit_stdout: bool = False,
) -> Dict[str, Any]:
    root = project_root()
    txt_path = txt_path or (root / "research" / "Bluelotus_V3_Report.txt")
    word_path = word_path or (root / "research" / "Bluelotus_V3_Report.docx")
    excel_path = excel_path or (root / "research" / "Bluelotus_V3_Report.xlsx")
    json_path = json_path or (root / "research" / "research_report_delivery_latest.json")

    from research.validate_bluelotus_outputs import run_validation
    from governance.contract_validation import run_all_contract_validations

    validation = run_validation(
        txt_path=txt_path,
        word_path=word_path,
        excel_path=excel_path,
        json_path=json_path,
        print_report=emit_stdout,
    )

    contracts: Dict[str, Any] = {"ok": True, "skipped": True}
    if not skip_contracts:
        contracts = run_all_contract_validations(root)
        contracts["skipped"] = False

    hard_fails: List[Dict[str, Any]] = [
        r for r in validation.get("results", [])
        if r.get("result") == "FAIL" and _is_hard_fail(r.get("check"))
    ]

    manifest_check: Dict[str, Any] = {"ok": True, "skipped": True}
    if json_path.exists():
        try:
            import json
            delivery = json.loads(json_path.read_text(encoding="utf-8"))
            dc = delivery.get("deterministic_contract") or {}
            manifest = dc.get("report_source_manifest") or {}
            if manifest:
                from research.report_source_manifest import validate_manifest
                manifest_check = validate_manifest(manifest)
                manifest_check["skipped"] = False
            else:
                manifest_check = {"ok": False, "skipped": False, "reason": "deterministic_contract missing"}
        except Exception as exc:
            manifest_check = {"ok": False, "skipped": False, "reason": str(exc)}

    ok = not hard_fails and contracts.get("ok", True) and manifest_check.get("ok", True)
    status = "PASS" if ok else "BLOCKED"

    return {
        "status": status,
        "ok": ok,
        "validation": validation,
        "contracts": contracts,
        "manifest_check": manifest_check,
        "hard_fails": hard_fails,
        "pass_count": validation.get("pass_count", 0),
        "fail_count": validation.get("fail_count", 0),
    }
