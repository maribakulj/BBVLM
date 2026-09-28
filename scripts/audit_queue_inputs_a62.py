"""Read-only fixity check of the last visual experiment, not a new inference."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop'
old=json.loads((BASE/'bnl-bands-a60/blind/request.json').read_text())
expected={x['id']:x['sha256'] for x in old['items']}
checks=[]
for index, key in enumerate(['K843','K206','K591'],1):
    p=BASE/f'bnl-guard-a61/blind/V{index}.png'
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    checks.append({'path':str(p.relative_to(ROOT)),'sha256':actual,'matches':actual==expected[key]})
assert all(x['matches'] for x in checks)
report={'status':'passed','checks':checks,'inference_calls':0,'scope':'A61 input fixity only; no OCR/GT quality claim'}
(BASE/'queue-a62/source-integrity.json').write_text(json.dumps(report,indent=2)+'\n')
