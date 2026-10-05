import xml.etree.ElementTree as E,re,email.utils
from common import *
URL='https://trends.google.com/trending/rss?geo=KR'
NS={'ht':'https://trends.google.com/trending/rss'}
def parse(raw,collected_at):
 root=E.fromstring(raw);items=root.findall('./channel/item')
 if not items:raise ValueError('empty_or_changed_RSS')
 out=[]
 for pos,x in enumerate(items,1):
  keyword=x.findtext('title');bucket=x.findtext('ht:approx_traffic',namespaces=NS)
  if not keyword or not bucket:raise ValueError('required_RSS_field_missing')
  m=re.fullmatch(r'([\d,]+(?:\.\d+)?)\s*([KMB]?)\+',bucket,re.I)
  lower=int(float(m[1].replace(',',''))*{'':1,'K':1000,'M':1000000,'B':1000000000}[m[2].upper()]) if m else None
  pub=x.findtext('pubDate');parsed=email.utils.parsedate_to_datetime(pub).isoformat() if pub else None
  out.append({'source':'google_trending_rss','category':'NOW','keyword':keyword,'canonical_keyword':normalize(keyword),'collected_at':collected_at,'source_url':URL,'source_position':pos,'source_rank':None,'interest_score':None,'search_volume_bucket':bucket,'volume_lower_bound':lower,'volume_precision':'bucket_lower_bound','source_growth_rate':None,'trend_status':None,'published_at':parsed,'trend_started_at':None,'related_queries':None,'news_metadata':[{'title':n.findtext('ht:news_item_title',namespaces=NS),'url':n.findtext('ht:news_item_url',namespaces=NS),'source':n.findtext('ht:news_item_source',namespaces=NS)} for n in x.findall('ht:news_item',NS)],'coverage':'RSS_returned_items_only','series_scope':'KR_RSS_v1'})
 return out
