"""P/L integrity policy — broker-reported snapshot is authoritative."""
from __future__ import annotations

from typing import Any, Dict, List

PNL_INTEGRITY_POLICY = "BROKER_REPORTED_AUTHORITATIVE"


def collect_pnl_integrity_conflicts(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    """No live broker-vs-computed reconciliation; report P/L is taken as-is."""
    return []


_collect_pnl_integrity_conflicts = collect_pnl_integrity_conflicts
