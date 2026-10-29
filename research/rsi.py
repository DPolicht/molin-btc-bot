"""Disposable RSI research; no trading bot or existing project changes."""
import sys,json,math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from legacy_mean_reversion import Candle,INITIAL,FEE,validate,iso
from trend import Config,bracket_exit
ROOT=Path(__file__).resolve().parents[1]/'evidence'/'research-rsi'

def wilder_rsi(closes,period=14):
    out=[None]*len(closes)
    if len(closes)<=period:return out
    gains=[max(closes[i]-closes[i-1],0) for i in range(1,len(closes))]
    losses=[max(closes[i-1]-closes[i],0) for i in range(1,len(closes))]
    gain=sum(gains[:period])/period;loss=sum(losses[:period])/period
    def value(g,l):
        if g==0 and l==0:return 50.0
        if l==0:return 100.0
        return 100-100/(1+g/l)
    out[period]=value(gain,loss)
    for i in range(period+1,len(closes)):
        gain=(gain*(period-1)+gains[i-1])/period
        loss=(loss*(period-1)+losses[i-1])/period
        out[i]=value(gain,loss)
    return out


def rsi_events(candles,minutes):
    # Source begins on UTC midnight with complete contiguous minute candles.
    # The event timestamp is candle END: only then is its close available.
    stride=minutes*60
    completed=[c for c in candles if (c.time+60)%stride==0]
    values=wilder_rsi([c.close for c in completed])
    return {c.time+60:(values[i-1] if i else None,values[i]) for i,c in enumerate(completed)}


def replay(candles,events,start,end,tf,threshold,mode,stop,target,slippage=2):
    cfg=Config(stop_loss=stop,take_profit=target)
    slip=slippage/10000;cash=INITIAL;pos=None;trades=[];next_entry=start
    def sell(fill):
        nonlocal cash,pos,next_entry
        price,reason,timestamp=fill;gross=pos['size_btc']*price;fee=gross*FEE
        cash+=gross-fee
        trades.append(dict(pos,sell_time=timestamp,sell_price=price,sell_fee=fee,
                           fees=pos['buy_fee']+fee,pnl=gross-fee-pos['cost'],reason=reason))
        pos=None;next_entry=timestamp+30*60
    for c in candles:
        if c.time<start:continue
        if c.time>=end:break
        last=c.time==end-60;exited=False
        if pos:
            fill=bracket_exit(c,pos['buy_price'],cfg,slip)
            if last:sell((c.open*(1-slip),'end_of_window',c.time));exited=True
            elif fill and fill[2]==c.time:sell(fill);exited=True
            elif c.time-pos['buy_time']>=120*60:sell((c.open*(1-slip),'timeout',c.time));exited=True
            elif fill:sell(fill);exited=True
        if not pos and not exited and not last and c.time>=next_entry and c.time in events:
            prior,current=events[c.time]
            trigger=current is not None and (current<=threshold if mode=='oversold' else prior is not None and prior<=threshold<current)
            if trigger:
                budget=cash*.1;price=c.open*(1+slip);notional=budget/(1+FEE)
                pos=dict(buy_time=c.time,buy_price=price,size_btc=notional/price,cost=budget,buy_fee=notional*FEE,
                         rsi=current,previous_rsi=prior,signal_candle_end=c.time)
                cash-=budget
                fill=bracket_exit(c,price,cfg,slip)
                if fill:sell(fill)
    assert pos is None
    assert abs(cash-INITIAL-sum(t['pnl'] for t in trades))<1e-7
    assert all(start<=t['buy_time']<=t['sell_time']<end for t in trades)
    return dict(start=iso(start),end=iso(end),tf=tf,threshold=threshold,mode=mode,stop=stop,target=target,
                slippage=slippage,n=len(trades),profit=cash-INITIAL,final=cash,
                wins=sum(t['pnl']>0 for t in trades),fees=sum(t['fees'] for t in trades),trades=trades)


def main():
    snapshot=json.loads((ROOT/'candles.json').read_text())
    candles=[Candle(**x) for x in snapshot['candles']]
    validate(candles,snapshot['start'],snapshot['end'])
    end=snapshot['end'];rows=[]
    for tf in [15,30]:
        events=rsi_events(candles,tf)
        for threshold in [20,25,30]:
            for mode in ['oversold','recovery']:
                for stop,target in [(.003,.006),(.004,.008),(.006,.012)]:
                    args=(tf,threshold,mode,stop,target)
                    r=replay(candles,events,end-86400,end,*args)
                    r['previous_day']=replay(candles,events,end-2*86400,end-86400,*args)
                    r['fee_only']=replay(candles,events,end-86400,end,*args,0)
                    r['slippage_5bps']=replay(candles,events,end-86400,end,*args,5)
                    rows.append(r)
    rows.sort(key=lambda r:r['profit'],reverse=True)
    (ROOT/'results.json').write_text(json.dumps(dict(source=snapshot['fetched_at'],results=rows),indent=2))
    print('WINDOW',iso(end-86400),iso(end))
    print('TF threshold mode SL TP trades profit prior_profit prior_trades fee_only slip5')
    for r in rows:
        print(r['tf'],r['threshold'],r['mode'],r['stop'],r['target'],r['n'],round(r['profit'],2),round(r['previous_day']['profit'],2),r['previous_day']['n'],round(r['fee_only']['profit'],2),round(r['slippage_5bps']['profit'],2))
    return candles,rows

if __name__=='__main__':main()
