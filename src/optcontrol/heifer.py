"""
heifer.py -- HOW MUCH SHOULD YOU FEED A HEIFER, AND WHEN DO YOU SELL HER?
(deterministic optimal control, solved with Pontryagin's maximum principle)

This is the professor's own first research project, as he described it on
Oct 29: a heifer's weight W depends on what you feed her (f); you sell her at a
future date T for p dollars per pound; feed costs money now, the sale pays
later, so everything is discounted at the interest rate r.

The model (time t in DAYS)
--------------------------
State   W(t)  : live weight in pounds
Control f(t)  : pounds of feed per day (f >= 0)
Dynamics      : dW/dt = a * sqrt(f) - m * W
Objective     : maximize   J = p W(T) e^{-rT}  -  integral_0^T c f(t) e^{-rt} dt

Why these pieces (full reasoning in docs/DECISIONS.md, H1-H5):
  * a*sqrt(f): DIMINISHING RETURNS to feed. Doubling feed does not double gain.
  * -m*W: MAINTENANCE. A heavier animal burns more of what it eats just to stay
    the same size; with no feed she slowly loses weight.
  * linear sale value p*W(T) and linear feed cost c*f: prices are taken from
    the market (a small producer cannot move the price of cattle or corn).

Solving it by hand (Pontryagin)
-------------------------------
Present-value Hamiltonian ("profit flow + value of the weight you add"):

    H = -c f e^{-rt} + lambda(t) * (a sqrt(f) - m W)

lambda(t) = SHADOW VALUE of one more pound at time t, in today's dollars.

 1. Feed choice (dH/df = 0):    c e^{-rt} = lambda * a / (2 sqrt f)
                                 "feed until the last scoop costs exactly what
                                  the weight it adds is worth"
 2. Costate (dlambda/dt = -dH/dW): lambda' = m * lambda
 3. Transversality:              lambda(T) = p e^{-rT}  (at sale, a pound is
                                 worth its price)

From 2 and 3:  lambda(t) = p e^{-rT} e^{-m (T - t)}.
In CURRENT dollars the value of a pound at time t is

    mu(t) = lambda(t) e^{rt} = p * exp(-(r + m) (T - t)),

i.e. the sale price, discounted for interest (r) AND for the fact that a pound
added early "melts" through maintenance (m). Plugging into step 1:

    sqrt f*(t) = a mu(t) / (2c)   =>   f*(t) = ( a p / (2c) )^2 * exp(-2 (r+m) (T-t))

Feeding RISES as the sale date approaches: cheap maintenance early, heavy
feeding at the end. That is exactly what cattle feeders do in practice
("backgrounding" on cheap forage, then a "finishing" ration).

Is the first-order condition really the optimum?  Yes: H is concave in (W, f)
(sqrt is concave, the W term is linear, and lambda > 0), so Mangasarian's
sufficiency theorem says the Pontryagin path is the global maximum.

Everything below is a closed form; `solve_numerically` re-solves the same
problem by brute-force optimization so you can SEE the math is right.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize, minimize_scalar


@dataclass(frozen=True)
class HeiferParams:
    """All parameters in one place. Units are in the comments.

    Calibration (docs/DECISIONS.md, H3): chosen so the answer looks like a
    real feeding operation -- a 500 lb weaned heifer, fed for about 8 months,
    sold near 940 lb, average gain about 1.85 lb/day, daily feed rising from
    about 8 lb (cheap "backgrounding") to about 26 lb (a full "finishing"
    ration, the most a heifer that size will realistically eat).
    """
    W0: float = 500.0          # starting weight, lb
    a: float = 0.88            # growth efficiency, lb/day per sqrt(lb feed/day)
    m: float = 0.00225         # maintenance drag, per day
    p: float = 1.80            # sale price, $ per lb live weight
    c: float = 0.155           # feed cost, $ per lb of feed (~$310/ton ration)
    r_annual: float = 0.05     # 5% per year interest rate

    @property
    def r(self) -> float:
        """Daily continuously compounded interest rate."""
        return self.r_annual / 365.0


DEFAULT = HeiferParams()


# ---------------------------------------------------------------------------
# Closed-form optimal path for a FIXED sale date T
# ---------------------------------------------------------------------------
def shadow_price(t, T: float, P: HeiferParams = DEFAULT):
    """mu(t): value (in time-t dollars) of one more pound at time t."""
    t = np.asarray(t, dtype=float)
    return P.p * np.exp(-(P.r + P.m) * (T - t))


def optimal_feed(t, T: float, P: HeiferParams = DEFAULT):
    """f*(t) = (a mu(t) / (2c))^2, pounds of feed per day."""
    return (P.a * shadow_price(t, T, P) / (2.0 * P.c)) ** 2


def optimal_weight(t, T: float, P: HeiferParams = DEFAULT):
    """W*(t) under optimal feeding (exact solution of the linear ODE).

    dW/dt + mW = a sqrt(f*) = A e^{(r+m)t},  A = a^2 p e^{-(r+m)T} / (2c)
    => W(t) = W0 e^{-mt} + A e^{-mt} (e^{(r+2m)t} - 1) / (r + 2m)
    """
    t = np.asarray(t, dtype=float)
    A = P.a**2 * P.p * np.exp(-(P.r + P.m) * T) / (2.0 * P.c)
    k = P.r + 2.0 * P.m
    return P.W0 * np.exp(-P.m * t) + A * np.exp(-P.m * t) * np.expm1(k * t) / k


def feed_cost_pv(T: float, P: HeiferParams = DEFAULT) -> float:
    """Present value of all feed bought on [0, T] under the optimal plan.

    c f*(t) e^{-rt} = B e^{(r+2m)t}, B = a^2 p^2 e^{-2(r+m)T} / (4c)
    """
    B = P.a**2 * P.p**2 * np.exp(-2.0 * (P.r + P.m) * T) / (4.0 * P.c)
    k = P.r + 2.0 * P.m
    return float(B * np.expm1(k * T) / k)


def profit(T: float, P: HeiferParams = DEFAULT) -> float:
    """Present value of feeding optimally and selling at day T."""
    if T <= 0:
        return P.p * P.W0  # sell today
    return float(P.p * optimal_weight(T, T, P) * np.exp(-P.r * T) - feed_cost_pv(T, P))


def optimal_sale_day(P: HeiferParams = DEFAULT, T_max: float = 1500.0) -> float:
    """Outer problem: choose the sale date T that maximizes profit(T).

    This is a one-variable smooth problem, so a bounded scalar optimizer is
    the right tool (docs/DECISIONS.md, H5).
    """
    res = minimize_scalar(lambda T: -profit(T, P), bounds=(1.0, T_max),
                          method="bounded", options={"xatol": 1e-6})
    return float(res.x)


# ---------------------------------------------------------------------------
# Brute-force check: solve the SAME problem without any calculus
# ---------------------------------------------------------------------------
def simulate_weight(feed: np.ndarray, T: float, P: HeiferParams = DEFAULT) -> np.ndarray:
    """Weight path when feed is piecewise constant on N equal steps.

    On each step the ODE dW/dt = a sqrt(f) - m W has an exact solution, so
    there is no Euler error: W_{k+1} = W_k e^{-m dt} + (a sqrt(f_k)/m)(1 - e^{-m dt}).
    """
    N = len(feed)
    dt = T / N
    decay = np.exp(-P.m * dt)
    W = np.empty(N + 1)
    W[0] = P.W0
    for k in range(N):
        W[k + 1] = W[k] * decay + P.a * np.sqrt(max(feed[k], 0.0)) / P.m * (1.0 - decay)
    return W


def discretized_profit(feed: np.ndarray, T: float, P: HeiferParams = DEFAULT) -> float:
    """Profit of a piecewise-constant feeding plan (feed cost discounted exactly)."""
    N = len(feed)
    dt = T / N
    t0 = np.arange(N) * dt
    # integral of c f e^{-rt} over [t0, t0+dt] = c f e^{-r t0} (1 - e^{-r dt}) / r
    cost = np.sum(P.c * feed * np.exp(-P.r * t0) * (1.0 - np.exp(-P.r * dt)) / P.r)
    W = simulate_weight(feed, T, P)
    return float(P.p * W[-1] * np.exp(-P.r * T) - cost)


def solve_numerically(T: float, N: int = 60, P: HeiferParams = DEFAULT):
    """Maximize discretized_profit over N feed levels with L-BFGS-B.

    We optimize over u = sqrt(f) (so u >= 0 is a simple bound and the problem
    is smooth). Returns (step midpoints, numerically optimal feed, profit).
    """
    def neg(u):
        return -discretized_profit(np.asarray(u) ** 2, T, P)

    u0 = np.full(N, 3.0)  # start at 9 lb/day everywhere: a feasible, boring plan
    res = minimize(neg, u0, method="L-BFGS-B", bounds=[(0.0, None)] * N,
                   options={"maxiter": 5000, "ftol": 1e-14, "gtol": 1e-10})
    dt = T / N
    mid = (np.arange(N) + 0.5) * dt
    return mid, res.x**2, -res.fun


if __name__ == "__main__":
    T = optimal_sale_day()
    print(f"Optimal sale day: {T:.1f} (about {T/30.4:.1f} months)")
    print(f"Sale weight: {optimal_weight(T, T):.0f} lb")
    print(f"Feed at start {optimal_feed(0, T):.1f} lb/day, at sale {optimal_feed(T, T):.1f} lb/day")
    print(f"Profit (PV): ${profit(T):,.2f}  vs sell today ${DEFAULT.p*DEFAULT.W0:,.2f}")
