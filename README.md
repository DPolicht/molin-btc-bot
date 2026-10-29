# BTC/USD paper-trading experiment — Molin take-home

A runnable, long-only replay with explicit execution costs and auditable evidence.
**This is an experiment, not a claim of profitable trading.** The program reports
FAIL when the profit or five-round-trip condition is not met. It never changes
parameters to fit the just-downloaded evaluation window.

## Run from a fresh clone

Prerequisites: **Python 3.12+**, an internet connection and working system TLS
certificates. No packages, account, API keys, Docker or credentials are required.
On macOS install Python 3.12 from python.org; if its installer requests certificate
setup, run its bundled `Install Certificates.command`. Git is needed to clone.

```sh
git clone <YOUR_REPOSITORY_URL>
cd molin-btc-bot
python3 bot.py
```

The last line is the single execution command. It fetches fresh data every time;
there is no automatic fallback to saved prices. A normal experiment exits 0,
even if its strategy fails; data or software errors exit 1. PASS/FAIL is printed
and stored in `runs/latest/results.json`.

Other commands:

```sh
python3 -m unittest discover -s tests -v
python3 bot.py --days 3
python3 bot.py --slippage-bps 0
python3 bot.py --input evidence/live/candles.json --days 3 --output runs/reproduced
```

`--days 3` evaluates the latest and preceding two non-overlapping 24-hour
windows using the exact same strategy, with a separate $10,000 account each day.
`--input` is explicitly labelled an OFFLINE replay; it is not a latest-window run.
The report, candles and SHA-256 snapshot digest make results reproducible.

## Strategy

Hypothesis: some temporary sell-offs recover toward a recent mean, provided
the market is not in a pronounced downtrend. This is a hypothesis to test, not
an established edge. At a minute close, require the preceding close below the
30-minute mean minus 1.0 standard deviations, a rising latest close, and at least
0.10% distance back to the mean. The 60-minute mean must be at least 99.7% of
the 120-minute mean. These statistics use closed candles only.

Buy at the **next minute open**, allocating 25% of current cash including the
buy fee; hold at most one position. Exit at the next open after a close indicates
0.6% loss, 0.8% gain, 45 minutes held, or recovery to the 30-minute mean with
more than 0.25% price appreciation. The loss threshold is a close-based exit
signal, **not a guaranteed fill or intrabar stop**. Price gaps can exceed it.
A predefined liquidation at the last minute open ensures zero BTC before the
window ends. No entry is permitted at that open.

Every side costs 0.1%. Default adverse slippage is an additional 2 basis points
per side; `--slippage-bps 0` isolates the assignment's fee-only model. The
buy-and-hold comparison uses all $10,000 and identical costs, first minute open
to final minute open. Position-size differences matter when comparing returns.

## Clock and data assumptions

Source: Coinbase Exchange public `BTC-USD` one-minute candles:
`https://api.exchange.coinbase.com/products/BTC-USD/candles`.
Reference: https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
Coinbase candle order is `[time, low, high, open, close, volume]`.
Requests are paginated below the 300-candle limit, retried up to three times,
sorted and deduplicated. Missing minutes, invalid OHLCV and conflicting duplicate
values are rejected rather than filled with invented prices.

The evaluation is exactly 24 hours ending at the latest whole-minute boundary
at invocation (less than 60 seconds before invocation), excluding the unfinished
minute. This is an explicit candle-resolution interpretation of “last 24 hours”,
not tick-exact coverage up to the current second. The last minute's opening
price is the final executable mark. Two hours of earlier candles warm indicators
up; no position or P/L is carried from warm-up into evaluation.

The engine reveals only earlier closed candles to the decision function and
executes at the current open. It does not select advantageous intrabar paths,
use future highs/lows for fills, or optimize using the evaluation period. Minute
open fills with constant slippage remain a paper approximation; order-book depth,
latency, exchange lot sizes and partial fills are not modelled.

## How this was developed / what did not work

The design began with the cost hurdle: a fee-only round trip needs about 0.2002%
price appreciation to break even. The 0.10% entry discount is an exploratory heuristic,
not a fitted or statistically justified optimum. A simple mean-reversion idea was
chosen for auditability within the time box. The initial entry rules (1.3 standard deviations, 0.30% discount, 99.9% trend
filter) produced 0, 0 and 2 trades on the three downloaded days. A single
exploratory revision relaxed them to 1.0, 0.10% and 99.7%. Both outputs are
retained. These days are development data, not an untouched out-of-sample test.
No automatic strategy selection or parameter search runs at evaluation time.
The smaller discount does not itself cover costs; the strategy depends on
a larger subsequent recovery, which may never occur.

The included constant-price experiment proves that forced trading does not
solve the task: one round trip loses exactly its fees, and repeated round trips
lose more. Synthetic tests verify accounting and execution, **not profitability**.
No empirical claim about an unimplemented alternative strategy is made.
See `evidence/live-output.txt` and `VALIDATION.md` for what actually ran and the
observed result. Failed windows remain part of the evidence.

## Why a guaranteed rerun profit cannot be promised

With a constant BTC price and positive fees, every nonzero long round trip loses
money. Five required round trips therefore cannot produce a profit in that
admissible price path. A strictly falling price path is another counterexample.
That disproves a guarantee for every possible future window; it does not prove
that the particular future window chosen by the reviewer will lose.

The bot does not manufacture five tiny transactions solely to pass a counter.
It can make fewer than five trades, lose money, or both. Those are explicitly
reported assignment failures. Evidence across a few days is also far too little
to establish a persistent market edge. Profit on one rerun would not establish it.

## AI and authorship

Built with OpenAI Codex in ChatGPT: implementation, tests, documentation and
review assistance. Daniel should review and understand the code before presenting
it. Local commits are attributed to Codex, not falsely to Daniel. No real exchange
orders can be sent by this code. See `LOOM_OUTLINE.md` for a five-minute recording
outline; it is an outline, not a recorded video.

## Submission checklist

- Publish this repository, retaining the supplied `.git` history, and replace the
  clone placeholder with its real URL. Do not send the placeholder to reviewers.
- Run the live command on a clean Mac and record Python/macOS versions. Linux
  verification here does not satisfy the request to test on a clean Mac.
- Review actual results and explicitly acknowledge failed conditions.
- Record the Loom yourself, explaining the code and limitations in your own words.
- Send repository URL, setup command, evidence and Loom URL. No email is sent by
  this project.
