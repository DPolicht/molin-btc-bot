#!/usr/bin/env python3
"""Deterministic, long-only BTC/USD paper replay. Python standard library only."""
import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

FEE = 0.001
INITIAL = 10000.0
STEP = 60
WARMUP = 120


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace('+00:00', 'Z')


@dataclass(frozen=True)
class Candle:
    time: int
    low: float
    high: float
    open: float
    close: float
    volume: float


def validate(candles, start, end):
    expected = list(range(start, end, STEP))
    if [c.time for c in candles] != expected:
        raise ValueError('Missing, duplicate or out-of-order candles; refusing a partial replay.')
    for c in candles:
        values = [c.low, c.high, c.open, c.close, c.volume]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Non-finite market data')
        if not (0 < c.low <= min(c.open, c.close) <= max(c.open, c.close) <= c.high and c.volume >= 0):
            raise ValueError('Invalid OHLCV data')


def fetch(start, end):
    """Fetch real candles; retry incomplete responses without moving the window."""
    rows = {}

    def request_page(a, b):
        url = 'https://api.exchange.coinbase.com/products/BTC-USD/candles?' + urlencode(
            {'granularity': STEP, 'start': iso(a), 'end': iso(b)})
        for attempt in range(3):
            try:
                req = Request(url, headers={'User-Agent': 'MolinPaperBot/1.1',
                                           'Accept': 'application/json',
                                           'Cache-Control': 'no-cache'})
                with urlopen(req, timeout=20) as response:
                    data = json.load(response)
                if not isinstance(data, list):
                    raise ValueError('Unexpected Coinbase response')
                for row in data:
                    c = Candle(int(row[0]), *map(float, row[1:6]))
                    if start <= c.time < end:
                        if c.time in rows and rows[c.time] != c:
                            raise ValueError('Conflicting duplicate candles')
                        rows[c.time] = c
                return
            except (OSError, ValueError) as exc:
                if attempt == 2:
                    raise RuntimeError(f'Coinbase fetch failed: {exc}') from exc
                time.sleep(attempt + 1)

    for a in range(start, end, 240 * STEP):
        request_page(a, min(a + 240 * STEP, end))
        time.sleep(0.15)

    expected = set(range(start, end, STEP))
    for attempt in range(3):
        missing = sorted(expected - rows.keys())
        if not missing:
            break
        print(f'Coinbase returned {len(missing)} missing minute(s); '
              f'retrying real data ({attempt+1}/3), first: {iso(missing[0])}',
              file=sys.stderr, flush=True)
        time.sleep(2 ** (attempt + 1))
        # Requery the affected pages, overlapping neighbors to avoid edge effects.
        pages = sorted({(t - start) // (240 * STEP) for t in missing})
        for page in pages:
            a = max(start, start + page * 240 * STEP - STEP)
            b = min(end, start + (page + 1) * 240 * STEP + STEP)
            request_page(a, b)
            time.sleep(0.15)
    missing = sorted(expected - rows.keys())
    if missing:
        examples = ', '.join(iso(t) for t in missing[:5])
        raise RuntimeError(f'Coinbase still has {len(missing)} missing minute(s) '
                           f'after retries: {examples}. Window {iso(start)} to '
                           f'{iso(end)}. Refusing to invent or forward-fill prices.')
    candles = sorted(rows.values(), key=lambda c: c.time)
    validate(candles, start, end)
    return candles


def signal(history, entry=None):
    """Only CLOSED candles are passed here; fills occur at next minute open."""
    closes = [c.close for c in history[-WARMUP:]]
    if entry is not None:
        change = closes[-1] / entry['buy_price'] - 1
        if change <= -0.006:
            return 'stop'
        if change >= 0.008:
            return 'target'
        if history[-1].time + STEP - entry['buy_time'] >= 45 * STEP:
            return 'timeout'
        if closes[-1] >= statistics.mean(closes[-30:]) and change > 0.0025:
            return 'mean_reversion'
        return None
    if len(closes) < WARMUP:
        return None
    mean = statistics.mean(closes[-30:])
    std = statistics.pstdev(closes[-30:])
    # Avoid strong downtrends; require a meaningful discount and a recovery tick.
    trend_ok = statistics.mean(closes[-60:]) >= statistics.mean(closes[-120:]) * 0.997
    if (std > 0 and trend_ok and closes[-2] < mean - 1.0 * std
            and closes[-1] > closes[-2] and mean / closes[-1] - 1 > 0.001):
        return 'pullback'
    return None


def replay(candles, start, end, slippage_bps=2.0, decision=signal):
    validate(candles, start - WARMUP * STEP, end)
    cash, position, trades = INITIAL, None, []
    slip = slippage_bps / 10000
    history = []
    equity_peak, max_drawdown = INITIAL, 0.0
    for c in candles:
        if c.time >= start:
            reason = decision(history, position)
            # Final open is a scheduled liquidation known before the replay starts.
            last = c.time == end - STEP
            if position and (reason or last):
                price = c.open * (1 - slip)
                proceeds = position['size_btc'] * price
                sell_fee = proceeds * FEE
                cash += proceeds - sell_fee
                trade = dict(position, sell_time=c.time, sell_price=price,
                             sell_fee=sell_fee, reason='end_of_window' if last else reason)
                trade['fees'] = trade['buy_fee'] + sell_fee
                trade['pnl'] = proceeds - sell_fee - trade['cost']
                trades.append(trade)
                position = None
            elif not position and reason and not last:
                budget = cash * 0.25
                price = c.open * (1 + slip)
                notional = budget / (1 + FEE)
                position = dict(buy_time=c.time, buy_price=price, size_btc=notional / price,
                                buy_fee=notional * FEE, cost=budget)
                cash -= budget
            equity = cash + (position['size_btc'] * c.open * (1 - slip) * (1 - FEE) if position else 0)
            equity_peak = max(equity_peak, equity)
            max_drawdown = max(max_drawdown, 1 - equity / equity_peak)
        history.append(c)
    window = [c for c in candles if c.time >= start]
    # Same executable endpoints, fees and slippage as strategy.
    bh = INITIAL / (window[0].open * (1 + slip) * (1 + FEE))
    bh *= window[-1].open * (1 - slip) * (1 - FEE)
    return dict(start=iso(start), end=iso(end), liquidation_time=iso(end - STEP),
                final_balance=cash, profit_usd=cash-INITIAL, profit_pct=(cash/INITIAL-1)*100,
                trades=trades, number_of_trades=len(trades), btc_held=0.0,
                total_fees=sum(t['fees'] for t in trades), max_drawdown_pct=max_drawdown*100,
                buy_and_hold_balance=bh, buy_and_hold_profit_pct=(bh/INITIAL-1)*100,
                slippage_bps=slippage_bps,
                checks=dict(profitable=cash > INITIAL, at_least_5_trades=len(trades) >= 5,
                            flat=position is None))


def report(result):
    print(f"BTC/USD | {result['start']} -> {result['end']}")
    print('1m candles; final liquidation at final minute OPEN; fee 0.1% per side')
    print(f"Slippage: {result['slippage_bps']} bps per side")
    for i, t in enumerate(result['trades'], 1):
        print(f"{i:02} BUY {iso(t['buy_time'])} @ ${t['buy_price']:.2f} | "
              f"SELL {iso(t['sell_time'])} @ ${t['sell_price']:.2f} | "
              f"{t['size_btc']:.8f} BTC | buy fee ${t['buy_fee']:.4f} | "
              f"sell fee ${t['sell_fee']:.4f} | P/L ${t['pnl']:+.4f} | {t['reason']}")
    print(f"Trades: {result['number_of_trades']} | Final: ${result['final_balance']:.2f} | "
          f"P/L: ${result['profit_usd']:+.2f} ({result['profit_pct']:+.3f}%)")
    print(f"Fees: ${result['total_fees']:.2f} | BTC held: {result['btc_held']:.8f} | "
          f"Max drawdown (sampled equity): {result['max_drawdown_pct']:.3f}%")
    print(f"Buy & hold after identical costs: ${result['buy_and_hold_balance']:.2f} "
          f"({result['buy_and_hold_profit_pct']:+.3f}%)")
    for k, v in result['checks'].items():
        print(f"{'PASS' if v else 'FAIL'}: {k}")
    print('OVERALL: ' + ('PASS' if all(result['checks'].values()) else 'FAIL'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Explicit offline replay of a saved snapshot; never the default')
    parser.add_argument('--output', type=Path, default=Path('runs/latest'))
    parser.add_argument('--days', type=int, default=1, choices=range(1, 8), help='Also evaluate preceding non-overlapping 24h windows')
    parser.add_argument('--slippage-bps', type=float, default=2.0)
    args = parser.parse_args()
    if not math.isfinite(args.slippage_bps) or not 0 <= args.slippage_bps <= 100:
        parser.error('slippage must be between 0 and 100 bps')
    now = time.time()
    if args.input:
        snapshot = json.loads(args.input.read_text())
        end = snapshot['end_epoch']
        candles = [Candle(**c) for c in snapshot['candles']]
        print('OFFLINE SNAPSHOT REPLAY (not a fresh market-data run)')
    else:
        end = int(now // STEP) * STEP
        candles = fetch(end - args.days * 86400 - WARMUP * STEP, end)
        snapshot = dict(source='Coinbase Exchange BTC-USD', fetched_at=iso(now),
                        end_epoch=end, candles=[asdict(c) for c in candles])
    args.output.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(snapshot, indent=2) + '\n'
    (args.output / 'candles.json').write_text(raw)
    results = []
    for day in range(args.days):
        stop = end - day * 86400
        start = stop - 86400
        selected = [c for c in candles if start-WARMUP*STEP <= c.time < stop]
        result = replay(selected, start, stop, args.slippage_bps)
        result.update(run_at=iso(now), snapshot_sha256=hashlib.sha256(raw.encode()).hexdigest())
        results.append(result)
        report(result)
    (args.output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f"Evidence saved to {args.output}")
    return 0  # A losing strategy is a valid completed experiment, not a software crash.


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
