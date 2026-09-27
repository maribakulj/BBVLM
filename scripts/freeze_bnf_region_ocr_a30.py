#!/usr/bin/env python3
"""Freeze an unopened BnF region-OCR validation page and implementation."""
from __future__ import annotations
import hashlib,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/bnf-region-ocr-a30';A26=ROOT/'experiments/loop/bnf-impact-a26';MAN=A26/'source/archive-manifest.json';ARCH=A26/'source/impact.zip'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads(MAN.read_text());by={x['name']:x for x in m['members']};xs=sorted(n for n in by if re.fullmatch(r'IMPACT/PAGE/\d+_5\.xml',n));groups={}
 for n in xs:
  page=Path(n).stem.split('_')[0];groups.setdefault(page[:7],[]).append((page,n))
 group=sorted(groups)[1];page,xml=sorted(groups[group])[1];tif=f'IMPACT/T/{page}.tif';jpg=f'IMPACT/T/{int(page)}.jpg';image=tif if tif in by else jpg
 files={'protocol':EXP/'PROTOCOL.md','prompt':EXP/'VLM_PROMPT.md','preparer':ROOT/'scripts/prepare_bnf_region_ocr_a30.py','evaluator':ROOT/'scripts/evaluate_bnf_region_ocr_a30.py','metrics':ROOT/'src/bbvlm/metrics.py','archive_manifest':MAN}
 if sha(ARCH)!=m['sha256']:raise ValueError('archive hash mismatch')
 out={'schema':'bbvlm.bnf-region-ocr-a30-split/1','status':'frozen_unopened','selection':'second PAGE XML in second filename-prefix group; manifest names only','archive_sha256':m['sha256'],'page':{'group':group,'page':page,'xml':xml,'image':image,'xml_bytes':by[xml]['bytes'],'xml_crc32':by[xml]['crc32'],'image_bytes':by[image]['bytes'],'image_crc32':by[image]['crc32']},'selection_seed':'bbvlm-a30-regions-v1','opaque_seed':'bbvlm-a30-opaque-v1','created_unix':time.time(),'sealed_sha256':{k:sha(v) for k,v in files.items()}}
 (EXP/'split.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
