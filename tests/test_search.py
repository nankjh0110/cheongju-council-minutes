import importlib.util,tempfile,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('search',Path(__file__).resolve().parents[1]/'scripts/search.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class SearchTest(unittest.TestCase):
 def test_filters_and_attribution(self):
  with tempfile.TemporaryDirectory() as d:
   old=s.ROOT;s.ROOT=Path(d);(s.ROOT/'indexes/turns').mkdir(parents=True);rows=[];turns=[]
   try:
    for year in [2024,2025]:
     path=f'{year}.md';(s.ROOT/path).write_text('# 합성\n## ○가의원 위원\n어린이 물놀이장 점검\n## ○나의원 위원\n예산 확인\n');rows.append({'id':str(year),'path':path,'date':f'{year}-01-01','year':year,'term':3,'committee':'C','title':'합성 회의','url':'https://example.invalid','body_start_line':1});turns.append({'id':str(year)+'a','meeting_id':str(year),'speaker':'가의원','role':'위원','start_line':2,'end_line':3});turns.append({'id':str(year)+'b','meeting_id':str(year),'speaker':'나의원','role':'위원','start_line':4,'end_line':5})
    (s.ROOT/'indexes/meetings.json').write_text(json.dumps(rows))
    for year in [2024,2025]:(s.ROOT/f'indexes/turns/{year}.jsonl').write_text('\n'.join(json.dumps(t) for t in turns if t['meeting_id']==str(year)))
    self.assertEqual(s.search('어린이 물놀이장')['total'],2);self.assertEqual(s.search('어린이 물놀이장',years=[2025])['total'],1);self.assertEqual(s.search('물놀이장',speaker='나의원')['total'],0);self.assertEqual(s.search('물놀이장',speaker='가의원')['total'],2);self.assertEqual(s.search('[?]')['total'],0);self.assertEqual(s.search('물놀이장',limit=1,offset=1)['returned'],1)
   finally:s.ROOT=old
if __name__=='__main__':unittest.main()
