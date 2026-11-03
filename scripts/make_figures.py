"""
Reproduce every figure in figures/ and every number in results/results.json.

    python scripts/make_figures.py

Nothing in the README is typed by hand: each number there comes from
results/results.json, which this script writes.
"""

import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from optcontrol import gold, heifer, offer, tree  # noqa: E402

FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)

INK, VIO, MINT, CORAL, LEM = "#24203A", "#5B4BDB", "#0F8F6F", "#E5533D", "#C98F00"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})
results = {}

# ------------------------------------------------------------------ tree ---
Tf, Tz = tree.fisher_rotation(), tree.faustmann_rotation()
T = np.linspace(12, 120, 500)
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(T, tree.growth_rate(T), color=MINT, lw=2.5, label="tree's growth rate $Q'/Q=b/T^2$")
ax[0].axhline(tree.R, color=CORAL, ls="--", lw=2, label=f"bank: r = {tree.R:.0%}")
ax[0].plot(T, tree.R / (1 - np.exp(-tree.R * T)), color=LEM, ls=":", lw=2,
           label="Faustmann hurdle $r/(1-e^{-rT})$")
ax[0].axvline(Tf, color=INK, lw=0.8); ax[0].axvline(Tz, color=INK, lw=0.8, ls=":")
ax[0].text(Tf + 1, 0.15, f"cut once: {Tf:.0f} yrs"); ax[0].text(Tz - 34, 0.012, f"replant: {Tz:.1f} yrs")
ax[0].set_ylim(0, 0.3); ax[0].set_xlabel("age of the stand T (years)"); ax[0].set_ylabel("rate per year")
ax[0].set_title("Wait while the tree beats the bank"); ax[0].legend(frameon=False, fontsize=9)
ax[1].plot(T, tree.present_value(T), color=VIO, lw=2.5)
ax[1].plot([Tf], [tree.present_value(Tf)], "o", color=CORAL, ms=8)
ax[1].set_xlabel("age at harvest T (years)"); ax[1].set_ylabel("present value ($ per hectare)")
ax[1].set_title("Present value of one harvest peaks at T* = 50")
fig.savefig(os.path.join(FIG, "tree.png")); plt.close(fig)
results["tree"] = {"fisher_T": Tf, "faustmann_T": Tz, "pv_at_fisher": float(tree.present_value(Tf)),
                   "volume_at_fisher": float(tree.volume(Tf))}

# ---------------------------------------------------------------- heifer ---
P = heifer.DEFAULT
Ts = heifer.optimal_sale_day()
t = np.linspace(0, Ts, 300)
mid, f_num, J_num = heifer.solve_numerically(Ts, N=40)
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot(t, heifer.optimal_feed(t, Ts), color=MINT, lw=2.5, label="Pontryagin (pencil and paper)")
ax[0].plot(mid, f_num, "o", color=CORAL, ms=4, label="brute-force optimizer (40 steps)")
ax[0].set_xlabel("day"); ax[0].set_ylabel("feed (lb per day)"); ax[0].legend(frameon=False)
ax[0].set_title("Feed little early, a lot before the sale")
ax[1].plot(t, heifer.optimal_weight(t, Ts), color=VIO, lw=2.5)
ax[1].set_xlabel("day"); ax[1].set_ylabel("weight (lb)"); ax[1].set_title("Weight path")
TT = np.linspace(0, 700, 400)
ax[2].plot(TT, [heifer.profit(x) for x in TT], color=INK, lw=2.5)
ax[2].axvline(Ts, color=CORAL, ls="--"); ax[2].axhline(P.p * P.W0, color="gray", ls=":", lw=1)
ax[2].text(Ts + 12, 960, f"sell on day {Ts:.0f}")
ax[2].text(420, P.p * P.W0 + 6, "sell today", color="gray")
ax[2].set_xlabel("sale day T"); ax[2].set_ylabel("profit, present value ($)")
ax[2].set_title("Choosing the sale date")
fig.savefig(os.path.join(FIG, "heifer.png")); plt.close(fig)
results["heifer"] = {
    "sale_day": Ts, "sale_months": Ts / 30.44, "sale_weight": float(heifer.optimal_weight(Ts, Ts)),
    "feed_start": float(heifer.optimal_feed(0, Ts)), "feed_end": float(heifer.optimal_feed(Ts, Ts)),
    "profit": heifer.profit(Ts), "sell_today": P.p * P.W0,
    "avg_daily_gain": float((heifer.optimal_weight(Ts, Ts) - P.W0) / Ts),
    "total_feed_lb": float(np.trapezoid(heifer.optimal_feed(t, Ts), t)),
    "numeric_profit_40_steps": J_num,
    "max_feed_gap_lb_per_day": float(np.max(np.abs(f_num - heifer.optimal_feed(mid, Ts)))),
}

# ----------------------------------------------------------------- offer ---
V = offer.reservation_value()
_, path = offer.value_iteration(V0=0.0)
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
x = np.linspace(0, 1, 300)
ax[0].plot(x, x, color=INK, lw=1.5, label="45-degree line")
ax[0].plot(x, [offer.bellman(v) for v in x], color=VIO, lw=2.5, label=r"$T(V)=0.9(1+V^2)/2$")
for a_, b_ in zip(path[:6], path[1:7]):
    ax[0].plot([a_, a_], [a_, b_], color=CORAL, lw=1); ax[0].plot([a_, b_], [b_, b_], color=CORAL, lw=1)
