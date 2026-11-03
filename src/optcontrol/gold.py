"""
gold.py -- THE GOLD TRADER'S CONTROL-LIMIT POLICY  (stochastic optimal control)

From the capstone discussion on Oct 29: a student's parents bought gold in
Guyana below the world price and sold it in New York above it.  Between buying
and selling they bear price risk, pay to move the gold, tie up capital (the
interest rate r), and risk losing the shipment.  The professor wrote the
answer as a control-limit policy C(r, F_eps, K): it depends on the interest
rate r, the distribution of the price shock F_eps, and the cost K.

Our version (time step = 1 WEEK, money in $ per troy ounce)
-----------------------------------------------------------
State  s_t : the New York premium = what one ounce sells for in New York minus
             what you paid for it.  It moves around randomly:
                 s_{t+1} = mu + rho (s_t - mu) + sigma * eps_{t+1},  eps ~ N(0,1)
             (an AR(1): it drifts back toward its average mu; rho = how sticky).
Action     : SELL now (ship to New York) or HOLD one more week.
SELL pays  : s_t - K               (K = shipping, insurance, assay, fees)
HOLD costs : h per week            (h = interest on the money tied up in the gold,
                                    X * r/52, plus expected losses, X * q)
Discount   : beta = exp(-r / 52) per week.

Bellman equation
----------------
        V(s) = max{  s - K ,  -h + beta * E[ V(s') | s ]  }
                   (sell)       (hold one more week)

Because selling gets better as s rises while holding depends on s only through
tomorrow's distribution, the optimal policy is a single cutoff:

        SELL iff s >= s*      <-- control-limit policy

There is no pencil-and-paper formula for s* here (the expectation over a
continuous AR(1) has no closed form), so we solve it on a computer:
  1. Tauchen's method turns the AR(1) into a Markov chain on a grid of s values.
  2. Value iteration solves the Bellman equation on that grid.
  3. The cutoff is where "sell" and "hold" cross (linear interpolation).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class GoldParams:
    """Illustrative parameters; every value is justified in docs/DECISIONS.md (G2)."""
    mu: float = 40.0                 # long-run average premium, $/oz
    rho: float = 0.80                # weekly persistence of the premium
    sigma: float = 20.0              # weekly shock size, $/oz
    K: float = 25.0                  # cost to ship and sell, $/oz
    X: float = 2500.0                # capital tied up per ounce, $/oz
    r: float = 0.05                  # annual interest rate (opportunity cost)
    loss_annual: float = 0.01        # 1% yearly chance the gold is lost/seized

    @property
    def beta(self) -> float:
        return float(np.exp(-self.r / 52.0))

    @property
    def q_week(self) -> float:
        """Weekly loss probability implied by the annual one."""
        return 1.0 - (1.0 - self.loss_annual) ** (1.0 / 52.0)

    @property
    def h(self) -> float:
        """Weekly holding cost: interest on the gold's value + expected loss."""
        return self.X * (self.r / 52.0 + self.q_week)

    @property
    def stationary_sd(self) -> float:
        return self.sigma / np.sqrt(1.0 - self.rho**2)


DEFAULT = GoldParams()


def tauchen(mu: float, rho: float, sigma: float, n: int = 201, m: float = 4.0):
    """Tauchen (1986): approximate s' = mu + rho(s-mu) + sigma*eps by an n-state chain.

    Grid: n equally spaced points covering mu +/- m stationary standard deviations.
    P[i, j] = probability of moving from grid point i to grid point j: the
    normal probability of landing in the "bin" around point j.  The end bins
    are open-ended so each row sums to exactly 1.
    """
    sd = sigma / np.sqrt(1.0 - rho**2)
    grid = np.linspace(mu - m * sd, mu + m * sd, n)
    step = grid[1] - grid[0]
    cond_mean = mu + rho * (grid - mu)                        # E[s' | s_i]
    upper = (grid[None, :] + step / 2 - cond_mean[:, None]) / sigma
    lower = (grid[None, :] - step / 2 - cond_mean[:, None]) / sigma
    P = norm.cdf(upper) - norm.cdf(lower)
    P[:, 0] = norm.cdf(upper[:, 0])                           # everything below
    P[:, -1] = 1.0 - norm.cdf(lower[:, -1])                   # everything above
    return grid, P


