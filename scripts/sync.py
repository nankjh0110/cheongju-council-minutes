"""Refresh the public archive from BOTH official inventories. No credentials needed."""
import argparse, collections, concurrent.futures, datetime as dt, json, re, shutil
import tempfile, time, urllib.parse, urllib.request, ssl
from html.parser import HTMLParser
from pathlib import Path
import build, validate
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://councilrec.cheongju.go.kr'
# Official server needs RSA TLS 1.2 suites omitted by Python 3.12 defaults.
# Keep certificate/hostname verification and TLS >= 1.2 enabled.
TLS = ssl.create_default_context()
TLS.minimum_version = ssl.TLSVersion.TLSv1_2
TLS.set_ciphers('DEFAULT')

def fetch(url, params=None):
    for attempt in range(3):
        try:
            time.sleep(.2)
            request = urllib.request.Request(url, None if params is None else urllib.parse.urlencode(params).encode(), headers={'User-Agent': 'CheongjuMinutesArchive/1.0 (+https://github.com/nankjh0110/cheongju-council-minutes)'})
            with urllib.request.urlopen(request, timeout=40, context=TLS) as response:
                return response.read().decode('utf-8-sig')
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)

def inventory(kind, today):
    endpoint = BASE + '/minutes/svc/web/cms/mnts/SvcMntsTree' + kind + '.php'
    def tree(node):
        rows = json.loads(fetch(endpoint, {k:v for k,v in node.items() if k.startswith('var')}))
        if not isinstance(rows, list): raise ValueError('Invalid official inventory')
        return rows
    def branch(node, depth=0):
        if depth > 8: raise ValueError('Unexpected tree depth')
        out = []
        for child in tree(node):
            if child.get('var12'):
                title = node['text'] + ' ' + child['text']
                match = re.search(r'(20\d{2})\.(\d{2})\.(\d{2})', title)
                if not match or not str(child['var12']).isdigit(): raise ValueError('Invalid meeting metadata')
                date = dt.date(*map(int, match.groups())).isoformat()
                if '2022-07-01' <= date <= min(today, '2030-06-30'):
                    if child.get('var09') not in ('Y','N'): raise ValueError('Unknown publication status')
                    out.append(dict(id='minutes-'+str(child['var12']), title=title, date=date, year=int(date[:4]), term=3 if date<'2026-07-01' else 4, committee=child['var02'], publication_status='provisional' if child['var09']=='N' else 'published', url=BASE+'/minutes/svc/web/cms/mnts/SvcMntsViewer.php?schSn='+str(child['var12'])))
            else: out.extend(branch(child, depth+1))
        return out
    roots = tree({'var10':'SvcMntsTree'+kind+'Gnrtn'})
    selected = [n for n in roots if (str(n.get('var01')) in ('3','4') if kind=='Gnrtn' else str(n.get('var01','')).isdigit() and 2022<=int(n['var01'])<=min(int(today[:4]),2030))]
    if not selected: raise ValueError('Empty official roots')
    out=[]
    for node in selected:
        rows=branch(node)
        if kind=='Gnrtn' and any(r['term']!=int(node['var01']) for r in rows): raise ValueError('Term/date mismatch')
        out.extend(rows)
    return out

