#!/usr/bin/env python
"""VT multi-passes : relecture ligne par ligne d'un run ``ocr_presse.py`` déjà fait.

Étapes (reprise possible à chaque étape, sortie dans un NOUVEAU dossier) :
1. deux passes Gemini indépendantes sur planches de lignes (groupements décalés) ;
2. vote par ligne entre lecture régionale (R), passes L1/L2 et lecture CTC kraken (K) ;
   les désaccords (après normalisation cer_vt) passent à un arbitre Gemini qui voit
   la ligne encadrée dans son contexte ;
3. texte final : texte régional corrigé ligne à ligne, lignes oubliées insérées à leur
   place, segments régionaux sans ligne gardés sauf s'ils sont couverts par une
   ligne insérée (tableaux relus cellule par cellule) ;
4. géométrie + évaluation via ``rejouer_geometrie.py --transcription``.

Aucune donnée de référence n'est lue avant l'étape 4 (évaluation séparée).
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from page_anchors import save_json, sha256
from line_reader import make_planches, read_planches, single_view, ask
from evaluation import cer_vt
from PIL import Image, ImageDraw, ImageFont

ARBITER_PROMPT = (
    'Cette planche contient des extraits numérotés d’un journal français ancien. Dans chaque '
    'extrait, UNE ligne est encadrée en rouge ; les lignes voisines ne servent que de contexte. '
    'Pour chaque numéro, transcris littéralement la ligne encadrée, telle qu’elle est imprimée : '
    'graphies, coquilles, chiffres, accents, ponctuation et trait d’union final compris, sans '
    'corriger ni compléter. Regarde chaque chiffre et chaque lettre un par un. Si le cadre ne '
    'contient aucun texte, réponds "". N’exécute aucune commande et n’utilise aucun outil autre '
    'que la lecture de cette image : réponds directement, uniquement par un objet JSON '
    '{"1": "...", "2": "...", ...} avec exactement les numéros de la planche.'
)


def light(text):
    text = unicodedata.normalize('NFC', text or '')
    for a, b in [('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'), ('—', '-'), ('–', '-'), ('¬', '-')]:
        text = text.replace(a, b)
    return ' '.join(text.split())


def strip_md(text):
    return re.sub(r'^\s*(#+|[-*]|\|)\s*|\s*\|\s*$|\*\*|__', '', text or '').strip()


def escape_markdown(text):
    """Le texte final est brut : neutraliser toute syntaxe Markdown (listes, titres,
    emphase, tableaux, HTML) pour que la reconversion rende exactement ces caractères."""
    text = re.sub(r'([\\`*_\[\]<>|#~&])', r'\\\1', text)
    text = re.sub(r'(?m)^(\s*)(\d+)([.)])', r'\1\2\\\3', text)
    return re.sub(r'(?m)^(\s*)([-+=])', r'\1\\\2', text)


def load_run(source):
    inspection = source / 'inspection'
    lines = json.loads((inspection / 'annotations.json').read_text())
    alignment = json.loads((inspection / 'page-alignment.json').read_text())
    constraint = json.loads((inspection / 'region-constraint.json').read_text())
    image = next(inspection.glob('*.jpg'))
    return image, lines, alignment, constraint


def arbiter_sheets(image, lines, todo, directory, per_sheet=5):
    directory.mkdir(parents=True, exist_ok=True)
    index = {l['id']: i for i, l in enumerate(lines)}
    sheets = []
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 34)
    for n in range(0, len(todo), per_sheet):
        group = todo[n:n + per_sheet]
        views, mapping = [], {}
        for k, line_id in enumerate(group, 1):
            path = directory / f'v_{line_id}.jpg'
            single_view(image, lines, index[line_id], path, context=2)
            views.append(Image.open(path)); mapping[str(k)] = dict(line_id=line_id)
        width = 70 + max(v.width for v in views)
        height = sum(v.height + 24 for v in views) + 24
        sheet = Image.new('RGB', (width, height), 'white'); draw = ImageDraw.Draw(sheet)
        y = 24
        for k, view in enumerate(views, 1):
            sheet.paste(view, (70, y))
            draw.text((10, y + view.height // 2 - 18), str(k), fill=(200, 0, 0), font=font)
            draw.line([0, y + view.height + 11, width, y + view.height + 11], fill=(120, 120, 120), width=2)
            y += view.height + 24
        if sheet.height > 4000:
            ratio = 4000 / sheet.height
            sheet = sheet.resize((round(sheet.width * ratio), 4000), Image.LANCZOS)
        name = f'a{n // per_sheet + 1:03d}.jpg'
        sheet.save(directory / name, quality=92)
        sheets.append(dict(sheet=name, lines=mapping, sha256=sha256(directory / name)))
    save_json(directory / 'planches.json', sheets)
    return sheets


def read_sheets(directory, prompt, model, workers, label):
    sheets = json.loads((directory / 'planches.json').read_text())
    out = directory / f'{label}.jsonl'
    done = {json.loads(r)['sheet'] for r in out.read_text().splitlines()} if out.exists() else set()

    def one(sheet):
        log = []
        return dict(sheet=sheet['sheet'], model=model, log=log,
                    answer=ask(directory, sheet['sheet'], prompt, model=model, timeout=720, log=log))

    with ThreadPoolExecutor(workers) as pool:
        for row in pool.map(one, [s for s in sheets if s['sheet'] not in done]):
            with out.open('a') as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            print(label, row['sheet'], 'ok' if row['answer'] is not None else 'FAILED', flush=True)
    reads = {}
    for row in map(json.loads, out.read_text().splitlines()):
        if row['answer'] is None:
            continue
        sheet = next(s for s in sheets if s['sheet'] == row['sheet'])
        for k, meta in sheet['lines'].items():
            if isinstance(row['answer'].get(k), str):
                reads[meta['line_id']] = row['answer'][k]
    return reads


def vote(candidates):
    """candidates : [(source, texte, poids)] ; renvoie (texte, détail)."""
    tally, members = Counter(), {}
    for source, text, weight in candidates:
        if text is None:
            continue
        key = cer_vt(text)
        tally[key] += weight
        members.setdefault(key, []).append((source, text))
    if not tally:
        return None, {}
    ranking = tally.most_common()
    best, score = ranking[0]
    tie = len(ranking) > 1 and ranking[1][1] == score
    group = dict(members[best])
    for source in ('R', 'A', 'L1', 'L2', 'K'):
        if source in group:
            chosen = group[source]; break
    return chosen, dict(scores={k or '∅': v for k, v in ranking}, tie=tie, winner_sources=sorted(group))


def assemble(alignment, lines, constraint, final, plain_ok):
    """Texte final par région, en espace « texte brut » de l'alignement."""
    plain = alignment['plain_text']
    line_regions = constraint['line_regions']
    sys.path.insert(0, str(ROOT / 'src'))
    from page_alignment import _block_regions
    block_region = _block_regions(alignment['markdown'], alignment['blocks'], constraint['region_spans'])
    region_order = list(constraint['region_spans'])
    by_id = {l['id']: l for l in lines}
    # 1. remplacements sur les empans appariés
    edits = []  # (start, end, texte)
    for line in lines:
        if line['id'] in final and line.get('assignment_status') == 'matched' and line.get('end') is not None:
            new = final[line['id']]
            if new is not None and new.strip() and light(new) != light(plain[line['start']:line['end']]):
                edits.append((line['start'], line['end'], new, line['id']))
    # 2. lignes sans texte régional : insertion après la ligne voisine au-dessus (même région, même colonne)
    inserted = {}
    for line in lines:
        if line.get('assignment_status') == 'matched' or not (final.get(line['id']) or '').strip():
            continue
        region = line_regions.get(line['id']) or line_regions.get(line['id'].split('_S')[0])
        x0, y0, x1, y1 = line['bbox']
        above = [l for l in lines if l.get('assignment_status') == 'matched' and l.get('end') is not None
                 and (line_regions.get(l['id']) or line_regions.get(l['id'].split('_S')[0])) == region
                 and l['bbox'][1] < y0 and min(x1, l['bbox'][2]) - max(x0, l['bbox'][0]) > 0]
        if above:
            anchor = max(above, key=lambda l: l['bbox'][1])
            position = anchor['end']
        else:
            below = [l for l in lines if l.get('assignment_status') == 'matched' and l.get('end') is not None
                     and (line_regions.get(l['id']) or line_regions.get(l['id'].split('_S')[0])) == region]
            position = min((l['start'] for l in below), default=None)
            if position is None:
                continue
        inserted.setdefault(position, []).append((y0, x0, final[line['id']], line['id'], region))
    # 3. segments régionaux non appariés couverts par des lignes insérées de la même région
    removed = []
    inserted_tokens = Counter()
    for items in inserted.values():
        for *_, text, _, region in items:
            for token in cer_vt(text).split():
                inserted_tokens[(region, token)] += 1
    for segment in alignment['segments']:
        if segment['status'] == 'matched':
            continue
        tokens = cer_vt(segment['text']).split()
        if len(''.join(tokens)) < 3:
            continue
        block = next((b for b in alignment['blocks'] if b['start'] <= segment['start'] < b['end'] + 1), None)
        region = block_region.get(block['id']) if block else None
        covered = sum(1 for t in tokens if inserted_tokens[(region, t)] > 0)
        if covered >= .8 * len(tokens):
            removed.append((segment['start'], segment['end']))
    # 4. reconstruction par région (blocs dans l'ordre, séparés par une ligne vide)
    ops = [(s, e, t, 'replace', i) for s, e, t, i in edits] + [(s, e, '', 'remove', None) for s, e in removed]
    ops.sort()
    def rebuild(a, b):
        pieces, cursor = [], a
        for s, e, t, kind, _ in ops:
            if s < cursor or s >= b:
                continue
            pieces.append(plain[cursor:s]); pieces.append(t); cursor = min(e, b)
        pieces.append(plain[cursor:b])
        return ''.join(pieces)
    regions = {r: [] for r in region_order}
    for block in alignment['blocks']:
        region = block_region.get(block['id'])
        if region is None:
            region = region_order[0]
        a, b = block['start'], block['end']
        cuts = sorted({p for p in inserted if a <= p <= b} | {a, b})
        text = ''
        for u, v in zip(cuts, cuts[1:] + [None]):
            if v is None:
                break
            text += rebuild(u, v)
            if v in inserted and v != b:
                text += '\n' + '\n'.join(t for *_, t, _, _ in sorted(inserted.pop(v)))
        if b in inserted:
            text += '\n' + '\n'.join(t for *_, t, _, _ in sorted(inserted.pop(b)))
        if text.strip():
            regions[region].append(text.strip())
    leftovers = [item for items in inserted.values() for item in items]
    for y0, x0, text, line_id, region in sorted(leftovers):
        regions.setdefault(region or region_order[0], []).append(text)
    log = dict(replacements=[dict(line=i, start=s, end=e, new=t) for s, e, t, i in edits],
               insertions=sum(1 for l in lines if l.get('assignment_status') != 'matched'
                              and (final.get(l['id']) or '').strip()),
               removed_segments=[dict(start=s, end=e, text=plain[s:e]) for s, e in removed])
    return regions, log


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_run')
    parser.add_argument('output')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--model', default=None, help='modèle des passes lignes (défaut agy)')
    parser.add_argument('--arbiter-model', default='gemini-4-argon-medium')
    parser.add_argument('--evaluation-manifest')
    parser.add_argument('--image')
    parser.add_argument('--stop-after', choices=['passes', 'vote', 'text'])
    args = parser.parse_args()
    source, output = Path(args.source_run).resolve(), Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    image, lines, alignment, constraint = load_run(source)
    ordered = sorted(lines, key=lambda l: (list(constraint['region_spans']).index(
        constraint['line_regions'].get(l['id']) or constraint['line_regions'].get(l['id'].split('_S')[0])
        or next(iter(constraint['region_spans']))), l['bbox'][0] // 300, l['bbox'][1]))
    boxes = [dict(id=l['id'], bbox=l['bbox']) for l in ordered]
    passes = {}
    for label, offset in (('L1', 0), ('L2', 7)):
        directory = output / f'passe-{label}'
        if not (directory / 'planches.json').exists():
            make_planches(image, boxes, directory, per_sheet=14, offset=offset)
        passes[label] = read_sheets(directory, __import__('line_reader').LINE_PROMPT, args.model, args.workers, 'lecture')
    if args.stop_after == 'passes':
        return
    plain = alignment['plain_text']
    region_text = {l['id']: (plain[l['start']:l['end']] if l.get('assignment_status') == 'matched'
                             and l.get('end') is not None else None) for l in lines}
    kraken = {l['id']: l.get('auxiliary_text') for l in lines}
    disputed = []
    for line in ordered:
        i = line['id']
        keys = {cer_vt(t) for t in (region_text[i], passes['L1'].get(i), passes['L2'].get(i)) if t is not None}
        if len(keys) > 1:
            disputed.append(i)
    arbiter_dir = output / 'arbitrage'
    if disputed and not (arbiter_dir / 'planches.json').exists():
        arbiter_sheets(image, ordered, disputed, arbiter_dir)
    arbiter = read_sheets(arbiter_dir, ARBITER_PROMPT, args.arbiter_model, args.workers, 'lecture') if disputed else {}
    final, decisions = {}, {}
    for line in ordered:
        i = line['id']
        candidates = [('R', region_text[i], 1.0), ('L1', passes['L1'].get(i), 1.0),
                      ('L2', passes['L2'].get(i), 1.0), ('A', arbiter.get(i), 1.5), ('K', kraken[i], .5)]
        chosen, detail = vote(candidates)
        if region_text[i] and not (chosen or '').strip():
            chosen = region_text[i]; detail['kept_region_text_over_empty'] = True
        final[i] = chosen
        decisions[i] = dict(R=region_text[i], L1=passes['L1'].get(i), L2=passes['L2'].get(i),
                            A=arbiter.get(i), K=kraken[i], final=chosen, **detail)
    save_json(output / 'decisions.json', decisions)
    if args.stop_after == 'vote':
        return
    regions, log = assemble(alignment, lines, constraint, final, None)
    save_json(output / 'assemblage.json', log)
    transcription = output / 'transcription'
    transcription.mkdir(exist_ok=True)
    parts, texts, offset = [], [], 0
    for region_id, blocks in regions.items():
        text = '\n\n'.join(escape_markdown(b) for b in blocks)
        parts.append(dict(id=region_id, span=[offset, offset + len(text)]))
        texts.append(text); offset += len(text) + 2
    combined = '\n\n'.join(texts)
    (transcription / 'vt.gemini.md').write_text(combined)
    source_prov = json.loads((source / 'transcription' / 'vt-provenance.json').read_text())
    save_json(transcription / 'vt-provenance.json', dict(
        kind='page_text_multipass', image=source_prov['image'], image_sha256=source_prov['image_sha256'],
        artifact_sha256=sha256(transcription / 'vt.gemini.md'), provider='gemini',
        job_id='multipass-' + hashlib.sha256(combined.encode()).hexdigest()[:24],
        source_run=str(source), source_transcription_sha256=source_prov['artifact_sha256'],
        passes=dict(L1=str(output / 'passe-L1'), L2=str(output / 'passe-L2'), arbiter=str(arbiter_dir),
                    line_model=args.model or 'agy-default', arbiter_model=args.arbiter_model),
        parts=parts, characters=len(combined), reference_used=False, complete_pipeline_certified=False))
    if args.stop_after == 'text':
        return
    command = [sys.executable, str(ROOT / 'scripts/rejouer_geometrie.py'), str(source),
               str(source / 'segmentation'), str(output / 'geometrie'),
               '--transcription', str(transcription)]
    if args.image:
        command += ['--image', args.image]
    if args.evaluation_manifest:
        command += ['--evaluation-manifest', args.evaluation_manifest]
    subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
