"""
tree.py -- WHEN DO YOU CUT A TREE?  (deterministic optimal stopping)

This is the warm-up example from the Oct 29 lecture: "a tree grows; its
biological rate of return falls; if there is an interest rate from a competing
asset, you harvest the tree at T*."

The model
---------
Timber volume of the stand (cubic meters) after T years:

        Q(T) = exp(a - b / T)

Why this curve? (see docs/DECISIONS.md, decision T1)
  * Q starts near 0, grows, and levels off at exp(a): trees have a mature size.
  * Its growth RATE  Q'(T)/Q(T) = b / T**2  falls as the tree ages, which is
    exactly the "biological rate of return goes down" picture from lecture.
  * It gives a closed-form answer, so we can check the computer against algebra.

You sell the timber for p dollars per cubic meter and money in the bank earns
the continuously compounded interest rate r.  Cutting at age T is worth, today,

        PV(T) = p * Q(T) * exp(-r T).

The rule (single rotation, a.k.a. Fisher's rule)
------------------------------------------------
Take logs:  log PV = log p + a - b/T - r T.
Derivative: b/T**2 - r = 0          =>  Q'/Q = r
Second derivative: -2 b / T**3 < 0  =>  it is a maximum, not a minimum.

        T* = sqrt(b / r)

In words: WAIT WHILE THE TREE GROWS FASTER THAN MONEY IN THE BANK.

Extension: the Faustmann rule (you replant after every cut)
-----------------------------------------------------------
If the land is replanted forever, every year of waiting also delays ALL future
rotations, so waiting is more expensive and you cut sooner:

        Q'(T)/Q(T) = r / (1 - exp(-r T))

The right-hand side is bigger than r, so T_Faustmann < T_Fisher.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

# ---------------------------------------------------------------------------
# Default parameters (every number is justified in docs/DECISIONS.md, T2)
# ---------------------------------------------------------------------------
A = float(np.log(600.0))  # mature volume exp(a) = 600 m^3 per hectare
B = 100.0                 # curvature: how slowly the stand approaches maturity
R = 0.04                  # 4% per year real interest rate
P = 50.0                  # $50 per m^3 stumpage price


def volume(T, a: float = A, b: float = B):
    """Timber volume Q(T) in m^3. Works on floats or numpy arrays."""
    T = np.asarray(T, dtype=float)
    return np.exp(a - b / T)


def growth_rate(T, b: float = B):
    """Biological rate of return Q'(T)/Q(T) = b / T^2 (per year)."""
    T = np.asarray(T, dtype=float)
    return b / T**2


def present_value(T, p: float = P, a: float = A, b: float = B, r: float = R):
    """Present value of cutting once at age T: p * Q(T) * exp(-r T)."""
    T = np.asarray(T, dtype=float)
    return p * volume(T, a, b) * np.exp(-r * T)


def fisher_rotation(b: float = B, r: float = R) -> float:
    """Closed-form single-rotation age T* = sqrt(b/r)."""
    if b <= 0 or r <= 0:
        raise ValueError("b and r must be positive")
    return float(np.sqrt(b / r))


def second_derivative_log_pv(T: float, b: float = B) -> float:
    """d^2/dT^2 of log PV(T) = -2b/T^3. Negative => the FOC is a maximum."""
    return -2.0 * b / T**3


def faustmann_rotation(b: float = B, r: float = R) -> float:
    """Rotation age when the land is replanted forever.

    Solves  b/T^2 = r / (1 - exp(-rT)).  There is no closed form, so we use
    Brent's method: a bracketing root-finder that cannot diverge as long as the
    function changes sign on the bracket (we check that it does).
    """
    def g(T):
        return b / T**2 - r / (1.0 - np.exp(-r * T))

    lo, hi = 1.0, fisher_rotation(b, r)  # Faustmann age is below Fisher's
    if g(lo) * g(hi) > 0:
        raise RuntimeError("root not bracketed; check parameters")
    return float(brentq(g, lo, hi, xtol=1e-12))


def faustmann_land_value(T, p: float = P, a: float = A, b: float = B, r: float = R):
    """Value of bare land replanted every T years forever.

    Rotations pay p*Q(T) at times T, 2T, 3T, ...  A geometric series gives
        LEV(T) = p Q(T) e^{-rT} / (1 - e^{-rT}).
    """
    T = np.asarray(T, dtype=float)
    d = np.exp(-r * T)
    return p * volume(T, a, b) * d / (1.0 - d)


if __name__ == "__main__":
    Tf = fisher_rotation()
    print(f"Fisher (cut once):        T* = {Tf:.2f} years, PV = ${present_value(Tf):,.0f}/ha")
    Tz = faustmann_rotation()
    print(f"Faustmann (replant):      T* = {Tz:.2f} years")
