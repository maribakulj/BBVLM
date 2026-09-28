"""Verify blind A71 IDs/hashes and summarize visual classifications."""
import hashlib, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/loop/next-a71'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((OUT/'manifest.json').read_text());response=json.loads((OUT/'luna-response.json').read_text())
 expected={r['id']:r for r in manifest['views']};records=response['records']
 assert response['schema']=='bbvlm.a71.luna/1';assert len(records)==len(expected)==12
 assert {r['id'] for r in records}==set(expected)
 allowed={'visible_text','non_text_or_rule','ambiguous'}
 for row in records:
  source=expected[row['id']];assert row['label'] in allowed
  assert isinstance(row['safe_rectangular_recall'],bool)
  assert row['observed_sha256']==source['sha256']==sha(ROOT/source['path'])
 counts=Counter(r['label'] for r in records);safe=sum(r['safe_rectangular_recall'] for r in records)
 report={'status':'blind_visual_diagnostic_not_ground_truth','reader':'gpt-6-luna',
  'views':len(records),'labels':dict(counts),'safe_rectangular_recall':safe,
  'records':records,'ids_and_hashes_valid':True,'test_pages_opened':0,
  'reference_modified':False,'all_scientific_gates_passed':False,
  'limitations':['Oracle-selected from consumed A70 misses.','One visual reader is not adjudication.',
                 'Visible text does not define exact region ownership or perfect ALTO boxes.']}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ('views','labels','safe_rectangular_recall')},indent=2))
if __name__=='__main__':main()
