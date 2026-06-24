"""Filesystem paths for SLICDO learning spine."""
from __future__ import annotations

import os
from pathlib import Path

from learning.constants import (
    CLAIMS_PATH_NAME,
    LEARNING_DIR_NAME,
    MEMORY_EDGES_PATH_NAME,
    OUTCOME_TAGS_PATH_NAME,
    PROMOTION_LEDGER_NAME,
    RESOLUTIONS_PATH_NAME,
    WEEKLY_CALIB_PATH_NAME,
)


def project_root() -> Path:
    env = os.environ.get("BLUELOTUS_PROJECT_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def learning_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / LEARNING_DIR_NAME


def claims_path(root: Path | None = None) -> Path:
    return learning_dir(root) / CLAIMS_PATH_NAME


def resolutions_path(root: Path | None = None) -> Path:
    return learning_dir(root) / RESOLUTIONS_PATH_NAME


def weekly_calibration_path(root: Path | None = None) -> Path:
    return learning_dir(root) / WEEKLY_CALIB_PATH_NAME


def outcome_tags_path(root: Path | None = None) -> Path:
    return learning_dir(root) / OUTCOME_TAGS_PATH_NAME


def memory_edges_path(root: Path | None = None) -> Path:
    return learning_dir(root) / MEMORY_EDGES_PATH_NAME


def promotion_ledger_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "governance" / PROMOTION_LEDGER_NAME


def learning_cycle_latest_path(root: Path | None = None) -> Path:
    return learning_dir(root) / "learning_cycle_latest.json"


def learning_proposals_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "governance" / "learning_proposals_latest.json"
