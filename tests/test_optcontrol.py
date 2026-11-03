"""
Tests: every closed-form answer in this repo is checked against an
independent computer calculation.  Run from the repo root with:

    pytest -q

If a test fails, the math in the docs and the code disagree -- which is
exactly what a test is for.
"""

import numpy as np
import pytest

from optcontrol import gold, heifer, offer, tree


# ----------------------------------------------------------------- tree ----
def test_fisher_rotation_is_50_years():
    assert tree.fisher_rotation() == pytest.approx(50.0)


def test_fisher_rule_growth_equals_interest():
    T = tree.fisher_rotation()
    assert tree.growth_rate(T) == pytest.approx(tree.R)        # Q'/Q = r
    assert tree.second_derivative_log_pv(T) < 0                # a maximum


def test_fisher_rotation_maximizes_present_value_on_a_grid():
    T = np.linspace(10, 150, 140_001)
    assert T[np.argmax(tree.present_value(T))] == pytest.approx(50.0, abs=1e-3)


def test_faustmann_is_shorter_and_maximizes_land_value():
    Tz = tree.faustmann_rotation()
    assert Tz < tree.fisher_rotation()
    T = np.linspace(10, 150, 140_001)
    assert T[np.argmax(tree.faustmann_land_value(T))] == pytest.approx(Tz, abs=1e-3)


# --------------------------------------------------------------- heifer ----
def test_shadow_price_equals_sale_price_at_sale():
    T = 200.0
    assert heifer.shadow_price(T, T) == pytest.approx(heifer.DEFAULT.p)


def test_closed_form_weight_solves_the_ode():
    """Feed the closed-form plan into an exact step-by-step simulation."""
    T, N = 240.0, 20_000
    mid = (np.arange(N) + 0.5) * T / N
    W_sim = heifer.simulate_weight(heifer.optimal_feed(mid, T), T)
    assert W_sim[-1] == pytest.approx(heifer.optimal_weight(T, T), rel=1e-5)


def test_pontryagin_matches_brute_force_optimization():
    """The calculus answer and a 60-variable numerical optimizer agree."""
    T = 240.0
    mid, f_num, J_num = heifer.solve_numerically(T, N=60)
    assert J_num == pytest.approx(heifer.profit(T), rel=1e-4)
    assert np.max(np.abs(f_num - heifer.optimal_feed(mid, T))) < 0.05   # lb/day


def test_optimal_sale_day_is_a_maximum():
    T = heifer.optimal_sale_day()
    for dT in (-20, -5, 5, 20):
        assert heifer.profit(T) > heifer.profit(T + dT)
    assert heifer.profit(T) > heifer.profit(0)                  # beats selling today


def test_feeding_rises_toward_the_sale():
    T = heifer.optimal_sale_day()
    f = heifer.optimal_feed(np.linspace(0, T, 50), T)
    assert np.all(np.diff(f) > 0)


# ---------------------------------------------------------------- offer ----
def test_offer_closed_form_value():
    assert offer.reservation_value(0.9) == pytest.approx(0.626789, abs=1e-6)


@pytest.mark.parametrize("beta", [0.5, 0.9, 0.95, 0.99])
def test_closed_form_solves_bellman_and_matches_value_iteration(beta):
    V = offer.reservation_value(beta)
    assert offer.bellman(V, beta) == pytest.approx(V, abs=1e-12)
    V_vi, _ = offer.value_iteration(beta)
    assert V_vi == pytest.approx(V, abs=1e-8)


def test_value_iteration_from_zero_equals_finite_deadline_cutoffs():
    _, path = offer.value_iteration(0.9, V0=0.0)
    cut = offer.finite_horizon_cutoffs(10, 0.9)
    assert np.allclose(path[:10], cut)


def test_bellman_map_is_a_contraction():
    rng = np.random.default_rng(0)
    for _ in range(1000):
        a, b = rng.random(2)
        assert offer.contraction_modulus(a, b, 0.9) <= 0.9 + 1e-12


def test_simulated_policy_value_matches_theory():
    V = offer.reservation_value()
    mean, se = offer.simulate_policy(V)
    assert abs(mean - V) < 4 * se


def test_reservation_cutoff_beats_other_cutoffs():
    V = offer.reservation_value()
    best, _ = offer.simulate_policy(V)
    for c in (0.3, 0.5, 0.75, 0.9):
        other, _ = offer.simulate_policy(c)   # same seed = common random numbers
        assert best > other


# ----------------------------------------------------------------- gold ----
def test_tauchen_rows_are_probabilities():
    _, P = gold.tauchen(40, 0.8, 20, n=101)
    assert np.all(P >= 0)
    assert np.allclose(P.sum(axis=1), 1.0)


def test_tauchen_chain_has_the_right_long_run_mean_and_sd():
    grid, P = gold.tauchen(40, 0.8, 20, n=201)
    w, v = np.linalg.eig(P.T)                                   # stationary distribution
    pi = np.real(v[:, np.argmin(np.abs(w - 1))]); pi /= pi.sum()
    mean = pi @ grid
    sd = np.sqrt(pi @ (grid - mean) ** 2)
    assert mean == pytest.approx(40, abs=0.01)
    assert sd == pytest.approx(20 / np.sqrt(1 - 0.64), rel=0.02)


def test_policy_is_a_single_cutoff():
    out = gold.solve()
    sell_better = out["sell"] >= out["hold"]
    first = np.argmax(sell_better)
    assert not sell_better[:first].any() and sell_better[first:].all()


def test_cutoff_moves_the_right_way():
    rows = gold.comparative_statics()
    by = lambda name: [r["cutoff"] for r in rows if r["parameter"] == name]
    assert np.all(np.diff(by("r")) < 0)            # costlier money -> sell sooner
    assert np.all(np.diff(by("loss_annual")) < 0)  # riskier holding -> sell sooner
    assert np.all(np.diff(by("sigma")) > 0)        # bigger swings -> wait for a better one


def test_cutoff_is_stable_when_grid_is_refined():
    c201 = gold.solve(n=201)["cutoff"]
    c801 = gold.solve(n=801)["cutoff"]
    assert abs(c201 - c801) < 0.5                  # dollars per ounce


def test_optimal_cutoff_beats_alternatives_in_simulation():
    best = gold.simulate()[0]
    for c in (-np.inf, 40.0, 70.0):
        assert best > gold.simulate(cutoff=c)[0]
