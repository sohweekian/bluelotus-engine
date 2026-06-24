"""
BGTM-V1 — Correlated-Equilibrium envelope + outcome mapping
===========================================================
Port of ce_envelope from matlab/bgtm_validate.m.

For surviving Nash equilibria with disjoint support (the Hormuz case after
trembling-hand elimination of NE3), the max-social-payoff CE reduces to
renormalisation of the NE selection probabilities. The general LP form
(linprog) is reserved for overlapping supports and is not needed at
BGTM-V1 scale.

GOVERNANCE: pure deterministic numerics. No LLM, no broker path.
"""

from __future__ import annotations

from typing import Sequence


def ce_envelope(ne_probs: Sequence[float]) -> list[float]:
    """Renormalise surviving NE selection probabilities into CE weights."""
    vals = [float(x) for x in ne_probs]
    total = sum(vals)
    if total <= 0:
        n = len(vals)
        return [1.0 / n] * n if n else []
    return [x / total for x in vals]


def outcome_probabilities(ce_weights: Sequence[float], outcome_map: Sequence[Sequence[float]]) -> list[float]:
    """Marginal market-outcome probabilities: omega = O^T w.

    ce_weights: length-K weights over surviving NE.
    outcome_map: K x M row-stochastic matrix; row k = NE_k's outcome dist.
    Returns length-M outcome probability vector. Mirrors MATLAB (w' * O)'.
    """
    w = [float(x) for x in ce_weights]
    if not outcome_map:
        return []
    M = len(outcome_map[0])
    omega = [0.0] * M
    for k, row in enumerate(outcome_map):
        wk = w[k]
        for j in range(M):
            omega[j] += wk * float(row[j])
    return omega
