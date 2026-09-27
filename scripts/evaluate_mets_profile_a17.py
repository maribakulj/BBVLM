"""A17: export and audit a MODS/PREMIS/image-linked METS package.

No recognition, layout, VLM or source annotation is consulted.  The public
source-image checksum is copied only after matching the A15 provenance event.
"""
from pathlib import Path
import hashlib
import json

from lxml import etree as E

from bbvlm import document as D
from bbvlm.__main__ import export_package
from bbvlm.formats import METS, MODS, PREMIS, XLINK, tag


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/loop/spiritualist-v1'
INPUT = BASE/'ink-extension-a16c-0044/package/document.json'
IMAGE = ROOT/'corpora/spiritualist/companion/Spiritualist_Images/0044.png'
OUT = BASE/'mets-profile-a17-0044'


def main():
    d = D.load(INPUT)
    pages = [n for n in d['nodes'] if n['kind'] == 'page']
    hashes = {e['source_image_sha256'] for e in d['events'] if e.get('source_image_sha256')}
    if len(pages) != 1 or len(hashes) != 1:
        raise ValueError('A17 requires one unambiguous page/image provenance hash')
    actual = hashlib.sha256(IMAGE.read_bytes()).hexdigest()
    expected = next(iter(hashes))
    if actual != expected:
        raise ValueError('restored public image does not match recorded provenance')
    pages[0]['image_sha256'] = actual
    pages[0]['image_size_bytes'] = IMAGE.stat().st_size
    d['events'].append({'type':'mets_profile_a17',
        'source':'existing graph plus verified public source-image bytes',
        'changes':'MODS projection, PREMIS fixity, image/OCR physical pointers',
        'recognition_passes':0,'layout_passes':0,'vlm_passes':0})
    package = export_package(d, OUT/'package', ROOT/'schemas')
    root = E.parse(str(OUT/'package/mets.xml'))
    groups = {g.get('USE'): [f.get('ID') for f in g.findall(tag(METS,'file'))]
              for g in root.findall('.//'+tag(METS,'fileGrp'))}
    physical = root.findall(".//"+tag(METS,'structMap')+"[@TYPE='PHYSICAL']//"+tag(METS,'div')+"[@TYPE='page']")
    pointers = [[p.get('FILEID') for p in div.findall(tag(METS,'fptr'))] for div in physical]
    image_file = root.find(".//"+tag(METS,'file')+"[@ID='FILE_IMAGE_P0001']")
    href = image_file.find(tag(METS,'FLocat')).get(tag(XLINK,'href'))
    report = {
        'schema':'bbvlm.mets-profile-a17/1',
        'status':'profile_export_complete_with_declared_limit',
        'scope':'A16c consumed partial page; packaging/provenance only',
        'input_graph_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        'source_image_sha256_verified_before_export':actual,
        'file_groups':groups, 'physical_page_fileids':pointers,
        'mods_identifier':root.findtext('.//'+tag(MODS,'identifier')),
        'premis_objects':len(root.findall('.//'+tag(PREMIS,'object'))),
        'premis_events':len(root.findall('.//'+tag(PREMIS,'event'))),
        'image_href_matches_graph':href == pages[0]['image'],
        'package':package,
        'passes':{'layout':0,'recognition':0,'vlm':0},
        'accepted_for_project_completion_gate':False,
        'limitations':[
            'MODS 3.8 official XSD could not be retrieved through the upstream 403; local profile structure is checked but standalone MODS XSD validation remains false',
            'the remote image checksum is verified against restored bytes during A17, but the portable package intentionally omits the public image bytes',
            'the source graph has no independently sourced bibliographic title/date/authority record, so MODS contains only a local identifier and explicit automatic record provenance',
            'METS/PREMIS validity and fixity do not certify OCR, geometry, OLR or metadata truth'
        ]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
