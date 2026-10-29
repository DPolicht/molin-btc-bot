# Five-minute Loom — speaker script

Aim for around five minutes at a calm pace. Read this as a guide, not a promise
of future profits. Sections labelled SCREEN are directions, not spoken text.
Do not claim the macOS workflow passed unless you have seen it pass.

## 0:00–0:40 — What I built

SCREEN: repository homepage, then Terminal in the project folder.

“Hi, I'm Daniel. This is my submission for the Molin take-home: a long-only
Bitcoin paper-trading bot that replays the latest twenty-four hours.

It starts with ten thousand dollars, fetches real BTC-USD candles from Coinbase,
and runs with one Python command. There are no third-party dependencies, API
keys or real orders. The strategy is fixed; the bot doesn't search for a winning
configuration when the reviewer runs it.”

SCREEN: run `python3 bot.py`. While data loads, open strategy.json.

## 0:40–1:35 — Strategy and hypothesis

“The idea is to buy a recovered pullback within a rising short-term trend.
I use twenty- and sixty-period exponential moving averages on closed one-minute
candles. Price must be above the fast average, the fast average above the slow
one, and the slow average must be rising. The preceding close must have been
at or below its fast average. That gives a recovery signal rather than simply
buying any rising candle.

Each position uses ten percent of available cash. The stop loss is zero point
four percent below the executed entry, and the take profit is zero point eight
percent above it. There is also a two-hour time limit and a five-minute cooldown.

The hypothesis is that trend alignment filters some weak rebounds, while a
pullback entry avoids chasing a breakout. That's a reason to investigate the
strategy, not evidence that it has a persistent edge.”

## 1:35–2:30 — Data and fair execution

SCREEN: trend.py, entry_signal, then bracket_exit and the execution loop.

“Coinbase provides public one-minute candles without authentication. I fetch
paginated data, validate that minutes are complete, and reject missing or
inconsistent prices. The unfinished minute is excluded.

An entry decision sees only earlier closed candles. The simulated buy happens
at the next minute open. Every buy and sell pays a zero point one percent fee,
plus two basis points of adverse slippage by default.

Protective orders use one-minute highs and lows. If both the stop and target
are touched in one bar, I assume the stop happens first. Stops can also gap
through their level. Intrabar exit timestamps are minute-end labels, because
OHLC data doesn't reveal the exact touch second. The account is liquidated
before the window ends.”

## 2:30–3:30 — What I tried

SCREEN: EXPERIMENTS.md, then trend comparison table.

“I started with mean reversion. It produced trades, but losses and fees outweighed
the recoveries. I then compared twenty-four trend configurations. The submitted
EMA twenty-sixty pullback was selected using the development window and then
frozen before another fresh data fetch.

I also explored previous-day support levels, support combined with trend
confirmation, and RSI on fifteen- and thirty-minute candles. Some alternatives
produced small profits, but only one or two trades. The RSI variant that reached
five trades lost money. I retained negative results rather than hiding them.

These were exploratory comparisons. Selecting a winner using the same day's
results introduces selection bias, even though each individual trade uses only
past prices.”

## 3:30–4:25 — Result and limitations

SCREEN: evidence/trend/live-confirmation-output.txt; distinguish this saved result
from the new live run. If today's run loses, show that too.

“The recorded fresh-fetch run, ending October twenty-ninth at eight forty-one
UTC, completed six round trips, held zero Bitcoin at the end, and finished at
ten thousand dollars and forty cents after costs.

That meets the numerical conditions for that particular window, but the profit
is tiny. The preceding two windows lost money. Increasing slippage erased the
development-day profit, and moving the endpoint by only three minutes reduced
the result from one dollar fifteen to forty cents. The overlapping fresh fetch
isn't an independent validation set.

If this new live run has a different result, that's expected: it uses a different
window. I wouldn't claim that the recorded profit guarantees the reviewer's rerun.”

## 4:25–5:00 — What can reasonably keep working

SCREEN: test output and README verification section.

“What I expect to remain repeatable is the process: fetching fresh prices,
applying the same causal rules, accounting for costs, and reporting the truth.
The code has sixteen passing tests, including sizing, fees, gap handling and
causality checks. Those tests verify software behavior, not a trading edge.

The market hypothesis may work during sustained local uptrends, but persistent
profitability hasn't been established. Before using real capital, I would need
untouched rolling tests across different regimes and more realistic execution
costs. My deliverable is an auditable experiment with clear evidence and limits.”