def solve(params: GoldParams = DEFAULT, n: int = 201, tol: float = 1e-10,
          max_iter: int = 100_000):
    """Value iteration on the Tauchen grid.

    Returns a dict with the grid, V, the sell and hold values, the cutoff s*,
    and the number of iterations used.
    """
    grid, P = tauchen(params.mu, params.rho, params.sigma, n)
    sell = grid - params.K
    V = np.maximum(sell, 0.0)                                  # a sensible start
    for it in range(1, max_iter + 1):
        hold = -params.h + params.beta * (P @ V)
        V_new = np.maximum(sell, hold)
        if np.max(np.abs(V_new - V)) < tol:
            V = V_new
            break
        V = V_new
    else:
        raise RuntimeError("value iteration did not converge")
    hold = -params.h + params.beta * (P @ V)
    return {"grid": grid, "V": V, "sell": sell, "hold": hold,
            "cutoff": cutoff_from(grid, sell, hold), "iterations": it}


def cutoff_from(grid, sell, hold) -> float:
    """Smallest premium where selling beats holding (interpolated between grid points)."""
    gap = sell - hold                     # negative = hold is better, positive = sell
    idx = np.where(gap >= 0)[0]
    if len(idx) == 0:
        return float("inf")               # never sell on this grid
    j = idx[0]
    if j == 0:
        return float(grid[0])             # sell everywhere on the grid
    g0, g1 = gap[j - 1], gap[j]
    return float(grid[j - 1] + (0 - g0) * (grid[j] - grid[j - 1]) / (g1 - g0))


def comparative_statics(base: GoldParams = DEFAULT):
    """How the cutoff C(r, F_eps, K) moves when we change one input at a time."""
    rows = []
    variations = {
        "r":           [0.02, 0.05, 0.10, 0.20],
        "K":           [10.0, 25.0, 40.0],
        "sigma":       [10.0, 20.0, 40.0],
        "rho":         [0.5, 0.8, 0.95],
        "loss_annual": [0.0, 0.01, 0.05, 0.20],
    }
    for name, values in variations.items():
        for v in values:
            p = replace(base, **{name: v})
            rows.append({"parameter": name, "value": v, "cutoff": solve(p)["cutoff"],
                         "h": p.h})
    return rows


def simulate(params: GoldParams = DEFAULT, cutoff: float | None = None,
             n_paths: int = 20_000, max_weeks: int = 2_000, seed: int = 6875):
    """Monte Carlo: start in a typical week and follow a cutoff rule.

    The starting premium is drawn from the long-run (stationary) distribution
    N(mu, stationary_sd^2), so the result is the value of the rule "on an
    average day you happen to be holding gold".

    Returns mean discounted net payoff, its standard error, and the mean number
    of weeks until the sale.  cutoff=None uses the optimal one.
    """
    if cutoff is None:
        cutoff = solve(params)["cutoff"]
    rng = np.random.default_rng(seed)
    s = params.mu + params.stationary_sd * rng.standard_normal(n_paths)
    alive = np.ones(n_paths, bool)
    value = np.zeros(n_paths)
    weeks = np.zeros(n_paths)
    disc = np.ones(n_paths)
    for t in range(max_weeks):
        sell_now = alive & (s >= cutoff)
        value[sell_now] += disc[sell_now] * (s[sell_now] - params.K)
        weeks[sell_now] = t
        alive &= ~sell_now
        if not alive.any():
            break
        value[alive] -= disc[alive] * params.h                 # pay to hold a week
        disc[alive] *= params.beta
        s = params.mu + params.rho * (s - params.mu) + params.sigma * rng.standard_normal(n_paths)
    return float(value.mean()), float(value.std(ddof=1) / np.sqrt(n_paths)), float(weeks.mean())


if __name__ == "__main__":
    out = solve()
    p = DEFAULT
    print(f"weekly holding cost h = ${p.h:.2f}/oz, beta = {p.beta:.5f}")
    print(f"optimal cutoff s* = ${out['cutoff']:.2f}/oz  ({out['iterations']} iterations)")
    for c in [-np.inf, p.mu, out["cutoff"], out["cutoff"] + 30]:
        m, se, w = simulate(cutoff=c)
        print(f"  cutoff {c:6.2f}: value {m:7.2f} +/- {1.96*se:.2f}, mean wait {w:5.1f} weeks")
