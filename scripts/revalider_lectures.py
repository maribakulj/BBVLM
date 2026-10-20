#!/usr/bin/env python
"""Revalider, sans nouvel appel Gemini, les lectures de régions rejetées à tort.

Le 20/10/2026, l'agent a ouvert les images par read_file (clé "Path") au lieu de
view_file ("AbsolutePath") : la preuve d'ouverture ne les voyait pas et des
lectures complètes ont été classées incomplete_after_retries. Pour chaque région
rejetée, on refait la vérification avec region_agy.observed_paths corrigé sur la
conversation du DERNIER essai (celui dont la réponse est dans vt.gemini.md) :
statut SUCCESS, image ouverte, réponse non vide sans IMAGE_ABSENTE. Le texte
n'est jamais modifié ; la provenance garde la trace de la revalidation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from region_agy import observed_paths

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('transcription', help='dossier transcription/ d\'un run ocr_presse')
args = parser.parse_args()
report = {}
for prov_path in sorted(Path(args.transcription).glob('*/vt-provenance.json')):
    prov = json.loads(prov_path.read_text())
    if prov.get('reading_status') != 'incomplete_after_retries':
        continue
    region = prov_path.parent
    last = prov['calls'][-1] if prov.get('calls') else {}
    text = (region / 'vt.gemini.md').read_text(encoding='utf-8')
    cid = last.get('conversation_id')
    paths = observed_paths(cid) if cid else []
    ok = (last.get('status') == 'SUCCESS' and prov['image'] in paths and text.strip()
          and 'IMAGE_ABSENTE' not in text
          and hashlib.sha256((region / 'vt.gemini.md').read_bytes()).hexdigest() == prov['artifact_sha256'])
    report[region.name] = bool(ok)
    if not ok:
        continue
    last['image_opened'] = True
    prov['native_history_provenance']['input_views']['observed_paths'] = paths
    prov['native_history_provenance']['trailing_native_errors'] = []
    prov['native_history_provenance']['revalidation'] = dict(
        date='2026-10-20', reason='image ouverte par read_file ("Path") non reconnue par la première vérification',
        conversation_id=cid, gemini_calls=0)
    prov['uncertain'] = '[illisible]' in text
    prov['reading_status'] = 'native_response_saved_pending_independent_evaluation'
    prov_path.write_text(json.dumps(prov, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=1))
