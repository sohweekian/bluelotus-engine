"""
BGTM-V1 — Global Games threshold
================================
Port of global_games_threshold from matlab/bgtm_validate.m plus the
Carlsson-Van Damme / Morris-Shin risk-dominance adjustment under private
information noise sigma (thesis §7.6).

The raw payoff-indifference point solves
    theta * g_win + (1 - theta) * g_lose = g_outside.
Under strategic uncertainty sigma, the threshold is pulled toward 0.5
(risk-dominance), reproducing the thesis value theta* = 0.68 from sigma = 0.15.

GOVERNANCE: pure deterministic numerics. No LLM, no broker path.
"""

from __future__ import annotations


def raw_threshold(g_win: float, g_lose: float, g_outside: float) -> float:
    """Payoff-indifference belief for taking the risky action."""
    denom = g_win - g_lose
    if denom == 0:
        return 0.5
    return (g_outside - g_lose) / denom


def global_games_threshold(g_win: float, g_lose: float, g_outside: float, sigma: float = 0.0) -> float:
    """Risk-dominance-adjusted threshold under private-information noise sigma.

    theta* = theta_raw + (0.5 - theta_raw) * sigma.
    sigma=0 returns the raw indifference point; sigma=0.15 reproduces the
    thesis Hormuz EXECUTE_CLOSURE threshold of 0.68.
    """
    theta_raw = raw_threshold(g_win, g_lose, g_outside)
    return theta_raw + (0.5 - theta_raw) * sigma


def classify_kill_state(p_kill: float) -> str:
    """Map a kill probability to the NITE-PEI state ladder (thesis §7.6)."""
    if p_kill < 0.10:
        return "INACTIVE"
    if p_kill < 0.35:
        return "WATCH"
    if p_kill < 0.65:
        return "TRIGGERED"
    return "CONFIRMED"
