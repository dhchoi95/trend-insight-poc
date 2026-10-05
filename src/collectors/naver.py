import os,datetime as dt,json
from common import *
URLS={'search':'https://naverapihub.apigw.ntruss.com/search-trend/v1/search','shopping':'https://naverapihub.apigw.ntruss.com/shopping/v1/category/keywords'}
def build_request(kind,config,end_date):
 end=dt.date.fromisoformat(end_date);groups=config['keyword_groups']
 if not 1<=len(groups)<=5:raise ValueError('requires_1_to_5_keyword_groups')
 payload={'startDate':(end-dt.timedelta(days=60)).isoformat(),'endDate':end.isoformat(),'timeUnit':'date'}
 if kind=='search':payload['keywordGroups']=groups
 else:
  if not config.get('shopping_category'):raise ValueError('verified_shopping_category_required')
  payload.update(category=config['shopping_category'],keyword=[{'name':g['groupName'],'param':[g['keywords'][0]]} for g in groups])
 return payload

def fetch(kind,config,end_date):
 key=os.environ.get('NAVER_HUB_CLIENT_ID');secret=os.environ.get('NAVER_HUB_CLIENT_SECRET')
 if not key or not secret:raise RuntimeError('missing_NAVER_HUB_credentials')
 request=build_request(kind,config,end_date)
 raw=http(URLS[kind],request,{'X-NCP-APIGW-API-KEY-ID':key,'X-NCP-APIGW-API-KEY':secret})
 return raw,request

def parse(raw,request,collected_at,kind,watchlist_version):
 data=json.loads(raw);source='naver_search' if kind=='search' else 'naver_shopping_click'
 if data.get('timeUnit')!='date' or not data.get('results'):raise ValueError('invalid_naver_response')
 batch=hash_json(request);scope=hash_json({k:v for k,v in request.items() if k not in ['startDate','endDate']}|{'watchlist_version':watchlist_version})
 records=[]
 for group in data['results']:
  for x in group['data']:
   score=float(x['ratio'])
   if not 0<=score<=100:raise ValueError('ratio_out_of_range')
   records.append({'source':source,'category':'FASHION','keyword':group['title'],'canonical_keyword':normalize(group['title']),'period':x['period'],'collected_at':collected_at,'source_url':URLS[kind],'interest_score':score,'source_rank':None,'rank':None,'search_volume_bucket':None,'source_growth_rate':None,'trend_status':None,'series_scope':scope,'normalization_batch':batch,'metric_unit':'search_relative_index' if kind=='search' else 'shopping_click_relative_index','watchlist_version':watchlist_version,'coverage':'configured_keyword_groups_only'})
 # Internal watchlist rank, same response and date only; competition ranking ties.
 for period in {r['period'] for r in records}:
  local=[r for r in records if r['period']==period]
  for r in local:r['rank']=1+sum(x['interest_score']>r['interest_score'] for x in local)
 return records
