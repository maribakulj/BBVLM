#!/usr/bin/env python
"""CER indépendant d'une sortie Gemini ; les références restent hors production."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_pipeline import verify_transcription
from page_reference_text import load_page_reference
from page_text_evaluation import score_page_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='Manifeste d’évaluation indépendant')
    parser.add_argument('transcription', help='Dossier vt.gemini.md + vt-provenance.json')
    parser.add_argument('report')
    parser.add_argument('--reference-dpi', type=float)
    args = parser.parse_args()
    directory = Path(args.transcription)
    markdown = directory / 'vt.gemini.md'
    provenance = directory / 'vt-provenance.json'
    metadata = json.loads(provenance.read_text())
    manifest = json.loads(Path(args.manifest).read_text())
    matches = [row for row in manifest['pages']
               if row['image_sha256'] == metadata['image_sha256']]
    if len(matches) != 1:
        raise ValueError('Une référence unique liée à cette image est requise pour calculer le CER')
    row = matches[0]
    # L'image peut avoir été déplacée depuis la transcription : seule son
    # empreinte fait foi ; le manifeste fournit alors le chemin courant.
    image = metadata['image'] if Path(metadata['image']).exists() else row['image']
    verify_transcription(image, markdown, provenance)
    reference_path = Path(row['reference'])
    if hashlib.sha256(reference_path.read_bytes()).hexdigest() != row['reference_sha256']:
        raise ValueError('La référence diffère du manifeste gelé')
    reference, audit = load_page_reference(reference_path, dpi=args.reference_dpi)
    scores, _ = score_page_text(reference, markdown.read_text())
    scores.update(page_id=row['id'], image_sha256=row['image_sha256'],
                  reference_sha256=row['reference_sha256'],
                  markdown_sha256=metadata['artifact_sha256'],
                  reference_text_audit=audit,
                  reference_status=('independent_human_reference' if row['human_text']
                                    else 'diagnostic_nonhuman_reference'))
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(target)
    print(json.dumps(scores['text']['hipe_ocrepair_2026'], ensure_ascii=False))


if __name__ == '__main__':
    main()
