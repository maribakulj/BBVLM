"""Fetch exactly the frozen A69 public images with upstream blob verification."""
import concurrent.futures, json
from pathlib import Path
from fetch_crop_pilot_a66 import ROOT, REV, fetch
OUT=ROOT/'experiments/loop/next-a69'
def main():
 split=json.loads((OUT/'split.json').read_text()); names=split['pages']
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  rows=list(pool.map(fetch,names))
 (OUT/'assets.json').write_text(json.dumps({'revision':REV,'images':rows,'test_pages_opened':0},indent=2)+'\n')
 print(json.dumps({'verified_images':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
if __name__=='__main__':main()
