"""Long-only trend hypotheses and causal bracket-order replay."""
from dataclasses import dataclass, asdict
from bot import Candle, FEE, INITIAL, STEP, WARMUP, validate, iso

@dataclass(frozen=True)
class Config:
    family: str = 'breakout'
    fast: int = 10
    slow: int = 40
    breakout: int = 15
    stop_loss: float = .004
    take_profit: float = .008
    allocation: float = .10
    max_hold: int = 120
    cooldown: int = 5


def ema(values, period):
    value = values[0]
    alpha = 2 / (period + 1)
    for x in values[1:]:
        value += alpha * (x - value)
    return value


def entry_signal(history, cfg):
    """All arguments are closed bars strictly before execution time."""
    if len(history) < WARMUP:
        return False
    bars = history[-WARMUP:]
    closes = [c.close for c in bars]
    fast = ema(closes, cfg.fast)
    slow = ema(closes, cfg.slow)
    old_slow = ema(closes[:-5], cfg.slow)
    if not (closes[-1] > fast > slow > old_slow):
        return False
    if cfg.family == 'breakout':
        return closes[-1] > max(c.high for c in bars[-cfg.breakout-1:-1])
    if cfg.family == 'pullback':
        prior_fast = ema(closes[:-1], cfg.fast)
        return closes[-2] <= prior_fast and closes[-1] > fast
    raise ValueError('Unknown trend family')


def bracket_exit(c, buy_price, cfg, slip):
    """Resting SL/TP. If both touched in one minute, stop wins conservatively."""
    stop = buy_price * (1 - cfg.stop_loss)
    target = buy_price * (1 + cfg.take_profit)
    if c.open <= stop:
        return c.open * (1-slip), 'stop_gap', c.time
    if c.open >= target:
        return target * (1-slip), 'target_gap_capped', c.time
    if c.low <= stop:
        return stop * (1-slip), 'stop', c.time+STEP
    if c.high >= target:
        return target * (1-slip), 'target', c.time+STEP
    return None


def replay_trend(candles, start, end, cfg=Config(), slippage_bps=2.0):
    validate(candles, start-WARMUP*STEP, end)
    if not (0 < cfg.allocation <= 1 and 0 < cfg.stop_loss < 1 and cfg.take_profit > 0):
        raise ValueError('Invalid sizing or risk parameters')
    if not (0 <= slippage_bps <= 100):
        raise ValueError('Invalid slippage')
    cash, position, trades, history = INITIAL, None, [], []
    slip = slippage_bps / 10000
    next_entry = start
    peak, max_dd = INITIAL, 0.0

    def close_position(fill):
        nonlocal cash, position, next_entry
        price, reason, stamp = fill
        proceeds = position['size_btc'] * price
        sell_fee = proceeds * FEE
        cash += proceeds-sell_fee
        t = dict(position, sell_time=stamp, sell_price=price, sell_fee=sell_fee,
                 reason=reason, fees=position['buy_fee']+sell_fee,
                 pnl=proceeds-sell_fee-position['cost'])
        trades.append(t)
        # Intrabar fill timestamps are bucket end, not fabricated exact trade times.
        next_entry = stamp + cfg.cooldown*STEP
        position = None

    for c in candles:
        if c.time < start:
            history.append(c)
            continue
        last = c.time == end-STEP
        exited = False
        if position:
            if last:
                close_position((c.open*(1-slip), 'end_of_window', c.time))
                exited = True
            else:
                # Resting protective orders have priority over a scheduled market exit
                # at the same open when an opening gap crosses a bracket.
                fill = bracket_exit(c, position['buy_price'], cfg, slip)
                if fill and fill[2] == c.time:
                    close_position(fill)
                    exited = True
                elif c.time-position['buy_time'] >= cfg.max_hold*STEP:
                    close_position((c.open*(1-slip), 'timeout', c.time))
                    exited = True
                elif fill:
                    close_position(fill)
                    exited = True
        if not position and not exited and not last and c.time >= next_entry and entry_signal(history,cfg):
            budget = cash*cfg.allocation
            price = c.open*(1+slip)
            notional = budget/(1+FEE)
            position = dict(buy_time=c.time, buy_price=price, size_btc=notional/price,
                            buy_fee=notional*FEE, cost=budget)
            cash -= budget
            # Brackets are installed immediately after the paper market entry.
            fill = bracket_exit(c, price, cfg, slip)
            if fill:
                close_position(fill)
        # Close marks have become observable now. This is not used for entry decisions.
        equity = cash + (position['size_btc']*c.close*(1-slip)*(1-FEE) if position else 0)
        peak = max(peak,equity)
        max_dd = max(max_dd,1-equity/peak)
        history.append(c)
    window = [c for c in candles if c.time >= start]
    bh=INITIAL/(window[0].open*(1+slip)*(1+FEE))*window[-1].open*(1-slip)*(1-FEE)
    return dict(start=iso(start),end=iso(end),liquidation_time=iso(end-STEP),config=asdict(cfg),
                final_balance=cash,profit_usd=cash-INITIAL,profit_pct=(cash/INITIAL-1)*100,
                trades=trades,number_of_trades=len(trades),btc_held=0.0 if position is None else position['size_btc'],
                total_fees=sum(t['fees'] for t in trades),max_drawdown_pct=max_dd*100,
                buy_and_hold_balance=bh,buy_and_hold_profit_pct=(bh/INITIAL-1)*100,
                slippage_bps=slippage_bps,
                checks=dict(profitable=cash>INITIAL,at_least_5_trades=len(trades)>=5,flat=position is None))
