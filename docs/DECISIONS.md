# Decision Log: Every Choice, Why, and What I Rejected

This file exists so that every "why did you…?" question already has a written answer.
Each decision has an ID; the code comments point here (for example `docs/DECISIONS.md, H3`).

Format for each entry: **Decision → Why → Alternatives I rejected (and why) → What would change if this were different.**

---

## Big picture

### D1. Four problems, ordered from easiest to hardest
- **Decision:** tree → heifer → offer → gold.
- **Why:** each problem adds exactly **one** new idea:
  1. tree: optimize over time at all (one decision, a closed form);
  2. heifer: the decision is a whole *plan*, which needs Pontryagin;
  3. offer: *randomness*, which needs Bellman with an expectation;
  4. gold: randomness with *memory* (an AR(1)), so no closed form, which needs a computer.

  A student who understands the step before can always follow the next one.
- **Rejected:** starting with the general HJB equation (too abstract for a first exposure), or teaching only the gold problem (no way to check the answer against a formula).

### D2. All examples come from the October 29 class
- **Decision:** the tree, the heifer and the gold trader are the professor's own examples.
- **Why:** the audience has already heard the stories, so their attention goes to the method. It also shows the presentation answers the professor's prompt ("stochastic control… whoever draws this one will want to start with deterministic optimal control").
- **Rejected:** textbook examples like rocket landing or the Merton portfolio problem. They're correct but unfamiliar to this class.

### D3. Every closed form is checked by an independent computer calculation
- **Decision:** formula vs grid search (tree), formula vs a 40-variable optimizer (heifer), formula vs value iteration vs simulation (offer), coarse vs fine grids and simulation (gold).
- **Why:** a derivation can contain a sign error. Two methods that share no code agreeing is strong evidence both are right. It also answers "how do you know?" before anyone asks.

### D4. A running example shared by all three repos
- **Decision:** the offer problem ($V^*=0.627$) appears in all three presentations.
- **Why:** it is the only stochastic control problem with a **one-line exact answer**. Repo 2 shows reinforcement learning rediscovering 0.627 without knowing the offer distribution; repo 3 shows value iteration and Newton finding it. One number ties the three talks together.

---

## Problem 1: the tree

### T1. Growth curve $Q(T)=e^{a-b/T}$
- **Why:**
  1. it has the right shape: starts near zero, rises, levels off at a mature size $e^a$;
  2. its growth rate $b/T^2$ **falls with age**, which is the professor's picture;
  3. it gives a closed-form rotation $T^*=\sqrt{b/r}$, so the first example has a pencil answer.
- **Rejected:**
  - Logistic or Chapman–Richards curves: realistic, but the first-order condition has no closed form.
  - A quadratic: it eventually goes negative, so it has no biological meaning.

### T2. Parameter values $e^a=600$ m³/ha, $b=100$, $r=4\%$, $p=\$50$/m³
- **Why:**
  - $b/r=2{,}500$ makes $T^*$ exactly 50 years, a round number the audience can remember.
  - 50 years is a typical rotation for many commercial softwood stands.
  - 4% is a common real discount rate in forestry analysis.
  - The price only scales profit; it **does not affect $T^*$** (it cancels in the log derivative). That's worth saying out loud.
- **Would change:** a higher $r$ gives a shorter rotation ($T^*\propto1/\sqrt r$).

### T3. Single rotation (Fisher) first, Faustmann as an extension
- **Why:** Fisher's rule "growth rate = interest rate" is the cleanest statement of the trade-off. Faustmann adds the opportunity cost of the *land* and gives a shorter rotation (45.8 years).
- **Root finder:** Brent's method on the bracket [1, Fisher age]. It is guaranteed to converge when the function changes sign on the bracket, and the code checks that it does. Newton could diverge from a bad start (see repo 3).

---

## Problem 2: the heifer

### H1. Diminishing returns: growth $a\sqrt{f}$
- **Why:**
  - Doubling feed does not double gain; animals convert feed less efficiently at high intake.
  - The square root is the simplest concave function that also gives a **closed-form** optimal feed: the first-order condition is $1/\sqrt f\propto$ price.
- **Rejected:**
  - **Linear growth $a f$:** then $H$ is linear in $f$, and the optimal control is "bang-bang" (feed zero or the maximum). That's mathematically legitimate, but less intuitive and unrealistic.
  - **$f^\gamma$ with a general $\gamma$:** same structure, just messier exponents. $\gamma=\tfrac12$ keeps the algebra on one line.

### H2. Maintenance drag $-mW$
- **Why:**
  - A heavier animal spends more energy just to maintain itself. Without it, weight would never be lost and holding the animal would be free.
  - It also makes the costate equation $\dot\lambda=m\lambda$, which solves in one line.
