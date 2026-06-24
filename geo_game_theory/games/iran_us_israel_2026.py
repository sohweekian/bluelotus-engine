"""
BGTM-V1 Extension — IRAN_US_ISRAEL_2026 (3-player lasting peace game)
======================================================================
3-player Normal Form Game:
  Player 1 — IRAN (Supreme Council / IRGC)
  Player 2 — US   (White House / State / Treasury — Trump context)
  Player 3 — ISRAEL (Netanyahu government / IDF)

Strategy sets (3 per player):
  IRAN:   [NEGOTIATE(0), DELAY(1), ESCALATE(2)]
  US:     [PRESS(0),     ENGAGE(1), WITHDRAW(2)]
  ISRAEL: [ACCEPT(0),   DETER(1),  STRIKE(2)]

Payoff scale: 8=max win, -6=max loss (consistent with HORMUZ_2026).
Dimension ordering: [Iran_strat, US_strat, Israel_strat]

GOVERNANCE: expert-model equilibria, not empirical predictions (BLV3-DOCTRINE-008).
CIO_ONLY_MANUAL. No execution authority. Research reference only.
"""

from __future__ import annotations

import numpy as np

from ..qre_solver import solve_qre, softmax
from ..global_games import global_games_threshold
from ..geo_lr_bridge import bayes_posterior, clamp_lr, geo_lr
from .hormuz_2026 import solve as hormuz_solve

GAME_ID = "IRAN_US_ISRAEL_2026"
LAMBDA_GEO = 1.5   # same rationality as HORMUZ_2026

IRAN_STRATEGIES   = ["NEGOTIATE", "DELAY",   "ESCALATE"]
US_STRATEGIES     = ["PRESS",     "ENGAGE",  "WITHDRAW"]
ISRAEL_STRATEGIES = ["ACCEPT",    "DETER",   "STRIKE"]

# ── IRAN payoffs [Iran, US, Israel] ─────────────────────────────────────────
# Iran utility drivers: sanctions_relief(+), nuclear_program_preserved(+),
#                       regime_survival(+), proxy_network_intact(+)
U_iran = np.array([
    # IRAN: NEGOTIATE
    [[ 5.0,  3.0, -3.0],   # US: PRESS  — Israel: ACCEPT/DETER/STRIKE
     [ 7.0,  4.0, -4.0],   # US: ENGAGE
     [ 2.0,  1.0, -5.0]],  # US: WITHDRAW
    # IRAN: DELAY
    [[ 1.0,  2.0, -2.0],
     [ 4.0,  3.0, -1.0],
     [ 3.0,  2.0, -3.0]],
    # IRAN: ESCALATE
    [[-1.0, -2.0, -6.0],
     [ 2.0,  0.0, -5.0],
     [ 4.0,  1.0, -3.0]],
])

# ── US payoffs ───────────────────────────────────────────────────────────────
# US utility drivers: deal_credit(+), no_war(+), oil_stable(+), Israel_secure(+)
U_us = np.array([
    # IRAN: NEGOTIATE
    [[ 6.0,  5.0, -3.0],
     [ 8.0,  5.0, -4.0],
     [ 3.0,  1.0, -5.0]],
    # IRAN: DELAY
    [[ 2.0,  3.0, -2.0],
     [ 4.0,  3.0, -3.0],
     [ 1.0,  0.0, -4.0]],
    # IRAN: ESCALATE
    [[-1.0, -2.0, -6.0],
     [-1.0, -1.0, -5.0],
     [-3.0, -2.0, -5.0]],
])

# ── ISRAEL payoffs ───────────────────────────────────────────────────────────
# Israel utility drivers: nuclear_threat_eliminated(+), no_proxy_war(+),
#                         US_backing(+), strategic_autonomy(+)
U_israel = np.array([
    # IRAN: NEGOTIATE
    [[ 5.0,  6.0,  4.0],
     [ 4.0,  5.0,  2.0],
     [ 1.0,  3.0,  5.0]],
    # IRAN: DELAY
    [[ 2.0,  4.0,  5.0],
     [ 2.0,  3.0,  4.0],
     [-1.0,  2.0,  6.0]],
    # IRAN: ESCALATE
    [[-2.0,  0.0,  3.0],
     [-3.0, -1.0,  2.0],
     [-4.0, -1.0,  1.0]],
])

