import math
import unittest
from bot import Candle, FEE, INITIAL, STEP, WARMUP, replay, signal, validate

START = WARMUP * STEP
END = START + 86400

def market(price=lambda i: 100.0):
    return [Candle(i*STEP, price(i), price(i), price(i), price(i), 1)
            for i in range(END//STEP)]

class ReplayTests(unittest.TestCase):
    def test_flat_round_trip_loses_exact_fees(self):
        def once(h, p):
            return 'enter' if h[-1].time == START-STEP else ('exit' if p else None)
        r = replay(market(), START, END, 0, once)
        expected = INITIAL * .75 + INITIAL * .25 / (1+FEE) * (1-FEE)
        self.assertAlmostEqual(r['final_balance'], expected)
        self.assertAlmostEqual(r['profit_usd'], sum(t['pnl'] for t in r['trades']))
        self.assertEqual(r['number_of_trades'], 1)
        self.assertFalse(r['checks']['profitable'])

    def test_next_open_execution_and_scheduled_liquidation(self):
        data = market(lambda i: 100 + i * .01)
        def enter(h, p):
            self.assertLess(h[-1].time, START if not p else END)
            return 'enter' if not p else None
        r = replay(data, START, END, 0, enter)
        t = r['trades'][0]
        self.assertEqual(t['buy_time'], START)
        self.assertEqual(t['buy_price'], data[WARMUP].open)
        self.assertEqual(t['sell_time'], END-STEP)
        self.assertEqual(t['reason'], 'end_of_window')
        self.assertEqual(r['btc_held'], 0)

    def test_future_changes_do_not_change_prefix_orders(self):
        def periodic(h, p):
            return 'tick' if len(h) % 10 == 0 else None
        a = market()
        b = market(lambda i: 100 if i < 800 else 200)
        ra = replay(a, START, END, 0, periodic)
        rb = replay(b, START, END, 0, periodic)
        self.assertEqual([t for t in ra['trades'] if t['sell_time'] < 800*STEP],
                         [t for t in rb['trades'] if t['sell_time'] < 800*STEP])

    def test_signal_requires_past_warmup(self):
        self.assertIsNone(signal(market()[:119]))
        self.assertIsNone(signal(market()[:120]))

    def test_gap_duplicate_nan_rejected(self):
        data = market()
        for bad in [data[:-1], data+[data[-1]], [Candle(0, 100,100,100,math.nan,1)]+data[1:]]:
            with self.assertRaises(ValueError):
                validate(bad, 0, END)

    def test_no_final_minute_entry(self):
        def last_only(h, p):
            return 'entry' if h[-1].time == END-2*STEP else None
        r = replay(market(), START, END, 0, last_only)
        self.assertEqual(r['number_of_trades'], 0)

    def test_slippage_reduces_result_and_benchmark(self):
        def periodic(h, p):
            return 'tick' if len(h) % 10 == 0 else None
        a = replay(market(), START, END, 0, periodic)
        b = replay(market(), START, END, 2, periodic)
        self.assertLess(b['final_balance'], a['final_balance'])
        self.assertLess(b['buy_and_hold_balance'], a['buy_and_hold_balance'])
        self.assertGreater(b['final_balance'], 0)

if __name__ == '__main__':
    unittest.main()
