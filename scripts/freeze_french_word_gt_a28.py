#!/usr/bin/env python3
"""Freeze all eight pages of the two catalogue-French SBB works."""
from pathlib import Path
import hashlib,json,time

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop'
EXP=BASE/'french-word-gt-a28';TREE=BASE/'reference-a18/source/tree.json'
REV='481f7235acfc1f78e88b3c2f22f551595c3f2032'
WORKS=('borrdisc_689809840','catapabin_657601357')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    tree=json.loads(TREE.read_text());assert tree['sha']==REV and not tree['truncated']
    blobs={x['path']:x for x in tree['tree'] if x['type']=='blob'};pages=[]
    for work in WORKS:
        xmls=sorted(p for p in blobs if p.startswith(f'data/{work}/OCR-D-GT-PAGE/') and p.endswith('.xml'))
        images=sorted(p for p in blobs if p.startswith(f'data/{work}/OCR-D-IMG/') and p.endswith('.tif'))
        if len(xmls)!=4 or len(images)!=4:raise ValueError(f'expected four PAGE/TIFF pairs for {work}')
        for xp,ip in zip(xmls,images):
            page=Path(xp).stem.replace('OCR-D-GT-PAGE_','')
            if page!=Path(ip).stem.replace('OCR-D-IMG_',''):raise ValueError('page mismatch')
            pages.append({'work':work,'page':page,'xml':xp,'image':ip,
              'xml_blob':blobs[xp]['sha'],'image_blob':blobs[ip]['sha'],
              'xml_size':blobs[xp]['size'],'image_size':blobs[ip]['size']})
    sealed={'protocol':EXP/'PROTOCOL.md','opener':ROOT/'scripts/open_french_word_gt_a28.py',
      'evaluator':ROOT/'scripts/evaluate_french_word_gt_a28.py',
      'candidate_core_a25':ROOT/'scripts/evaluate_french_holdout_a25.py','tree':TREE}
    obj={'schema':'bbvlm.french-word-gt-a28-split/1','status':'frozen_unopened',
      'repository':'OCR-D/OCR-D-GT-VD-SBB','revision':REV,
      'selection':'all four pages of both works independently catalogued fre; tree metadata and paths only',
      'works':list(WORKS),'pages':pages,'created_unix':time.time(),
      'protocol_sha256':sha(EXP/'PROTOCOL.md'),
      'sealed_sha256':{k:sha(v) for k,v in sealed.items()}}
    (EXP/'split.json').write_text(json.dumps(obj,indent=2)+'\n');print(json.dumps(obj,indent=2))
if __name__=='__main__':main()
