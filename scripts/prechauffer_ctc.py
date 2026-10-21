#!/usr/bin/env python
"""Ancres et probabilités CTC calculées PENDANT la lecture Gemini.

Elles ne dépendent que de l'image, des lignes automatiques et du plan de
régions, pas de la transcription. Ce script remplit à l'avance les caches que
page_pipeline.run relit ensuite à l'identique :
- <inspection>/ctc-anchors (cache par ligne de page_anchors.ctc_anchors) ;
- <inspection>/ctc-posteriors/posteriors.npz (sauté par run s'il existe).
À lancer avec l'environnement kraken.
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from page_anchors import ctc_anchors, save_json
from page_pipeline import prepare_lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('automatic_lines')
    parser.add_argument('inspection')
    parser.add_argument('--region-plan')
    parser.add_argument('--no-block-ctc', action='store_true')
    args = parser.parse_args()
    inspection = Path(args.inspection).resolve()
    inspection.mkdir(parents=True, exist_ok=True)
    lines, constraint = prepare_lines(args.image, args.automatic_lines, args.region_plan, not args.no_block_ctc)
    work = inspection / 'prechauffage'
    work.mkdir(exist_ok=True)
    save_json(work / 'segmentation.json', lines)
    anchors = ctc_anchors(args.image, lines, inspection / 'ctc-anchors')
    if constraint is not None and not args.no_block_ctc:
        posterior_dir = inspection / 'ctc-posteriors'
        if not (posterior_dir / 'posteriors.npz').exists():
            subprocess.run([sys.executable, str(ROOT / 'scripts/ctc_posteriors.py'), args.image,
                            str(work / 'segmentation.json'), str(posterior_dir),
                            '--model', anchors['model']['path']], check=True)
    save_json(work / 'fini.json', dict(lignes=len(lines)))


if __name__ == '__main__':
    main()
