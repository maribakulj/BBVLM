#!/usr/bin/env python3
"""Extract only sealed A26 members after checking every sealed hash."""
from __future__ import annotations
import hashlib,json,time,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; EXP=ROOT/'experiments/loop/bnf-impact-a26'
SRC=EXP/'source'; ARCHIVE=SRC/'impact.zip'; SPLIT=EXP/'split.json'
TARGET=EXP/'opened'

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())

def main():
    raw=SPLIT.read_bytes(); s=json.loads(raw)
    if s['status']!='frozen_unopened': raise ValueError('split is not frozen_unopened')
    checks={'protocol':EXP/'PROTOCOL.md','evaluator':ROOT/'scripts/evaluate_bnf_impact_a26.py',
      'candidate_core_a25':ROOT/'scripts/evaluate_french_holdout_a25.py',
      'extractor':ROOT/'scripts/open_bnf_impact_a26.py',
      'archive_manifest':SRC/'archive-manifest.json'}
    for key,path in checks.items():
        if sha(path)!=s['sealed_sha256'][key]: raise ValueError(f'sealed file changed: {key}')
    if sha(ARCHIVE)!=s['archive_sha256']: raise ValueError('archive hash mismatch')
    wanted=[]
    for p in s['pages']: wanted += [p['xml'],p['image']]
    wanted += ['IMPACT/documents.xlsx','IMPACT/ark.txt','IMPACT/readme.docx']
    files=[]
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in wanted:
            data=z.read(name); info=z.getinfo(name)
            path=TARGET/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
            files.append({'name':name,'bytes':len(data),'crc32':f'{info.CRC:08x}','sha256':sha_bytes(data)})
    opened={'schema':'bbvlm.bnf-impact-a26-opened/1','status':'opened_verified',
      'split_sha256':sha_bytes(raw),'opened_unix':time.time(),'files':files}
    (EXP/'opened.json').write_text(json.dumps(opened,indent=2)+'\n')
    print(json.dumps(opened,indent=2))
if __name__=='__main__': main()
