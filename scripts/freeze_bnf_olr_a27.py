#!/usr/bin/env python3
"""Freeze one unopened BnF/IMPACT OLR page and all candidate code hashes."""
from __future__ import annotations
import hashlib,json,re,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/loop/bnf-impact-olr-a27'
A26=ROOT/'experiments/loop/bnf-impact-a26'
MANIFEST=A26/'source/archive-manifest.json'
ARCHIVE=A26/'source/impact.zip'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest=json.loads(MANIFEST.read_text()); by_name={x['name']:x for x in manifest['members']}
    xmls=sorted(n for n in by_name if re.fullmatch(r'IMPACT/PAGE/\d+_5\.xml',n))
    groups={}
    for name in xmls:
        page=Path(name).stem.split('_')[0];groups.setdefault(page[:7],[]).append((page,name))
    first_group=sorted(groups)[0];page,xml=sorted(groups[first_group])[1]
    tif=f'IMPACT/T/{page}.tif';jpg=f'IMPACT/T/{int(page)}.jpg';image=tif if tif in by_name else jpg
    files={
      'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md',
      'preparer':ROOT/'scripts/prepare_bnf_olr_a27.py',
      'evaluator':ROOT/'scripts/evaluate_bnf_olr_a27.py',
      'order_core':ROOT/'src/bbvlm/order.py','semantic_core':ROOT/'src/bbvlm/semantic.py',
      'archive_manifest':MANIFEST}
    split={'schema':'bbvlm.bnf-impact-olr-a27-split/1','status':'frozen_unopened',
      'selection':'second PAGE XML lexicographically in first filename-prefix group; central-directory names only',
      'archive_sha256':manifest['sha256'],'archive_bytes':manifest['bytes'],
      'page':{'group':first_group,'page':page,'xml':xml,'image':image,
        'xml_bytes':by_name[xml]['bytes'],'xml_crc32':by_name[xml]['crc32'],
        'image_bytes':by_name[image]['bytes'],'image_crc32':by_name[image]['crc32']},
      'opaque_token_seed':'bbvlm-a27-frozen-seed-v1','created_unix':time.time(),
      'sealed_sha256':{k:sha(v) for k,v in files.items()}}
    if sha(ARCHIVE)!=manifest['sha256']: raise ValueError('archive hash mismatch')
    (EXP/'split.json').write_text(json.dumps(split,indent=2)+'\n')
    print(json.dumps(split,indent=2))
if __name__=='__main__':main()

