"""Recognize the fixed word-annotated pages once, with reference line geometry.

No word coordinates enter PERO. Cache is reusable across geometric experiments.
This is an oracle-line experiment, not end-to-end page segmentation evaluation.
"""
from pathlib import Path
import sys,json,time,configparser,argparse,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2,torch
from lxml import etree as E
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser
from bbvlm.pero import save_cache

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--pages',nargs='*');args=ap.parse_args()
model=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
config=configparser.ConfigParser();config.read(model/'config_cpu.ini')
config['PAGE_PARSER']['RUN_LAYOUT_PARSER']='no'
torch.set_num_threads(4)
parser=PageParser(config,device=torch.device('cpu'),config_path=str(model))
for xml in sorted((ROOT/'corpora/newseye-validation').rglob('*.xml')):
    if args.pages and xml.stem not in args.pages:continue
    r=E.parse(str(xml));ns={'p':r.getroot().nsmap[None]}
    if not r.findall('.//p:Word',ns):continue
    out=ROOT/'experiments/loop/cache'/xml.stem
    if (out/'cache.json').exists():print('cached',xml.stem,flush=True);continue
    image=next(p for p in [xml.with_suffix('.tif'),xml.with_suffix('.jpg'),xml.with_suffix('.png')] if p.exists())
    page=PageLayout(file=str(xml))
    ids={l.id for l in page.lines_iterator()}
    expected={l.get('id') for l in r.findall('.//p:TextLine',ns)}
    missing=sorted(expected-ids)
    t=time.monotonic();page=parser.process_page(cv2.imread(str(image)),page)
    elapsed=time.monotonic()-t
    save_cache(page,out,'PERO public eu/cz newspapers 2022-09-26; pero-ocr 0.7.0')
    (out/'run.json').write_text(json.dumps({'source_xml':str(xml.relative_to(ROOT)),
        'image':str(image.relative_to(ROOT)),'xml_sha256':hashlib.sha256(xml.read_bytes()).hexdigest(),
        'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'lines':len(ids),
        'reference_lines_missing_from_pero':missing,'seconds':elapsed,'threads':4,
        'layout_input':'reference line polygons and baselines; no word coordinates'},indent=2))
    print(xml.stem,'lines',len(ids),'seconds',round(elapsed,2),'missing',len(missing),flush=True)
