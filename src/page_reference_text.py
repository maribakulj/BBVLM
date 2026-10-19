"""Références textuelles entières, réservées exclusivement à l'évaluation."""
from pathlib import Path
import re
from lxml import etree
from evaluation import load_reference, nfc


def load_page_reference(path, dpi=None):
    root=etree.parse(str(path)).getroot()
    if etree.QName(root).localname.lower()=='alto':
        lines=load_reference(path,dpi=dpi)
        return lines,dict(loader_revision=2,scope='all_ALTO_TextLine',
                          nonempty_lines=len(lines),reference_order='ALTO_document_order')
    all_lines=root.findall('.//{*}TextLine')
    regions=[r for r in root.iter() if isinstance(r.tag,str) and etree.QName(r).localname in ('TextRegion','TableRegion')]
    refs=root.findall('.//{*}ReadingOrder//{*}RegionRefIndexed')
    ordered_ids=[r.get('regionRef') for r in sorted(refs,key=lambda r:int(r.get('index')))]
    def key(region):
        if region.get('id') in ordered_ids:return ordered_ids.index(region.get('id'))
        match=re.search(r'readingOrder\s*\{\s*index:\s*(\d+)',region.get('custom',''))
        return len(ordered_ids)+(int(match[1]) if match else regions.index(region))
    result=[];seen=set();empty=0;missing_coordinates=0
    unreferenced_tables=[]
    def add(line,region_type):
        nonlocal empty,missing_coordinates
        if line in seen:return
        seen.add(line)
        text=line.findtext('{*}TextEquiv/{*}Unicode')
        if text is None:
            text=' '.join(w.findtext('{*}TextEquiv/{*}Unicode') or '' for w in line.findall('{*}Word'))
        text=nfc(text.strip())
        if not text:empty+=1;return
        if line.find('{*}Coords') is None:missing_coordinates+=1
        result.append(dict(id=line.get('id') or f'reference_line_{len(result)+1}',
                           text=text,reference_region_type=region_type))
    for region in sorted(regions,key=key):
        kind=etree.QName(region).localname
        if kind=='TableRegion' and region.get('id') not in ordered_ids:
            unreferenced_tables.append(region.get('id'))
        # Les TableCell sont parcourues ; aucune ligne n'est éliminée pour
        # absence de coordonnées dans cette notation exclusivement textuelle.
        for line in region.findall('.//{*}TextLine'):add(line,kind)
    outside=[]
    for line in all_lines:
        if line not in seen:
            outside.append(line.get('id'));add(line,'outside_TextRegion_TableRegion')
    duplicates=[];ids=set()
    for line in result:
        if line['id'] in ids:duplicates.append(line['id'])
        ids.add(line['id'])
    audit=dict(loader_revision=2,scope='all_nonempty_PAGE_TextLine_including_TableCell',
               xml_text_lines=len(all_lines),nonempty_lines=len(result),empty_lines=empty,
               lines_without_coordinates=missing_coordinates,duplicate_ids=duplicates,
               table_lines=sum(r['reference_region_type']=='TableRegion' for r in result),
               tables_absent_from_explicit_reading_order=unreferenced_tables,
               lines_outside_text_table_regions=outside,
               reference_order='explicit_REGION_order_then_custom_then_document',
               order_incomplete=bool(unreferenced_tables or outside))
    return result,audit
