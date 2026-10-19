#!/usr/bin/env python
"""Gemini libre → appariement → image et ALTO prêts pour inspection.

La segmentation fournie doit être automatique. La reprise réutilise le journal
Gemini existant et ne soumet pas une seconde lecture après un délai dépassé.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from page_minimal_markdown import MinimalMarkdownReader
from page_pipeline import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('automatic_lines', help='Dossier de segmentation automatique')
    parser.add_argument('output')
    parser.add_argument('--gemini-pane', required=True)
    parser.add_argument('--timeout', type=int, default=900)
    parser.add_argument('--transcription-dir', help='Reprendre une lecture déjà journalisée')
    parser.add_argument('--anchor-reader', choices=('cached', 'ctc'), default='ctc')
    parser.add_argument('--model')
    parser.add_argument('--evaluation-manifest', help='Références réservées au calcul du CER après production')
    parser.add_argument('--reference-dpi', type=float)
    args = parser.parse_args()
    image = Path(args.image).resolve()
    output = Path(args.output).resolve()
    transcription = (Path(args.transcription_dir).resolve()
                     if args.transcription_dir else output / 'transcription')
    export = output / 'inspection'
    reader = MinimalMarkdownReader(args.gemini_pane,
                                   transcription / 'page-lecture-jobs', args.timeout)
    reader.read_page(image, transcription)
    report = run(image, transcription / 'vt.gemini.md',
                 transcription / 'vt-provenance.json', args.automatic_lines, export,
                 anchor_reader=args.anchor_reader, model_path=args.model)
    # L'export copie les pixels source ; ce manifeste donne la paire exacte
    # même si seules certaines lignes ont pu être placées.
    paths = {'image': export / image.name, 'alto': export / 'page.alto.xml',
             'markdown': export / 'vt.gemini.md',
             'geometry_report': export / 'geometry-report.json'}
    evaluation = None
    if args.evaluation_manifest:
        report_path = export / 'cer-hipe.json'
        command = [sys.executable, str(ROOT / 'scripts/evaluer_ocr_page.py'),
                   args.evaluation_manifest, str(transcription), str(report_path)]
        if args.reference_dpi is not None:
            command.extend(['--reference-dpi', str(args.reference_dpi)])
        subprocess.run(command, check=True)
        evaluation = json.loads(report_path.read_text())['text']['hipe_ocrepair_2026']
        paths['cer_report'] = report_path
    delivery = dict(files={k: str(p) for k, p in paths.items()},
                    sha256={k: hashlib.sha256(p.read_bytes()).hexdigest()
                            for k, p in paths.items()},
                    lines_exported=report.get('lines_exported'),
                    lines_total=report.get('lines_total'),
                    criteria_met=report.get('criteria_met', False),
                    cer_hipe= evaluation,
                    cer_status='measured' if evaluation is not None else 'reference_not_supplied')
    target = output / 'livraison.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(delivery, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)
    print(json.dumps(delivery, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
