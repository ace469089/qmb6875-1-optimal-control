# FAQ: Questions the Professor Is Likely to Ask

Answers are written to be said out loud. Numbers come from `results/results.json`.

**Jump to:** [Big picture](#big-picture) · [Tree](#tree) · [Heifer](#heifer) · [Bellman and the offer problem](#bellman-and-the-offer-problem) · [Gold](#gold) · [Continuous time](#continuous-time) · [Computation and trust](#computation-and-trust)

---

## Big picture

**What is optimal control, in one sentence?**
Choosing a whole plan over time when each choice changes the situation you'll face next, so you can't optimize one period at a time.

**How is it different from ordinary optimization?**
Ordinary optimization picks a number. Control picks a *function* (a plan for every date or every state), and the choices are linked through the dynamics. The heifer's feed today changes her weight tomorrow, which changes what feed is worth tomorrow.

**What makes it *stochastic*?**
Tomorrow's state depends on luck as well as your choice. In the math, the only change is an expectation in front of the future: $V(x)=\max_u\{R+\beta E[V(x')]\}$.

**Why did you start with deterministic control?**
You suggested it in class ("start with deterministic optimal control"). It's also where the key idea, pricing the state, is easiest to see before randomness hides it.

---

## Tree

**Why does the price $p$ not appear in the rotation age?**
$\log PV=\log p+a-b/T-rT$, and $\log p$ is a constant, so it drops out of the derivative. Price changes *how much* the timber is worth, not *when* it's best to cut.

**Why does a higher interest rate shorten the rotation?**
The tree has to beat a higher hurdle. $T^*=\sqrt{b/r}$, so quadrupling $r$ halves the rotation.

**Why is the replanting (Faustmann) rotation shorter?**
Waiting one more year delays not just this harvest but every future harvest on that land. The hurdle becomes $r/(1-e^{-rT})>r$, so you stop sooner: 45.8 vs 50 years.

**How do you know 50 is a maximum and not a minimum?**
The second derivative of $\log PV$ is $-2b/T^3<0$. The test also grid-searches 140,001 ages and finds the peak at 50.000.

---

## Heifer

**What exactly is the costate $\lambda$?**
The value, in today's dollars, of having one more pound of heifer at time $t$. Equivalently it's the slope of the value function, $\lambda=\partial V/\partial W$. It turns a dynamic problem into a sequence of static ones: each day, compare a scoop's cost with $\lambda\times$(pounds it adds).

**Why does the optimal feed rise over time?**
A pound added early has to be maintained (it "melts" at rate $m$) and the money waits longer (rate $r$). In current dollars a pound is worth $p\,e^{-(r+m)(T-t)}$, so it is cheapest to add weight close to the sale. Feedlots do the same: backgrounding, then finishing.

**What's the Hamiltonian, intuitively?**
"Profit flow right now plus the value of the state you're building right now." Maximizing it each instant, with the right state prices, maximizes the total.

**Are Pontryagin's conditions sufficient, or only necessary?**
Here they're sufficient. $H=-cfe^{-rt}+\lambda(a\sqrt f-mW)$ is concave in $(W,f)$ because $\sqrt f$ is concave, the $W$ term is linear, and $\lambda>0$. By Mangasarian's theorem the path is the global maximum.

**What is the transversality condition and why $\lambda(T)=pe^{-rT}$?**
At the sale, a pound is worth exactly what the buyer pays for it, discounted to today. It pins down the level of the shadow price; without it, the costate equation has infinitely many solutions.

**How did you choose the sale date?**
For each $T$ I computed the best feeding plan and its profit, then maximized profit over $T$ with a bounded scalar search. The answer is day 239. The profit curve is single-peaked, and a test confirms that day 239 beats ±5 and ±20 days.

**What if feeding were linear, $\dot W=af$?**
Then $H$ is linear in $f$, so the optimum is bang-bang: feed nothing while $\lambda a<ce^{-rt}$, then the maximum intake. Same principle, cruder plan. I used $\sqrt f$ because diminishing returns are realistic and give a smooth closed form.

**Your parameters were chosen, not estimated. Isn't that a problem?**
For teaching, no. The **structure** of the answer (feed rises at rate $2(r+m)$, sell when marginal profit from waiting hits zero) doesn't depend on them. I calibrated them so the output looks like a real operation: 500 → 942 lb in about 8 months, feed peaking near 26 lb/day. My first calibration said "sell in 36 days," which no one does, so I rejected it (see DECISIONS H3). Your own project did the next step: estimating the growth equation from real heifers weighed monthly.

**How do you know your formula is right?**
A 40-variable optimizer with no calculus, starting from a flat 9 lb/day, finds the same plan to within 0.0004 lb/day and the same profit to the penny.

---

## Bellman and the offer problem

**What is the value function?**
$V(x)$ = the best total discounted payoff you can get starting from state $x$, if you behave optimally from then on.

**What is the principle of optimality?**
Whatever happened before, an optimal plan must be optimal from here on. That's what lets you write the problem as "one decision + $V$ of wherever you land."

**Why is the offer answer a single cutoff?**
Accepting pays $w$, increasing in the offer. Waiting pays $V^*$, which doesn't depend on today's offer because offers are independent. A rising line crosses a flat one once.

