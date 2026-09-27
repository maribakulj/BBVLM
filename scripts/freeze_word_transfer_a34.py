#!/usr/bin/env python3
from pathlib import Path
import collections, hashlib, json, time

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop';EXP=BASE/'word-transfer-a34'
TREE=BASE/'reference-a18/source/tree.json';REV='481f7235acfc1f78e88b3c2f22f551595c3f2032'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    tree=json.loads(TREE.read_text());assert tree['sha']==REV and not tree['truncated']
    blobs={x['path']:x for x in tree['tree'] if x['type']=='blob'}
    consumed=set()
    for rel in ('reference-a18/split.json','french-holdout-a25/split.json','french-word-gt-a28/split.json'):
        obj=json.loads((BASE/rel).read_text()); consumed.update(x.get('work') for x in obj.get('pages',[]) if x.get('work'))
    works=collections.defaultdict(lambda:{'xml':[],'image':[]})
    for path in blobs:
        parts=path.split('/')
        if len(parts)<4 or parts[0]!='data':continue
        if '/OCR-D-GT-PAGE/' in path and path.endswith('.xml'):works[parts[1]]['xml'].append(path)
        if '/OCR-D-IMG/' in path and path.lower().endswith('.tif'):works[parts[1]]['image'].append(path)
    eligible=[w for w,v in works.items() if w not in consumed and len(v['xml'])==len(v['image'])==4]
    chosen=sorted(eligible,key=lambda w:hashlib.sha256(('A34-independent-transfer:'+w).encode()).hexdigest())[:3]
    pages=[]
    for work in chosen:
        for xp,ip in zip(sorted(works[work]['xml']),sorted(works[work]['image'])):
            page=Path(xp).stem.replace('OCR-D-GT-PAGE_','');assert page==Path(ip).stem.replace('OCR-D-IMG_','')
            pages.append({'work':work,'page':page,'xml':xp,'image':ip,'xml_blob':blobs[xp]['sha'],
                          'image_blob':blobs[ip]['sha'],'xml_size':blobs[xp]['size'],'image_size':blobs[ip]['size']})
    sealed={'protocol':EXP/'PROTOCOL.md','freeze':ROOT/'scripts/freeze_word_transfer_a34.py',
            'opener':ROOT/'scripts/open_word_transfer_a34.py','evaluator':ROOT/'scripts/evaluate_word_transfer_a34.py',
            'core':ROOT/'scripts/evaluate_french_holdout_a25.py','components':ROOT/'src/bbvlm/component_boxes.py','tree':TREE}
    out={'schema':'bbvlm.word-transfer-a34-split/1','status':'frozen_unopened','repository':'OCR-D/OCR-D-GT-VD-SBB',
         'revision':REV,'selection':'deterministic SHA-256 selection of three unconsumed four-page works',
         'excluded_consumed_works':sorted(consumed),'eligible_work_count':len(eligible),'works':chosen,'pages':pages,
         'created_unix':time.time(),'sealed_sha256':{k:sha(v) for k,v in sealed.items()}}
    (EXP/'split.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
