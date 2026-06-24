"""
BGTM-V1 Game Spec — GLOBAL_RATES_2026 (thesis §8)
=================================================
4-player Stackelberg sequential game (Fed leader; BOJ, ECB followers; JGB
market). Encodes the BOJ payoff vectors under the true world (Fed HOLD) and
the counterfactual (Fed deep cuts), used to derive the HAWKISH_BOJ Geo-LR.

GOVERNANCE: expert-model equilibria, not empirical predictions (BLV3-DOCTRINE-008).
"""

from __future__ import annotations

from ..geo_lr_bridge import bayes_posterior, clamp_lr, geo_lr
from ..qre_solver import softmax

GAME_ID = "GLOBAL_RATES_2026"

# BOJ strategy ordering: [GUIDANCE_MODIFY, HIKE_25, HOLD_loose, HIKE_50].
BOJ_STRATEGIES = ["GUIDANCE_MODIFY", "HIKE_25BP", "HOLD_LOOSE", "HIKE_50BP"]
PAYOFFS_TRUE = [5.0, 3.0, -4.0, -2.0]    # given Fed HOLD (thesis §8.2)
PAYOFFS_FALSE = [1.0, -1.0, 4.0, -3.0]   # counterfactual: Fed deep cuts
LAMBDA_CB = 0.74                         # calibrated central-bank rationality
PRIOR_HAWKISH_BOJ = 0.95


def spe_strategy_index() -> int:
    """Subgame-perfect strategy = argmax of true-world payoffs (backward induction)."""
    return max(range(len(PAYOFFS_TRUE)), key=lambda k: PAYOFFS_TRUE[k])


def solve() -> dict:
    """Compute the BOJ Geo-LR and posterior (mirrors MATLAB Case II)."""
    p_true = softmax(PAYOFFS_TRUE, LAMBDA_CB)
    p_false = softmax(PAYOFFS_FALSE, LAMBDA_CB)
    spe = spe_strategy_index()
    lr_raw = geo_lr(p_true[spe], p_false[spe])
    lr = clamp_lr(lr_raw)
    posterior = bayes_posterior(PRIOR_HAWKISH_BOJ, lr["lr"])
    return {
        "game_id": GAME_ID,
        "spe_strategy": BOJ_STRATEGIES[spe],
        "p_move_true": p_true[spe],
        "p_move_false": p_false[spe],
        "geo_lr": lr["lr"],
        "geo_lr_manual_review": lr["manual_review_required"],
        "prior": PRIOR_HAWKISH_BOJ,
        "posterior": posterior,
        "manual_execution_required": True,
    }
