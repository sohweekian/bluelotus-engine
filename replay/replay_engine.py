from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from backtest.backtest_engine import run_strategy_scenario_backtest
from backtest.performance_metrics import summarize_results
from backtest.result_writer import build_backtest_result

from .point_in_time_guard import validate_point_in_time
from .replay_schema import REPLAY_VERSION
from .scenario_catalog import build_scenario_catalog
from .strategy_catalog import build_strategy_catalog


def build_deterministic_replay(dataset: Dict[str, Any]) -> Dict[str, Any]:
    strategies = build_strategy_catalog()
    scenarios = build_scenario_catalog()
    rows = run_strategy_scenario_backtest(strategies, scenarios)
    summary = summarize_results(rows)
    guard = validate_point_in_time(dataset)
    return {
        "version": REPLAY_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "strategy_count": len(strategies),
        "scenario_count": len(scenarios),
        "strategies": strategies,
        "scenarios": scenarios,
        "benchmark_results": rows,
        "summary": summary,
        "backtest_result": build_backtest_result(summary, rows),
        **guard,
        "execution_authority": "CIO_ONLY_MANUAL",
        "order_routing_enabled": False,
        "orders_generated": 0,
        "advisory_only": True,
    }
