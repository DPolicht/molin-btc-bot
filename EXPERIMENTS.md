# Experiment log

These are exploratory historical tests, not independent validation. Different
experiments used slightly different rolling endpoints, listed below, so their
P/L values are not a controlled comparison on one identical window. All use
0.1% fees per side and default 2 bps adverse slippage per side. No experiment
changed the chosen strategy automatically at runtime.

| Experiment | Latest tested outcome | Conclusion |
|---|---|---|
| Revised mean reversion, 25% sizing | 16 trades, -$136.86; preceding days -$47.61 and -$90.99 | More entries did not overcome costs and falling prices. |
| Trend candidates, 10% sizing | 24 configurations. Selected EMA20/60 pullback: 6 trades, +$1.15 in development; frozen fresh-fetch rerun: 6 trades, +$0.40 | The submitted candidate met all three numerical conditions in the recorded rerun, but profit was tiny. |
| Previous-day support only, 10% sizing | 18 configurations. No profitable configuration; best active one: 2 trades, -$3.65 | Buying near support without trend confirmation was insufficient in this sample. |
| Support plus trend, 10% sizing | 54 hybrid configurations plus 18 controls. Three hybrids positive. Best: S2, wait up to 30 minutes for EMA20/60 alignment, SL/TP 0.3%/0.6%: 1 trade, +$3.79 | Positive examples had only 1–2 trades; none met the five-trade condition. |
| RSI(14), 15m and 30m, 10% sizing | 36 configurations; six positive. Best: 30m recovery above RSI30, SL/TP 0.3%/0.6%: 1 trade, +$3.79. The 15m oversold RSI30 candidate with five trades lost $14.43 | Recovery was more promising than low RSI alone in this sample, but no candidate combined profit with five trades. |

## UTC windows and evidence

- Mean reversion: 2026-10-28 08:19 to 2026-10-29 08:19;
  `evidence/revised-output.txt` and `evidence/revised/`.
- Trend development: 2026-10-28 08:38 to 2026-10-29 08:38;
  `evidence/trend/COMPARISON.md` and `comparison.json`.
- Chosen bot fresh-fetch rerun: 2026-10-28 08:41 to 2026-10-29 08:41;
  `evidence/trend/live-confirmation-output.txt` and `live-confirmation/`.
- Support: 2026-10-28 08:48 to 2026-10-29 08:48;
  `evidence/research-support/results.json`.
- Support plus trend: 2026-10-28 08:55 to 2026-10-29 08:55;
  `evidence/research-support/hybrid-results.json`.
- RSI: 2026-10-28 09:05 to 2026-10-29 09:05;
  `evidence/research-rsi/results.json`.

The preceding day produced no entries in the support and RSI experiments; it
therefore did not provide evidence of a repeated edge. Small positive historical
examples from different methods are not independent proof of profitability.

## Reproduce research

These commands use the explicitly saved datasets, print comparisons and overwrite
the corresponding generated research result files. They do not fetch the latest
prices or change strategy.json:

```sh
python3 research_trend.py
python3 research/support.py
python3 research/support_trend.py
python3 research/rsi.py
```

Support levels use the preceding completed UTC day's high, low and close:
P=(H+L+C)/3, S1=2P-H, S2=P-(H-L), plus the preceding daily low. RSI uses Wilder's
14-period smoothing on completed 15m/30m bars. Intrabar exits use one-minute
candles with the same conservative bracket-fill rules as the submitted bot.

Research on the final three alternatives was conducted after the executable
trend candidate had been selected. Its configuration and trading code remain
unchanged; only research and submission documentation were added later.
