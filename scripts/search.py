"""Offline full-text/attributed-speech search. Python standard library only."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def search(query,years=None,term=None,committee=None,speaker=None,limit=20,offset=0):
 if not query.strip():raise ValueError('검색어가 필요합니다.')
 pattern=re.compile(r'\s*'.join(re.escape(x) for x in query.split()),re.I)
 meetings=json.loads((ROOT/'indexes/meetings.json').read_text());selected={m['id']:m for m in meetings if (not years or m['year'] in years) and (not term or m['term']==term) and (not committee or m['committee']==committee or committee in m['title'])};results=[];cache={}
 def lines(m):
  if m['id'] not in cache:cache[m['id']]=(ROOT/m['path']).read_text().splitlines()
  return cache[m['id']]
 if speaker:
  candidates=[]
  for shard in sorted((ROOT/'indexes/turns').glob('*.jsonl')):
   if years and int(shard.stem) not in years:continue
   with shard.open() as f:candidates.extend(json.loads(line) for line in f if line.strip())
  candidates=[t for t in candidates if t['speaker']==speaker and t['meeting_id'] in selected]
 else:candidates=[{'meeting_id':m['id'],'start_line':m['body_start_line'],'end_line':None} for m in selected.values()]
 for t in candidates:
  m=selected[t['meeting_id']];body='\n'.join(lines(m)[t['start_line']-1:t['end_line']]);match=pattern.search(body)
  if not match:continue
  line=t['start_line']+body[:match.start()].count('\n');excerpt=body[max(0,match.start()-100):match.end()+220]
  results.append({'id':t.get('id',m['id']),'meeting_id':m['id'],'title':m['title'],'date':m['date'],'term':m['term'],'committee':m['committee'],'speaker':t.get('speaker'),'role':t.get('role'),'path':m['path'],'line':line,'source_url':m['url'],'excerpt':excerpt})
 results.sort(key=lambda r:(r['date'],r['meeting_id'],r['line']),reverse=True)
 return {'query':query,'unit':'발언 구간' if speaker else '회의록','total':len(results),'offset':offset,'returned':len(results[offset:offset+limit]),'results':results[offset:offset+limit]}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('query');p.add_argument('--years',nargs='+',type=int);p.add_argument('--term',type=int,choices=[3,4]);p.add_argument('--committee');p.add_argument('--speaker');p.add_argument('--limit',type=int,default=20);p.add_argument('--offset',type=int,default=0);p.add_argument('--json',action='store_true');a=p.parse_args()
 if not 1<=a.limit<=1000 or a.offset<0:p.error('limit는 1~1000, offset은 0 이상입니다.')
 d=search(a.query,a.years,a.term,a.committee,a.speaker,a.limit,a.offset)
 if a.json:print(json.dumps(d,ensure_ascii=False,indent=2))
 else:
  print(f'{d["unit"]} {d["total"]}건 중 {d["returned"]}건 표시 (offset {a.offset})')
  for r in d['results']:print(f'\n{r["date"]} {r["title"]}\n{r["path"]}:{r["line"]}\n{r["excerpt"]}\n공식 원문: {r["source_url"]}')
