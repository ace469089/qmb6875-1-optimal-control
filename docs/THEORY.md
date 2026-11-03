# The Full Lesson: Optimal Control From Zero

This file assumes you know what a derivative is and what an expected value is. Nothing else.
Each section ends with a **"check it yourself"** pointer to the code that verifies the math.

**Contents**
0. [The one question, and the four ingredients](#0-the-one-question-and-the-four-ingredients)
1. [Problem 1: when to cut a tree (one number, no randomness)](#1-problem-1-when-to-cut-a-tree)
2. [Problem 2: feeding a heifer (a whole plan, no randomness)](#2-problem-2-feeding-a-heifer)
3. [From continuous time to steps: the Bellman equation](#3-from-continuous-time-to-steps-the-bellman-equation)
4. [Problem 3: the offer problem (randomness enters)](#4-problem-3-the-offer-problem)
5. [Problem 4: the gold trader (randomness that remembers)](#5-problem-4-the-gold-trader)
6. [Continuous time with noise: the HJB equation](#6-continuous-time-with-noise-the-hjb-equation)
7. [The map of the whole subject](#7-the-map-of-the-whole-subject)

---

## 0. The one question, and the four ingredients

Ordinary optimization picks **one number**: the price that maximizes profit, the quantity that minimizes cost.
**Optimal control** picks a **plan over time**, where each step of the plan changes where you will be at the next step.

Every problem in this repo has the same four ingredients:

| Ingredient | Symbol | Plain English | Heifer example |
|---|---|---|---|
| **State** | $x$ (or $W$, $s$) | where you are right now | the heifer's weight $W$ |
| **Control** (action) | $u$ (or $f$) | the knob you turn | pounds of feed per day $f$ |
| **Dynamics** (law of motion) | $\dot x=g(x,u)$ or $x'=g(x,u,\varepsilon)$ | how today's choice moves you to tomorrow | $\dot W=a\sqrt f-mW$ |
| **Objective** | $J$ | what you're maximizing, with future money discounted | sale value minus feed costs |

Two more words you'll see everywhere:

- **Discounting.** A dollar later is worth less than a dollar now, because a dollar now can earn interest.
  - In continuous time, a dollar $t$ years from now is worth $e^{-rt}$ today.
  - In steps, a dollar one step from now is worth $\beta<1$ today ($\beta=e^{-r\Delta t}$).
- **Policy.** A rule that says what to do in every situation: "if the premium is above $50.49, ship."
  The goal of optimal control is to find the **best policy**.

> **Deterministic** means tomorrow is fully determined by today's state and action (Problems 1–2).
> **Stochastic** means tomorrow also depends on luck (Problems 3–4). The only change to the math is an expectation $E[\cdot]$ in front of the future.

---

## 1. Problem 1: when to cut a tree

*Code: [`src/optcontrol/tree.py`](../src/optcontrol/tree.py) · Tests: `test_fisher_*`, `test_faustmann_*`*

### Setup

A stand of trees holds $Q(T)=e^{a-b/T}$ cubic meters of timber at age $T$ years.
- $e^{a}=600$ m³/hectare is the mature size (the curve levels off there).
- $b=100$ controls how slowly it gets there.

Timber sells for $p=\$50$/m³. The bank pays $r=4\%$ per year.

### The decision

Cut at age $T$, and you get $p\,Q(T)$, received $T$ years from now, so its value today is

$$PV(T)=p\,Q(T)\,e^{-rT}.$$

### Solve it

Maximizing $PV$ is the same as maximizing $\log PV$, because $\log$ is increasing. The log turns products into sums:

$$\log PV(T)=\log p + a - \frac{b}{T} - rT.$$

Set the derivative to zero:

$$\frac{d}{dT}\log PV = \frac{b}{T^2} - r = 0 \quad\Longrightarrow\quad \boxed{\;\frac{Q'(T)}{Q(T)} = r\;} \quad\Longrightarrow\quad T^*=\sqrt{\frac{b}{r}}=\sqrt{\frac{100}{0.04}}=50.$$

Here $Q'/Q=\frac{d}{dT}\log Q=b/T^2$ is the tree's **growth rate**, which the professor called its *biological rate of return*.

**Is it a maximum?** The second derivative of $\log PV$ is $-2b/T^3<0$, so yes.

### Read the answer in English

> **Wait while the tree grows faster than money in the bank.** The moment the tree's growth rate falls below the interest rate, cut it and put the money in the bank.

At 50 years the stand holds 81.2 m³/ha, and cutting then is worth \$549/ha today.

### Extension: the Faustmann rule (you replant)

If the land is replanted after every cut, forever, the land's value is a geometric series of identical rotations:

$$LEV(T)=\frac{p\,Q(T)\,e^{-rT}}{1-e^{-rT}}.$$

Maximizing gives

$$\frac{Q'(T)}{Q(T)}=\frac{r}{1-e^{-rT}}.$$

The right side is **bigger than $r$**, because waiting a year also delays every future crop. So you cut sooner: $T^*=45.83$ years, found numerically with Brent's root-finder.

**Why we started with Fisher.** It has a closed form and a one-line intuition, which is what a first example should have. Faustmann is the follow-up answer for when someone asks "what about replanting?"

### Why this is optimal *control*, not just calculus

It's the simplest possible control problem. The "plan" has one decision (when to stop), and the state (tree volume) evolves on its own. This is an **optimal stopping** problem. Problems 3 and 4 are optimal stopping problems too, just with randomness.

---

## 2. Problem 2: feeding a heifer

*Code: [`src/optcontrol/heifer.py`](../src/optcontrol/heifer.py) · Tests: `test_pontryagin_matches_brute_force_optimization` and others*

This is the professor's own first research project. Now the choice is a **function** $f(t)$, how much to feed on every single day. That's infinitely many numbers, so "take the derivative and set it to zero" doesn't apply directly. We need a new tool.

### Setup (time in days)

| Symbol | Meaning | Value |
|---|---|---|
| $W(t)$ | live weight, lb (the **state**) | starts at $W_0=500$ |
| $f(t)\ge0$ | feed, lb/day (the **control**) | chosen |
| $a$ | growth efficiency | 0.88 |
| $m$ | maintenance drag per day | 0.00225 |
| $p$ | sale price, $/lb | 1.80 |
| $c$ | feed cost, $/lb | 0.155 |
| $r$ | interest, per day | 0.05/365 |

**Dynamics:**

$$\dot W(t)=a\sqrt{f(t)}-m\,W(t)$$

- $a\sqrt f$: diminishing returns. The 20th pound of feed adds less weight than the 1st.
- $-mW$: maintenance. A bigger animal burns more just to stay the same size, and without feed she slowly loses weight.

**Objective:** sell at day $T$ and maximize the present value of profit:

$$J=\underbrace{p\,W(T)\,e^{-rT}}_{\text{sale, discounted}}-\underbrace{\int_0^T c\,f(t)\,e^{-rt}\,dt}_{\text{feed bill, discounted}}.$$

### The key idea: put a price on the state

Feeding today has two effects: it costs money now, and it raises tomorrow's weight. To compare them, Pontryagin's idea is to put a **price tag** $\lambda(t)$ on one pound of weight at time $t$, measured in today's dollars. This price is called the **costate** or **shadow value**.

With that price, write the **Hamiltonian**, "profit flow right now + value of the weight you're adding right now":

$$H=-c\,f\,e^{-rt}+\lambda(t)\,\big(a\sqrt f-mW\big).$$

**Pontryagin's maximum principle** says the optimal plan satisfies three conditions:

| Condition | Math | English |
|---|---|---|
| 1. Choose the control to maximize $H$ | $\dfrac{\partial H}{\partial f}=0:\;\;c\,e^{-rt}=\lambda\,\dfrac{a}{2\sqrt f}$ | feed until the last scoop costs exactly what the weight it adds is worth |
| 2. The price of the state evolves | $\dot\lambda=-\dfrac{\partial H}{\partial W}=m\,\lambda$ | how a pound's value changes over time |
| 3. Transversality (the end condition) | $\lambda(T)=p\,e^{-rT}$ | on sale day, a pound is worth exactly its sale price |

### Solve it

From conditions 2 and 3: $\lambda(t)=p\,e^{-rT}e^{-m(T-t)}$.

It's easier to read in **current** dollars, $\mu(t)=\lambda(t)e^{rt}$:

$$\mu(t)=p\,e^{-(r+m)(T-t)}.$$

A pound added on day $t$ is worth the sale price, discounted twice: once for interest ($r$) and once because an early pound "melts" through maintenance ($m$) before sale day.

Put this into condition 1 and solve for $f$:

$$\sqrt{f^*(t)}=\frac{a\,\mu(t)}{2c}\qquad\Longrightarrow\qquad \boxed{\;f^*(t)=\Big(\frac{a\,p}{2c}\Big)^2e^{-2(r+m)(T-t)}\;}$$

**Read it in English:** feeding rises steadily toward the sale. Early pounds are expensive to keep (they melt and the money waits), so you add most of the weight late. Real feedlots do exactly this: cheap "backgrounding" on forage, then a high-energy "finishing" ration.

Then the weight equation is linear, with the exact solution coded in `optimal_weight`.

### Choosing the sale date

For each sale date $T$ we now know the best plan and its profit $J(T)$. The best date maximizes $J(T)$, which is a one-variable problem solved with a bounded scalar optimizer.

| Result | Value |
|---|---|
| Best sale day | **239.3** (≈ 7.9 months) |
| Sale weight | **942 lb** (avg gain 1.85 lb/day) |
| Feed on day 0 → sale day | **8.3 → 26.1 lb/day** |
| Total feed | 3,724 lb |
| Profit (present value) | **$1,074.51** |
| Selling the 500 lb heifer today | $900.00 |

Selling earlier wastes cheap growth. Selling later means maintenance eats more and more of each scoop, while the money waits longer.

### Is the first-order condition really the best plan?

Pontryagin's conditions are **necessary**. They are also **sufficient** here (Mangasarian's theorem), because $H$ is **concave** in $(W,f)$ jointly: $\sqrt f$ is concave, the $W$ term is linear, and $\lambda>0$. So there is no better plan hiding somewhere else.

### Check it with a computer that knows no calculus

`solve_numerically` splits the 239 days into 40 equal steps and treats the 40 feed levels as unknowns. It computes profit exactly for any plan, and lets a standard optimizer (L-BFGS-B) climb uphill from a dull starting plan (9 lb/day every day).

**Result:** the optimizer's plan matches the formula to within **0.0004 lb/day**, and its profit is $1,074.50 vs $1,074.51. (The tiny gap is because 40 constant steps can't exactly trace a smooth curve.)

> **Why bother with Pontryagin if a computer can do this?** The formula *explains* the answer: feed rises at rate $2(r+m)$ because of interest and maintenance. The optimizer only reports numbers. With 40 unknowns brute force is easy. With many states, years of daily decisions, and randomness, it isn't, which is where Bellman (next) and repo 3 come in.

---

## 3. From continuous time to steps: the Bellman equation

Chop time into periods (days, weeks). Let $V(x)$ = **the best total payoff you can get starting from state $x$**. This is the **value function**.

Richard Bellman's observation, the **principle of optimality**:

> Whatever you did to get here, an optimal plan must be optimal **from here on**.

So the best you can do from $x$ is "what you're paid today + the discounted best you can do from wherever you land":

$$\boxed{\;V(x)=\max_u\Big\{\,R(x,u)+\beta\,V(x')\Big\},\qquad x'=g(x,u)\;}$$

This one equation turns an infinite sequence of decisions into **one decision plus a function**, $V$, that summarizes the entire future.

**Connection to Pontryagin.** The heifer's shadow price is the slope of the value function: $\lambda(t)=\partial V/\partial W$. "The value of one more pound" and "how much the best total payoff rises if you had one more pound" are the same thing. Pontryagin is the continuous-time, slope version; Bellman is the discrete-time, level version.

### Adding randomness

If tomorrow depends on luck, $x'=g(x,u,\varepsilon)$, you can't know $V(x')$. You can only average over what might happen:

$$V(x)=\max_u\Big\{\,R(x,u)+\beta\,E\big[V(x')\mid x,u\big]\Big\}.$$

That expectation is **the only difference** between deterministic and stochastic control.

---

## 4. Problem 3: the offer problem

*Code: [`src/optcontrol/offer.py`](../src/optcontrol/offer.py) · Tests: `test_offer_*`, `test_value_iteration_*`, `test_bellman_map_is_a_contraction`*

This is the running example in all three repos, because its answer is known exactly, so every method can be checked against it.

### Setup

Each period one offer $w\sim\text{Uniform}(0,1)$ arrives. Offers are independent of each other.
- **Accept:** you get $w$ and the game ends.
- **Reject:** you get nothing this period and a new offer comes next period.
- Patience: $\beta=0.9$.

Examples: a buyer's bid for your gold, a job offer (the professor's *reservation wage*), a bid on your house.

### Bellman equation

Let $V$ = value of being "between offers." When offer $w$ shows up, you'll take the better of $w$ and waiting again:

$$V=\beta\,E\big[\max(w,V)\big].$$

Compute the expectation by splitting at $V$:
- offers below $V$ are rejected (worth $V$);
- offers above $V$ are taken (worth $w$).

$$E[\max(w,V)]=\int_0^V V\,dw+\int_V^1 w\,dw=V^2+\frac{1-V^2}{2}=\frac{1+V^2}{2}.$$

So $V=\beta(1+V^2)/2$, i.e. $\beta V^2-2V+\beta=0$, and

$$V^*=\frac{1-\sqrt{1-\beta^2}}{\beta}=\frac{1-\sqrt{0.19}}{0.9}=0.6268.$$

We take the "minus" root because the "plus" root ($\approx1.60$) is above 1, and waiting can never be worth more than the best possible offer.

**Policy:** accept iff $w\ge0.627$.

### Why the answer is a single cutoff (a control-limit policy)

Accepting pays $w$, which rises one-for-one with the offer. Waiting pays $V^*$, which **does not depend on today's offer**. A rising line crosses a flat line exactly once, so there is one cutoff. This is the simplest case of a general result: when "stop" gets better with the state faster than "continue" does, the optimal policy is a threshold.

### More patient = pickier

| $\beta$ | 0.50 | 0.90 | 0.95 | 0.99 |
|---|---|---|---|---|
| cutoff $V^*$ | 0.268 | 0.627 | 0.724 | 0.868 |

### Solving it without the formula: value iteration

Define the **Bellman map** $T(V)=\beta(1+V^2)/2$. The answer is a **fixed point**, a $V$ with $T(V)=V$. Start anywhere and apply $T$ repeatedly:

$$V_0=0\ \to\ 0.450\ \to\ 0.541\ \to\ 0.582\ \to\ 0.602\ \to\ 0.613\ \to\ \cdots\ \to\ 0.6268\quad(38\text{ steps to }10^{-10}).$$

**Why this must converge (the contraction mapping theorem).** For any two guesses,

$$|T(V_1)-T(V_2)|=\tfrac{\beta}{2}|V_1^2-V_2^2|=\tfrac{\beta}{2}|V_1+V_2|\,|V_1-V_2|\le\beta\,|V_1-V_2|.$$

Each application of $T$ shrinks the gap between any two guesses by at least $\beta<1$. So all guesses get squeezed onto the same point: the answer exists, is unique, and value iteration finds it from **any** start. The test `test_bellman_map_is_a_contraction` checks this on 1,000 random pairs.

### A beautiful fact: value iteration = a shrinking deadline

Suppose you must accept one of at most $n$ offers.
- With **1** offer left you accept anything: cutoff **0**.
- With **2** left you accept if $w$ beats waiting for the last one: cutoff $\beta\cdot E[w]=0.45$.
- With **3** left: cutoff **0.541**, and so on.

These are **exactly** the value-iteration numbers above (test: `test_value_iteration_from_zero_equals_finite_deadline_cutoffs`). Value iteration from 0 literally solves longer and longer deadline problems, and the infinite-horizon answer is the limit as the deadline disappears.

### Check by simulation

The code plays the policy 100,000 times. Average payoff: **0.6266 ± 0.0009** (theory 0.6268).

Other cutoffs, same random numbers:

| cutoff | 0.30 | 0.50 | **0.627** | 0.75 | 0.90 |
|---|---|---|---|---|---|
| value | 0.561 | 0.613 | **0.627** | 0.606 | 0.450 |

---

## 5. Problem 4: the gold trader

*Code: [`src/optcontrol/gold.py`](../src/optcontrol/gold.py) · Tests: `test_tauchen_*`, `test_policy_is_a_single_cutoff`, `test_cutoff_*`, `test_optimal_cutoff_beats_alternatives_in_simulation`*

### The story (from class)

A student's parents bought gold in Guyana below the world price and sold it in New York above it. While they held it, they bore price risk, tied up money that could earn interest elsewhere, paid to move it, and risked losing it. (The professor's version involved compatriots waiting at JFK.)

The professor said the optimum is a **control-limit policy** $C(r,F_\varepsilon,K)$ that depends on the interest rate, the distribution of the shock, and the costs.

### Our model (one step = one week, money in $/oz)

| Piece | Model | Value |
|---|---|---|
| State: NY premium $s_t$ | $s_{t+1}=\mu+\rho(s_t-\mu)+\sigma\varepsilon_{t+1}$, $\varepsilon\sim N(0,1)$ | $\mu=40$, $\rho=0.8$, $\sigma=20$ |
| Sell now | receive $s-K$ | $K=25$ |
| Hold a week | pay $h=X\,(r/52+q)$ | $X=2{,}500$, $r=5\%$, 1%/yr loss risk ⇒ $h=\$2.89$ |
| Discount | $\beta=e^{-r/52}$ | 0.99904 |

The premium is an **AR(1)**: it gets pulled back toward its average $\mu$ ($\rho$ is how sticky it is). In the long run it is spread $N(40,\,33.3^2)$.

### Bellman equation

$$V(s)=\max\Big\{\underbrace{s-K}_{\text{ship now}},\ \underbrace{-h+\beta\,E[V(s')\mid s]}_{\text{hold one more week}}\Big\}.$$

Unlike Problem 3, today's premium **predicts** tomorrow's (the state has memory), so "hold" now depends on $s$. The expectation over a normal shock inside a max has no closed form, so we go to the computer.

### Solving on a computer (details in repo 3)

1. **Tauchen's method** replaces the continuous premium with 201 grid points spanning ±4 long-run standard deviations, plus a $201\times201$ table $P_{ij}$ of the probability of moving from point $i$ to point $j$. Tests check that the rows sum to 1 and that the chain's long-run mean (40) and standard deviation (33.3) match the AR(1).
2. **Value iteration** applies $V\leftarrow\max\{s-K,\,-h+\beta PV\}$ until the largest change is below $10^{-10}$ (196 steps).
3. **The cutoff** is where "ship" and "hold" cross, found by linear interpolation between grid points.

**Answer: ship once the premium is at least $50.49/oz.** On 401 and 801 grid points it is $50.49 again, so the answer is not an artifact of the grid.

Note that the cutoff is **above** the average premium of $40. When the premium is merely average, it's worth paying $2.89/week to wait for a better one.

### Comparative statics: what moves $C(r,F_\varepsilon,K)$

| Change | Cutoff moves | Why |
|---|---|---|
| Interest rate $r$: 2% → 5% → 10% → 20% | 68.6 → 50.5 → 29.6 → −2.1 | each week of waiting costs more interest on the $2,500 tied up |
| Loss risk: 0% → 1% → 5% → 20% a year | 55.7 → 50.5 → 32.9 → −20.0 | holding is riskier, so take what you can get |
| Shock size $\sigma$: 10 → 20 → 40 | 32.9 → 50.5 → 96.9 | bigger swings make a great premium more likely, so waiting is worth more (*option value*) |
| Persistence $\rho$: 0.5 → 0.8 → 0.95 | 53.1 → 50.5 → 19.8 | with slow mean reversion, a bad premium stays bad for weeks of holding costs |
| Shipping cost $K$: 10 → 25 → 40 | 50.3 → 50.5 → 50.6 | barely moves: you pay $K$ whenever you ship, so waiting only postpones it |

A negative cutoff means "ship now even at a loss." When holding is expensive enough, cutting your losses beats paying to wait.

### Does the policy actually earn more? (simulation, 20,000 shipments)

Each shipment starts in a typical week, drawn from the long-run distribution. All rules face the **same** random premiums (common random numbers), so differences are due to the rule, not luck.

| Rule | Value ($/oz, ± 95% interval) | Mean wait |
|---|---|---|
| ship immediately | 14.86 ± 0.46 | 0 weeks |
| ship once premium ≥ average (40) | 25.54 ± 0.36 | 3.1 weeks |
| **optimal (≥ 50.49)** | **26.59 ± 0.40** | 5.2 weeks |
| too picky (≥ 80.49) | 4.04 ± 0.98 | 21.7 weeks |

Two lessons:
- Patience pays: 26.59 vs 14.86.
- Too much patience is ruinous: 4.04. Holding costs pile up while you wait for a premium that rarely comes.

---

## 6. Continuous time with noise: the HJB equation

The professor mentioned that "anybody with knowledge of continuous-time stochastic control would say: why not use stochastic calculus?" For completeness, here is what that looks like.

If the state follows a diffusion $dx=\mu(x,u)\,dt+\sigma(x)\,dB$ (where $dB$ is Brownian motion noise), the Bellman equation becomes the **Hamilton–Jacobi–Bellman (HJB)** equation:

$$rV(x)=\max_u\Big\{R(x,u)+V'(x)\,\mu(x,u)+\tfrac12\sigma^2(x)\,V''(x)\Big\}.$$

- $rV$: the "interest" the value must earn.
- $R$: today's payoff flow.
- $V'\mu$: value from where the state is drifting.
- $\tfrac12\sigma^2V''$: the extra term from **Itô's lemma**. Noise matters through the *curvature* of $V$, the same Jensen's-inequality idea from the midterm, $E[g(X)]\approx g(\mu)+\tfrac12g''\sigma^2$.

**Why we don't solve it here.** HJB is a nonlinear differential equation in $V$. As the professor put it, only a "minuscule family" of problems have closed-form solutions; the rest are solved numerically (repo 3) or learned (repo 2). Our discrete-time Bellman equation is exactly what you'd use to approximate HJB on a computer.

---

## 7. The map of the whole subject

| | **No randomness** | **Randomness** |
|---|---|---|
| **Continuous time** | Pontryagin: Hamiltonian, costate (heifer) | HJB equation (Section 6) |
| **Discrete time** | Bellman, $V(x)=\max\{R+\beta V(x')\}$ | Bellman with $E[\cdot]$ (offer, gold) |
| **Solved by** | calculus when possible, optimizer otherwise | closed form if lucky, value iteration on a grid, or **learn it** (repo 2) |

**The three-sentence summary:**
1. Optimal control picks a plan, not a number, because today's choice moves tomorrow's state.
2. Price the state (Pontryagin) or summarize the future in a value function (Bellman), and a hard problem becomes "one decision + a function."
3. Randomness only adds an expectation, but it usually kills the closed form, which is why the next two repos exist.
