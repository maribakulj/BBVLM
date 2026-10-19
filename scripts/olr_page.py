#!/usr/bin/env python
"""Passe OLR complète d'une page déjà placée : structure Gemini (1 appel), ancrage des
blocs dans le texte aligné, rattachement des lignes non couvertes, ALTO avec OLR,
et, si un manifeste d'évaluation est donné, mesure contre les régions de la VT."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from page_olr_gemini import ask_structure, anchor_blocks, attach_uncovered_lines
from olr_alto import apply

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('placement', help='dossier inspection(-refined) : page.alto.xml, page-alignment.json, image')
parser.add_argument('output')
parser.add_argument('--evaluation-manifest'); parser.add_argument('--page-id')
parser.add_argument('--model', default='gemini-3.8-flash-medium')
args = parser.parse_args()
placement, output = Path(args.placement).resolve(), Path(args.output).resolve()
output.mkdir(parents=True, exist_ok=True)
image = next(p for p in placement.iterdir() if p.suffix.lower() in ('.jpg', '.png', '.tif') and p.stem != 'plan-preview')
local = output / image.name
if not local.exists():
    shutil.copy2(image, local)
structure = output / 'olr-gemini.json'
result = json.loads(structure.read_text()) if structure.exists() else ask_structure(output, local, model=args.model)
if not result.get('complete') and args.model.endswith('-medium'):
    # Pages très denses : en réflexion moyenne, Flash s'arrête en erreur après
    # ~60 k jetons de réflexion (La Presse 0476474) ; repli en réflexion basse.
    structure.rename(output / 'olr-gemini-echec-medium.json')
    result = ask_structure(output, local, model=args.model.replace('-medium', '-low'))
if not result.get('complete'):
    raise SystemExit('Passe OLR incomplète (image non ouverte ou réponse invalide) : voir olr-gemini.json')
alignment = json.loads((placement / 'page-alignment.json').read_text())
anchored = anchor_blocks(result['blocs'], alignment)
attached = attach_uncovered_lines(anchored, alignment)
(output / 'olr-ancre.json').write_text(json.dumps(anchored, ensure_ascii=False, indent=1))
report = dict(blocs=len(anchored), ancres=sum(b.get('status') == 'ancre' for b in anchored), lignes_rattachees=attached,
              alto=apply(placement / 'page.alto.xml', output / 'olr-ancre.json', output / 'page.olr.alto.xml'),
              appels=result.get('calls'))
if args.evaluation_manifest and args.page_id:
    from mesurer_olr import evaluate
    report['mesure_vt'] = evaluate(args.evaluation_manifest, output / 'page.olr.alto.xml', args.page_id)
(output / 'olr-rapport.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in report.items() if k != 'appels'}, ensure_ascii=False, indent=1))
