# BTC/USD paper-trading bot — Molin take-home

A fixed, long-only trend-pullback strategy starting with **$10,000**, allocating
**10% of available cash** per position. It never submits real orders.

## Setup and one-command execution

Prerequisites: **Python 3.12+**, working internet/TLS, and Git to clone the repo.
No pip dependencies, account or API keys are required. On a clean Mac, install
Python 3.12+ from https://www.python.org/downloads/macos/ and run its bundled
`Install Certificates.command` if HTTPS certificate setup is needed.

Clone the repository URL supplied in the submission email:

```sh
git clone YOUR_REPOSITORY_URL molin-btc-bot
cd molin-btc-bot
python3 bot.py
```

After setup, **`python3 bot.py` is the single run command**. It fetches the latest
window every time, prints all trades and checks, and saves raw candles and
results under `runs/latest/`. Windows: `py -3 bot.py` or `Run_Bot.bat`.
For the attached ZIP, extract it, open its `molin-btc-bot` folder in Terminal,
and run the same command; Git is not required for the ZIP route.

**Verification:** tested with Python 3.12.14 on Linux, including a fresh local
clone, 16 passing tests and reproduction of the saved live run. The first GitHub-hosted macOS run passed the original 13 tests and the saved
replay, but the live step failed on incomplete Coinbase candles. A follow-up fix
adds targeted data retries and three feed tests (16 total locally). Its macOS
rerun is pending. The included workflow checks both offline and live execution.
A green workflow verifies execution, not future profitability. Read its live
output to check whether the trading conditions passed.

## Strategy: when, how and why

Buy a recovered pullback within a locally rising trend. On closed one-minute
candles require price > EMA20 > EMA60, with EMA60 higher than five minutes
previously; the preceding close must have been at or below its EMA20. Execute
at the next minute open. EMAs are seeded and recomputed over the last 120
closed bars, including two hours of pre-window warm-up.

Allocate 10% of cash, including the buy fee, with one position at a time. Place
a **0.4% stop loss** and **0.8% take profit** relative to the executed buy price.
Close after 120 minutes if neither is hit; wait five minutes after an exit.
Liquidate at the final minute open and do not enter there. This guarantees
flatness in the replay, not profitability. The economic hypothesis is that
buying a recovered pullback can capture continuation without chasing a breakout.

Fees are **0.1% on each side**, plus default adverse slippage of **2 bps per
side**. Stops and targets are evaluated against one-minute OHLC. If both are
touched, the stop wins; stop gaps fill at the worse opening price and favorable
target gaps are capped. Intrabar exit times are labelled at candle end because
the exact touch time is unknown. These assumptions do not model order-book
liquidity, latency, partial fills or exchange lot sizes.

## BTC price source and window

The bot calls the free, public **Coinbase Exchange BTC-USD candles REST API**
using Python's standard-library HTTPS client:

`https://api.exchange.coinbase.com/products/BTC-USD/candles`

It requests 60-second candles with explicit UTC start/end times, in pages of
at most 240 minutes, below the API's 300-candle limit. Coinbase rows are parsed
as `[time, low, high, open, close, volume]`; results are sorted and deduplicated.
Transport requests are retried up to three times; incomplete candle sets also
trigger up to three targeted refetch rounds, keeping the original window fixed. Missing minutes, conflicting duplicates
or invalid OHLCV cause an error, not invented prices or an offline fallback.

The window is exactly 24 hours ending at invocation rounded down to the minute
(less than 60 seconds before invocation). The unfinished minute is excluded.
The final executable mark is the last minute open. This is a disclosed
minute-resolution interpretation of the brief. Warm-up affects indicators only.
Every entry uses earlier closed candles; no decision uses its execution bar's
future high/low/close. Buy-and-hold uses the same first/final opens and costs,
but invests the whole account rather than 10%. Drawdown is sampled equity,
not a tick-level maximum. API reference:
https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles

## Development and experiments

The cost hurdle came first: fees alone require about 0.2002% appreciation for a
round trip to break even. Mean reversion was tried first, followed by 24 fixed
trend configurations. EMA20/60 pullback was selected using the development day,
then frozen before a fresh data fetch. It is an **in-sample selection**; the
fresh-fetch window overlaps development and is not independent validation.

