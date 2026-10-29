#!/usr/bin/env python3
"""Fetch and replay the latest 24h of BTC/USD with a fixed long-only trend strategy."""
import argparse
import hashlib
import json
import math
import sys
import time
from dataclasses import asdict
from pathlib import Path
from legacy_mean_reversion import Candle, FEE, INITIAL, STEP, WARMUP, iso, fetch, validate, signal, replay, report as legacy_report
from trend import Config, replay_trend


def report(result):
    cfg=result['config']
    print(f"TREND {cfg['family']} | EMA {cfg['fast']}/{cfg['slow']} | position {100*cfg['allocation']:.0f}% | "
          f"SL {100*cfg['stop_loss']:.2f}% | TP {100*cfg['take_profit']:.2f}%")
    print('SL/TP intrabar times are reported at candle END; exact touch time is unknown.')
    legacy_report(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,help='Explicit offline snapshot replay, never the default')
    parser.add_argument('--output',type=Path,default=Path('runs/latest'))
    parser.add_argument('--days',type=int,default=1,choices=range(1,8))
    parser.add_argument('--slippage-bps',type=float,default=2.0)
    args=parser.parse_args()
    if not math.isfinite(args.slippage_bps) or not 0<=args.slippage_bps<=100:
        parser.error('slippage must be between 0 and 100 bps')
    cfg=Config(**json.loads(Path(__file__).with_name('strategy.json').read_text()))
    now=time.time()
    if args.input:
        snapshot=json.loads(args.input.read_text())
        end=snapshot['end_epoch']
        candles=[Candle(**c) for c in snapshot['candles']]
        print('OFFLINE SNAPSHOT REPLAY (not a fresh market-data run)')
    else:
        end=int(now//STEP)*STEP
        print('Fetching Coinbase BTC/USD candles...',flush=True)
        candles=fetch(end-args.days*86400-WARMUP*STEP,end)
        snapshot=dict(source='Coinbase Exchange BTC-USD',fetched_at=iso(now),end_epoch=end,
                      candles=[asdict(c) for c in candles])
    args.output.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(snapshot,indent=2)+'\n'
    (args.output/'candles.json').write_text(raw)
    results=[]
    for day in range(args.days):
        stop=end-day*86400; start=stop-86400
        selected=[c for c in candles if start-WARMUP*STEP<=c.time<stop]
        result=replay_trend(selected,start,stop,cfg,args.slippage_bps)
        result.update(run_at=iso(now),snapshot_sha256=hashlib.sha256(raw.encode()).hexdigest())
        results.append(result)
        report(result)
    (args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'Evidence saved to {args.output}')
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
