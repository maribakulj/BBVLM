#!/usr/bin/env python
"""OCR par régions source, chaque appel repris depuis son journal natif.

Le plan spatial est établi sans référence textuelle. L'assemblage ne corrige
aucun mot et conserve les limites des régions dans un manifeste séparé.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_region_markdown import RegionMarkdownReader
from page_anchors import save_json, sha256
from page_region_audit import coverage as source_coverage


def prepare(image, plan, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    with Image.open(image) as page:
        width, height = page.size
        seen = set()
        for i, region in enumerate(sorted(plan['regions'], key=lambda r: r['order'])):
            name = region['id']
            if not name.replace('-', '').replace('_', '').isalnum() or name in seen:
                raise ValueError('Identifiant de région invalide ou dupliqué')
            seen.add(name)
            x0, y0, x1, y1 = region['bbox']
            if not all(type(v) is int for v in region['bbox']) or not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                raise ValueError('Région hors image ou coordonnées non entières')
            directory = output / name
            directory.mkdir(exist_ok=True)
            crop = page.crop((x0, y0, x1, y1))
            target = directory / 'image.png'
            if not target.exists():
                crop.save(target)
            else:
                with Image.open(target) as saved:
                    if saved.size != crop.size or saved.convert('RGB').tobytes() != crop.convert('RGB').tobytes():
                        raise ValueError('Crop existant modifié')
            views = []
            # Une colonne haute est fournie en vues natives de 2800 pixels.
            # Les 120 pixels de recouvrement ne sont transcrits qu'une fois.
            if crop.height > 3000:
                start = 0
                while start < crop.height:
                    stop = min(start + 2800, crop.height)
                    path = directory / f'detail-{len(views)+1:02d}.png'
                    detail = crop.crop((0, start, crop.width, stop))
                    if not path.exists():
                        detail.save(path)
                    else:
                        with Image.open(path) as saved:
                            if saved.size != detail.size or saved.convert('RGB').tobytes() != detail.convert('RGB').tobytes():
                                raise ValueError('Vue existante modifiée')
                    views.append(dict(path=str(path), source_bbox=[x0, y0+start, x1, y0+stop], sha256=sha256(path)))
                    if stop == crop.height:
                        break
                    start = stop - 120
            records.append({**region, 'image': str(target), 'image_sha256': sha256(target), 'views': views})
    manifest = dict(image=str(Path(image).resolve()), image_sha256=sha256(image),
                    coordinate_system='source_pixels_xyxy', regions=records,
                    plan=plan, reference_used=False)
    target = output / 'regions.json'
    if target.exists() and json.loads(target.read_text()) != manifest:
        raise ValueError('Plan modifié ; utiliser un nouveau dossier')
    save_json(target, manifest)
    return manifest


def region_task(region):
    task = ('Transcris intégralement et littéralement le texte visible dans cette région de journal, '
            'en Markdown simple. Lis du haut vers le bas. Conserve les graphies, chiffres, accents '
            'et ponctuation, sans reformuler, corriger, résumer ni compléter les mots coupés. '
            'Recopie l’imprimé tel qu’il est, coquilles comprises : une lettre fautive, retournée '
            'ou abîmée se transcrit comme elle apparaît (par exemple « maisou » reste « maisou »), '
            'même si le mot devient faux. Pour un mot coupé en fin de ligne, garde le trait '
            'd’union et transcris chaque moitié exactement comme imprimée, sans la corriger '
            'd’après le mot entier. '
            'Une tache, une salissure, un point d’encre isolé ou un défaut du papier n’est pas un '
            'signe : ne le transcris pas, et n’ajoute jamais d’apostrophe ni de ponctuation à '
            'l’intérieur d’un mot à cause d’une tache (« émeutes du mois », pas « érneutes d’u mo’is »). '
            'Ne complète pas avec le texte situé hors du crop. Garde les lignes imprimées dans '
            'les paragraphes. Aucun préambule ni conclusion : seulement la transcription. '
            'Note [illisible] pour une partie réellement indéchiffrable. ')
    if region['views']:
        task += ('L’image principale situe la région. Consulte impérativement TOUTES les vues de détail '
                 'à résolution source pour lire les petits caractères. Elles se suivent verticalement '
                 'avec 120 pixels de recouvrement : transcris ce recouvrement une seule fois. ')
    return task


def transcribe(manifest, output, pane, timeout=900, workers=None):
    # Lectures Gemini simultanées : BBVLM_GEMINI_WORKERS (défaut 3).
    workers = workers or int(os.environ.get('BBVLM_GEMINI_WORKERS', '3'))
    output = Path(output).resolve()
    if str(pane).startswith('agy') and workers > 1:
        # Lectures indépendantes (session neuve chacune) lancées en parallèle ;
        # la boucle ci-dessous reprend ensuite les résultats complets sauvegardés.
        from concurrent.futures import ThreadPoolExecutor
        from region_agy import read_region
        model = pane.split(':', 1)[1] if ':' in pane else 'gemini-3.8-flash-medium'

        def pending(region):
            prov = output / region['id'] / 'vt-provenance.json'
            return not (prov.exists() and json.loads(prov.read_text()).get('reading_status') ==
                        'native_response_saved_pending_independent_evaluation')

        def one(region):
            read_region(output / region['id'], region['image'], [v['path'] for v in region['views']],
                        region_task(region), model=model, timeout=timeout)

        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(one, [r for r in manifest['regions'] if pending(r)]))
    parts = []
    offset = 0
    for region in manifest['regions']:
        directory = output / region['id']
        task = region_task(region)
        if str(pane).startswith('agy'):
            # Mode non interactif (agy -p), session neuve par région ; « agy:<modèle> ».
            from region_agy import read_region
            from types import SimpleNamespace
            model = pane.split(':', 1)[1] if ':' in pane else 'gemini-3.8-flash-medium'
            saved = (json.loads((directory / 'vt-provenance.json').read_text())
                     if (directory / 'vt-provenance.json').exists() else {})
            if (directory / 'vt.gemini.md').exists() and saved.get('reading_status') == \
                    'native_response_saved_pending_independent_evaluation':
                reading = SimpleNamespace(text=(directory / 'vt.gemini.md').read_text(), job_id=saved['job_id'],
                                          uncertain=saved['uncertain'], model=saved['model_native'])
            else:
                got = read_region(directory, region['image'], [v['path'] for v in region['views']], task,
                                  model=model, timeout=timeout)
                reading = SimpleNamespace(text=got['text'], job_id=got['job_id'], uncertain=got['uncertain'],
                                          model=got['model'])
        else:
            reader = RegionMarkdownReader(pane, directory / 'jobs', task,
                                          [v['path'] for v in region['views']], timeout)
            reading = reader.read_page(region['image'], directory)
        text = reading.text
        native_metadata = json.loads((directory / 'vt-provenance.json').read_text())
        native_errors = native_metadata.get('native_history_provenance', {}).get('trailing_native_errors', [])
        view_coverage=source_coverage(region,native_metadata)
        parts.append(dict(id=region['id'], bbox=region['bbox'], order=region['order'],
                          path=str(directory / 'vt.gemini.md'), sha256=sha256(directory / 'vt.gemini.md'),
                          provenance=str(directory / 'vt-provenance.json'),
                          job_id=reading.job_id, uncertain=reading.uncertain,
                          reading_status=native_metadata.get('reading_status', 'unknown'),
                          empty=not text.strip(),
                          source_pixel_coverage=view_coverage,
                          interrupted=bool(native_errors),
                          span=[offset, offset+len(text)]))
        offset += len(text) + 2
        save_json(output / 'progress.json', dict(completed=len(parts), total=len(manifest['regions']), parts=parts))
        print(json.dumps(dict(region=region['id'], completed=len(parts), total=len(manifest['regions']),
                              characters=len(text), uncertain=reading.uncertain)), flush=True)
    combined = '\n\n'.join(Path(p['path']).read_text() for p in parts)
    target = output / 'vt.gemini.md'
    if target.exists() and target.read_text() != combined:
        raise ValueError('Assemblage existant différent')
    target.write_text(combined)
    save_json(output / 'vt-provenance.json', dict(kind='page_markdown_regions',
              image=manifest['image'], image_sha256=manifest['image_sha256'],
              artifact_sha256=sha256(target), provider='gemini',
              job_id='regions-' + hashlib.sha256(''.join(p['job_id'] for p in parts).encode()).hexdigest()[:24],
              model_native=reading.model, model_claim=None,
              uncertain=any(p['uncertain'] or p['source_pixel_coverage']['fraction']!=1 for p in parts), characters=len(combined),
              assembly='verbatim_regions_joined_with_two_newlines', parts=parts,
              interrupted_regions=[p['id'] for p in parts if p['interrupted']],
              empty_regions=[p['id'] for p in parts if p['empty']],
              incomplete_pixel_coverage_regions=[p['id'] for p in parts if p['source_pixel_coverage']['fraction']!=1],
              reading_status=('partial_native_interruption' if any(p['interrupted'] for p in parts)
                              else 'native_responses_saved_pending_independent_evaluation'),
              reference_used=False, complete_pipeline_certified=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('plan', help='JSON régions en pixels source, ordre inclus')
    parser.add_argument('output')
    parser.add_argument('--pane', required=True)
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    manifest = prepare(args.image, json.loads(Path(args.plan).read_text()), args.output)
    transcribe(manifest, args.output, args.pane, args.timeout)
