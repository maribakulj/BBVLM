"""Freeze A25 from Git tree paths only; never download or parse validation bytes."""
from pathlib import Path
import hashlib,json,time

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop'
OUT=BASE/'french-holdout-a25';TREE=BASE/'reference-a18/source/tree.json'
REV='481f7235acfc1f78e88b3c2f22f551595c3f2032';WORK='briedefra_788606417'

def main():
    protocol=OUT/'PROTOCOL.md';assert protocol.exists()
    tree=json.loads(TREE.read_text());assert tree['sha']==REV and not tree['truncated']
    blobs={x['path']:x for x in tree['tree'] if x['type']=='blob'}
    xml=sorted(p for p in blobs if p.startswith(f'data/{WORK}/OCR-D-GT-PAGE/') and p.endswith('.xml'))
    images=sorted(p for p in blobs if p.startswith(f'data/{WORK}/OCR-D-IMG/') and p.endswith('.tif'))
    assert len(xml)==len(images)==4
    pages=[]
    for xp,ip in zip(xml,images):
        assert Path(xp).stem.replace('OCR-D-GT-PAGE_','')==Path(ip).stem.replace('OCR-D-IMG_','')
        pages.append({'work':WORK,'page':Path(xp).stem.split('_')[-1],
          'xml':xp,'image':ip,'xml_blob':blobs[xp]['sha'],'image_blob':blobs[ip]['sha'],
          'xml_size':blobs[xp]['size'],'image_size':blobs[ip]['size']})
    obj={'schema':'bbvlm.french-holdout-a25-split/1','repository':'OCR-D/OCR-D-GT-VD-SBB',
      'revision':REV,'selection':'tree paths only; all four pages of previously unused work briedefra_788606417',
      'protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
      'tree_sha256':hashlib.sha256(TREE.read_bytes()).hexdigest(),'created_unix':time.time(),'pages':pages,
      'status':'frozen_unopened'}
    (OUT/'split.json').write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps({'pages':pages,'protocol_sha256':obj['protocol_sha256']},indent=2))
if __name__=='__main__':main()
