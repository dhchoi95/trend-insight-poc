import argparse,os,sys,json,datetime as dt,urllib.error,shutil
from common import *
from collectors.google_rss import parse as parse_google
from collectors import naver
from processors.store import connect,save_run,prior_google
from analytics.metrics import calculate,cross_source
from llm.editor import imported,via_api
from outputs.render import render

def run(args):
 db=connect(ROOT/'data/trends.sqlite3');rawdir=ROOT/'data/raw';rawdir.mkdir(parents=True,exist_ok=True)
 config=json.loads((ROOT/'config/watchlist.json').read_text());status={};rows=[]
 if args.offline:
  raw=(rawdir/'google_kr.xml').read_bytes();meta=json.loads((rawdir/'google_kr_fetch.json').read_text());ts=meta['collected_at']
 else:
  ts=now();url='https://trends.google.com/trending/rss?geo=KR'
  raw=http(url);meta={'url':url,'status':200,'collected_at':ts,'bytes':len(raw)}
  (rawdir/'google_kr.xml').write_bytes(raw);dump(rawdir/'google_kr_fetch.json',meta)
 date=dt.datetime.fromisoformat(ts).astimezone(ZoneInfo('Asia/Seoul')).date().isoformat();out=ROOT/'output'/date;out.mkdir(parents=True,exist_ok=True)
 for name in ['insight.json','daily_brief.md','instagram.md','blog.md','website.md','newsletter.md','website.json','run_summary.json']:(out/name).unlink(missing_ok=True)
 (out/'raw').mkdir(exist_ok=True);(out/'raw/google_kr.xml').write_bytes(raw);dump(out/'raw/google_kr_fetch.json',meta)
 google=parse_google(raw,ts);previous=prior_google(db,date,google[0]['series_scope']);prevkeys={r['canonical_keyword'] for r in previous} if previous is not None else None
 for r in google:r['new_to_observed_feed']=None if prevkeys is None else r['canonical_keyword'] not in prevkeys
 save_run(db,hash_json({'source':'google','ts':ts,'raw':raw.decode()}),date,'google_trending_rss','success',ts,out/'raw/google_kr.xml',google)
 rows+=google;status['NOW']='success';end=(dt.date.fromisoformat(date)-dt.timedelta(days=1)).isoformat()
 request=naver.build_request('search',config,end);dump(out/'raw/naver_search_request.json',request)
 fashion=[]
 if args.offline or not (os.environ.get('NAVER_HUB_CLIENT_ID') and os.environ.get('NAVER_HUB_CLIENT_SECRET')):
  status['FASHION']='not_collected: credentials_missing_or_offline'
 else:
  try:
   nraw,request=naver.fetch('search',config,end);(out/'raw/naver_search.json').write_bytes(nraw)
   fashion=naver.parse(nraw,request,now(),'search',config['version']);rows+=fashion;status['FASHION']='success'
   save_run(db,hash_json({'source':'naver','ts':ts,'raw':nraw.decode()}),date,'naver_search','success',ts,out/'raw/naver_search.json',fashion)
  except (urllib.error.URLError,ValueError,KeyError,RuntimeError) as e:
   status['FASHION']='failed: '+type(e).__name__ # Never log credential-bearing requests.
 save_run(db,hash_json({'date':date,'source':'naver_status','status':status['FASHION']}),date,'naver_search_status',status['FASHION'],ts,'',[])
 observed=[];facts=[]
 def fact(kind,text):
  ref='F'+str(len(facts)+1).zfill(4);facts.append({'id':ref,'type':kind,'text':text});return ref
 for r in google[:30]:
  ref=fact('Source Fact',f"{r['keyword']} — Google 한국 Trending Now RSS 검색량 구간 {r['search_volume_bucket']} (피드 표시값, 정확한 검색 횟수·공식 순위 아님)")
  observed.append({'source':r['source'],'category':'NOW','keyword':r['keyword'],'source_position':r['source_position'],'search_volume_bucket':r['search_volume_bucket'],'daily_growth_pct':None,'rank_change':None,'seven_day_momentum_pct':None,'thirty_day_momentum_pct':None,'persistent_rise':None,'fast_rising':None,'new_to_observed_feed':r['new_to_observed_feed'],'fact_refs':[ref]})
 for keyword in sorted({r['keyword'] for r in fashion}):
  selected=[r for r in fashion if r['keyword']==keyword];values={r['period']:r['interest_score'] for r in selected};ranks={r['period']:r['rank'] for r in selected};target=next((r for r in selected if r['period']==end),None)
  if target is None:continue
  metrics=calculate(values,end,ranks);ref=fact('Source Fact',f"{keyword} — {end} 네이버 검색 상대지수 {target['interest_score']} (현재 동일 요청 내 정규화, 정확한 검색량 아님)")
  refs=[ref]
  for key in ['daily_growth_pct','seven_day_momentum_pct','thirty_day_momentum_pct','rank_change']:
   if metrics[key] is not None:refs.append(fact('Calculated Metric',f"{keyword} — {key}: {metrics[key]} (동일 API 응답 구간에서 계산)"))
  observed.append({'source':'naver_search','category':'FASHION','keyword':keyword,'metric_period':end,'interest_score':target['interest_score'],'internal_watchlist_rank':target['rank'],'rank_scope':'configured_groups_only','new_to_observed_feed':None,**metrics,'fact_refs':refs})
 signals={'fast_rising':[],'persistent_rise':[],'new_to_observed_feed':[],'falling':[],'cross_source':cross_source(observed,config['aliases'])}
 for r in observed:
  for key in ['fast_rising','persistent_rise','new_to_observed_feed']:
   if r.get(key) is True:signals[key].append(r['keyword'])
  if r.get('daily_growth_pct') is not None and r['daily_growth_pct']<0:signals['falling'].append(r['keyword'])
 fact('Calculated Metric',f'이번 성공 수집 RSS의 관측 항목 수: {len(google)}개 (공식 전체 트렌드 수 아님)')
 inp={'report_date':date,'collected_at':ts,'coverage':status,'history':{'google_previous_day_available':previous is not None,'naver_history':'within_one_response_only' if fashion else 'unavailable'},'calculated_aggregates':{'observed_rss_item_count':len(google),'observed_fashion_daily_record_count':len(fashion)},'observed':observed,'signals':signals,'facts':facts,'limitations':['RSS 순서는 공식 순위가 아니다','검색량 구간으로 증가율을 계산하지 않는다','첫 관측은 새 트렌드 판정이 아니다','관련 뉴스 제목을 배경 사실로 사용하지 않는다']}
 dump(ROOT/'data/processed/normalized.json',rows);dump(out/'metrics/metrics.json',observed);dump(out/'metrics/llm_input.json',inp)
 editorial=None
 if args.llm_file:editorial=imported(pathlib.Path(args.llm_file),inp,db)
 elif args.llm_api:editorial=via_api(inp,db)
 if editorial:dump(out/'insight.json',editorial)
 else:
  for name in ['insight.json','instagram.md','blog.md','website.md','newsletter.md','website.json']:(out/name).unlink(missing_ok=True)
 render(out,inp,editorial)
 result={'date':date,'sources':status,'google_items':len(google),'naver_daily_records':len(fashion),'editorial':editorial['provenance'] if editorial else 'not_run','input_hash':hash_json(inp),'output':str(out)}
 dump(out/'run_summary.json',result);db.close();print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',help='Replay archived RSS; retains original collection date');g=p.add_mutually_exclusive_group();g.add_argument('--llm-file');g.add_argument('--llm-api',action='store_true');run(p.parse_args())