**Why the minus root of the quadratic?**
The plus root is about 1.60, but you can never value waiting above the best possible offer (1). So $V^*=0.627$.

**Why does value iteration converge from any start?**
The Bellman map is a contraction: $|T(V_1)-T(V_2)|\le\beta|V_1-V_2|$. Each iteration shrinks every gap by at least 10%, so all starting points are squeezed onto the unique fixed point (Banach fixed-point theorem). A test checks the inequality on 1,000 random pairs.

**What do the value-iteration numbers mean?**
Starting from $V_0=0$, iterate $k$ is the cutoff you'd use with $k+1$ offers left before a deadline: 0, 0.45, 0.541, 0.582, … Value iteration solves ever-longer finite-horizon problems, and the infinite-horizon answer is the limit.

**How does this connect to the midterm?**
It's the reservation wage from the latent-variable discussion: someone works only if the offered wage exceeds their reservation wage. Here we *derive* the reservation value instead of assuming it.

**What if offers came from a different distribution?**
Same equation, $V=\beta E[\max(w,V)]$; only the expectation changes. For a non-uniform $F$ you'd solve it numerically (value iteration or Newton, repo 3).

---

## Gold

**What's the state, and why not the gold price?**
The New York premium, i.e. what NY pays minus what the ounce cost. If the world price moves, purchase and sale prices move together, so the timing decision depends on the premium (your $\varepsilon$). Holding still costs interest on the gold's full value, which is in $h$.

**Where's your $C(r,F_\varepsilon,K)$?**
It's the cutoff $s^*$. The comparative-statics table varies $r$, the shock distribution ($\sigma,\rho$), and $K$ one at a time.

**Why does $K$ barely move the cutoff?**
You pay $K$ whenever you ship, now or later, so it subtracts from both options. The only effect is through discounting: waiting delays paying $K$ by a little. Going from $K=10$ to $40$ moves the cutoff only from 50.35 to 50.63. What *does* matter is any cost paid **per week of waiting** ($h$: interest and loss risk), because that is the price of patience. So in your $C(r,F_\varepsilon,K)$, $r$ and $F_\varepsilon$ do the heavy lifting.

**Why does a bigger $\sigma$ raise the cutoff?**
Option value. With bigger swings, a very high premium is more likely soon, so turning down a decent one costs less in expectation. That's the same logic as financial options being worth more when volatility is higher.

**Why does a *more* persistent premium ($\rho=0.95$) *lower* the cutoff?**
Persistence is about how fast a bad premium recovers. With $\rho=0.5$ the premium snaps back to $40 in about a week, so waiting is cheap. With $\rho=0.95$ the half-life is about 13.5 weeks, so waiting for recovery means paying $2.89 for many weeks. Better to take a merely okay premium now.

**Why can the cutoff be negative?**
If holding is costly enough (20%/yr loss risk, or $r=20\%$), shipping at a loss beats paying ever more to wait. Cutting losses is part of the optimal policy.

**Is a risk-neutral trader realistic?**
It's the standard starting point. A risk-averse trader dislikes the uncertainty of waiting, so they'd ship sooner (a lower cutoff). You'd replace payoffs with utilities, $u(s-K)$; the Bellman equation and the solution method stay the same.

**Why weekly time steps?**
Shipping decisions happen on a scale of days to weeks. Weekly keeps $\beta$ and $h$ readable. A daily model would give a similar cutoff, with more grid steps and iterations.

**How do you know the grid isn't driving the answer?**
The cutoff is $50.49 on 201, 401 and 801 grid points (the change is under 1 cent), and a test enforces stability within $0.50.

**Does the optimal rule actually make more money?**
In 20,000 simulated shipments (same random premiums for every rule): optimal $26.59/oz, ship immediately $14.86, wait-for-average $25.54, too picky $4.04.

**How would the capstone student actually estimate this?**
Fit the AR(1) to his mother's records of premiums (estimate $\mu,\rho,\sigma$ by regressing $s_{t+1}$ on $s_t$), plug in his family's costs, and solve. Or, as he did, use reinforcement learning straight from the data (repo 2).

---

## Continuous time

**What's the HJB equation?**
The continuous-time, stochastic version of Bellman: $rV=\max_u\{R+V'\mu+\tfrac12\sigma^2V''\}$. The $\tfrac12\sigma^2V''$ term comes from Itô's lemma; noise matters through the curvature of $V$, just like Jensen's inequality.

**Why didn't you solve the HJB?**
Few HJB equations have closed forms. You said in class that only a minuscule family does. Discretizing time and the state, as in the gold problem, is the standard numerical way to approximate it.

**How is Pontryagin related to Bellman?**
They are two views of the same problem. The costate equals the slope of the value function, $\lambda=V'(x)$. Pontryagin works with slopes along one optimal path; Bellman works with values in every state.

---

## Computation and trust

**How do you know the code is right?**
24 automated tests, each comparing two independent methods: formula vs grid, formula vs optimizer, formula vs value iteration vs simulation, coarse vs fine grid. Run `pytest`.

**Can I reproduce every number?**
Yes. `python scripts/make_figures.py` regenerates all figures and `results/results.json`, with fixed random seeds.

**Why Python?**
You recommended Python and R as the lingua franca, and it runs free in Colab. The slowest computation here takes about a second.
