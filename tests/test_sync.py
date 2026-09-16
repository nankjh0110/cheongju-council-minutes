import sys, tempfile, unittest
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
    def test_empty_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([],[],{})
    def test_conflict_fails(self):
        with self.assertRaises(ValueError): sync.merge_inventories([self.row()],[dict(self.row(),date='2024-01-01')],{})
    def test_error_page_rejected(self):
        with self.assertRaises(ValueError): sync.extract('<html>Service unavailable</html>')
    def test_body_and_updates(self):
        html='<!-- 회의록내용 --><p>○위원장 홍길동</p><p>'+('시설 점검을 요청합니다. '*20)+'</p><!--// 회의록내용 -->'
        text=sync.extract(html)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);row=self.row()
            first=sync.update_record(root,row,None,text,'2026-09-16')
            original=(root/first['path']).read_bytes()
            second=sync.update_record(root,row,first,text,'2026-09-17')
            self.assertEqual(original,(root/first['path']).read_bytes())
            self.assertEqual(first['sha256'],second['sha256'])
            third=sync.update_record(root,row,second,text+'\n추가 발언입니다.','2026-09-18')
            self.assertNotEqual(second['sha256'],third['sha256'])
            finalized=sync.update_record(root,dict(row,publication_status='published'),dict(third,publication_status='provisional'),text+'\n추가 발언입니다.','2026-09-19')
            self.assertEqual(finalized['publication_status'],'published')
if __name__=='__main__': unittest.main()
