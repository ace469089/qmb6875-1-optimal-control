# How to Present This (15 minutes, or 60 seconds if cold-called)

## If you are cold-called: the 60-second version

> "Optimal control is choosing a plan over time when today's choice changes tomorrow.
> Four ingredients: a state, a control, dynamics linking them, and a discounted payoff.
> Deterministic example: cut a tree when its growth rate falls to the interest rate, so $T^*=\sqrt{b/r}=50$ years.
> With a whole plan, like feeding a heifer, Pontryagin puts a price on each pound and you feed until a scoop costs what it adds. That's why feeding rises toward the sale.
> In steps, Bellman's equation says value now = payoff today + discounted value tomorrow. Stochastic just adds an expectation.
> Example: offers uniform on 0 to 1 with $\beta=0.9$, so $V=0.9(1+V^2)/2$ and you accept above 0.627.
> That's a control-limit policy, like the gold trader's: ship when the premium tops a cutoff that falls with the interest rate and rises with volatility."

## The 15-minute talk

| Min | Show | Say (key line) | Board |
|---|---|---|---|
| 0–1 | README top | "Every example tonight is one question: what do I do now when today's choice changes tomorrow?" | the question |
| 1–3 | Theory §0 table | "Four ingredients: state, control, dynamics, payoff." | 4-row table with heifer column |
| 3–5 | `figures/tree.png` | "Wait while the tree beats the bank: $b/T^2=r$, 50 years. Replanting makes you cut sooner: 45.8." | $\max_T pQe^{-rT}\Rightarrow Q'/Q=r$ |
| 5–8 | `figures/heifer.png` | "Now we pick a plan. Price each pound with $\lambda$; feed until a scoop costs what it adds. Early pounds melt, so feed late. A computer with no calculus gets the same red dots." | three Pontryagin conditions; $f^*(t)$ formula |
| 8–9 | Theory §3 | "In steps: Bellman. Randomness adds one $E$." | $V(x)=\max_u\{R+\beta E[V(x')]\}$ |
| 9–12 | `figures/offer.png` | "Offers on 0–1, accept or wait. $V=0.9(1+V^2)/2$, so 0.627. Value iteration from 0 gives the deadline cutoffs: 0, 0.45, 0.54…" | the integral split at $V$; quadratic |
| 12–14 | `figures/gold.png` | "Your gold trader: ship at $50.49. Interest and loss risk lower it; volatility raises it; $K$ barely matters, because you pay it either way." | Bellman with $\max\{s-K,-h+\beta E V\}$ |
| 14–15 | Theory §7 map | "Pontryagin, Bellman, HJB: same idea. When the math runs out we learn it (Person 2) or compute it (Person 3)." | 2×2 map |

## Live demo (optional, 30 seconds each)

```bash
python -m optcontrol.offer    # closed form vs value iteration vs simulation
python -m optcontrol.gold     # cutoff + simulated values of four rules
pytest -q                     # "24 passed": every formula double-checked
```

## Hand-off line to Person 2

> "Everything I did assumed we **know** the rules: the offer distribution, the AR(1). Person 2 drops that assumption and learns the same 0.627 by trial and error."

## The three questions most likely to come

1. **"What is $\lambda$?"** The value of one more pound, i.e. the slope of the value function.
2. **"Why one cutoff?"** Stopping rises with the state; continuing doesn't (or rises more slowly). They cross once.
3. **"How do you know it's right?"** Every formula is matched by an independent computer method, and the 24 tests enforce it.

More in [FAQ.md](FAQ.md).
