"""
BGTM-V1 Game Spec — HORMUZ_2026 (thesis §7)
===========================================
7-player signalling game with subsequent coordination stage. Encodes the
expert-initialised inputs that the MATLAB oracle validates: NE selection
probabilities, the NE->outcome map, the P1 QRE payoffs, and the global-games
threshold payoffs.

GOVERNANCE: expert-model equilibria, not empirical predictions (BLV3-DOCTRINE-008).
"""

from __future__ import annotations

from ..ce_envelope import ce_envelope, outcome_probabilities
from ..global_games import global_games_threshold
from ..qre_solver import softmax

GAME_ID = "HORMUZ_2026"

# Nash equilibria after refinement cascade (thesis §7.4). NE3 is eliminated by
# trembling-hand perfection -> only NE1, NE2 survive.
NE_LABELS = ["NE1_talks_alive", "NE2_standoff", "NE3_escalation"]
NE_BASE_PROBS = [0.42, 0.31, 0.12]
SURVIVING = [0, 1]  # indices surviving the cascade

# NE -> market-outcome map (thesis §7.5). Rows = surviving NE; cols = outcomes
# [talks, threat_sustained, breakthrough, partial_closure, full_closure].
OUTCOME_LABELS = [
    "w1_talks", "w2_threat", "w3_breakthrough", "w4_partial", "w5_full",
]
OUTCOME_MAP = [
    [0.55, 0.20, 0.20, 0.04, 0.01],  # NE1
    [0.22, 0.41, 0.13, 0.16, 0.08],  # NE2
]

# P1 (Iran Military) QRE softening: MAINTAIN_THREAT vs EXECUTE_CLOSURE blended EU.
P1_PAYOFFS = [4.0, 3.0]   # [MAINTAIN_THREAT, EXECUTE_CLOSURE blended]
LAMBDA_GEO = 1.5

# Global-games threshold for EXECUTE_CLOSURE (thesis §7.6).
GG_WIN, GG_LOSE, GG_OUTSIDE, GG_SIGMA = 8.0, -6.0, 4.0, 0.15


def solve() -> dict:
    """Compute the Hormuz equilibrium summary (mirrors MATLAB Case I)."""
    surviving_probs = [NE_BASE_PROBS[i] for i in SURVIVING]
    ce_w = ce_envelope(surviving_probs)
    omega = outcome_probabilities(ce_w, OUTCOME_MAP)
    p1 = softmax(P1_PAYOFFS, LAMBDA_GEO)
    theta_star = global_games_threshold(GG_WIN, GG_LOSE, GG_OUTSIDE, GG_SIGMA)
    return {
        "game_id": GAME_ID,
        "ce_weights": dict(zip([NE_LABELS[i] for i in SURVIVING], ce_w)),
        "outcome_probabilities": dict(zip(OUTCOME_LABELS, omega)),
        "qre_maintain_threat": p1[0],
        "qre_execute_closure": p1[1],
        "global_games_theta_star": theta_star,
        "manual_execution_required": True,
    }
