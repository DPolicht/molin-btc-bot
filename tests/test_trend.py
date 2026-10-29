import unittest
from unittest.mock import patch
from bot import Candle, INITIAL, FEE
from trend import Config, bracket_exit, replay_trend, entry_signal
from test_bot import market, START, END

class TrendTests(unittest.TestCase):
    def test_ambiguous_bar_takes_stop_first(self):
        fill=bracket_exit(Candle(60,98,103,100,101,1),100,Config(stop_loss=.01,take_profit=.02),0)
        self.assertEqual(fill,(99,'stop',120))

    def test_stop_gap_uses_worse_open(self):
        fill=bracket_exit(Candle(60,95,98,97,96,1),100,Config(stop_loss=.01),.0002)
        self.assertAlmostEqual(fill[0],97*.9998)
        self.assertEqual(fill[1],'stop_gap')

    def test_target_gap_is_capped(self):
        fill=bracket_exit(Candle(60,103,105,104,104,1),100,Config(take_profit=.02),0)
        self.assertEqual(fill,(102,'target_gap_capped',60))

    @patch('trend.entry_signal',return_value=True)
    def test_ten_percent_and_cash_accounting(self,_):
        r=replay_trend(market(),START,END,Config(),0)
        self.assertEqual(r['trades'][0]['cost'],1000)
        self.assertAlmostEqual(r['profit_usd'],sum(t['pnl'] for t in r['trades']))
        self.assertEqual(r['btc_held'],0)
        for t in r['trades']:
            self.assertGreaterEqual(t['buy_time'],START)
            self.assertLess(t['sell_time'],END)
        self.assertLess(r['final_balance'],INITIAL)

    @patch('trend.entry_signal',return_value=True)
    def test_entry_bar_stop_and_no_reentry_same_bar(self,_):
        data=market()
        data[START//60]=Candle(START,98,100,100,99,1)
        r=replay_trend(data,START,END,Config(stop_loss=.01),0)
        self.assertEqual(r['trades'][0]['reason'],'stop')
        self.assertEqual(r['trades'][0]['sell_time'],START+60)
        self.assertGreater(r['trades'][1]['buy_time'],START+60)

    def test_real_signal_and_prefix_are_causal(self):
        data=market(lambda i:100+i*.01)
        self.assertTrue(entry_signal(data[:120],Config(breakout=5)))
        a=replay_trend(data,START,END,Config(),0)
        altered=data[:800]+[Candle(c.time,90,90,90,90,1) for c in data[800:]]
        b=replay_trend(altered,START,END,Config(),0)
        self.assertEqual([t for t in a['trades'] if t['sell_time']<800*60],
                         [t for t in b['trades'] if t['sell_time']<800*60])

if __name__=='__main__': unittest.main()
