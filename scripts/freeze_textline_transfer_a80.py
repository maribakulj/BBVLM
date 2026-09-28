"""Freeze new names only; no source pixels or XML values read."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/loop/next-a80/dense'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 splitpath=ROOT/'experiments/loop/chronicling-a58/official_split.json';s=json.loads(splitpath.read_text());exclude=set()
 for a in [69,74,76]:exclude.update(json.loads((ROOT/f'experiments/loop/next-a{a}/split.json').read_text())['pages'])
 inventory={r['file'][:-4] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 pages=[];strata=[]
 for lo,hi in [(1600,1749),(1750,1849),(1850,1900),(1901,1945)]:
  eligible=[n for n in s['Training'] if n in inventory and n not in exclude and (m:=re.search(r'(1[6-9]\d{2})',n)) and lo<=int(m.group(1))<=hi]
  n=min(eligible,key=lambda n:hashlib.sha256(('A80-v1:'+n).encode()).hexdigest());pages.append(n);strata.append({'range':[lo,hi],'eligible':len(eligible),'selected':n})
 assert len(set(pages))==4 and not set(pages)&set(s['Test']) and not set(pages)&exclude
 code={p:sha(ROOT/p) for p in ['scripts/evaluate_textline_transfer_a80.py','scripts/merge_yolo_regions_a80.py','scripts/merge_horizontal_components_a78.py']}
 result={'schema':'bbvlm.a80.split/1','status':'frozen_unopened_for_a80','pages':pages,'strata':strata,'excluded_pages':sorted(exclude),'official_split_sha256':sha(splitpath),'protocol_sha256':sha(OUT/'PROTOCOL.md'),'implementation_sha256':code,'test_pages_opened':0}
 (OUT/'split.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(pages))
if __name__=='__main__':main()
