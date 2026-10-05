"""Synthetic fixtures exist ONLY in tests; never treated as collected samples."""
import unittest,sys,pathlib,datetime as dt,tempfile,json,copy
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from common import normalize
from analytics.metrics import calculate,pct,cross_source
from collectors.google_rss import parse
from collectors.naver import build_request,parse as parse_naver
from processors.store import connect,save_run,prior_google
from llm.editor import validate
class Tests(unittest.TestCase):
 def test_zero_missing_and_gap(self):
  self.assertIsNone(pct(4,0));self.assertIsNone(pct(None,3))
  m=calculate({'2026-01-01':1,'2026-01-03':3},'2026-01-03');self.assertIsNone(m['daily_growth_pct']);self.assertIsNone(m['persistent_rise'])
 def test_momentum_same_window(self):
  start=dt.date(2026,1,1);v={(start+dt.timedelta(days=i)).isoformat():1 if i<7 else 2 for i in range(14)}
  m=calculate(v,'2026-01-14');self.assertEqual(m['seven_day_momentum_pct'],100);self.assertIsNone(m['thirty_day_momentum_pct'])
 def test_spike_needs_future(self):
  v={f'2026-01-{i:02}':1 for i in range(1,8)};v['2026-01-08']=4
  self.assertTrue(calculate(v,'2026-01-08')['spike_candidate']);self.assertIsNone(calculate(v,'2026-01-08')['one_day_spike'])
  v['2026-01-09']=1;self.assertTrue(calculate(v,'2026-01-08')['one_day_spike'])
 def test_rank_sign_and_ties(self):
  m=calculate({'2026-01-01':1,'2026-01-02':2},'2026-01-02',{'2026-01-01':18,'2026-01-02':5});self.assertEqual(m['rank_change'],-13);self.assertEqual(m['rank_rise'],13)
 def test_cross_source_needs_measured_rise(self):
  rows=[{'keyword':'KBO','source':'google_trending_rss','daily_growth_pct':None},{'keyword':'kbo','source':'naver_search','daily_growth_pct':10}];self.assertEqual(cross_source(rows,{}),[])
 def test_actual_rss_and_replay(self):
  meta=json.loads((ROOT/'data/raw/google_kr_fetch.json').read_text());rows=parse((ROOT/'data/raw/google_kr.xml').read_bytes(),meta['collected_at'])
  self.assertEqual(len(rows),10);self.assertTrue(all(r['source_rank'] is None for r in rows));self.assertTrue(all(r['source_growth_rate'] is None for r in rows));self.assertEqual(rows[6]['search_volume_bucket'],'5000+')
  with tempfile.TemporaryDirectory() as d:
   db=connect(pathlib.Path(d)/'test.sqlite');save_run(db,'run','2026-10-05','google_trending_rss','success',meta['collected_at'],'test.xml',rows);save_run(db,'run','2026-10-05','google_trending_rss','success',meta['collected_at'],'test.xml',rows)
   self.assertEqual(db.execute('SELECT count(*) FROM snapshot').fetchone()[0],10);self.assertIsNone(prior_google(db,'2026-10-05',rows[0]['series_scope']));self.assertEqual(len(prior_google(db,'2026-10-06',rows[0]['series_scope'])),10);db.close()
 def test_editor_guard(self):
  inp=json.loads((ROOT/'output/2026-10-05/metrics/llm_input.json').read_text());r=json.loads((ROOT/'src/llm/work_session_editorial.json').read_text())['report'];validate(r,inp)
  for modification in ['numeric','ref','signal']:
   bad=copy.deepcopy(r)
   if modification=='numeric':bad['one_line']['text']='판매량 100 증가'
   if modification=='ref':bad['one_line']['fact_refs']=['F9999']
   if modification=='signal':bad['sections']['persistent']=[bad['one_line']]
   with self.assertRaises(ValueError):validate(bad,inp)
 def test_naver_request_and_relative_parser_synthetic(self):
  config=json.loads((ROOT/'config/watchlist.json').read_text());req=build_request('search',config,'2026-10-04');self.assertEqual(req['startDate'],'2026-08-05')
  with self.assertRaises(ValueError):build_request('shopping',config,'2026-10-04')
  raw=json.dumps({'timeUnit':'date','results':[{'title':'테스트 A','data':[{'period':'2026-10-04','ratio':50}]},{'title':'테스트 B','data':[{'period':'2026-10-04','ratio':50}]}]}).encode()
  records=parse_naver(raw,req,'2026-10-05T00:00:00+00:00','search','test-only');self.assertEqual([r['rank'] for r in records],[1,1])
 def test_normalization(self):self.assertEqual(normalize('  ＫＢＯ  '),'kbo');self.assertEqual(normalize('ETF  200'),'etf 200')
if __name__=='__main__':unittest.main()
