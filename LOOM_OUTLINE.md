# Five-minute Loom — trend experiment

0:00–0:40: Show the single command and describe the deliverable: BTC/USD paper
replay, $10,000, 10% cash per position, no real orders.

0:40–1:30: Explain rising EMA20/EMA60 alignment and recovery after a pullback.
Show the 0.4% stop, 0.8% target, 120-minute timeout and five-minute cooldown.
Explain that allocation reduces exposure, not the probability of a losing trade.

1:30–2:30: Show trend.py. Entry uses past closed candles, then next open fills.
Explain intrabar protective exits, stop-first ambiguous bars, stop gaps, fees,
slippage and scheduled liquidation. Minute-end SL/TP times are labels, not exact
observed fill times.

2:30–3:40: Show comparison of all 24 candidates. Disclose that the selected day
was used to choose the configuration. Show the small profit, preceding losses,
and slippage sensitivity. Show exact latest fresh-fetch output and acknowledge
whether that rerun passes; do not substitute an older result without saying so.

3:40–4:30: Show tests for cash accounting, causal signals, bracket priority and
no final-minute entry. Explain that software tests do not prove a trading edge.

4:30–5:00: State the conclusion: a functioning, rerunnable trend experiment,
with no robust profitability established. A future window may lose money.
Discuss what you would test next if the time box allowed: independent rolling
windows, regime sensitivity and more realistic execution costs.
