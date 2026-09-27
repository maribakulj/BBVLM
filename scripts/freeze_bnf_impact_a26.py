#!/usr/bin/env python3
"""Freeze A26 paths and implementation hashes without opening ZIP members."""
from __future__ import annotations
import hashlib, json, re, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/loop/bnf-impact-a26'; SRC=EXP/'source'
MANIFEST=SRC/'archive-manifest.json'; PROTOCOL=EXP/'PROTOCOL.md'
EVALUATOR=ROOT/'scripts/evaluate_bnf_impact_a26.py'
CORE=ROOT/'scripts/evaluate_french_holdout_a25.py'
EXTRACTOR=ROOT/'scripts/open_bnf_impact_a26.py'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    m=json.loads(MANIFEST.read_text()); names={x['name']:x for x in m['members']}
    xmls=sorted(n for n in names if re.fullmatch(r'IMPACT/PAGE/\d+_5\.xml',n))
    groups={}
    for name in xmls:
        digits=Path(name).stem.split('_')[0]
        groups.setdefault(digits[:7],[]).append((digits,name))
    if len(groups)!=4: raise ValueError(f'expected four filename groups, got {sorted(groups)}')
    pages=[]
    for group, entries in sorted(groups.items()):
        digits,xml=sorted(entries)[0]
        tif=f'IMPACT/T/{digits}.tif'; jpg=f'IMPACT/T/{int(digits)}.jpg'
        image=tif if tif in names else jpg if jpg in names else None
        if image is None: raise ValueError(f'no manifest image for {xml}')
        pages.append({'group':group,'page':digits,'xml':xml,'image':image,
          'xml_bytes':names[xml]['bytes'],'xml_crc32':names[xml]['crc32'],
          'image_bytes':names[image]['bytes'],'image_crc32':names[image]['crc32']})
    split={'schema':'bbvlm.bnf-impact-a26-split/1','status':'frozen_unopened',
      'selection':'first PAGE XML lexicographically in each of four filename-prefix groups; manifest names only',
      'archive_sha256':m['sha256'],'archive_bytes':m['bytes'],
      'created_unix':time.time(),'pages':pages,
      'sealed_sha256':{'protocol':sha(PROTOCOL),'evaluator':sha(EVALUATOR),
        'candidate_core_a25':sha(CORE),'extractor':sha(EXTRACTOR),
        'archive_manifest':sha(MANIFEST)}}
    (EXP/'split.json').write_text(json.dumps(split,indent=2)+'\n')
    print(json.dumps(split,indent=2))
if __name__=='__main__': main()
