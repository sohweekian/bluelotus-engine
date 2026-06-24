"""Central execution safety doctrine — CIO_ONLY_MANUAL invariant."""
from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping

EXECUTION_AUTHORITY = "CIO_ONLY_MANUAL"
ORDER_ROUTING_ENABLED = False
LLM_ORDER_GENERATION = False
SYSTEM_ORDERS_GENERATED = 0


def execution_doctrine_defaults() -> Dict[str, Any]:
    return {
        "execution_authority": EXECUTION_AUTHORITY,
        "order_routing_enabled": ORDER_ROUTING_ENABLED,
        "llm_order_generation": LLM_ORDER_GENERATION,
        "orders_generated": SYSTEM_ORDERS_GENERATED,
        "manual_execution_required": True,
    }


def merge_execution_doctrine(payload: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Apply doctrine defaults without overwriting explicit safe values."""
    defaults = execution_doctrine_defaults()
    for key, value in defaults.items():
        payload.setdefault(key, value)
    if payload.get("execution_authority") not in (None, EXECUTION_AUTHORITY):
        raise ValueError(f"execution_authority must be {EXECUTION_AUTHORITY}")
    if payload.get("order_routing_enabled") is True:
        raise ValueError("order_routing_enabled must be False")
    return payload


def assert_execution_safe(payload: Mapping[str, Any], label: str = "payload") -> None:
    """Fail closed when execution doctrine is violated."""
    authority = payload.get("execution_authority")
    if authority is not None and authority != EXECUTION_AUTHORITY:
        raise ValueError(f"{label}: execution_authority must be {EXECUTION_AUTHORITY}, got {authority!r}")
    if payload.get("order_routing_enabled") is True:
        raise ValueError(f"{label}: order_routing_enabled must be False")
    orders = payload.get("orders_generated")
    if orders is not None and int(orders) != SYSTEM_ORDERS_GENERATED:
        raise ValueError(f"{label}: orders_generated must be {SYSTEM_ORDERS_GENERATED}")
