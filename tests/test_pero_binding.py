import unittest
from types import SimpleNamespace as S
from lxml import etree as E
from bbvlm.pero import bind_native_alto_ids

class NativeBindingTests(unittest.TestCase):
    def fixture(self):
        xml=b'<alto xmlns="urn:test"><TextBlock ID="block_R"><TextLine HPOS="1" VPOS="2" WIDTH="9" HEIGHT="8"><String CONTENT="abc"/></TextLine></TextBlock></alto>'
        r=S(id='R',lines=[S(id='Lopaque',transcription='abc',polygon=[[1,2],[10,2],[10,10],[1,10]])])
        return xml,[r]

    def test_binds_line_and_word_ids(self):
        xml,regions=self.fixture();root=E.fromstring(bind_native_alto_ids(xml,regions))
        self.assertEqual(root.find('.//{*}TextLine').get('ID'),'Lopaque')
        self.assertEqual(root.find('.//{*}String').get('ID'),'Lopaque_W0001')

    def test_rejects_changed_text_count_or_geometry(self):
        for old,new in [(b'abc',b'abd'),(b'WIDTH="9"',b'WIDTH="8"'),(b'block_R',b'block_S')]:
            xml,regions=self.fixture()
            with self.assertRaises(ValueError):bind_native_alto_ids(xml.replace(old,new),regions)
        xml,regions=self.fixture();regions[0].lines.append(regions[0].lines[0])
        with self.assertRaises(ValueError):bind_native_alto_ids(xml,regions)
