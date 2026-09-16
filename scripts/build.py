"""Export only allowlisted public minutes from the local audit-game corpus."""
import argparse,collections,datetime,gzip,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(b):return hashlib.sha256(b).hexdigest()
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data,encoding='utf-8')
def export(source):
 corpus=json.loads((source/'data/council-corpus.json').read_text());catalog={r['id']:r for r in json.loads((source/'data/catalog.json').read_text())};records=[]
 for m in sorted(corpus['minutes'],key=lambda x:(x['date'],x['id'])):
  assert '2022-07-01'<=m['date']<=corpus['endDate'];assert m['term']==(3 if m['date']<'2026-07-01' else 4)
  assert re.fullmatch(r'minutes-\d+',m['id']);assert m['asset']=='/corpus/'+m['id']+'.md.bin';assert m['url'].startswith('https://councilrec.cheongju.go.kr/')
  raw=gzip.decompress((source/'public'/m['asset'].lstrip('/')).read_bytes());assert digest(raw)==catalog[m['id']]['sha256'],m['id']
  # Preserve archived Markdown bytes exactly after the metadata header.
  path=f'minutes/term-{m["term"]}/{m["year"]}/{m["id"]}.md'
  meta={k:m[k] for k in ['id','title','date','year','term','committee','url']};meta['source_sha256']=digest(raw)
  front='---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in meta.items())+'---\n\n'
  payload=front.encode()+raw;(ROOT/path).parent.mkdir(parents=True,exist_ok=True);(ROOT/path).write_bytes(payload)
  records.append({**meta,'path':path,'sha256':digest(payload),'bytes':len(payload),'body_start_line':front.count('\n')+1})
 save(ROOT/'indexes/meetings.json',json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 manifest={k:corpus[k] for k in ['startDate','endDate','checkedAt','latestMeetingDate','listed','collected','byYear','byTerm','sourceUrl','unavailable']};manifest.update(schema_version=1,scope='공식 공개 목록의 제3·4대 회의록 수집본. 첨부파일·사진판·미공개 자료 전체를 보장하지 않습니다.',history_policy='회의일은 메타데이터에 기록합니다. Git 커밋 시간은 실제 수집·변경 시간이며 회의일로 소급하지 않습니다.')
 save(ROOT/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');reindex();print(f'Exported {len(records)} meetings')
def reindex():
 meetings=json.loads((ROOT/'indexes/meetings.json').read_text());turns=[];speakers=collections.defaultdict(list)
 for m in meetings:
  lines=(ROOT/m['path']).read_text().splitlines();starts=[i for i,line in enumerate(lines) if re.match(r'^##\s+○',line)]
  for n,start in enumerate(starts):
   end=starts[n+1] if n+1<len(starts) else len(lines);heading=re.sub(r'^##\s+○','',lines[start]);label=re.split(r'\u2003|\t',heading,maxsplit=1)[0].strip()
   # Older records place speech on a new line; only accept a short two-token label.
   tokens=re.sub(r'\([^)]*\)','',label).split();name='';role=''
   if len(tokens)==2:
    if re.fullmatch(r'[가-힣]{2,5}',tokens[0]) and re.fullmatch(r'(?:위원장대리|부위원장|위원장|부의장|의장|의원|위원)',tokens[1]):name,role=tokens
    elif re.fullmatch(r'[가-힣]{2,5}',tokens[1]):role,name=tokens
   row={'id':m['id']+f'-turn-{n+1:04d}','meeting_id':m['id'],'path':m['path'],'date':m['date'],'term':m['term'],'committee':m['committee'],'speaker':name,'role':role,'label':label if len(label)<100 else '', 'start_line':start+1,'end_line':end}
   turns.append(row)
   if name:speakers[name].append(row)
 for year in sorted(set(m['year'] for m in meetings)):
  save(ROOT/f'indexes/turns/{year}.jsonl',''.join(json.dumps(t,ensure_ascii=False,separators=(',',':'))+'\n' for t in turns if t['date'].startswith(str(year))))
 summary=[{'name':name,'turn_count':len(ts),'meeting_count':len(set(t['meeting_id'] for t in ts)),'roles':sorted(set(t['role'] for t in ts)),'first_date':min(t['date'] for t in ts),'last_date':max(t['date'] for t in ts)} for name,ts in sorted(speakers.items())]
 save(ROOT/'indexes/speakers.json',json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 for key,groups in [('years',collections.defaultdict(list)),('committees',collections.defaultdict(list)),('terms',collections.defaultdict(list))]:
  field={'years':'year','committees':'committee','terms':'term'}[key]
  for m in meetings:groups[str(m[field])].append(m)
  intro=f'# {key} 목록\n\n'
  for value,ms in sorted(groups.items()):
   intro+=f'- [{value} ({len(ms)}건)]({value}.md)\n';body=f'# {value} 회의록 · {len(ms)}건\n\n'
   for m in sorted(ms,key=lambda x:x['date'],reverse=True):body+=f'- {m["date"]} [{m["title"]}](../../{m["path"]}) · `{m["id"]}`\n'
   save(ROOT/f'indexes/{key}/{value}.md',body)
  save(ROOT/f'indexes/{key}/README.md',intro)
 print(f'Indexed {len(turns)} speech sections, {len(summary)} speaker labels')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path);a=p.parse_args();export(a.source.resolve()) if a.source else reindex()
