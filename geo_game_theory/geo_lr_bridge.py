"""
BGTM-V1 — Geo-LR Bridge
=======================
Port of geo_lr from matlab/bgtm_validate.m, plus the LR blending and
posterior update from thesis §5.

- geo_lr():        ratio of move probability under thesis-true vs thesis-false
- clamp_lr():      enforce thesis §5.4 bounds [0.1, 10.0], flag out-of-range
- blend_lr():      cold-start interpolation static<->dynamic, alpha = n/30
- bayes_posterior(): single-LR Bayesian thesis update

GOVERNANCE: advisory only. All bridge outputs carry manual_execution_required.
"""

from __future__ import annotations

from . import GEO_LR_MAX, GEO_LR_MIN


def geo_lr(p_event_true: float, p_event_false: float) -> float:
    """Geo-LR Bridge (thesis §5.2): P(move|true) / P(move|false)."""
    if p_event_false <= 0:
        return GEO_LR_MAX
    return p_event_true / p_event_false


def clamp_lr(lr: float) -> dict:
    """Apply safety bounds (thesis §5.4). Out-of-range -> manual review flag."""
    clamped = min(GEO_LR_MAX, max(GEO_LR_MIN, lr))
    return {
        "lr": clamped,
        "lr_raw": lr,
        "manual_review_required": lr < GEO_LR_MIN or lr > GEO_LR_MAX,
        "manual_execution_required": True,
    }


def blend_lr(lr_static: float, lr_geo: float, calibration_n: int) -> float:
    """Cold-start blend (thesis §5.3): (1-a)*static + a*geo, a = min(1, n/30)."""
    alpha = min(1.0, calibration_n / 30.0)
    return (1.0 - alpha) * lr_static + alpha * lr_geo


def bayes_posterior(prior: float, lr: float) -> float:
    """Single-LR Bayesian update (thesis §5.1)."""
    num = prior * lr
    return num / (num + (1.0 - prior))
