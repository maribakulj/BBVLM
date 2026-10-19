#!/usr/bin/env python
"""Rejouer localisation + géométrie d'une page déjà transcrite, sans appel Gemini.

Entrées figées d'un run ``ocr_presse.py`` existant (plan de régions et
transcription) ; sortie dans un NOUVEAU dossier. Le run source n'est jamais
modifié. Sert à mesurer un changement d'algorithme d'appariement/géométrie sur
exactement le même texte imposé.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from page_anchors import save_json, sha256
from page_pipeline import run, KRAKEN_PYTHON


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_run')
    parser.add_argument('automatic_lines')
    parser.add_argument('output')
    parser.add_argument('--image')
    parser.add_argument('--evaluation-manifest')
    parser.add_argument('--minimum-text-coverage', type=float, default=.97)
    parser.add_argument('--no-region-constraint', action='store_true')
    parser.add_argument('--no-block-ctc', action='store_true', help='sans découpage par vraisemblance CTC')
    parser.add_argument('--transcription', help='dossier vt.gemini.md + vt-provenance.json (défaut : celui du run source)')
    args = parser.parse_args()
    source, output = Path(args.source_run).resolve(), Path(args.output).resolve()
    if output.exists() and any(output.iterdir()) and not (output / 'state.json').exists():
        raise SystemExit('Dossier de sortie non vide et étranger')
    output.mkdir(parents=True, exist_ok=True)
    text = Path(args.transcription).resolve() if args.transcription else source / 'transcription'
    prov = json.loads((text / 'vt-provenance.json').read_text())
    image = Path(args.image or prov['image']).resolve()
    plan = source / 'layout/plan.json'

    def state(stage, **kw):
        save_json(output / 'state.json', dict(stage=stage, source_run=str(source), **kw))

    state('geometry')
    inspection = output / 'inspection'
    report = run(image, text / 'vt.gemini.md', text / 'vt-provenance.json', Path(args.automatic_lines),
                 inspection, anchor_reader='ctc', repair_ownership=True,
                 region_plan=None if args.no_region_constraint else plan,
                 block_ctc=not args.no_block_ctc)
    variants = {'inspection': report['text_coverage']['fraction'] or 0}
    geometry = json.loads((inspection / 'geometry-report.json').read_text())
    selected = inspection
    if geometry['statuses'].get('alignement_non_resolu', 0) or variants['inspection'] < args.minimum_text_coverage:
        state('boundary_recovery', variants=variants)
        from page_boundary_recovery import recover
        refined = output / 'inspection-refined'
        refined_report = recover(image, inspection, refined, KRAKEN_PYTHON)
        variants['inspection-refined'] = refined_report['text_coverage']['fraction'] or 0
        if variants['inspection-refined'] >= variants['inspection']:
            report, selected = refined_report, refined
    files = {'image': selected / image.name, 'alto': selected / 'page.alto.xml',
             'markdown': selected / 'vt.gemini.md', 'export_report': selected / 'page-export.json',
             'ownership_audit': selected / 'ownership-audit.json'}
    delivery = dict(source_run=str(source), selected=selected.name, variants=variants,
                    text_coverage=report['text_coverage'],
                    text_coverage_gate=dict(minimum=args.minimum_text_coverage,
                        passed=(report['text_coverage']['fraction'] or 0) >= args.minimum_text_coverage),
                    region_constraint=not args.no_region_constraint, block_ctc=not args.no_block_ctc,
                    reading_certified=False, geometry_certified=False)
    if args.evaluation_manifest:
        cer = selected / 'cer-hipe.json'
        subprocess.run([sys.executable, str(ROOT / 'scripts/evaluer_ocr_page.py'),
                        args.evaluation_manifest, str(text), str(cer)], check=True)
        files['cer_hipe'] = cer
        delivery['cer_note'] = ('CER du texte Gemini (identique au run source) : '
                                'la géométrie ne change pas la lecture.')
        # Rapport complet des écarts Gemini ↔ VT, à chaque passe.
        sys.path.insert(0, str(ROOT / 'scripts'))
        from rapport_differences import build
        verifications = output / 'verifications-visuelles.json'
        differences = build(args.evaluation_manifest, text, selected, output / 'differences',
                            title=image.stem, verifications=verifications if verifications.exists() else None)
        files['differences'] = output / 'differences' / 'differences.html'
        delivery['differences_gemini_vt'] = dict(total=differences['differences'], by_category=differences['by_category'])
    delivery['files'] = {k: str(p) for k, p in files.items()}
    delivery['sha256'] = {k: sha256(p) for k, p in files.items()}
    save_json(output / 'livraison.json', delivery)
    state('exported', delivery=delivery)
    print(json.dumps(delivery, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
