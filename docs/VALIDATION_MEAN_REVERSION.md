# Validation and observed outcome

## Final live run

- Invocation: 2026-10-29T08:22:27.495334Z (UTC).
- Evaluated window: 2026-10-28T08:22:00Z to 2026-10-29T08:22:00Z.
- Real public BTC/USD candles fetched by the bot, without keys.
- Completed round trips: 16.
- Final cash: $9863.14; P/L: $-136.86 (-1.369%).
- Fees: $79.43; slippage: 2 bps each side.
- Buy-and-hold: $9841.23 (-1.588%).
- Flat: PASS. Five trades: PASS. Profitable: FAIL. Overall assignment: FAIL.

Full output: evidence/final-live-output.txt. Machine-readable trades and input:
evidence/final-live/. Do not describe this implementation as a profitable bot.

## What was checked

Python 3.12.14, Linux. Seven unit tests pass, covering fees,
next-open execution, unchanged prefix trades when future prices change, warm-up,
invalid/gapped data rejection, no final-minute entries and slippage sensitivity.
A fresh local git clone ran the saved three-day replay and passed the same seven
tests from its project directory. No pip dependencies were installed.
Live retrieval completed for the three-day baseline and again for this final run.
A clean Mac was not available and has NOT been tested. macOS verification remains
a submission prerequisite, not a completed claim.

## Experiments retained

- Baseline live: 0 / 0 / 2 trades, latest first; no profitable day.
- Revised entries, same saved three days: 16 / 12 / 18 trades; all lose.
- Fee-only sensitivity, same snapshot: 15 / 12 / 18 trades; all lose.
- Final revised live run: reported above; parameters were frozen before this fetch,
  but its window heavily overlaps development data. It is not independent validation.

The archived git history records actual implementation stages. No historic commits
were invented. No remote repository was created, no Loom recorded and no application
email sent. The ZIP includes .git so history can be retained when publishing.
The work was performed in this session; no claim is made about Daniel's own
hands-on time or work on a Mac.
