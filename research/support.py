"""Temporary research only: previous-day support hypotheses, no bot changes."""
import sys,json
from pathlib import Path
from dataclasses import asdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from legacy_mean_reversion import Candle,INITIAL,FEE,STEP,iso,validate
from trend import Config,bracket_exit

ROOT=Path(__file__).resolve().parents[1]/'evidence'/'research-support'
s=json.loads((ROOT/'candles.json').read_text()); candles=[Candle(**x) for x in s['candles']]
validate(candles,s['start'],s['end'])
daily={}
for c in candles:
 daily.setdefault(c.time//86400,[]).append(c)
levels={}
for day,bars in daily.items():
 if len(bars)!=1440: continue
 high=max(c.high for c in bars); low=min(c.low for c in bars); close=bars[-1].close
 p=(high+low+close)/3
 levels[day+1]=dict(previous_low=low,S1=2*p-high,S2=p-(high-low),previous_high=high,previous_close=close,pivot=p)

def replay(start,end,level_name,mode,stop,target,slip_bps=2):
 cfg=Config(stop_loss=stop,take_profit=target,allocation=.1,max_hold=120,cooldown=30)
 slip=slip_bps/10000; cash=INITIAL; pos=None; trades=[]; next_entry=start; history=[]
 def sell(fill):
  nonlocal cash,pos,next_entry
  price,reason,stamp=fill; gross=pos['size_btc']*price; fee=gross*FEE
  cash+=gross-fee
  trades.append(dict(pos,sell_time=stamp,sell_price=price,sell_fee=fee,reason=reason,pnl=gross-fee-pos['cost'],fees=pos['buy_fee']+fee))
  pos=None;next_entry=stamp+30*60
 for c in candles:
  if c.time<start:
   history.append(c);continue
  if c.time>=end:break
  last=c.time==end-60;exited=False
  if pos:
   fill=bracket_exit(c,pos['buy_price'],cfg,slip)
   if last: sell((c.open*(1-slip),'end_of_window',c.time));exited=True
   elif fill and fill[2]==c.time: sell(fill);exited=True
   elif c.time-pos['buy_time']>=120*60: sell((c.open*(1-slip),'timeout',c.time));exited=True
   elif fill: sell(fill);exited=True
  if not pos and not exited and not last and c.time>=next_entry:
   day=c.time//86400
   # Do not trade a signal formed on yesterday's candle at the UTC date rollover.
   if day in levels and len(history)>=2 and history[-1].time//86400==day:
    h=history[-1];prev=history[-2];level=levels[day][level_name]
    bullish=h.close>h.open
    if mode=='bounce':
     trigger=(level*.999 <= h.low <= level*1.001 and level*1.0005<=h.close<=level*1.003 and bullish)
    else:
     trigger=(prev.close<=level and level*1.0005<=h.close<=level*1.003 and bullish)
    if trigger:
     budget=cash*.1; price=c.open*(1+slip);notional=budget/(1+FEE)
     pos=dict(buy_time=c.time,buy_price=price,size_btc=notional/price,buy_fee=notional*FEE,cost=budget,support=level,support_day=iso(day*86400),signal_time=h.time)
     cash-=budget
     fill=bracket_exit(c,price,cfg,slip)
     if fill:sell(fill)
  history.append(c)
 assert pos is None
 assert all(start<=t['buy_time']<=t['sell_time']<end for t in trades)
 assert abs((cash-INITIAL)-sum(t['pnl'] for t in trades))<1e-7
 return dict(start=iso(start),end=iso(end),level=level_name,mode=mode,stop=stop,target=target,slippage_bps=slip_bps,profit=cash-INITIAL,final=cash,n=len(trades),fees=sum(t['fees'] for t in trades),wins=sum(t['pnl']>0 for t in trades),trades=trades)

end=s['end'];rows=[]
for level in ['previous_low','S1','S2']:
 for mode in ['bounce','reclaim']:
  for sl,tp in [(.003,.006),(.004,.008),(.006,.012)]:
   r=replay(end-86400,end,level,mode,sl,tp)
   r['previous_day']=replay(end-2*86400,end-86400,level,mode,sl,tp)
   r['fee_only']=replay(end-86400,end,level,mode,sl,tp,0)
   r['slippage_5bps']=replay(end-86400,end,level,mode,sl,tp,5)
   rows.append(r)
rows.sort(key=lambda r:r['profit'],reverse=True)
(ROOT/'results.json').write_text(json.dumps(dict(source=s['fetched_at'],levels=levels,results=rows),indent=2))
print('WINDOW',iso(end-86400),iso(end))
print('LEVELS')
for day,l in levels.items(): print(iso(day*86400),{k:round(v,2) for k,v in l.items()})
print('level mode SL TP trades profit prior_profit fee_only slip5')
for r in rows: print(r['level'],r['mode'],r['stop'],r['target'],r['n'],round(r['profit'],2),round(r['previous_day']['profit'],2),round(r['fee_only']['profit'],2),round(r['slippage_5bps']['profit'],2))
print('BEST TRADES')
for t in rows[0]['trades']:
 print(iso(t['buy_time']),iso(t['sell_time']),round(t['support'],2),round(t['buy_price'],2),round(t['sell_price'],2),t['reason'],round(t['pnl'],4))