ax[0].plot([V], [V], "o", color=CORAL, ms=8)
ax[0].set_title(f"Fixed point V* = {V:.3f}"); ax[0].set_xlabel("V"); ax[0].legend(frameon=False)
ax[1].plot(range(len(path)), path, "o-", color=VIO, ms=4, label="value iteration from 0")
ax[1].axhline(V, color=CORAL, ls="--", label="closed form")
ax[1].set_xlabel("iteration k  (= offers left - 1)"); ax[1].set_ylabel("cutoff")
ax[1].set_title("Same numbers as a shrinking deadline"); ax[1].legend(frameon=False)
betas = np.linspace(0.05, 0.995, 200)
ax[2].plot(betas, [offer.reservation_value(b) for b in betas], color=MINT, lw=2.5)
ax[2].set_xlabel(r"patience $\beta$"); ax[2].set_ylabel("accept offers above")
ax[2].set_title("More patient = pickier")
fig.savefig(os.path.join(FIG, "offer.png")); plt.close(fig)
sim_m, sim_se = offer.simulate_policy(V)
results["offer"] = {
    "V_star": V, "vi_iterations_from_0": len(path) - 1, "first_cutoffs": list(map(float, path[:7])),
    "cutoff_by_beta": {str(b): offer.reservation_value(b) for b in (0.5, 0.9, 0.95, 0.99)},
    "simulated_value": sim_m, "simulated_se": sim_se,
    "simulated_other_cutoffs": {str(c): offer.simulate_policy(c)[0] for c in (0.3, 0.5, 0.75, 0.9)},
}

# ------------------------------------------------------------------ gold ---
G = gold.DEFAULT
out = gold.solve()
s_star = out["cutoff"]
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
g = out["grid"]; keep = (g > -40) & (g < 140)
ax[0].plot(g[keep], out["sell"][keep], color=CORAL, lw=2.5, label="sell now: $s-K$")
ax[0].plot(g[keep], out["hold"][keep], color=VIO, lw=2.5, label=r"hold: $-h+\beta E[V(s')|s]$")
ax[0].axvline(s_star, color=INK, ls="--"); ax[0].text(s_star + 2, -50, f"s* = ${s_star:.2f}")
ax[0].set_xlabel("today's premium s ($/oz)"); ax[0].set_ylabel("value ($/oz)")
ax[0].set_title("Control-limit policy: sell above s*"); ax[0].legend(frameon=False)
rows = gold.comparative_statics()
fmt = {"r": ("r", lambda v: f"{v:.0%}"), "K": ("K", lambda v: f"${v:.0f}"),
       "sigma": ("σ", lambda v: f"${v:.0f}"), "rho": ("ρ", lambda v: f"{v:.2f}"),
       "loss_annual": ("loss/yr", lambda v: f"{v:.0%}")}
cols = {"r": VIO, "K": "gray", "sigma": MINT, "rho": LEM, "loss_annual": CORAL}
ylab, y = [], 0
for name in ["r", "loss_annual", "sigma", "rho", "K"]:
    for rr in [q for q in rows if q["parameter"] == name]:
        is_base = rr["value"] == getattr(G, name)
        ax[1].plot([rr["cutoff"]], [y], "o", color=cols[name], ms=9 if is_base else 7,
                   mfc=cols[name] if not is_base else "white", mew=2)
        ylab.append(f"{fmt[name][0]} = {fmt[name][1](rr['value'])}"); y += 1
    y += 0.6; ylab.append("")
pos, yy = [], 0
for l in ylab:
    if l:
        pos.append(yy); yy += 1
    else:
        yy += 0.6
ax[1].set_yticks(pos); ax[1].set_yticklabels([l for l in ylab if l], fontsize=9)
ax[1].invert_yaxis(); ax[1].axvline(s_star, color=INK, lw=0.8, ls="--")
ax[1].set_xlabel("cutoff s* ($/oz);  hollow dot = baseline")
ax[1].set_title("What moves the cutoff C(r, F, K)")
rng = np.random.default_rng(25)
s = np.empty(40); s[0] = G.mu
for k in range(39):
    s[k + 1] = G.mu + G.rho * (s[k] - G.mu) + G.sigma * rng.standard_normal()
sold = int(np.argmax(s >= s_star))
ax[2].plot(range(40), s, color=INK, lw=1.5, marker="o", ms=3)
ax[2].axhline(s_star, color=CORAL, ls="--", label="cutoff s*")
ax[2].axhline(G.mu, color="gray", ls=":", label=r"average premium $\mu$")
ax[2].plot([sold], [s[sold]], "*", color=CORAL, ms=16, label=f"sell in week {sold}")
ax[2].set_xlabel("week"); ax[2].set_ylabel("premium ($/oz)"); ax[2].legend(loc="upper right", fontsize=9, framealpha=0.95)
ax[2].set_title("One simulated shipment")
fig.savefig(os.path.join(FIG, "gold.png")); plt.close(fig)
sims = {}
for name, c in [("sell_immediately", -np.inf), ("wait_for_average", G.mu), ("optimal", s_star),
                ("too_picky_plus_30", s_star + 30)]:
    m_, se_, w_ = gold.simulate(cutoff=c)
    sims[name] = {"cutoff": None if not np.isfinite(c) else c, "value": m_, "se": se_, "mean_weeks": w_}
results["gold"] = {
    "params": {"mu": G.mu, "rho": G.rho, "sigma": G.sigma, "K": G.K, "X": G.X, "r": G.r,
               "loss_annual": G.loss_annual, "beta": G.beta, "h": G.h, "q_week": G.q_week,
               "stationary_sd": G.stationary_sd},
    "cutoff": s_star, "iterations": out["iterations"],
    "cutoff_n401": gold.solve(n=401)["cutoff"], "cutoff_n801": gold.solve(n=801)["cutoff"],
    "comparative_statics": rows, "simulation": sims,
}

with open(os.path.join(ROOT, "results", "results.json"), "w") as fh:
    json.dump(results, fh, indent=2, default=float)
print(json.dumps(results, indent=1, default=float)[:3000])
