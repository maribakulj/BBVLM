import tempfile,unittest,json
from pathlib import Path
from bbvlm.retrieval import build_index,search
from bbvlm.__main__ import export_package
from test_document_workflow import sample,ROOT

class RetrievalTests(unittest.TestCase):
    def test_diplomatic_evidence_is_unchanged_and_index_is_rebuildable(self):
        d=sample();d['nodes'][2]['text']='Präſident Frei⸗';d['nodes'][2]['needs_alignment']=True
        with tempfile.TemporaryDirectory() as t:
            db=Path(t)/'search.sqlite';build_index(d,db)
            hit=search(db,'Präsident')[0]
            self.assertEqual(hit['text'],'Präſident Frei⸗')
            self.assertEqual(hit['evidence']['line'],'L1')
            self.assertTrue(hit['evidence']['needs_alignment'])
            self.assertEqual(search(db,'Prasident'),[])
            d['nodes'][2]['text']='changed';build_index(d,db)
            self.assertEqual(search(db,'Präsident'),[])
    def test_export_links_index_and_query_does_not_accept_fts_operators(self):
        with tempfile.TemporaryDirectory() as t:
            export_package(sample(),t,ROOT/'schemas')
            self.assertIn('retrieval.sqlite',(Path(t)/'mets.xml').read_text())
            self.assertEqual(search(Path(t)/'retrieval.sqlite','hello OR absent'),[])
            self.assertEqual(len(search(Path(t)/'retrieval.sqlite','hello')),1)
if __name__=='__main__':unittest.main()
