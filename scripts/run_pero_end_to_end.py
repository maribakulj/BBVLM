"""Native full-page PERO baseline: no reference geometry or text enters inference."""
from pathlib import Path
import sys,json,time,configparser
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2,torch
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser
from bbvlm.pero import save_cache
ROOT=Path(__file__).resolve().parents[1]
model=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
c=configparser.ConfigParser();c.read(model/'config_cpu.ini');torch.set_num_threads(4)
p=PageParser(c,device=torch.device('cpu'),config_path=str(model))
for page_id in ['0253902-001','0401692-003','752234-003']:
    out=ROOT/'experiments/loop/end-to-end'/page_id
    if (out/'run.json').exists():continue
    source=json.loads((ROOT/'experiments/loop/cache'/page_id/'run.json').read_text())
    image=cv2.imread(str(ROOT/source['image']));start=time.monotonic()
    page=p.process_page(image,PageLayout(id=page_id,page_size=image.shape[:2]));out.mkdir(parents=True,exist_ok=True)
    save_cache(page,out,'PERO 0.7.0; public eu/cz newspapers 2022-09-26; full-page inference')
    (out/'native.alto.xml').write_text(page.to_altoxml_string())
    report={'image':source['image'],'image_sha256':source['image_sha256'],'seconds':time.monotonic()-start,'regions':len(page.regions),'lines':sum(1 for _ in page.lines_iterator()),'reference_inputs':False}
    (out/'run.json').write_text(json.dumps(report,indent=2));print(page_id,report,flush=True)
