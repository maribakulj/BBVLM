#!/usr/bin/env python
"""Apparier une VT Gemini de page sauvegardée et produire ses exports."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_pipeline import KRAKEN_PYTHON, run


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('markdown')
    parser.add_argument('provenance')
    parser.add_argument('automatic_lines', help='Dossier segmentation.json + segmentation-config.json')
    parser.add_argument('output')
    parser.add_argument('--anchor-reader', choices=('cached', 'ctc'), default='cached')
    parser.add_argument('--alignment-only', action='store_true')
    parser.add_argument('--kraken-python', default=str(KRAKEN_PYTHON))
    parser.add_argument('--model')
    parser.add_argument('--minimum-similarity', type=float, default=.72)
    parser.add_argument('--ambiguity-margin', type=float, default=.06)
    args = parser.parse_args()
    result = run(args.image, args.markdown, args.provenance, args.automatic_lines, args.output,
                 anchor_reader=args.anchor_reader, geometry=not args.alignment_only,
                 kraken_python=args.kraken_python, model_path=args.model,
                 minimum_similarity=args.minimum_similarity, ambiguity_margin=args.ambiguity_margin)
    print(json.dumps({k: result[k] for k in ('text_coverage', 'coverage', 'criteria_met', 'status')
                      if k in result}, ensure_ascii=False))
