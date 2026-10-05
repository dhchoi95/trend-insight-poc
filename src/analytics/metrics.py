import datetime as dt,statistics

def pct(today,previous):
 return None if today is None or previous is None or previous<=0 else (today-previous)/previous*100

def window(values,end,days):
 dates=[(end-dt.timedelta(days=i)).isoformat() for i in range(days)]
 return [values[d] for d in dates] if all(d in values for d in dates) else None

def calculate(values,end_date,ranks=None):
 end=dt.date.fromisoformat(end_date);today=values.get(end_date);prevdate=(end-dt.timedelta(days=1)).isoformat();prev=values.get(prevdate);ranks=ranks or {}
 daily=pct(today,prev);last7=window(values,end,7);prev7=window(values,end-dt.timedelta(days=7),7);last30=window(values,end,30);prev30=window(values,end-dt.timedelta(days=30),30);baseline=window(values,end-dt.timedelta(days=1),7);last5=window(values,end,5)
 yesterday=ranks.get(prevdate);rank=ranks.get(end_date)
 # A one-day spike can only be confirmed retrospectively with a following day.
 following=values.get((end+dt.timedelta(days=1)).isoformat());candidate=None if baseline is None or today is None else (statistics.mean(baseline)>0 and today>=3*statistics.mean(baseline))
 return {'daily_growth_pct':daily,'rank_change':None if rank is None or yesterday is None else rank-yesterday,'rank_rise':None if rank is None or yesterday is None else yesterday-rank,'seven_day_momentum_pct':None if not last7 or not prev7 else pct(statistics.mean(last7),statistics.mean(prev7)),'thirty_day_momentum_pct':None if not last30 or not prev30 else pct(statistics.mean(last30),statistics.mean(prev30)),'persistent_rise':None if not last5 else all(last5[i]>last5[i+1] for i in range(4)),'spike_candidate':candidate,'one_day_spike':None if following is None or baseline is None or candidate is None else bool(candidate and following<=1.5*statistics.mean(baseline)),'fast_rising':None if daily is None else daily>=50,'days_available':len(values)}

def cross_source(rows,aliases):
 # True metric rises only; a traffic bucket alone is never a rise.
 import unicodedata,re
 def norm(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
 amap={norm(k):norm(v) for k,v in aliases.items()};groups={}
 for x in rows:
  metric=x.get('daily_growth_pct')
  if metric is None or metric<=0:continue
  key=norm(x['keyword']);key=amap.get(key,key);groups.setdefault(key,set()).add(x['source'])
 return [{'keyword':k,'sources':sorted(v)} for k,v in groups.items() if any(s.startswith('naver') for s in v) and any(s.startswith('google') for s in v)]
