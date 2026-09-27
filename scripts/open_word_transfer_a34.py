#!/usr/bin/env python3
import hashlib,json,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/loop';EXP=BASE/'word-transfer-a34';SOURCE=EXP/'source'
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def fsha(p):return sha(p.read_bytes())
def main():
    s=json.loads((EXP/'split.json').read_text());assert s['status']=='frozen_unopened'
    checks={'protocol':EXP/'PROTOCOL.md','freeze':ROOT/'scripts/freeze_word_transfer_a34.py','opener':Path(__file__),
            'evaluator':ROOT/'scripts/evaluate_word_transfer_a34.py','core':ROOT/'scripts/evaluate_french_holdout_a25.py',
            'components':ROOT/'src/bbvlm/component_boxes.py','tree':BASE/'reference-a18/source/tree.json'}
    for k,p in checks.items():assert fsha(p)==s['sealed_sha256'][k],f'sealed changed {k}'
    files=[]
    for page in s['pages']:
        for kind in ('xml','image'):
            rel=page[kind];url=f"https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/{s['revision']}/{rel}"
            with urllib.request.urlopen(url,timeout=180) as r:data=r.read()
            assert blob(data)==page[kind+'_blob'];dst=SOURCE/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
            files.append({'kind':kind,'path':rel,'bytes':len(data),'git_blob':blob(data),'sha256':sha(data)})
    out={'schema':'bbvlm.word-transfer-a34-opened/1','status':'opened_verified','opened_unix':time.time(),
         'split_sha256':fsha(EXP/'split.json'),'files':files}
    (EXP/'opened.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
