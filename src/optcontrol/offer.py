"""
offer.py -- WHICH OFFER SHOULD YOU ACCEPT?  (the simplest stochastic control problem)

The running example for all three presentations.

Story: each period one offer w arrives (a bid for your gold, a job offer, a
buyer for your house).  Offers are independent draws from Uniform(0, 1).
  * ACCEPT  -> you get w and the game ends.
  * REJECT  -> nothing today; next period a new offer arrives.
A dollar next period is worth beta dollars today (beta = 0.9).

Bellman equation
----------------
Let V be the value of being "between offers" (before seeing the next one).
When an offer w arrives you take the better of w and waiting:

        V = beta * E[ max(w, V) ]

For w ~ U(0,1):  E[max(w, V)] = integral_0^V V dw + integral_V^1 w dw = (1 + V^2)/2

        V = beta (1 + V^2) / 2   <=>   beta V^2 - 2 V + beta = 0
        V* = (1 - sqrt(1 - beta^2)) / beta          (take the root below 1)

POLICY: accept iff w >= V*.  With beta = 0.9, V* = 0.6268.
This one-cutoff rule is a CONTROL-LIMIT (or "reservation") policy.

Three ways to get the same number are in this file:
  1. the closed form above,
  2. value iteration (start anywhere, apply the Bellman map until it stops moving),
  3. backward induction on a finite deadline (n offers left).  Surprise:
     the value-iteration sequence started at 0 IS the finite-deadline sequence.
"""

from __future__ import annotations

import numpy as np

BETA = 0.9


def expected_max_uniform(V: float) -> float:
    """E[max(w, V)] for w ~ Uniform(0,1) and 0 <= V <= 1."""
    V = float(np.clip(V, 0.0, 1.0))
    return (1.0 + V * V) / 2.0


def bellman(V: float, beta: float = BETA) -> float:
    """The Bellman map T(V) = beta * E[max(w, V)]."""
    return beta * expected_max_uniform(V)


def reservation_value(beta: float = BETA) -> float:
    """Closed-form V* = (1 - sqrt(1 - beta^2)) / beta."""
    if not 0.0 < beta < 1.0:
        raise ValueError("beta must be strictly between 0 and 1")
    return (1.0 - np.sqrt(1.0 - beta**2)) / beta


def value_iteration(beta: float = BETA, V0: float = 0.0, tol: float = 1e-10,
                    max_iter: int = 10_000):
    """Iterate V_{k+1} = T(V_k). Returns (V*, list of iterates).

    Stops when |V_{k+1} - V_k| < tol.  Because T is a contraction with modulus
    at most beta, the true error is then at most beta/(1-beta) * tol.
    """
    path = [V0]
    V = V0
    for _ in range(max_iter):
        V_new = bellman(V, beta)
        path.append(V_new)
        if abs(V_new - V) < tol:
            return V_new, path
        V = V_new
    raise RuntimeError("value iteration did not converge")


def finite_horizon_cutoffs(n_offers: int, beta: float = BETA) -> np.ndarray:
    """Acceptance cutoff when n offers remain (including the one in hand).

    With 1 offer left you accept anything (cutoff 0).  With n left you accept
    if w beats beta * U_{n-1}, where U_k = E[max(w, cutoff_k)] is the value of
    facing k more offers.  Returns cutoffs[n-1] for n = 1..n_offers.
    """
    cut = np.zeros(n_offers)
    U_prev = 0.0  # value of facing 0 offers = 0
    for n in range(1, n_offers + 1):
        cut[n - 1] = beta * U_prev
        U_prev = expected_max_uniform(cut[n - 1])
    return cut


def contraction_modulus(V1: float, V2: float, beta: float = BETA) -> float:
    """|T(V1) - T(V2)| / |V1 - V2|  (always <= beta: the contraction property)."""
    return abs(bellman(V1, beta) - bellman(V2, beta)) / abs(V1 - V2)


def simulate_policy(cutoff: float, beta: float = BETA, n_paths: int = 100_000,
                    seed: int = 6875):
    """Monte Carlo check: average discounted payoff of 'accept iff w >= cutoff'.

    Waiting time is geometric with success probability (1 - cutoff), so we can
    simulate it in one vectorized shot instead of a Python loop.
    """
    rng = np.random.default_rng(seed)
    p_accept = 1.0 - cutoff
    waits = rng.geometric(p_accept, size=n_paths) - 1          # rejected offers
    accepted = cutoff + p_accept * rng.random(n_paths)          # U(cutoff, 1)
    payoff = beta ** (waits + 1) * accepted                     # +1: first offer is next period
    return float(payoff.mean()), float(payoff.std(ddof=1) / np.sqrt(n_paths))


if __name__ == "__main__":
    V = reservation_value()
    Vvi, path = value_iteration()
    print(f"closed form V* = {V:.6f}")
    print(f"value iteration V* = {Vvi:.6f} after {len(path)-1} steps")
    print("finite-deadline cutoffs n=1..6:", np.round(finite_horizon_cutoffs(6), 4))
    m, se = simulate_policy(V)
    print(f"simulated value of the policy = {m:.4f} +/- {1.96*se:.4f}")
