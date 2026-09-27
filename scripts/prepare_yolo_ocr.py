"""A13 blind OCR probe on predicted paragraph crops; never reads source XML."""
from pathlib import Path
import hashlib,json,math,random,time
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop/spiritualist-v1'
OUT=BASE/'yolo-ocr-a13-0044'

def main():
    image=ROOT/'corpora/spiritualist/companion/Spiritualist_Images/0044.png'
    detector=BASE/'doclayout-yolo-pilot-0044/report.json'
    preds=json.loads(detector.read_text())['predicted']
    eligible=[(i,p) for i,p in enumerate(preds)
              if p['class_name']=='plain text' and 80<=p['bbox'][3]-p['bbox'][1]<=260]
    chosen=random.Random(2026092713).sample(eligible,3)
    im=Image.open(image).convert('RGB');out=OUT/'input';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i,p in chosen:
        token='R'+hashlib.sha256(f'a13-0044-{i}'.encode()).hexdigest()[:8]
        x0,y0,x1,y1=p['bbox']
        crop=[max(0,math.floor(x0)-4),max(0,math.floor(y0)-2),
              min(im.width,math.ceil(x1)+4),min(im.height,math.ceil(y1)+2)]
        target=out/f'{token}.png';im.crop(crop).save(target)
        rows.append({'id':token,'image':target.name,'bbox':crop,'detector_bbox':p['bbox'],
                     'detector_index':i,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    request={'schema':'bbvlm.blind-region-ocr/1','created_unix':time.time(),
        'page_consumed':True,'selection':'seed 2026092713, 3 random plain-text detections with height 80..260px; short-region diagnostic, not representative',
        'source_image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
        'detector_report_sha256':hashlib.sha256(detector.read_bytes()).hexdigest(),
        'reference_used_for_selection_or_crops':False,'regions':rows,
        'contract':{'regions':[{'id':'exact request ID','text':'diplomatic transcription with physical line breaks',
                               'uncertain':'boolean','notes':'visible ambiguities only'}]},
        'conventions':'Preserve spelling, case, punctuation and visible line-end hyphens; no dehyphenation or silent correction. Mark unreadable characters with replacement character. Do not include neighboring fragments outside intended block.',
        'score_policy':'Reference lines selected by center in detector bbox; order by source y; collapse whitespace in both strings only; separate raw strings retained. No case, punctuation or hyphen folding. Source reference provisional.',
        'escalation_policy':'uncertain regions or nonzero edit distance may receive a blind Sol reread, never reference text or corrections; post-score routing labelled oracle-assisted diagnostic'}
    (out/'request.json').write_text(json.dumps(request,indent=2)+'\n')
    print(json.dumps({'regions':rows,'eligible':len(eligible)},indent=2))

if __name__=='__main__':main()
