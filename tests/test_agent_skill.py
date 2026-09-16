import importlib.util,json,hashlib,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('agent_query',ROOT/'skills/cheongju-council-minutes/scripts/query.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
class AgentSkillTests(unittest.TestCase):
 def test_search_read_attribution_and_integrity(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'minutes').mkdir();(root/'indexes/turns').mkdir(parents=True)
   rows=[]
   for year in (2024,2025):
    raw='# 회의\n## ○가의원 위원\n어린이 물놀이장 안전\n## ○나의원 위원\n계약 검토\n'.encode();path=f'minutes/{year}.md';(root/path).write_bytes(raw)
    rows.append(dict(id=f'minutes-{year}',path=path,sha256=hashlib.sha256(raw).hexdigest(),body_start_line=1,year=year,date=f'{year}-01-01',committee='C101',title='합성 위원회',url='https://example.invalid',publication_status='provisional'))
    turns=[dict(id=f'{year}-a',meeting_id=f'minutes-{year}',speaker='가의원',role='위원',start_line=2,end_line=3),dict(id=f'{year}-b',meeting_id=f'minutes-{year}',speaker='나의원',role='위원',start_line=4,end_line=5)]
    (root/f'indexes/turns/{year}.jsonl').write_text('\n'.join(json.dumps(t) for t in turns))
   (root/'manifest.json').write_text(json.dumps({'collected':2}));(root/'indexes/meetings.json').write_text(json.dumps(rows));(root/'indexes/speakers.json').write_text('[]')
   self.assertEqual(q.execute(root,'search',query='물놀이장',years=[2025])['total'],1)
   self.assertEqual(q.execute(root,'search',query='물놀이장',speakers=['나의원'])['total'],0)
   result=q.execute(root,'speeches',speakers=['가의원','나의원'],limit=1,offset=1)
   self.assertEqual(result['total'],4);self.assertEqual(result['returned'],1);self.assertEqual(result['by_speaker'],{'가의원':2,'나의원':2})
   self.assertEqual(result['results'][0]['publication_status'],'provisional')
   result=q.execute(root,'read',meeting='minutes-2025',start=3,limit=1)
   self.assertEqual(result['lines'][0],{'line':3,'text':'어린이 물놀이장 안전'})
   with self.assertRaises(ValueError):q.execute(root,'read',meeting='../../private')
   (root/'minutes/2025.md').write_text('tampered')
   with self.assertRaises(ValueError):q.execute(root,'read',meeting='minutes-2025')
 def test_distribution_is_self_contained(self):
  spec=importlib.util.spec_from_file_location('package',ROOT/'scripts/package_skill.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'skill.zip';p.package(path)
   with zipfile.ZipFile(path) as z:
    self.assertEqual(len(z.namelist()),4);self.assertIn('cheongju-council-minutes/scripts/query.py',z.namelist())
    z.extractall(Path(folder)/'unpacked')
   import subprocess,sys
   r=subprocess.run([sys.executable,str(Path(folder)/'unpacked/cheongju-council-minutes/scripts/query.py'),'--help'],capture_output=True)
   self.assertEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
