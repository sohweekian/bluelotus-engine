"""
BGTM-V1 Extension — SPACE_ROTATION_7P_2026
==========================================
7-player normal-form capital-rotation game (expert-initialised).

Players (capital / price-regime actors):
  0 ASTS  1 PL  2 RKLB  3 LUNR  4 RDW  5 SPCX  6 SPY

Strategies (3 each):
  ACCUMULATE | HOLD | DISTRIBUTE

Payoffs encode CIO rotation thesis:
  SPCX DISTRIBUTE + proxy ACCUMULATE = rotation win
  SPY DISTRIBUTE = macro headwind for high-beta space
  ASTS ACCUMULATE penalised (CIO overloaded / concentration)

GOVERNANCE: expert-model, not empirical forecast (BLV3-DOCTRINE-008).
CIO_ONLY_MANUAL. Research reference only.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

import numpy as np

from ..qre_solver import solve_qre

GAME_ID = "SPACE_ROTATION_7P_2026"
LAMBDA_GEO = 1.5

PLAYERS = ["ASTS", "PL", "RKLB", "LUNR", "RDW", "SPCX", "SPY"]
STRATEGIES = ["ACCUMULATE", "HOLD", "DISTRIBUTE"]

# Index maps
IDX = {t: i for i, t in enumerate(PLAYERS)}
SPACE_PROXIES = {0, 1, 2, 3, 4}  # ASTS..RDW
SPCX_I = IDX["SPCX"]
SPY_I = IDX["SPY"]
ASTS_I = IDX["ASTS"]

# Capital-flow prior from latest dataset (institutional_bias -> action affinity)
FLOW_PRIOR = {
    "ASTS": {"ACCUMULATE": 1.0, "HOLD": 0.2, "DISTRIBUTE": -0.5},
    "PL": {"ACCUMULATE": -0.3, "HOLD": 0.3, "DISTRIBUTE": 0.6},
    "RKLB": {"ACCUMULATE": 0.9, "HOLD": 0.1, "DISTRIBUTE": -0.2},
    "LUNR": {"ACCUMULATE": 1.0, "HOLD": 0.0, "DISTRIBUTE": -0.3},
    "RDW": {"ACCUMULATE": -0.2, "HOLD": 0.4, "DISTRIBUTE": 0.7},
    "SPCX": {"ACCUMULATE": -1.0, "HOLD": 0.0, "DISTRIBUTE": 1.2},  # CIO judgment: outflow
    "SPY": {"ACCUMULATE": 0.2, "HOLD": 0.6, "DISTRIBUTE": 0.5},  # mild risk-off tape
}

ACTION_VAL = {"ACCUMULATE": 1, "HOLD": 0, "DISTRIBUTE": -1}


def _profile_payoff(player_i: int, actions: Tuple[int, ...]) -> float:
    """Expert payoff for one player at a pure strategy profile."""
    a_name = [STRATEGIES[a] for a in actions]
    av = [ACTION_VAL[n] for n in a_name]

    ticker = PLAYERS[player_i]
    base = FLOW_PRIOR[ticker][a_name[player_i]]

  # Rotation: proxies gain when SPCX distributes and they accumulate
    spcx_d = av[SPCX_I] == -1
    spy_d = av[SPY_I] == -1
    proxy_acc = sum(1 for j in SPACE_PROXIES if av[j] == 1)

    p = base

    if player_i in SPACE_PROXIES:
        if spcx_d and av[player_i] == 1:
            p += 2.5
        if spcx_d and av[player_i] == 0:
            p += 0.8
        if spy_d:
            p -= 1.8 if av[player_i] == 1 else 0.6
        # crowding among proxies
        if av[player_i] == 1:
            p -= 0.35 * max(0, proxy_acc - 1)
        # ASTS concentration cap
        if player_i == ASTS_I and av[player_i] == 1:
            p -= 2.0
        # semi-panic beta: distribute less painful than accumulate for weak names
        if ticker in ("PL", "RDW") and av[player_i] == -1 and spy_d:
            p += 0.5

    elif player_i == SPCX_I:
        # SPCX rewards distributing when proxies absorb flow
        if av[SPCX_I] == -1:
            p += 1.5 + 0.4 * proxy_acc
        if av[SPCX_I] == 1 and proxy_acc >= 2:
            p -= 2.5
        if spy_d and av[SPCX_I] == -1:
            p += 0.5

    elif player_i == SPY_I:
        # Macro basket: prefers hold in dispersion; distribute on crowded beta chase
        if proxy_acc >= 4 and any(av[j] == 1 for j in SPACE_PROXIES):
            p += 1.2 if av[SPY_I] == -1 else (-0.8 if av[SPY_I] == 1 else 0.3)
        if spcx_d and proxy_acc >= 2:
            p += 0.6 if av[SPY_I] == 0 else 0.0
        if av[SPY_I] == 1 and spy_d:
            p -= 1.0

    return float(p)


def build_tensors() -> List[np.ndarray]:
    n = len(PLAYERS)
    m = len(STRATEGIES)
    dims = (m,) * n
    tensors = [np.zeros(dims) for _ in range(n)]
    for actions in itertools.product(range(m), repeat=n):
        for i in range(n):
            tensors[i][actions] = _profile_payoff(i, actions)
    return tensors


def _pure_nash(tensors: List[np.ndarray]) -> List[Tuple[int, ...]]:
    n = len(PLAYERS)
    m = len(STRATEGIES)
    equilibria = []
    for actions in itertools.product(range(m), repeat=n):
        ok = True
        for i in range(n):
            cur = tensors[i][actions]
            for alt in range(m):
                if alt == actions[i]:
                    continue
                dev = list(actions)
                dev[i] = alt
                if tensors[i][tuple(dev)] > cur + 1e-9:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            equilibria.append(actions)
    return equilibria


def _label_profile(actions: Tuple[int, ...]) -> str:
    parts = [f"{PLAYERS[i]}:{STRATEGIES[a]}" for i, a in enumerate(actions)]
    spcx = STRATEGIES[actions[SPCX_I]]
    proxies = [STRATEGIES[actions[i]] for i in sorted(SPACE_PROXIES)]
    acc = sum(1 for a in proxies if a == "ACCUMULATE")
    if spcx == "DISTRIBUTE" and acc >= 3:
        tag = "ROTATION_CORE"
    elif spcx == "DISTRIBUTE" and acc >= 1:
        tag = "PARTIAL_ROTATION"
    elif all(a == "DISTRIBUTE" for a in proxies) and spcx == "HOLD":
        tag = "BROAD_SPACE_OUTFLOW"
    elif STRATEGIES[actions[SPY_I]] == "DISTRIBUTE" and acc <= 1:
        tag = "MACRO_RISK_OFF"
    else:
        tag = "MIXED"
    return tag


def solve() -> dict:
    tensors = build_tensors()
    n = len(PLAYERS)
    m = len(STRATEGIES)

    qre = solve_qre(tensors, lam=LAMBDA_GEO, damp=0.5, tol=1e-9, max_iter=800)
    strategies = qre["strategies"]

    dominant = {
        PLAYERS[i]: STRATEGIES[int(np.argmax(strategies[i]))]
        for i in range(n)
    }

    # Key scenario probabilities (independent QRE product)
    def p_action(player: str, action: str) -> float:
        i = IDX[player]
        return strategies[i][STRATEGIES.index(action)]

    p_rotation_core = (
        p_action("SPCX", "DISTRIBUTE")
        * p_action("RKLB", "ACCUMULATE")
        * p_action("LUNR", "ACCUMULATE")
        * (p_action("PL", "ACCUMULATE") + p_action("PL", "HOLD") * 0.5)
    )
    p_spcx_out = p_action("SPCX", "DISTRIBUTE")
    p_proxy_inflow = np.prod([p_action(t, "ACCUMULATE") for t in ["RKLB", "LUNR"]])
    p_asts_hold = p_action("ASTS", "HOLD") + p_action("ASTS", "DISTRIBUTE") * 0.3
    p_spy_risk_off = p_action("SPY", "DISTRIBUTE")

    nash = _pure_nash(tensors)
    nash_labeled = [
        {
            "profile": {PLAYERS[i]: STRATEGIES[a] for i, a in enumerate(prof)},
            "tag": _label_profile(prof),
            "payoffs": {PLAYERS[i]: round(float(tensors[i][prof]), 2) for i in range(n)},
        }
        for prof in nash[:12]
    ]

    return {
        "game_id": GAME_ID,
        "players": PLAYERS,
        "strategies": STRATEGIES,
        "contingency_cells": m**n,
        "qre_strategies": {
            PLAYERS[i]: {STRATEGIES[j]: round(strategies[i][j], 4) for j in range(m)}
            for i in range(n)
        },
        "dominant_qre_strategy": dominant,
        "outcome_probabilities": {
            "spcx_distribute": round(p_spcx_out, 4),
            "rklb_lunr_accumulate_joint": round(float(p_proxy_inflow), 4),
            "rotation_core_proxy": round(float(p_rotation_core), 4),
            "asts_hold_or_trim": round(float(p_asts_hold), 4),
            "spy_distribute": round(float(p_spy_risk_off), 4),
        },
        "pure_nash_count": len(nash),
        "pure_nash_profiles": nash_labeled,
        "qre_converged": qre["converged"],
        "qre_iterations": qre["iterations"],
        "manual_execution_required": True,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(solve(), indent=2))
