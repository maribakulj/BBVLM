"""Score the sealed A69 candidates after metadata-only writer failure."""
import hashlib, importlib.metadata, json, time
from evaluate_transfer_a69 import ROOT, OUT, add, metrics, parse_xml
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def version(name):
 try:return importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:return None
def main():
 started=time.perf_counter();split=json.loads((OUT/'split.json').read_text());names=split['pages']
 candidates=json.loads((OUT/'candidates.json').read_text())['pages']
 predictions=json.loads((OUT/'predictions.json').read_text());assert [r['page'] for r in predictions]==names
 expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
 per_page={};xml_hashes={}
 for name in names:
  regions,lines,xh=parse_xml(name,expected);xml_hashes[name]=xh;per_page[name]=metrics(candidates[name],regions,lines)
 aggregate={p:add([per_page[n][p] for n in names]) for p in ('native','fixed','ink_crossing')}
 n,f,i=aggregate['native'],aggregate['fixed'],aggregate['ink_crossing']
 checks={'lt50_noninferior':i['lt50']<=n['lt50'],
  'lt95_relative_reduction_ge20pct':i['lt95']<=.8*n['lt95'],
  'added_area_le60pct_fixed':i['added_area']<=.6*f['added_area'],
  'foreign_boxes_le_fixed':i['foreign_added_boxes_gt1pct']<=f['foreign_added_boxes_gt1pct'],
  'foreign_fraction_le_fixed_plus2pp':i['foreign_fraction_of_added']<=f['foreign_fraction_of_added']+.02,
  'no_page_mean_regression':all(per_page[x]['ink_crossing']['mean_best_coverage']+1e-12>=per_page[x]['native']['mean_best_coverage'] for x in names)}
 report={'status':'frozen_transfer_not_global_validation','retry_reason':'A69 inference completed; original writer failed only on unavailable opencv-python distribution metadata.',
  'candidate_sha256_before_xml':sha(OUT/'candidates.json'),'predictions_sha256':sha(OUT/'predictions.json'),
  'pages':names,'aggregate':aggregate,'per_page':per_page,'gate_checks':checks,'local_gate_passed':all(checks.values()),
  'xml_sha256':xml_hashes,'model_forwards_reused':len(predictions),'new_model_forwards':0,
  'test_pages_opened':0,'vlm_calls':0,'ocr_calls':0,'score_seconds':time.perf_counter()-started,
  'versions':{'torch':version('torch'),'doclayout_yolo':version('doclayout_yolo'),
              'opencv_python_headless':version('opencv-python-headless'),'shapely':version('shapely')},
  'all_scientific_gates_passed':False,
  'limitations':['Official Training pages used as BBVLM transfer because Validation geometry was consumed by A65.',
                 'A58 structurally audited all XML; this is not a pristine corpus claim.',
                 'Annotation coverage and foreign overlap are not perfect ALTO or semantic ownership truth.']}
 (OUT/'report-v2.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'aggregate':aggregate,'gate_checks':checks,'local_gate_passed':all(checks.values())},indent=2))
if __name__=='__main__':main()