def merge_inventories(year, term, old):
    if not year or not term: raise ValueError('Empty inventory; refusing update')
    merged={}
    for row in year+term:
        prior=merged.get(row['id'])
        if prior and any(prior[k]!=row[k] for k in ('date','committee','publication_status')): raise ValueError('Conflicting inventory: '+row['id'])
        merged[row['id']]=row
    missing=set(old)-set(merged)
    if missing: raise ValueError('Existing records disappeared; manual review required: '+','.join(sorted(missing)))
    return merged

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
        if tag in ('p','br','tr','div'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
        if tag in ('p','div'): self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def extract(raw):
    match=re.search(r'<!-- 회의록내용 -->([\s\S]*?)(?:<!--// 회의록내용|<!-- //회의록내용|<div class="pageTopBtn")',raw)
    if match: section=match[1]
    else:
        start=raw.find("<div id='anh'>"); end=raw.find('<!--// minutesContent',start)
        if start<0 or end<start: raise ValueError('Missing official minutes body')
        section=raw[start:end]
    parser=Plain(); parser.feed(section)
    text=re.sub(r'\n\s*\n+','\n\n',''.join(parser.parts)).strip()
    if len(text)<100 or '○' not in text: raise ValueError('Empty or unexpected minutes body')
    return text

def canonical(text):
    return re.sub(r'\s+',' ',re.sub(r'(?m)^##\s+(?=○)','',text)).strip()

def update_record(root, row, old, text, now):
    result={**(old or {}),**row}
    if text is None: return result
    content_hash=build.digest(canonical(text).encode())
    unchanged=old and old.get('content_sha256')==content_hash
    if old and 'content_sha256' not in old:
        body=(root/old['path']).read_text().split('---\n',2)[2].lstrip('\n')
        # Compare the entire official body, including agenda and meeting header.
        legacy=re.sub(r'\A# [^\n]*\n\n(?:- [^\n]*\n)+\n','',body,count=1)
        unchanged=canonical(legacy)==canonical(text)
    result.update(content_sha256=content_hash, body_checked_at=now)
    if unchanged: return result
    source=f'# {row["title"]}\n\n- 출처: {row["url"]}\n- 회의일: {row["date"]}\n- 수집일: {now}\n- 원문 식별자: {row["id"].split("-")[1]}\n- 의회 대수: 제{row["term"]}대\n\n'+re.sub(r'(?m)^○','## ○',text)+'\n'
    meta={k:row[k] for k in ('id','title','date','year','term','committee','url')};meta['source_sha256']=build.digest(source.encode())
    front='---\n'+''.join(f'{k}: {json.dumps(v,ensure_ascii=False)}\n' for k,v in meta.items())+'---\n\n'
    payload=(front+source).encode(); path=f'minutes/term-{row["term"]}/{row["year"]}/{row["id"]}.md'
    build.save(root/path,payload.decode())
    result.update(meta,path=path,sha256=build.digest(payload),bytes=len(payload),body_start_line=front.count('\n')+1)
    return result

def run(mode):
    now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9))); today=now.date().isoformat(); stamp=now.isoformat()
    if mode=='auto': mode='full' if now.weekday()==0 else 'incremental'
    old={r['id']:r for r in json.loads((ROOT/'indexes/meetings.json').read_text())}
    print('Reading both official inventories...',flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        yf=pool.submit(inventory,'Year',today); tf=pool.submit(inventory,'Gnrtn',today)
        years,terms=yf.result(),tf.result()
    live=merge_inventories(years,terms,old)
    needed=[r for r in live.values() if mode=='full' or r['id'] not in old or old[r['id']].get('publication_status')!='published' or r['publication_status']=='provisional']
    print(f'{len(live)} listed; checking {len(needed)} bodies ({mode})',flush=True)
    def download(row): return row['id'],extract(fetch(row['url']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        bodies={}
        for i,(key,value) in enumerate(pool.map(download,needed),1):
            bodies[key]=value
            if i%50==0: print(f'Checked {i}/{len(needed)}',flush=True)
    # All network operations must succeed before touching the working archive.
    with tempfile.TemporaryDirectory(prefix='minutes-sync-') as temp:
        stage=Path(temp)
        for directory in ('minutes','indexes'): shutil.copytree(ROOT/directory,stage/directory)
        rows=[update_record(stage,r,old.get(r['id']),bodies.get(r['id']),stamp) for r in sorted(live.values(),key=lambda r:(r['date'],r['id']))]
        manifest=json.loads((ROOT/'manifest.json').read_text())
        manifest.update(endDate=today,checkedAt=stamp,latestMeetingDate=max(r['date'] for r in rows),listed=len(rows),collected=len(rows),byYear=dict(collections.Counter(str(r['year']) for r in rows)),byTerm=dict(collections.Counter(str(r['term']) for r in rows)),provisional=sum(r['publication_status']=='provisional' for r in rows))
        report=dict(checkedAt=stamp,mode=mode,collected=len(rows),new=sorted(set(live)-set(old)),changed=[r['id'] for r in rows if r['id'] in old and r['sha256']!=old[r['id']]['sha256']],bodiesChecked=len(bodies),provisional=manifest['provisional'],onlyTerm=sorted({r['id'] for r in terms}-{r['id'] for r in years}),onlyYear=sorted({r['id'] for r in years}-{r['id'] for r in terms}))
        for path,obj in [('indexes/meetings.json',rows),('manifest.json',manifest),('reports/latest-sync.json',report)]: build.save(stage/path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
        previous_build,previous_validate=build.ROOT,validate.ROOT
        try:
            build.ROOT=validate.ROOT=stage;build.reindex();validate.validate()
        finally: build.ROOT,validate.ROOT=previous_build,previous_validate
        for file in stage.rglob('*'):
            if file.is_file():
                target=ROOT/file.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
    readme=(ROOT/'README.md').read_text()
    status=f'<!-- archive-status -->\n최종 확인: **{today}** · **{len(rows)}건** (제3대 {manifest["byTerm"].get("3",0)}건 / 제4대 {manifest["byTerm"].get("4",0)}건). 임시회의록 {manifest["provisional"]}건 포함. 가장 최근 회의일: {manifest["latestMeetingDate"]}.\n<!-- /archive-status -->'
    readme=re.sub(r'<!-- archive-status -->[\s\S]*?<!-- /archive-status -->',lambda _:status,readme)
    build.save(ROOT/'README.md',readme);print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['auto','incremental','full'],default='incremental');run(parser.parse_args().mode)
