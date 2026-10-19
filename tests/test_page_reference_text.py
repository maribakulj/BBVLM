from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from page_reference_text import load_page_reference


def test_full_page_text_includes_table_cells_without_fabricating_reference_order(tmp_path):
    path=tmp_path/'reference.xml'
    path.write_text('''<PcGts xmlns="urn:page"><Page><ReadingOrder><OrderedGroup>
      <RegionRefIndexed index="0" regionRef="text"/></OrderedGroup></ReadingOrder>
      <TextRegion id="text"><TextLine id="a"><TextEquiv><Unicode>Texte.</Unicode></TextEquiv></TextLine></TextRegion>
      <TableRegion id="table" custom="readingOrder {index: 9;}"><TableCell>
      <TextLine id="b"><TextEquiv><Unicode>12 34</Unicode></TextEquiv></TextLine>
      <TextLine id="empty"><TextEquiv><Unicode> </Unicode></TextEquiv></TextLine>
      </TableCell></TableRegion></Page></PcGts>''')
    lines,audit=load_page_reference(path)
    assert [(r['id'],r['text']) for r in lines]==[('a','Texte.'),('b','12 34')]
    assert audit['table_lines']==1 and audit['empty_lines']==1
    assert audit['lines_without_coordinates']==2
    assert audit['order_incomplete'] is True
    assert audit['tables_absent_from_explicit_reading_order']==['table']