- **Effect on the answer:** this is **why feeding rises toward the sale**. A pound added early "melts" at rate $m$ before it can be sold.
- **Rejected:** maintenance proportional to $W^{0.75}$ (metabolic weight, what animal scientists use). It's more accurate, but it makes the costate equation nonlinear with no closed form.

### H3. Calibration: $W_0=500$, $a=0.88$, $m=0.00225$, $p=\$1.80$/lb, $c=\$0.155$/lb, $r=5\%$/yr
- **How I chose them:** I asked for an answer that *looks like a real feeding operation*, then picked parameters that deliver it:
  - a 500 lb weaned heifer;
  - fed for months, not days or years;
  - daily feed peaking near 26 lb (around the most a heifer that size will eat);
  - average gain near 2 lb/day.

  The code's result: 239 days, 942 lb, 1.85 lb/day gain, feed 8.3 → 26.1 lb/day.
- **What I rejected along the way:** my first calibration ($c=\$0.18$, $m=0.004$) said "sell after 36 days." Feed was so expensive relative to weight that feeding barely paid. I rejected it because the model is supposed to describe a business people actually run. **This is worth saying if asked:** checking that the answer is *plausible* is part of modeling, not cheating. The structure of the answer (feed rising toward the sale) is the same under both calibrations; only the numbers change.
- **Sources of realism:** live cattle and feeder prices in the mid-$1 to $2+/lb range in recent years; finishing rations a few hundred dollars per ton; typical intake ~2–2.5% of body weight. These are round, realistic numbers, not estimates.

### H4. Linear prices: sale value $pW$, feed cost $cf$
- **Why:** a single producer is a **price taker**; one person's heifer does not move the national cattle market.
- **Would change:** with a volume discount on feed or a premium for weight classes, the costate equation gains extra terms. The method is the same.

### H5. How the sale date is chosen
- **Decision:** solve the inner problem (best feeding plan for each $T$) with the formula, then choose $T$ with a bounded scalar optimizer.
- **Why:** profit as a function of $T$ is smooth with one peak (see `figures/heifer.png`), so a one-dimensional bounded search is reliable. The test `test_optimal_sale_day_is_a_maximum` confirms the found $T$ beats $T\pm5$ and $T\pm20$ days.
- **Equivalent textbook approach:** a free-terminal-time condition $H(T)=0$ adjusted for discounting. Optimizing $J(T)$ directly is the same answer and easier to explain.

