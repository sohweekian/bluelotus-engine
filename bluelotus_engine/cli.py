from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python() -> str:
    return sys.executable


def cmd_init_workspace(args: argparse.Namespace) -> int:
    root = Path(args.target).expanduser().resolve()
    pkg = _root()
    for name in ("config", "data", "research", "logs"):
        (root / name).mkdir(parents=True, exist_ok=True)
    sample = pkg / "data" / "samples" / "dataset_raw.demo.json"
    target = root / "data" / "frontend" / "dataset_raw.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() and sample.exists():
        target.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    env = root / ".env"
    if not env.exists():
        template = (pkg / ".env.template").read_text(encoding="utf-8")
        env.write_text(template.replace("{WORKSPACE}", str(root)), encoding="utf-8")
    print(f"Workspace ready: {root}")
    print("Edit .env then run: bluelotus pipeline --once --dry-run")
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    env = dict(**{k: str(v) for k, v in __import__("os").environ.items()})
    env.setdefault("BLUELOTUS_PROJECT_ROOT", str(Path.cwd()))
    env.setdefault("V3_PIPELINE_CONFIG_PATH", "config/v3_pipeline_research.yaml")
    env.setdefault("BLUELOTUS_CONFIG_FILE", "config/bluelotus3.yaml")
    module = "orchestration.run_v3_intelligence_pipeline"
    cmd = [_python(), "-m", module]
    if args.once:
        cmd.append("--once")
    if args.dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, cwd=str(Path.cwd()), env=env)
    return int(proc.returncode or 0)


def cmd_clerk(args: argparse.Namespace) -> int:
    cmd = [_python(), "-m", "orchestration.run_deterministic_clerk_cycle"]
    if args.cycle_id:
        cmd.append(f"--cycle-id={args.cycle_id}")
    return int(subprocess.run(cmd, cwd=str(Path.cwd())).returncode or 0)


def cmd_governance(args: argparse.Namespace) -> int:
    cmd = [_python(), "governance/governance_gate.py"]
    return int(subprocess.run(cmd, cwd=str(Path.cwd())).returncode or 0)


def cmd_slicdo(args: argparse.Namespace) -> int:
    cmd = [_python(), "scripts/run_slicdo_learning_cycle.py"]
    return int(subprocess.run(cmd, cwd=str(Path.cwd())).returncode or 0)


def cmd_nite_pei(args: argparse.Namespace) -> int:
    cmd = [_python(), "-m", "scripts.run_nite_pei_cycle"]
    return int(subprocess.run(cmd, cwd=str(Path.cwd())).returncode or 0)


def cmd_validate(args: argparse.Namespace) -> int:
    cmd = [_python(), "research/validate_bluelotus_outputs.py"]
    return int(subprocess.run(cmd, cwd=str(Path.cwd())).returncode or 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bluelotus",
        description="BlueLotus V3 research engine — deterministic governance and clerk tooling.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init-workspace", help="Create a local research workspace from samples")
    init_p.add_argument("--target", default=".", help="Workspace directory")
    init_p.set_defaults(func=cmd_init_workspace)

    pipe_p = sub.add_parser("pipeline", help="Run the research pipeline (no publish, no telegram)")
    pipe_p.add_argument("--once", action="store_true")
    pipe_p.add_argument("--dry-run", action="store_true")
    pipe_p.set_defaults(func=cmd_pipeline)

    clerk_p = sub.add_parser("clerk", help="Run deterministic Zone A clerk cycle")
    clerk_p.add_argument("--cycle-id", default="")
    clerk_p.set_defaults(func=cmd_clerk)

    sub.add_parser("governance-gate", help="Run governance gate on dataset").set_defaults(func=cmd_governance)
    sub.add_parser("slicdo", help="Run SLICDO learning cycle").set_defaults(func=cmd_slicdo)
    sub.add_parser("nite-pei", help="Run NITE-PEI Bayesian thesis update").set_defaults(func=cmd_nite_pei)
    sub.add_parser("validate", help="Validate report outputs").set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
