"""
BlueLotus V3 — BGTM-V1 (Geopolitical Game Theory Model)
=======================================================
Python production engine for the BGTM-V1 framework described in
research/BGTM_V1_PhD_Thesis_GameTheory_NashEquilibrium_2026.md.

The four core kernels (qre, ce_envelope, geo_lr_bridge, global_games) are
ports of the MATLAB validation oracle at matlab/bgtm_validate.m, which passes
13/13 thesis checks. The Python kernels are the in-process runtime engine
(sub-50 ms, no MATLAB startup tax); MATLAB is retained as an offline oracle.

GOVERNANCE: advisory only. No LLM order generation, no broker path.
All outputs carry manual_execution_required = True.
"""

from __future__ import annotations

BGTM_VERSION = "bgtm_v1.0"

# Safety invariants surfaced for downstream consumers / tests.
SAFETY = {
    "manual_execution_required": True,
    "llm_order_generation": False,
    "order_routing_enabled": False,
}

# Geo-LR safety bounds (thesis §5.4).
GEO_LR_MIN = 0.1
GEO_LR_MAX = 10.0