### H6. Brute-force check uses exact step-by-step dynamics
- **Decision:** within each of the 40 steps feed is constant, and the weight ODE is solved **exactly** on that step (not with Euler's method). The feed cost integral is also computed exactly.
- **Why:** then the only difference between the optimizer's problem and the true problem is "feed must be constant within a step," so any remaining gap is due to that, not to numerical error in the simulation.
- **Optimizer:** L-BFGS-B over $u=\sqrt f$ with the bound $u\ge0$. Optimizing over $\sqrt f$ keeps feed nonnegative with a simple bound and avoids the infinite slope of $\sqrt f$ at zero.
- **Starting plan:** 9 lb/day every day, deliberately boring, so the optimizer has to *find* the rising shape on its own.

---

## Problem 3: the offer problem

### O1. Offers are Uniform(0,1) and independent
- **Why:** this is the only common case where $E[\max(w,V)]$ is a one-line polynomial, so $V^*$ comes from the quadratic formula.
- **Would change:** with a different distribution $F$, the equation becomes $V=\beta\big(V F(V)+\int_V^\infty w\,dF\big)$. It is still one equation in one unknown, solved numerically.

### O2. $\beta=0.9$
- **Why:** it gives a cutoff (0.627) far enough from both 0 and 1 to make the point that you should be picky but not too picky. A table over $\beta\in\{0.5,0.9,0.95,0.99\}$ shows the comparative static.

### O3. Stopping rule $|V_{k+1}-V_k|<10^{-10}$
- **Why:** for a contraction with modulus $\beta$, the distance to the true answer is at most $\frac{\beta}{1-\beta}$ times the last step, i.e. $9\times10^{-10}$. That's far below any meaningful precision.

### O4. Simulation uses a geometric waiting time
- **Why:** with a fixed cutoff $c$, each offer is accepted with probability $1-c$, so the number of rejections is geometric. The accepted offer is Uniform$(c,1)$. This simulates 100,000 searches in one vectorized line, with no loop.
- **Common random numbers:** every cutoff is simulated with the same seed (6875), so comparisons between cutoffs aren't polluted by luck.

---

## Problem 4: the gold trader

### G1. State = the New York premium, not the gold price itself
- **Why:** the trader's profit is the *premium* (what NY pays minus what Guyana cost). If the world gold price moves, both the purchase and the sale move with it. The decision "ship now or wait" hinges on the premium, which is the professor's $\varepsilon$.
- **What this assumes:** the overall gold price is a martingale (no predictable drift) and the trader is risk-neutral. Holding then costs interest on the capital, but gold-price risk does not change the *expected* payoff.

### G2. Parameters
| Parameter | Value | Why |
|---|---|---|
| time step | 1 week | shipments are arranged on a scale of days to weeks; weekly keeps the numbers readable |
| $\mu$ | $40/oz | an illustrative average arbitrage margin, under 2% of the gold's value |
| $\rho$ | 0.8/week | premiums are sticky but revert within a few weeks (half-life ≈ 3.1 weeks) |
| $\sigma$ | $20/oz/week | large enough that waiting has real option value (long-run sd $33) |
| $K$ | $25/oz | shipping, insurance, assay and fees |
| $X$ | $2,500/oz | capital tied up per ounce (a round illustrative gold value) |
| $r$ | 5%/yr | the opportunity cost of money: the professor's point that money in gold isn't earning elsewhere |
| loss risk | 1%/yr | theft, seizure, or the deal collapsing (the JFK story) |

- **Calibration note:** with $\sigma=\$12$, my first choice, the optimal cutoff fell *below* the average premium. The trader would ship immediately in a typical week, which is a boring and uninformative answer. I raised $\sigma$ so the example actually shows waiting being optimal. The comparative-statics table shows exactly what happens at $\sigma=10$ (cutoff 32.9), so nothing is hidden.

### G3. Holding cost $h=X(r/52+q)$ instead of a separate "loss" state
- **Why:**
  - Interest on capital and the expected loss both scale with the gold's value and are paid every week you hold, so together they form one weekly cost.
  - Writing it as a cost keeps the state one-dimensional and the Bellman equation one line.
- **Rejected:** an explicit "gold lost" absorbing state. It's equivalent for a risk-neutral trader, but adds a state and a probability branch without adding insight.

### G4. Tauchen's method with 201 points over ±4 long-run standard deviations
- **Why Tauchen:** it is the standard, simple way to turn an AR(1) into a finite Markov chain (Tauchen, 1986), and it is easy to explain: "the probability of landing in each bin."
- **Why ±4 sd:** a premium beyond 4 sd has probability below 0.01%, so truncation is negligible.
- **Why 201 points:** the cutoff is $50.49 at 201, 401 and 801 points (changes under 1 cent), so 201 is accurate and fast.
- **Rejected:** Rouwenhorst's method. It's better when $\rho$ is close to 1 (0.99+), but at $\rho=0.8$ Tauchen is accurate (tests confirm the chain's mean and sd), and it is easier to explain.

### G5. Value iteration (not policy iteration) to solve it
- **Why:** it is the direct translation of the Bellman equation, so the code reads like the math. It takes 196 iterations and well under a second. Repo 3 compares it with policy iteration, which needs fewer but more expensive iterations.
- **Starting guess:** $V_0=\max(s-K,0)$, a sensible guess. Any start converges (contraction), but a sensible one is faster.

### G6. Cutoff found by linear interpolation between grid points
- **Why:** the raw grid only says the cutoff lies between two points about $1.33 apart. The sell-minus-hold gap is smooth, so interpolating gives sub-cent accuracy (confirmed by grid refinement).

### G7. Comparative statics: one parameter at a time
- **Why:** this is literally the professor's $C(r,F_\varepsilon,K)$. Each row isolates one channel. The test `test_cutoff_moves_the_right_way` checks the predicted directions: higher $r$ or higher loss risk gives a lower cutoff; higher $\sigma$ gives a higher one.

### G8. Simulation starts from the long-run distribution, with common random numbers
- **Why:** starting every path at exactly $\mu$ would answer "what if the premium happens to be average today?" Starting from the stationary distribution answers "what is this rule worth on a typical day?", which is the fair comparison. The same seed for every rule means the rules face identical premium paths.

---

## Code and engineering

### C1. Python with NumPy/SciPy/Matplotlib
- **Why:** the professor recommended learning Python and R first, as the lingua franca. Everything runs in Google Colab with no install.

### C2. A real package (`src/optcontrol/`) with tests, not just a notebook
- **Why:** notebooks are great for showing, but bad for checking. Code in modules can be imported by tests and the figure script, so the numbers in the README, notebook and tests all come from **one** implementation.

### C3. Every module runs on its own
- `python -m optcontrol.offer` prints that model's results, so you can demo any one problem in seconds.

### C4. Fixed random seeds
- **Why:** anyone re-running the code gets the same numbers as this README (reproducibility). 6875 is the course number.

### C5. One script writes every figure and every number
- **Why:** `scripts/make_figures.py` writes `results/results.json`, and the README numbers come from that file. If the code changes, the numbers can be regenerated, not retyped.

### C6. Closed forms written with `expm1` and logs
- **Why:** `np.expm1(x)` computes $e^x-1$ accurately when $x$ is small (the heifer's $(r+2m)t$ is small early on). Plain `exp(x)-1` would lose digits to rounding. It's a small detail, but exactly the kind of numerical care the professor discussed.
