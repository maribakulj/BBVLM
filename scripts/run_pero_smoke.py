from pathlib import Path
import sys,time,configparser,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch,cv2
from pero_ocr.core.layout import PageLayout
from pero_ocr.document_ocr.page_parser import PageParser
from bbvlm.pero import save_cache
root=Path(__file__).resolve().parents[1]
model=root/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
c=configparser.ConfigParser();c.read(model/'config_cpu.ini')
c['PAGE_PARSER']['RUN_LAYOUT_PARSER']='no'
torch.set_num_threads(4)
start=time.monotonic();parser=PageParser(c,device=torch.device('cpu'),config_path=str(model));print('loaded',round(time.monotonic()-start,2),flush=True)
page=PageLayout(file=str(root/'experiments/terra_luna/reference/page.xml'))
for region in page.regions:region.lines=region.lines[:3]
refs={l.id:l.transcription for l in page.lines_iterator()}
image=cv2.imread(str(root/'experiments/terra_luna/input/page.jpg'))
page=parser.process_page(image,page)
out=root/'experiments/loop/pero_smoke';out.mkdir(parents=True,exist_ok=True)
save_cache(page,out,'PERO public eu/cz newspapers 2022-09-26')
rows=[dict(id=l.id,reference=refs[l.id],text=l.transcription) for l in page.lines_iterator()]
(out/'recognition.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
page.to_altoxml(str(out/'native.alto.xml'))
print('lines',len(rows),'total_seconds',round(time.monotonic()-start,2),flush=True)
