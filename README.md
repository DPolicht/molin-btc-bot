# BTC/USD Trend Bot — Molin take-home experiment

A long-only, real-data paper replay starting with $10,000. Default position size:
**10% of available cash**. No leverage, shorting, API keys or real orders.
The fixed strategy is a trend pullback with **EMA 20/60, 0.4% SL, 0.8% TP**.

## Run

Prerequisites: Python 3.12+ and internet with working TLS certificates. No pip
packages are needed. From a fresh clone:

```sh
git clone <YOUR_REPOSITORY_URL>
cd molin-btc-bot
python3 bot.py
```

Replace the URL with the actual remote when publishing. On Windows, use
`py -3 bot.py` or double-click **Run_Bot.bat** to keep the window open afterward.
On macOS, install Python from python.org and run its bundled certificate installer
if required. A clean Mac has **not** been available for testing here.

The bot always fetches fresh Coinbase Exchange BTC-USD one-minute candles.
It prints every round trip, fees, P/L, buy-and-hold and assignment PASS/FAIL.
It saves raw data and JSON results in `runs/latest/`. Failed data retrieval does
not silently switch to old or synthetic data. A completed experiment exits 0 even
if unprofitable; retrieval/software errors exit 1.

```sh
python3 -m unittest discover -s tests -v
python3 bot.py --days 3
python3 bot.py --slippage-bps 0
python3 bot.py --input evidence/trend/candles.json --days 3 --output runs/reproduced
```

`--input` is explicitly labelled OFFLINE. It is not a fresh run. `--days 3`
evaluates the latest and two preceding non-overlapping days, each starting anew
with $10,000. Previous-day data warms the indicators, not the account.

## Follow-the-trend strategy

Only closed candles enter the signal. The newest close must be above EMA20;
EMA20 must be above EMA60; EMA60 must be above its value five minutes earlier.
The previous close must have been at or below its then-current EMA20. This
represents recovery after a pullback inside a rising trend.

The paper buy executes at the next minute open plus slippage, allocating 10%
of cash **including** the buy fee. Only one position may be held, so at least
90% of cash stays outside that new position. SL is 0.4% below the executed buy
price; TP is 0.8% above it. Orders become active on the entry bar. There is a
five-minute cooldown after exits; positions also close after 120 minutes.
There is no early exit merely because the EMA ordering changes.

The hypothesis is that aligned, rising averages identify local upward momentum,
and buying a recovered pullback avoids chasing an already extended breakout.
The tests do **not** establish a repeatable edge. The default configuration was
selected using the reported latest day and must be described as in-sample.

## Fees, execution and clocks

- Fee: 0.1% on every buy and sell; adverse slippage: default 2 basis points per side.
- Resting SL/TP can trigger inside a candle. If both are touched, the stop wins.
  Stop gaps fill at the worse opening price; favorable TP gaps are capped at the
  target. Slippage applies to exits as well. These are conservative assumptions,
  not proof of executable exchange fills.
- Intrabar exits are timestamped at the minute's **end**, because OHLC does not
  reveal the actual touch second. Reasons identify those exits. Open/gap and
  timeout exits have opening timestamps. No invented intrabar event order.
- No entry decision sees its execution candle's high, low or close. Protective
  orders are evaluated against that bar after the decision is fixed. No reentry
  is allowed within a candle after an exit.
- The window is 24 hours ending at invocation rounded down to the minute, less
  than 60 seconds before invocation. The unfinished minute is excluded. Final
  liquidation occurs at the last minute open; no entry is allowed at that open.
  This is a minute-resolution interpretation, not tick-exact coverage to now.
- Two hours of earlier candles warm indicators. EMAs are recomputed causally over
  the most recent 120 closed bars; they are finite-window seeded EMAs. No future
  prices or window-wide trend classification enter a trading decision.
- Buy-and-hold invests the whole $10,000 at the first open and liquidates at the
  final open with the same costs. Its exposure differs from the 10% strategy.
- Drawdown is sampled from minute-close liquidation equity and final fills;
  it does not measure every intrabar equity low. Depth, latency, exchange lot
  sizes and partial fills are not modelled.

A stop limits the intended price risk, not a guaranteed realized loss. With
$1,000 allocated, 0.4% price risk is roughly $4 before fees, gaps and slippage.
Smaller positions scale both profits and losses; they do not create an edge.

## Research log and result honesty

The original mean-reversion attempt lost money; code and evidence remain in
`legacy_mean_reversion.py`, `docs/` and the original evidence directories.
At Daniel's request, the next experiment compared 24 fixed combinations:

- Entry families: breakout or trend pullback.
- EMA fast/slow: 5/20, 10/40 or 20/60. Breakout lookbacks: 5, 15 or 30 minutes.
- SL/TP pairs: 0.3/0.6%, 0.4/0.8%, 0.5/1.0% or 0.6/1.2%.
- All use 10% allocation, 120-minute maximum hold and five-minute cooldown.

The comparison code was committed before its results were inspected. Results
for **all 24** are in `evidence/trend/COMPARISON.md` and `comparison.json`.
`research_trend.py` reproduces that explicit saved-data experiment. It is never
called automatically by the live bot. `strategy.json` is frozen; reruns do not
reselect the winner.

The best configuration on the development day made 6 trades and **+$1.15**
after fees and 2 bps slippage. The same configuration lost **$20.91 and $38.53**
on the preceding two windows. With 5 bps slippage it lost **$1.85** on the selected
day. Only one of the 24 candidates was profitable on that day. This is a tiny,
cost-sensitive selected result, not robust performance or out-of-sample evidence.
See `VALIDATION.md` for the subsequent fresh-fetch rerun and exact UTC windows.
That rerun overlaps development heavily and is not independent validation either.

No claim is made that a future 24h rerun will profit or make five trades. Positive
fees and a constant-price path provide a simple counterexample to a universal
profit guarantee. Selecting a historical winner does not resolve that limitation.

## Reproducibility, AI and submission

Raw snapshots, their SHA-256 digests, trades and development history are included.
Public feed: `https://api.exchange.coinbase.com/products/BTC-USD/candles`.
Documentation: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
Candles are paginated, sorted and validated; gaps and invalid or conflicting
rows cause failure rather than fabricated prices.

OpenAI Codex in ChatGPT assisted with implementation, strategy experiments,
tests and documentation. Commits honestly name Codex as author. Daniel must
review and understand the implementation before presenting it. The work was
performed during this conversation; no claim is made about Daniel's own
hands-on time. The earlier README and results are retained rather than rewritten
as if the final strategy had been chosen from the beginning.

Still required for submission: publish a remote repository retaining `.git`
history, verify the setup on a clean Mac, and record a five-minute Loom using
`LOOM_OUTLINE.md`. No remote repository, video or application email was created
or sent. This is a paper experiment, not a live-trading recommendation.
