#!/usr/bin/env python
"""Lire uniquement le manifeste public d'images. Aucun chemin de référence."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import math
import time


def run_page(command,out,wait_native_quota=False):
    """Reprendre après l'échéance native observée ; jamais après timeout seul."""
    out=Path(out)
    while True:
        with (out/'pipeline.log').open('a',encoding='utf-8') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        state_file=out/'pipeline-state.json'
        state=json.loads(state_file.read_text()) if state_file.exists() else {}
        if not result.returncode or not wait_native_quota or state.get('stage')!='waiting_for_native_quota':
            return result.returncode
        deadline=state.get('retry_at')
        if not isinstance(deadline,(int,float)) or not math.isfinite(deadline):
            raise ValueError('Quota natif sans échéance valide')
        wait_file=out/'native-quota-wait.json'
        def checkpoint(stage):
            temporary=wait_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(dict(stage=stage,retry_at=deadline,
                    evidence=state['evidence'],blind_timeout_retry=False),ensure_ascii=False,indent=2))
            temporary.replace(wait_file)
        checkpoint('waiting_for_displayed_native_reset')
        print(f'{out.name}: quota natif ; attente persistante jusqu’à {deadline:.0f}',flush=True)
        while time.time()<deadline:time.sleep(min(30,deadline-time.time()))
        checkpoint('deadline_elapsed_recover_existing_request')


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('outputs');ap.add_argument('--gemini-pane',required=True)
    ap.add_argument('--split',choices=('dev','reserved'),required=True)
    ap.add_argument('--segmentation',choices=('full','tiles','auto','auto-v2'),default='auto')
    ap.add_argument('--ctc-model')
    ap.add_argument('--segmentation-from',help='Reuse completed automatic segmentation suite, same image/config only')
    ap.add_argument('--batch-size',type=int,default=10)
    ap.add_argument('--reading-revision',default='v1')
    ap.add_argument('--reading-input',choices=('legacy','lines','sheets'),default='legacy')
    ap.add_argument('--line-refinement',choices=('none','ink'),default='none')
    ap.add_argument('--word-boundaries',choices=('auto','midpoint','ink','ink_clean','ink_clean_baseline','ink_clean_local'),default='auto')
    ap.add_argument('--char-alignment',choices=('auto','line','word'),default='auto')
    ap.add_argument('--word-verification',choices=('auto','none','blind'),default='auto')
    ap.add_argument('--wait-native-quota',action='store_true',help='Wait for an explicitly displayed native reset, then recover the identified request')
    ap.add_argument('--layout',choices=('auto','none','ppdl3'),default='auto');args=ap.parse_args()
    manifest=json.loads(Path(args.manifest).read_text());root=Path(__file__).resolve().parents[1]
    # Refuser même de lancer si l'évaluateur privé est donné par erreur.
    allowed={'id','family','split','image','image_sha256'}
    if any(set(row) != allowed for row in manifest['pages']):
        raise ValueError('Ce manifeste contient autre chose que les images publiques ; refus de production')
    for row in manifest['pages']:
        if row['split'] != args.split:
            continue
        if hashlib.sha256(Path(row['image']).read_bytes()).hexdigest() != row['image_sha256']:
            raise ValueError('Image modifiée : '+row['id'])
        out=Path(args.outputs)/row['id'];out.mkdir(parents=True,exist_ok=True)
        if args.segmentation_from:
            sys.path.insert(0,str(root/'src'))
            from segmentation import prime_from_suite
            prime_from_suite(row['image'],Path(args.segmentation_from)/row['id'],out,args.segmentation,args.line_refinement)
        command=[sys.executable,str(root/'src/pipeline.py'),row['image'],str(out),
                 '--gemini-pane',args.gemini_pane,'--segmentation',args.segmentation,
                 '--batch-size',str(args.batch_size),'--reading-revision',args.reading_revision,
                 '--reading-input',args.reading_input,'--line-refinement',args.line_refinement,
                 '--word-boundaries',args.word_boundaries,'--char-alignment',args.char_alignment,
                 '--word-verification',args.word_verification,'--layout',args.layout]
        if args.ctc_model:command.extend(['--ctc-model',args.ctc_model])
        code=run_page(command,out,args.wait_native_quota)
        if code:
            print(f'{row["id"]}: interruption sauvegardée ; relancer cette commande pour reprendre',flush=True)
            raise SystemExit(code)
        print(f'{row["id"]}: exporté, notation indépendante requise',flush=True)
