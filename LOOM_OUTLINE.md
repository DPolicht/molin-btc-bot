# Five-minute Loom outline

0:00–0:40 — Show the brief and the product. Explain: a causal paper replay,
not a profit guarantee. Show Python version and the single command.

0:40–1:40 — Explain the mean-reversion hypothesis, trend filter, cost hurdle,
position sizing and exits. Point out that parameters were not fitted to the
reviewer's future window.

1:40–2:40 — Share bot.py: show history-only signal input, next-open fill,
buy/sell fees, slippage, and scheduled liquidation. Explain the minute boundary.

2:40–3:40 — Show the actual live output, each assignment PASS/FAIL, buy-and-hold,
and preceding windows. If live retrieval fails, show the error honestly; an
offline or synthetic replay is not proof of live data access.

3:40–4:30 — Explain what the tests establish and what they cannot. Show the
constant-price fee counterexample. Do not claim that seven passing tests prove
an edge or that a historical profit predicts the next day.

4:30–5:00 — State your conclusion and next experiment: longer out-of-sample
validation, regimes and cost sensitivity before any real-money consideration.
Say clearly whether this version meets the profit and five-trade conditions.
