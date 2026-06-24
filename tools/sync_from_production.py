"""Copy sanitized BlueLotus V3 engine modules from production tree into this package."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1]

COPY_DIRS = [
    "governance",
    "learning",
    "nite_pei",
    "replay",
    "archive",
    "llm_clients",
    "schemas",
    "cio_context_capsule",
    "config",
]

COPY_FILES = [
    ("orchestration/__init__.py", "orchestration/__init__.py"),
    ("orchestration/run_v3_intelligence_pipeline.py", "orchestration/run_v3_intelligence_pipeline.py"),
    ("orchestration/deterministic_clerk_orchestrator.py", "orchestration/deterministic_clerk_orchestrator.py"),
    ("orchestration/cycle_context_builder.py", "orchestration/cycle_context_builder.py"),
    ("orchestration/publish_ready_pointer.py", "orchestration/publish_ready_pointer.py"),
    ("orchestration/run_deterministic_clerk_cycle.py", "orchestration/run_deterministic_clerk_cycle.py"),
    ("chief_strategist/__init__.py", "chief_strategist/__init__.py"),
    ("chief_strategist/deterministic_clerk_digest.py", "chief_strategist/deterministic_clerk_digest.py"),
    ("scripts/run_slicdo_learning_cycle.py", "scripts/run_slicdo_learning_cycle.py"),
    ("scripts/run_nite_pei_cycle.py", "scripts/run_nite_pei_cycle.py"),
    ("research/report_publish_gate.py", "research/report_publish_gate.py"),
    ("research/validate_bluelotus_outputs.py", "research/validate_bluelotus_outputs.py"),
    ("research/report_bundle.py", "research/report_bundle.py"),
    ("research/run_report_regression_audit.py", "research/run_report_regression_audit.py"),
    ("research/report_source_manifest.py", "research/report_source_manifest.py"),
    ("research/research_report_generator.py", "research/research_report_generator.py"),
    ("LICENSE", "LICENSE"),
    ("DISCLAIMER.md", "DISCLAIMER.md"),
]

EXCLUDE_ORCH = {
    "linear_agent_orchestrator.py",
    "run_v3_grand_cycle.py",
    "agent_execution_queue.py",
    "persist_v3_cycle_to_db.py",
}

PATCHES: list[tuple[str, str, str]] = [
    (
        "chief_strategist/deterministic_clerk_digest.py",
        "from agents.base_agent import sgt_now",
        "from bluelotus_engine.timeutil import sgt_now",
    ),
]

SANITIZE_PATTERNS = [
    (re.compile(r"C:\\\\bluelotus3", re.I), "{BLUELOTUS_ROOT}"),
    (re.compile(r"C:/bluelotus3", re.I), "{BLUELOTUS_ROOT}"),
]


def copy_tree(name: str) -> None:
    src = PRODUCTION / name
    dst = PACKAGE / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    print(f"copied dir {name}")


def copy_file(rel: str, dest_rel: str) -> None:
    src = PRODUCTION / rel
    dst = PACKAGE / dest_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copied file {rel}")


def apply_patches(rel_path: str) -> None:
    path = PACKAGE / rel_path
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    original = text
    for patch_rel, old, new in PATCHES:
        if patch_rel != rel_path:
            continue
        text = text.replace(old, new)
    for pattern, repl in SANITIZE_PATTERNS:
        text = pattern.sub(repl, text)
    if text != original:
        path.write_text(text, encoding="utf-8")


def patch_config_loader() -> None:
    path = PACKAGE / "llm_clients" / "config_loader.py"
    text = path.read_text(encoding="utf-8")
    needle = "def _discover_project_root() -> Path | None:"
    insert = '''def _discover_project_root() -> Path | None:
    import sys

    for entry in sys.path:
        candidate = Path(entry).resolve()
        if (candidate / "config" / "bluelotus3.yaml").exists():
            return candidate
        pkg = candidate / "bluelotus_engine"
        if pkg.is_dir() and (candidate / "governance").is_dir():
            return candidate
'''
    if needle in text and "bluelotus_engine" not in text.split(needle)[1][:400]:
        text = text.replace(
            "def _discover_project_root() -> Path | None:\n    for candidate_root in _candidate_roots():",
            insert + "    for candidate_root in _candidate_roots():",
        )
        path.write_text(text, encoding="utf-8")
        print("patched config_loader discovery")


def main() -> None:
    for name in COPY_DIRS:
        copy_tree(name)
    for rel, dest in COPY_FILES:
        copy_file(rel, dest)
    for patch_rel, _, _ in PATCHES:
        apply_patches(patch_rel)
    patch_config_loader()
    print("sync complete:", PACKAGE)


if __name__ == "__main__":
    main()
