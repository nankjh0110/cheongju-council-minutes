"""Validate public export integrity without network access."""
import collections,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate():
 manifest=json.loads((ROOT/'manifest.json').read_text());rows=json.loads((ROOT/'indexes/meetings.json').read_text());assert len(rows)==manifest['collected']==len({r['id'] for r in rows});assert len(list((ROOT/'minutes').rglob('*.md')))==len(rows)
 sources={};count=0
 for r in rows:
  path=(ROOT/r['path']).resolve();assert path.is_relative_to(ROOT/'minutes');raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'],r['id'];_,_,body=raw.split(b'---\n',2);body=body[1:];assert hashlib.sha256(body).hexdigest()==r['source_sha256'],r['id'];assert r['term']==(3 if r['date']<'2026-07-01' else 4);assert manifest['startDate']<=r['date']<=manifest['endDate'];assert r['url'].startswith('https://councilrec.cheongju.go.kr/');sources[r['id']]=raw.decode().splitlines()
 assert dict(collections.Counter(str(r['year']) for r in rows))==manifest['byYear'];assert dict(collections.Counter(str(r['term']) for r in rows))==manifest['byTerm']
 for line in (line for shard in (ROOT/'indexes/turns').glob('*.jsonl') for line in shard.read_text().splitlines()):
  t=json.loads(line);ls=sources[t['meeting_id']];assert 1<=t['start_line']<=t['end_line']<=len(ls);assert re.match(r'^##\s+○',ls[t['start_line']-1]);count+=1
 print(f'PASS {len(rows)} meetings, exact preserved source hashes, {count} speech spans, dates and coverage')
if __name__=='__main__':validate()
