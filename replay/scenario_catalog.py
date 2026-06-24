from __future__ import annotations

from typing import Dict, List

from .replay_schema import SCENARIOS


def build_scenario_catalog() -> List[Dict[str, object]]:
    weights = {
        "BASE_CASE": 0.20,
        "WARSH_HAWKISH_RATES_UP": 0.12,
        "BOJ_YEN_CARRY_UNWIND": 0.12,
        "GLOBAL_LEVERAGE_UNWIND": 0.14,
        "GOLD_PEACE_DIVIDEND": 0.10,
        "HIGH_BETA_RISK_OFF": 0.12,
        "VOL_SPIKE": 0.08,
        "LIQUIDITY_RECOVERY": 0.06,
        "SOFT_LANDING_RISK_ON": 0.06,
    }
    return [
        {
            "scenario_id": scenario,
            "probability_weight": weights.get(scenario, 0.05),
            "point_in_time": True,
            "lookahead_bias_guard": "PASS",
        }
        for scenario in SCENARIOS
    ]