# ── Global Games threshold for ISRAEL: STRIKE ────────────────────────────────
# When does Israel find it individually rational to strike?
# Win (nuclear eliminated): 7.0, Lose (war with no US): -5.0, Outside (deter): 3.0
GG_WIN_ISR, GG_LOSE_ISR, GG_OUTSIDE_ISR, GG_SIGMA_ISR = 7.0, -5.0, 3.0, 0.15


def solve() -> dict:
    """
    Compute the 3-player Iran-US-Israel QRE and lasting peace probability.

    Returns:
      game_id, qre_strategies (per player), outcome_probabilities,
      dominant_equilibrium, lasting_peace_probability,
      war_probability, standoff_probability,
      israel_strike_threshold, hormuz_baseline_comparison,
      manual_execution_required
    """
    # ── QRE fixed point ─────────────────────────────────────────────────────
    result = solve_qre(
        [U_iran, U_us, U_israel],
        lam=LAMBDA_GEO,
        damp=0.5,
        tol=1e-9,
        max_iter=500,
    )
    iran_q   = result["strategies"][0]
    us_q     = result["strategies"][1]
    israel_q = result["strategies"][2]

    # ── Outcome probabilities (joint strategy profile under QRE) ─────────────
    # Core lasting peace: NEGOTIATE × ENGAGE × ACCEPT
    p_peace_core = iran_q[0] * us_q[1] * israel_q[0]
    # Extended peace: Iran negotiates, US engages, Israel accepts OR deters
    p_peace_ext  = iran_q[0] * us_q[1] * (israel_q[0] + israel_q[1])
    # Managed standoff: Iran delays, US presses, Israel deters
    p_standoff   = iran_q[1] * us_q[0] * israel_q[1]
    # Israeli pre-emption: any profile where Israel STRIKE
    p_strike     = israel_q[2]
    # Iranian escalation
    p_escalate   = iran_q[2]
    # Full three-way conflict: escalate × press × strike
    p_war        = iran_q[2] * us_q[0] * israel_q[2]
    # US-Iran bilateral with Israel veto: Iran negotiates, US engages, Israel strikes
    p_veto       = iran_q[0] * us_q[1] * israel_q[2]

    # ── Israel global-games strike threshold ─────────────────────────────────
    theta_star_isr = global_games_threshold(
        GG_WIN_ISR, GG_LOSE_ISR, GG_OUTSIDE_ISR, GG_SIGMA_ISR
    )

    # ── Hormuz baseline for delta comparison ─────────────────────────────────
    hormuz = hormuz_solve()

    # ── Dominant strategy detection ──────────────────────────────────────────
    dominant = {
        "iran":   IRAN_STRATEGIES[int(np.argmax(iran_q))],
        "us":     US_STRATEGIES[int(np.argmax(us_q))],
        "israel": ISRAEL_STRATEGIES[int(np.argmax(israel_q))],
    }

    return {
        "game_id": GAME_ID,
        "qre_strategies": {
            "iran":   dict(zip(IRAN_STRATEGIES,   [round(x, 4) for x in iran_q])),
            "us":     dict(zip(US_STRATEGIES,     [round(x, 4) for x in us_q])),
            "israel": dict(zip(ISRAEL_STRATEGIES, [round(x, 4) for x in israel_q])),
        },
        "dominant_qre_strategy": dominant,
        "outcome_probabilities": {
            "lasting_peace_core":     round(p_peace_core, 4),
            "lasting_peace_extended": round(p_peace_ext,  4),
            "managed_standoff":       round(p_standoff,   4),
            "israeli_strike":         round(p_strike,     4),
            "iran_escalation":        round(p_escalate,   4),
            "full_war_3player":       round(p_war,        4),
            "bilateral_deal_vetoed":  round(p_veto,       4),
        },
        "israel_strike_threshold_theta_star": round(theta_star_isr, 4),
        "hormuz_baseline": {
            "p_breakthrough": round(hormuz["outcome_probabilities"]["w3_breakthrough"], 4),
            "p_talks":        round(hormuz["outcome_probabilities"]["w1_talks"], 4),
            "p_standoff":     round(hormuz["outcome_probabilities"]["w2_threat"], 4),
            "qre_maintain_threat": round(hormuz["qre_maintain_threat"], 4),
            "theta_star_hormuz":   round(hormuz["global_games_theta_star"], 4),
        },
        "qre_converged": result["converged"],
        "qre_iterations": result["iterations"],
        "manual_execution_required": True,
    }
