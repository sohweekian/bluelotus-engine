from __future__ import annotations

from typing import Dict, List

from .replay_schema import STRATEGIES


def build_strategy_catalog() -> List[Dict[str, object]]:
    return [
        {
            "strategy_id": strategy,
            "strategy_name": strategy.replace("_", " ").title(),
            "advisory_only": True,
            "orders_generated": 0,
            "order_routing_enabled": False,
        }
        for strategy in STRATEGIES
    ]

