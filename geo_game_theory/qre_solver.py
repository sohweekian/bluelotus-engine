"""
BGTM-V1 — Logit Quantal Response Equilibrium solver
===================================================
Port of qre_softmax / expected_payoff from matlab/bgtm_validate.m and
matlab/bgtm_heavy.m (McKelvey-Palfrey 1995).

- softmax():  numerically-stable logit choice probabilities (scalar path)
- solve_qre(): damped fixed-point iteration for an N-player game given a
  list of payoff tensors (NumPy), each of shape (m,)*N. Mirrors the MATLAB
  heavy-path contraction; runs the 10-player / 3**10 game in well under 50 ms.

GOVERNANCE: pure deterministic numerics. No LLM, no broker path.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def softmax(payoffs: Sequence[float], lam: float = 1.0) -> list[float]:
    """Logit QRE choice probabilities at rationality lambda.

    Mirrors MATLAB qre_softmax: shift by max for numerical stability.
    lam=0 -> uniform; lam->inf -> argmax (Nash).
    """
    v = [float(x) for x in payoffs]
    if not v:
        return []
    z = [lam * (x - max(v)) for x in v]
    e = [math.exp(x) for x in z]
    s = sum(e)
    return [x / s for x in e]


def _expected_payoff(U: np.ndarray, marginals: list[np.ndarray], i: int, N: int, m: int) -> np.ndarray:
    """Expected-payoff m-vector for player i.

    Contract payoff tensor U over the marginal strategy distributions of all
    OTHER players (full tensor broadcast). Mirrors MATLAB expected_payoff.
    """
    W = np.ones((m,) * N)
    for j in range(N):
        if j == i:
            continue
        shp = [1] * N
        shp[j] = m
        W = W * marginals[j].reshape(shp)
    T = U * W
    axes = tuple(d for d in range(N) if d != i)
    return np.sum(T, axis=axes).reshape(m)


def solve_qre(
    payoff_tensors: Sequence[np.ndarray],
    lam: float = 0.5,
    damp: float = 0.5,
    tol: float = 1e-9,
    max_iter: int = 500,
) -> dict:
    """Damped logit-QRE fixed point for an N-player normal-form game.

    payoff_tensors: list of N arrays each shaped (m,)*N; tensor i is player i's
    payoff over the joint strategy profile.

    Returns dict with strategies (N x m list), iterations, gap, converged.
    """
    N = len(payoff_tensors)
    if N == 0:
        return {"strategies": [], "iterations": 0, "gap": 0.0, "converged": True}
    m = payoff_tensors[0].shape[0]
    p = [np.full(m, 1.0 / m) for _ in range(N)]

    gap = float("inf")
    it = 0
    while it < max_iter and gap > tol:
        it += 1
        gap = 0.0
        new_p = list(p)
        for i in range(N):
            eu = _expected_payoff(payoff_tensors[i], p, i, N, m)
            qi = np.asarray(softmax(eu.tolist(), lam))
            new_p[i] = (1.0 - damp) * p[i] + damp * qi
            gap = max(gap, float(np.max(np.abs(new_p[i] - p[i]))))
        p = new_p

    return {
        "strategies": [pi.tolist() for pi in p],
        "iterations": it,
        "gap": gap,
        "converged": gap <= tol,
    }
