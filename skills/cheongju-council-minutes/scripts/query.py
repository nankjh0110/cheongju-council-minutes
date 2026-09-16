"""Read-only, offline council archive tools; no dependencies or AI credentials."""
import argparse, collections, hashlib, json, re
from pathlib import Path

def load(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    rows=json.loads((root/'indexes/meetings.json').read_text(encoding='utf-8'))
    return manifest,{r['id']:r for r in rows}

def read(root,row):
    path=(root/row['path']).resolve()
    if not path.is_relative_to(root.resolve()/'minutes'): raise ValueError('Archive path outside minutes')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['sha256']: raise ValueError('Archive hash mismatch: '+row['id'])
    return raw.decode('utf-8').splitlines()

def execute(root,command,query='',years=None,speakers=None,committee=None,offset=0,limit=20,meeting=None,start=1):
    if offset<0 or not 1<=limit<=100: raise ValueError('limit must be 1..100; offset >= 0')
    manifest,allrows=load(root)
    scope={k:manifest.get(k) for k in ('startDate','endDate','checkedAt','latestMeetingDate','collected','byTerm','provisional')}
    if command=='status': return {'scope':scope,'speakers':json.loads((root/'indexes/speakers.json').read_text(encoding='utf-8'))}
    if command=='read':
        if meeting not in allrows: raise ValueError('Unknown meeting ID')
        if start<1: raise ValueError('start must be >= 1')
        row=allrows[meeting];lines=read(root,row)
        if start>len(lines): raise ValueError('start exceeds document length')
        return {'scope':scope,'meeting':row,'total_lines':len(lines),'lines':[{'line':i+1,'text':line} for i,line in enumerate(lines) if start-1<=i<start-1+limit]}
    if command=='search' and not query.strip(): raise ValueError('Search query required')
    if command=='speeches' and not speakers: raise ValueError('Select at least one speaker')
    selected={k:r for k,r in allrows.items() if (not years or r['year'] in years) and (not committee or committee==r['committee'] or committee in r['title'])}
    pattern=re.compile(r'\s*'.join(re.escape(x) for x in query.split()),re.I) if query.strip() else None
    def candidates():
        if speakers:
            for shard in sorted((root/'indexes/turns').glob('*.jsonl')):
                if years and int(shard.stem) not in years: continue
                with shard.open(encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            turn=json.loads(line)
                            if turn['speaker'] in speakers and turn['meeting_id'] in selected: yield turn
        else:
            for row in selected.values(): yield {'meeting_id':row['id'],'start_line':row['body_start_line'],'end_line':None}
    cache={};results=[]
    for turn in candidates():
        row=selected[turn['meeting_id']]
        if row['id'] not in cache: cache[row['id']]=read(root,row)
        body='\n'.join(cache[row['id']][turn['start_line']-1:turn['end_line']])
        match=pattern.search(body) if pattern else None
        if pattern and not match: continue
        pos=match.start() if match else 0;end=match.end() if match else 0
        line=turn['start_line']+body[:pos].count('\n')
        results.append({'id':turn.get('id',row['id']),'meeting_id':row['id'],'date':row['date'],'title':row['title'],'speaker':turn.get('speaker'),'role':turn.get('role'),'publication_status':row.get('publication_status','unknown'),'path':row['path'],'line':line,'end_line':turn['end_line'],'excerpt':body[max(0,pos-100):end+350],'source_url':row['url'],'archive_url':'https://github.com/nankjh0110/cheongju-council-minutes/blob/main/'+row['path']+'#L'+str(line)})
    results.sort(key=lambda r:(r['date'],r['meeting_id'],r['line']),reverse=True)
    return {'scope':scope,'filters':{'query':query,'years':years,'speakers':speakers,'committee':committee},'unit':'speaker_segments' if speakers else 'meetings','total':len(results),'offset':offset,'returned':len(results[offset:offset+limit]),'by_speaker':dict(collections.Counter(r['speaker'] for r in results if r['speaker'])),'results':results[offset:offset+limit]}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('command',choices=['status','search','speeches','read']);p.add_argument('--query',default='');p.add_argument('--years',nargs='+',type=int);p.add_argument('--speakers',nargs='+');p.add_argument('--committee');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=20);p.add_argument('--meeting');p.add_argument('--start',type=int,default=1);a=p.parse_args()
    try: result=execute(a.repo.resolve(),a.command,a.query,a.years,a.speakers,a.committee,a.offset,a.limit,a.meeting,a.start)
    except (ValueError,OSError,KeyError) as e: p.exit(2,str(e)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
