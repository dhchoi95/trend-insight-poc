import datetime as dt,json,pathlib,hashlib,unicodedata,re,urllib.request
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1]
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def day():return dt.datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat()
def dump(path,value):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def normalize(s):return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
def hash_json(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def http(url,payload=None,headers=None):
 h={'User-Agent':'TrendInsightResearch/0.1','Accept':'application/json,application/rss+xml'};h.update(headers or {})
 if payload is not None:h['Content-Type']='application/json'
 req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None,headers=h)
 # No retry or redirect to another host, especially with credentials.
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*a,**kw):return None
 with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as r:
  raw=r.read(5_000_001)
  if len(raw)>5_000_000:raise ValueError('response_too_large')
  return raw
