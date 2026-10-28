import sys, tempfile, unittest, json
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import sync

class SyncTests(unittest.TestCase):
    def row(self,id='minutes-1'):
        return dict(id=id,title='시험 회의',date='2025-01-01',year=2025,term=3,committee='C101',publication_status='published',url=sync.BASE+'/minutes/svc/web/cms/mnts/SvcMntsViewer.php?schSn=1')
    def test_union_keeps_term_only(self):
        a,b=self.row(),self.row('minutes-2')
        self.assertEqual(len(sync.merge_inventories([a],[a,b],{})),2)
    def test_disappearance_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([self.row()],[self.row()],{'minutes-2':{}})
    def test_finalized_record_supersedes_provisional(self):
        provisional=dict(self.row(),publication_status='provisional')
        published=self.row('minutes-2')
        replaced={}
        live=sync.merge_inventories([published],[published],{'minutes-1':provisional},replaced)
        self.assertEqual(set(live),{'minutes-2'})
        self.assertEqual(replaced,{'minutes-1':'minutes-2'})
    def test_unmatched_provisional_disappearance_fails(self):
        provisional=dict(self.row(),publication_status='provisional')
        other=dict(self.row('minutes-2'),title='다른 회의')
        with self.assertRaises(ValueError): sync.merge_inventories([other],[other],{'minutes-1':provisional})
    def test_ambiguous_finalized_candidates_fail(self):
        old={'minutes-1':dict(self.row(),publication_status='provisional')}
        candidates=[self.row('minutes-2'),self.row('minutes-3')]
        with self.assertRaises(ValueError): sync.merge_inventories(candidates,candidates,old)
    def test_two_provisionals_cannot_share_one_replacement(self):
        old={key:dict(self.row(key),publication_status='provisional') for key in ('minutes-1','minutes-2')}
        with self.assertRaises(ValueError): sync.merge_inventories([self.row('minutes-3')],[self.row('minutes-3')],old)
    def test_other_date_or_committee_is_not_a_replacement(self):
        old={'minutes-1':dict(self.row(),publication_status='provisional')}
        for change in ({'date':'2025-01-02'},{'committee':'C501'}):
            with self.subTest(change=change):
                other=dict(self.row('minutes-2'),**change)
                with self.assertRaises(ValueError): sync.merge_inventories([other],[other],old)
    def test_published_disappearance_still_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([self.row('minutes-2')],[self.row('minutes-2')],{'minutes-1':self.row()})
    def test_empty_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([],[],{})
    def test_conflict_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([self.row()],[dict(self.row(),date='2024-01-01')],{})
    def test_error_page_rejected(self):
        with self.assertRaises(ValueError): sync.extract('<html>Service unavailable</html>')
    def test_unopened_meeting(self):
        text='청주시의회 본회의 의사일정 '+('안건 '*40)+'(개의되지 않음)'
        self.assertEqual(sync.extract('<!-- 회의록내용 -->'+text+'<!--// 회의록내용 -->'),text)
    def test_full_pipeline_and_failed_fetch_preserves_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            (root/'minutes').mkdir();(root/'indexes').mkdir()
            (root/'indexes/meetings.json').write_text('[]',encoding='utf-8')
            (root/'manifest.json').write_text(json.dumps({'startDate':'2022-07-01'}),encoding='utf-8')
            (root/'README.md').write_text('<!-- archive-status --><!-- /archive-status -->',encoding='utf-8')
            html='<!-- 회의록내용 -->○위원장 홍길동\n'+('시설 점검 요청. '*40)+'<!--// 회의록내용 -->'
            with patch.object(sync,'ROOT',root),patch.object(sync,'inventory',return_value=[self.row()]),patch.object(sync,'fetch',return_value=html):
                sync.run('full')
            baseline=(root/'indexes/meetings.json').read_bytes()
            self.assertEqual(json.loads((root/'manifest.json').read_text(encoding='utf-8'))['collected'],1)
            with patch.object(sync,'ROOT',root),patch.object(sync,'inventory',return_value=[self.row()]),patch.object(sync,'fetch',side_effect=OSError('offline')):
                with self.assertRaises(RuntimeError): sync.run('full')
            self.assertEqual((root/'indexes/meetings.json').read_bytes(),baseline)
    def test_pipeline_replaces_finalized_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            (root/'minutes').mkdir();(root/'indexes').mkdir()
            (root/'indexes/meetings.json').write_text('[]',encoding='utf-8')
            (root/'manifest.json').write_text(json.dumps({'startDate':'2022-07-01'}),encoding='utf-8')
            (root/'README.md').write_text('<!-- archive-status --><!-- /archive-status -->',encoding='utf-8')
            html='<!-- 회의록내용 -->○위원장 홍길동\n'+('시설 점검 요청. '*40)+'<!--// 회의록내용 -->'
            provisional=dict(self.row(),publication_status='provisional')
            with patch.object(sync,'ROOT',root),patch.object(sync,'inventory',return_value=[provisional]),patch.object(sync,'fetch',return_value=html):
                sync.run('full')
            old_path=root/json.loads((root/'indexes/meetings.json').read_text(encoding='utf-8'))[0]['path']
            self.assertTrue(old_path.exists())
            baseline=(root/'indexes/meetings.json').read_bytes()
            with patch.object(sync,'ROOT',root),patch.object(sync,'inventory',return_value=[self.row('minutes-2')]),patch.object(sync,'fetch',side_effect=OSError('offline')):
                with self.assertRaises(RuntimeError): sync.run('incremental')
            self.assertTrue(old_path.exists())
            self.assertEqual((root/'indexes/meetings.json').read_bytes(),baseline)
            with patch.object(sync,'ROOT',root),patch.object(sync,'inventory',return_value=[self.row('minutes-2')]),patch.object(sync,'fetch',return_value=html):
                sync.run('incremental')
            rows=json.loads((root/'indexes/meetings.json').read_text(encoding='utf-8'))
            self.assertEqual([r['id'] for r in rows],['minutes-2'])
            self.assertFalse(old_path.exists())
            self.assertEqual(json.loads((root/'reports/latest-sync.json').read_text(encoding='utf-8'))['superseded'],{'minutes-1':'minutes-2'})
    def test_body_and_updates(self):
        html='<!-- 회의록내용 --><p>○위원장 홍길동</p><p>'+('시설 점검을 요청합니다. '*20)+'</p><!--// 회의록내용 -->'
        text=sync.extract(html)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);row=self.row()
            first=sync.update_record(root,row,None,text,'2026-09-16')
            original=(root/first['path']).read_bytes()
            self.assertNotIn(b'\r\n',original)
            self.assertEqual(sync.build.digest(original),first['sha256'])
            second=sync.update_record(root,row,first,text,'2026-09-17')
            self.assertEqual(original,(root/first['path']).read_bytes())
            self.assertEqual(first['sha256'],second['sha256'])
            third=sync.update_record(root,row,second,text+'\n추가 발언입니다.','2026-09-18')
            self.assertNotEqual(second['sha256'],third['sha256'])
            finalized=sync.update_record(root,dict(row,publication_status='published'),dict(third,publication_status='provisional'),text+'\n추가 발언입니다.','2026-09-19')
            self.assertEqual(finalized['publication_status'],'published')
if __name__=='__main__': unittest.main()
