import sqlite3,json
from common import *
SQL='''PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS run(run_id TEXT PRIMARY KEY,report_date TEXT NOT NULL,source TEXT NOT NULL,status TEXT NOT NULL,collected_at TEXT,scope TEXT,raw_path TEXT);
CREATE TABLE IF NOT EXISTS keyword(source TEXT NOT NULL,canonical TEXT NOT NULL,category TEXT NOT NULL,first_seen_at TEXT NOT NULL,last_seen_at TEXT NOT NULL,PRIMARY KEY(source,canonical,category));
CREATE TABLE IF NOT EXISTS snapshot(run_id TEXT NOT NULL,source TEXT NOT NULL,canonical TEXT NOT NULL,category TEXT NOT NULL,period TEXT NOT NULL,scope TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(run_id,source,canonical,period),FOREIGN KEY(run_id) REFERENCES run(run_id));
CREATE TABLE IF NOT EXISTS report(input_hash TEXT NOT NULL,model TEXT NOT NULL,prompt_version TEXT NOT NULL,generated_at TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(input_hash,model,prompt_version));
CREATE INDEX IF NOT EXISTS snapshot_lookup ON snapshot(source,canonical,period,scope);
'''
def connect(path):
 path.parent.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(path);db.executescript(SQL);return db

def save_run(db,run_id,date,source,status,ts,raw_path,rows):
 with db:
  db.execute('INSERT OR IGNORE INTO run VALUES (?,?,?,?,?,?,?)',(run_id,date,source,status,ts,rows[0].get('series_scope') if rows else None,str(raw_path)))
  for r in rows:
   period=r.get('period',date)
   db.execute('INSERT INTO keyword VALUES (?,?,?,?,?) ON CONFLICT(source,canonical,category) DO UPDATE SET last_seen_at=max(keyword.last_seen_at,excluded.last_seen_at)',(source,r['canonical_keyword'],r['category'],ts,ts))
   db.execute('INSERT OR IGNORE INTO snapshot VALUES (?,?,?,?,?,?,?)',(run_id,source,r['canonical_keyword'],r['category'],period,r['series_scope'],json.dumps(r,ensure_ascii=False)))

def prior_google(db,date,scope):
 previous=(dt.date.fromisoformat(date)-dt.timedelta(days=1)).isoformat()
 row=db.execute("SELECT run_id FROM run WHERE source='google_trending_rss' AND status='success' AND report_date=? AND scope=? ORDER BY collected_at DESC LIMIT 1",(previous,scope)).fetchone()
 return [json.loads(r[0]) for r in db.execute('SELECT payload FROM snapshot WHERE run_id=?',(row[0],))] if row else None
