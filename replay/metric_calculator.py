from __future__ import annotations

import hashlib
from typing import Dict


def deterministic_score(strategy_id: str, scenario_id: str) -> Dict[str, float]:
    seed = hashlib.sha256(f"{strategy_id}:{scenario_id}".encode("utf-8")).hexdigest()
    n = int(seed[:8], 16)
    return_proxy = ((n % 2400) - 900) / 10000.0
    drawdown_proxy = -abs(((n // 97) % 1800) / 10000.0)
    sharpe_proxy = max(-2.0, min(2.0, return_proxy / max(0.03, abs(drawdown_proxy))))
    return {
        "return_proxy": round(return_proxy, 6),
        "max_drawdown_proxy": round(drawdown_proxy, 6),
        "sharpe_proxy": round(sharpe_proxy, 6),
    }

