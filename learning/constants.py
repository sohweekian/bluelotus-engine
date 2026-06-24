"""SLICDO anti-bloat constants."""
from __future__ import annotations

SLICDO_VERSION = "slicdo_deterministic_v2.0"
MAX_CLAIMS_PER_CYCLE = 100
MAX_CIO_CLAIMS_PER_CYCLE = 10
HOT_RETENTION_DAYS = 90
WEEKLY_AGGREGATE_DAYS = 7

# T1 = resolvable institutional bets (numeric engines)
T1_MODULES = frozenset({"nite_pei", "bgtm"})
# T2 = CIO predictions (human intent, numeric resolution)
T2_MODULES = frozenset({"cio_prediction"})

CLAIMS_PATH_NAME = "institutional_claims.jsonl"
RESOLUTIONS_PATH_NAME = "claim_resolutions.jsonl"
OUTCOME_TAGS_PATH_NAME = "outcome_tags.jsonl"
MEMORY_EDGES_PATH_NAME = "memory_edges.jsonl"
WEEKLY_CALIB_PATH_NAME = "weekly_calibration.jsonl"
LEARNING_DIR_NAME = "learning"
PROMOTION_LEDGER_NAME = "promotion_ledger.jsonl"