| Experiment | Observed outcome |
|---|---|
| Revised mean reversion | 16 trades, -$136.86 in its latest test; preceding two windows also lost. |
| Selected trend pullback | 6 trades, +$1.15 in development; frozen fresh-fetch run: 6 trades, +$0.40. |
| Previous-day support | No profitable variant among 18 tested. |
| Support + trend | Best hybrid: +$3.79, but only 1 trade; no hybrid reached five trades. |
| RSI 15m/30m | Best variant: +$3.79 with 1 trade; the candidate with 5 trades lost $14.43. |

Windows differ slightly between experiments. Full assumptions, UTC windows,
research scripts and all retained comparisons are in [EXPERIMENTS.md](EXPERIMENTS.md).
The submitted strategy also lost $20.91 and $38.53 on two preceding windows.
On its development snapshot, increasing slippage to 5 bps erased the profit.
The observed edge is therefore **not established**. No fixed long-only strategy
can guarantee profit in every future day with positive fees; a constant-price
path is a counterexample. The bot never reselects parameters during execution.

## Recorded own run — 2026-10-29

Invocation timestamp: **2026-10-29T08:41:30.183696Z UTC**. The complete original fresh-fetch output follows. The exact invocation timestamp
and raw-data SHA-256 are stored in
`evidence/trend/live-confirmation/results.json`; input candles are alongside it.
This is a historical result, not a claim about a run performed today by a reviewer.

```text
Fetching Coinbase BTC/USD candles...
TREND pullback | EMA 20/60 | position 10% | SL 0.40% | TP 0.80%
SL/TP intrabar times are reported at candle END; exact touch time is unknown.
BTC/USD | 2026-10-28T08:41:00Z -> 2026-10-29T08:41:00Z
1m candles; final liquidation at final minute OPEN; fee 0.1% per side
Slippage: 2.0 bps per side
01 BUY 2026-10-28T09:11:00Z @ $81428.03 | SELL 2026-10-28T11:11:00Z @ $81240.50 | 0.01226851 BTC | buy fee $0.9990 | sell fee $0.9967 | P/L $-4.2965 | timeout
02 BUY 2026-10-28T17:02:00Z @ $80458.87 | SELL 2026-10-28T18:37:00Z @ $81086.32 | 0.01241096 BTC | buy fee $0.9986 | sell fee $1.0064 | P/L $+5.7823 | target
03 BUY 2026-10-28T18:49:00Z @ $81029.05 | SELL 2026-10-28T20:02:00Z @ $81660.95 | 0.01233076 BTC | buy fee $0.9991 | sell fee $1.0069 | P/L $+5.7857 | target
04 BUY 2026-10-28T22:45:00Z @ $81248.59 | SELL 2026-10-29T00:45:00Z @ $81053.37 | 0.01230455 BTC | buy fee $0.9997 | sell fee $0.9973 | P/L $-4.3992 | timeout
05 BUY 2026-10-29T04:33:00Z @ $79818.37 | SELL 2026-10-29T06:33:00Z @ $79991.17 | 0.01251952 BTC | buy fee $0.9993 | sell fee $1.0015 | P/L $+0.1626 | timeout
06 BUY 2026-10-29T08:30:00Z @ $79953.64 | SELL 2026-10-29T08:40:00Z @ $79903.02 | 0.01249855 BTC | buy fee $0.9993 | sell fee $0.9987 | P/L $-2.6307 | end_of_window
Trades: 6 | Final: $10000.40 | P/L: $+0.40 (+0.004%)
Fees: $12.00 | BTC held: 0.00000000 | Max drawdown (sampled equity): 0.078%
Buy & hold after identical costs: $9779.51 (-2.205%)
PASS: profitable
PASS: at_least_5_trades
PASS: flat
OVERALL: PASS
Evidence saved to evidence/trend/live-confirmation
```

## Reproduce and inspect

```sh
python3 -m unittest discover -s tests -v
python3 bot.py --input evidence/trend/live-confirmation/candles.json --output runs/reproduced
python3 bot.py --days 3
```

`--input` is explicitly labelled an offline snapshot replay. Normal execution
always fetches fresh prices. A completed experiment exits 0 even if it loses;
data/software failures exit 1. Profit, five round trips and flatness each have
separate PASS/FAIL checks. Raw snapshots and JSON trade records are retained.

## AI tools and authorship

**OpenAI Codex in ChatGPT** assisted with implementation, tests, strategy
experiments and documentation. Daniel directed the experiment choices and
position-sizing requirements. Commits honestly identify Codex's contributions;
no historical commits were fabricated or attributed to Daniel. The repository
retains actual incremental development history. No real orders were placed.
