#!/usr/bin/env python3
"""Download sealed A28 members and verify pinned Git blobs."""
from __future__ import annotations
import hashlib,json,time,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/french-word-gt-a28';SOURCE=EXP/'source'
def sha(data):return hashlib.sha256(data).hexdigest()
def blob(data):return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def fsha(path):return sha(path.read_bytes())

def main():
    split=json.loads((EXP/'split.json').read_text())
    if split['status']!='frozen_unopened':raise ValueError('split not frozen_unopened')
    checks={'protocol':EXP/'PROTOCOL.md','opener':ROOT/'scripts/open_french_word_gt_a28.py',
      'evaluator':ROOT/'scripts/evaluate_french_word_gt_a28.py','candidate_core_a25':ROOT/'scripts/evaluate_french_holdout_a25.py',
      'tree':ROOT/'experiments/loop/reference-a18/source/tree.json'}
    for key,path in checks.items():
        if fsha(path)!=split['sealed_sha256'][key]:raise ValueError(f'sealed file changed: {key}')
    files=[]
    for page in split['pages']:
        for kind in ('xml','image'):
            rel=page[kind];url=f"https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/{split['revision']}/{rel}"
            with urllib.request.urlopen(url,timeout=180) as response:data=response.read()
            if blob(data)!=page[f'{kind}_blob']:raise ValueError(f'Git blob mismatch: {rel}')
            dst=SOURCE/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
            files.append({'kind':kind,'path':rel,'bytes':len(data),'git_blob':blob(data),'sha256':sha(data)})
    opened={'schema':'bbvlm.french-word-gt-a28-opened/1','status':'opened_verified','opened_unix':time.time(),
      'split_sha256':fsha(EXP/'split.json'),'files':files}
    (EXP/'opened.json').write_text(json.dumps(opened,indent=2)+'\n');print(json.dumps(opened,indent=2))
if __name__=='__main__':main()

