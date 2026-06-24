from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_agent_report(cycle_dir: Path, report: Dict[str, Any]) -> Dict[str, str]:
    report_dir = cycle_dir / "agent_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    agent_id = str(report["agent_id"])
    json_path = report_dir / f"{agent_id}.json"
    txt_path = report_dir / f"{agent_id}.txt"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    txt_path.write_text(render_report_text(report), encoding="utf-8")
    return {"json": str(json_path), "text": str(txt_path)}


def write_agent_error(cycle_dir: Path, agent_id: str, error: str) -> str:
    error_dir = cycle_dir / "agent_errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    path = error_dir / f"{agent_id}.json"
    path.write_text(json.dumps({"agent_id": agent_id, "error": error}, indent=2), encoding="utf-8")
    return str(path)


def render_report_text(report: Dict[str, Any]) -> str:
    lines = [
        str(report.get("agent_name", "")),
        "",
        f"Summary: {report.get('summary', '')}",
        f"Recommendation: {report.get('recommendation_to_chief_strategist', '')}",
        f"CIO attention: {report.get('requires_cio_attention', False)}",
        "",
        "Key findings:",
    ]
    lines.extend(f"- {item}" for item in report.get("key_findings", []))
    lines.append("")
    lines.append("Risk flags:")
    lines.extend(f"- {item}" for item in report.get("risk_flags", []))
    lines.append("")
    lines.append("Manual execution required: YES")
    lines.append("No automatic orders generated.")
    return "\n".join(lines)
