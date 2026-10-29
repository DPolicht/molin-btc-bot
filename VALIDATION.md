# Trend revision: verification and observed result

## Final fresh-fetch run with frozen configuration

- Run timestamp: 2026-10-29T08:41:30.183696Z UTC.
- Window: 2026-10-28T08:41:00Z to 2026-10-29T08:41:00Z.
- Configuration: trend pullback, finite-window EMA20/EMA60, 10% allocation,
  SL 0.4%, TP 0.8%, maximum hold 120 minutes, cooldown 5 minutes.
- Completed round trips: 6.
- Final cash: $10000.4043.
- P/L after fees and default slippage: $+0.4043 (+0.004043%).
- Fees: $12.0025; slippage 2 bps per side.
- Buy-and-hold after identical costs: $9779.51 (-2.205%).
- Profit / five trades / flat: PASS.

Full trade output: evidence/trend/live-confirmation-output.txt.
Machine-readable input/results: evidence/trend/live-confirmation/.

This is a very small positive result, not a robust edge. The preceding exploratory
window ending 08:38 UTC returned +$1.15; moving the endpoint three minutes to
08:41 UTC reduced it to +$0.40. The fresh fetch therefore demonstrates endpoint
sensitivity, not independent confirmation of profitability.

## Selection and negative evidence

All 24 trend candidates, including losers, are retained in
`evidence/trend/comparison.json` and `COMPARISON.md`. Their code was committed
before results were inspected. Exactly one candidate profited on the selected
latest day. The winning configuration was then frozen in strategy.json before
the fresh-fetch run above. Nothing reoptimizes during normal execution.

On the development snapshot (window ending 2026-10-29 08:38 UTC):

| Cost model | Latest P/L | Trades |
|---|---:|---:|
| Fee 0.1% per side, slippage 0 bps | +$3.15 | 6 |
| Fee 0.1% per side, slippage 2 bps | +$1.15 | 6 |
| Fee 0.1% per side, slippage 5 bps | -$1.85 | 6 |

The selected configuration lost $20.91 and $38.53 on the preceding two
non-overlapping days. These diagnostics do not show persistent profitability.
Selection on the latest day creates selection bias even though individual
trade decisions use only past data. Both limitations must be disclosed.

## Technical checks

Python 3.12.14 on Linux; no third-party packages. Thirteen
unit tests pass: legacy accounting and causality plus trend sizing, real-signal
prefix invariance, bracket priority, gap handling and same-bar stop behavior.
Live public-feed retrieval succeeded for three days and for the final one-day
rerun. The final frozen strategy's saved-data replay was also checked from a
fresh local git clone. Windows batch launcher added for convenience; a native
Windows execution environment was not available here. Clean macOS execution
has NOT been verified and remains a submission prerequisite.

OHLC cannot establish exact intrabar touch times or real exchange fillability.
The engine uses stop-first handling if both protective levels are touched, caps
favorable target gaps and applies adverse slippage. Drawdown is sampled, not a
tick-level maximum. No real orders are possible.

No remote repo, Loom or application email was created or sent. The ZIP retains
actual incremental .git history; commits are attributed to Codex. Earlier
mean-reversion evidence remains available under docs/ and original evidence/.
