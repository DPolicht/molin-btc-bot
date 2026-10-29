"""Explicit in-sample comparison; never called automatically by bot.py."""
import json
from dataclasses import asdict
from pathlib import Path
from bot import Candle, WARMUP, STEP
from trend import Config, replay_trend

p=Path('evidence/trend')
snapshot=json.loads((p/'candles.json').read_text())
candles=[Candle(**x) for x in snapshot['candles']]
end=snapshot['end_epoch']
rows=[]
# 24 prespecified configurations, not an unbounded search.
for family in ['breakout','pullback']:
 for fast,slow,lookback in [(5,20,5),(10,40,15),(20,60,30)]:
  for stop,target in [(.003,.006),(.004,.008),(.005,.01),(.006,.012)]:
   cfg=Config(family,fast,slow,lookback,stop,target)
   daily=[]
   for day in range(3):
    stop_time=end-day*86400; start=stop_time-86400
    data=[c for c in candles if start-WARMUP*STEP<=c.time<stop_time]
    daily.append(replay_trend(data,start,stop_time,cfg))
   rows.append(dict(config=asdict(cfg),days=daily))
rows.sort(key=lambda x:(all(x['days'][0]['checks'].values()),x['days'][0]['profit_usd']),reverse=True)
(p/'comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Exploratory trend comparison','',
 'Selection uses the latest day: these are IN-SAMPLE results, not independent validation.',
 'Previous days are diagnostics only. All 24 configurations are retained.', '',
 '| Family | EMA fast/slow | Breakout | SL / TP | Latest trades | Latest P/L USD | Prior day P/L | Two days prior P/L |',
 '|---|---|---|---|---:|---:|---:|---:|']
for r in rows:
 c=r['config']; d=r['days']
 lines.append(f"| {c['family']} | {c['fast']}/{c['slow']} | {c['breakout']} | {100*c['stop_loss']:.1f}% / {100*c['take_profit']:.1f}% | {d[0]['number_of_trades']} | {d[0]['profit_usd']:+.2f} | {d[1]['profit_usd']:+.2f} | {d[2]['profit_usd']:+.2f} |")
(p/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
