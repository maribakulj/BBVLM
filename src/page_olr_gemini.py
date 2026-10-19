"""Passe OLR Gemini : structure logique seule, ancrée ensuite par l'alignement.

Gemini voit la page entière une fois et rend, en JSON, la liste des blocs dans
l'ordre de lecture : type, article, colonne approximative, premiers et derniers
mots. Il ne rend PAS le texte complet (tâche légère : sur une page dense, la
transcription intégrale omet et invente). Chaque bloc est ensuite retrouvé
dans la transcription OCR par ses premiers/derniers mots ; sa géométrie est
celle des lignes où ce texte a été aligné. Un bloc introuvable est signalé,
jamais forcé. La preuve que l'image a été ouverte est exigée (journal agy).
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata

from region_agy import observed_paths, NO_TOOLS

TYPES = ('titre', 'intertitre', 'texte', 'tableau', 'annonce', 'en-tete', 'legende', 'autre')
PROMPT = (
    'Cette image est une page de journal français ancien. Décris sa STRUCTURE LOGIQUE, sans '
    'transcrire le texte complet. Liste TOUS les blocs de texte de la page, dans l’ordre de lecture '
    '(colonne par colonne, de haut en bas, en suivant les articles qui passent d’une colonne à la '
    'suivante). Pour chaque bloc : "n" (numéro dans l’ordre de lecture), "type" parmi '
    + ', '.join(f'"{t}"' for t in TYPES) +
    ', "article" (numéro de l’article auquel il appartient ; même numéro pour son titre et tous ses '
    'paragraphes, y compris sur plusieurs colonnes), "colonne" (1 = la plus à gauche), "debut" (les 6 '
    'premiers mots exactement comme imprimés) et "fin" (les 6 derniers mots exactement comme imprimés). '
    'Un paragraphe = un bloc ; un tableau = un bloc. N’oublie aucun bloc, même court (fins de '
    'paragraphe, annonces, bandeau). Ouvre d’abord l’image jointe ; si tu ne peux pas la voir, réponds '
    'uniquement IMAGE_ABSENTE. Réponds uniquement par un objet JSON {"blocs": [...]}.'
)


def ask_structure(directory, image, model='gemini-3.8-flash-medium', timeout=900, attempts=3):
    directory, image = Path(directory).resolve(), Path(image).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    question = PROMPT + f'\n\nImage : @{image.name}\nNe lis aucun autre fichier. ' + NO_TOOLS
    log, result = [], None
    for attempt in range(attempts):
        started = time.time()
        try:
            run = subprocess.run(['agy', '-p', question, '--print-timeout', f'{timeout-60}s', '--output-format',
                                  'json', '--model', model], cwd=image.parent, capture_output=True, text=True,
                                 timeout=timeout)
            envelope = json.loads(run.stdout) if run.stdout.strip().startswith('{') else {}
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            envelope = {}
        cid = envelope.get('conversation_id')
        opened = str(image) in (observed_paths(cid) if cid else [])
        response = envelope.get('response') or ''
        log.append(dict(attempt=attempt, seconds=round(time.time()-started, 1), status=envelope.get('status'),
                        usage=envelope.get('usage'), conversation_id=cid, image_opened=opened))
        match = re.search(r'\{.*\}', response, re.S)
        if envelope.get('status') == 'SUCCESS' and opened and match and 'IMAGE_ABSENTE' not in response:
            try:
                result = json.loads(match.group(0))
                break
            except json.JSONDecodeError:
                pass
    out = dict(model=model, image=str(image), calls=log, complete=result is not None,
               blocs=(result or {}).get('blocs', []))
    (directory / 'olr-gemini.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def _key(text):
    text = unicodedata.normalize('NFKC', text or '').lower().replace('ſ', 's')
    return ' '.join(re.sub(r'[\W_]+', ' ', text).split())


def anchor_blocks(blocs, alignment, annotations=None, cutoff=75):
    """Retrouve chaque bloc OLR dans le texte OCR (premiers/derniers mots, recherche
    floue sans espaces, monotone) ; une fin introuvable s'arrête au début du bloc
    suivant retrouvé. Géométrie = union des lignes alignées dans l'empan."""
    from rapidfuzz import fuzz
    plain = alignment['plain_text']
    key_chars, positions = [], []
    for i, ch in enumerate(plain):
        for c in _key(ch).replace(' ', ''):
            key_chars.append(c); positions.append(i)
    haystack = ''.join(key_chars)
    spans = [(a['start'], a['end'], a['bbox'], a['line_id']) for a in alignment['assignments']]

    def find(words, start):
        needle = _key(words).replace(' ', '')
        if len(needle) < 4:
            return None
        found = fuzz.partial_ratio_alignment(needle, haystack[start:], score_cutoff=cutoff)
        if found is None:
            return None
        return start + found.dest_start, start + found.dest_end, found.score

    # L'ordre de lecture de Gemini (articles d'une colonne à l'autre) n'est pas
    # celui du texte OCR (régions) : chaque début est cherché dans toute la page.
    starts = [find(bloc.get('debut', ''), 0) for bloc in blocs]
    found_starts = sorted(s[0] for s in starts if s is not None)
    out = []
    for k, bloc in enumerate(blocs):
        first = starts[k]
        if first is None:
            out.append({**bloc, 'status': 'debut_introuvable'}); continue
        # fin : au plus tard au début de bloc retrouvé qui suit dans le TEXTE OCR
        limit = next((s for s in found_starts if s > first[0]), len(haystack))
        last = find(bloc.get('fin', ''), first[0])
        if last is not None and last[1] <= limit:
            end_key, how = last[1], 'fin_retrouvee'
        else:
            end_key, how = limit, 'fin_au_bloc_suivant'
        a, b = positions[first[0]], positions[max(first[1], end_key)-1]+1
        members = [s for s in spans if s[0] < b and a < s[1]]
        bbox = None
        if members:
            boxes = [m[2] for m in members]
            bbox = [min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes)]
        out.append({**bloc, 'status': 'ancre', 'end_rule': how, 'start': a, 'end': b,
                    'lines': [m[3] for m in members], 'bbox': bbox, 'debut_score': round(first[2], 1)})
    return out


def attach_uncovered_lines(anchored, alignment, max_gap_lines=3.0):
    """Une ligne alignée qu'aucun bloc ne couvre (sous-titre non listé, intérieur
    d'un tableau, fin de bloc mal citée) rejoint le bloc qui la précède dans le
    texte OCR, s'il est voisin sur l'image (écart vertical ≤ max_gap_lines
    hauteurs de ligne et recouvrement horizontal). Sinon elle reste non attribuée."""
    assignments = sorted(alignment['assignments'], key=lambda a: a['start'])
    owner = {}
    for b in anchored:
        if b.get('status') == 'ancre':
            for lid in b.get('lines', []):
                owner.setdefault(lid, b['n'])
    by_n = {b['n']: b for b in anchored}
    current = None
    attached = 0
    for a in assignments:
        lid = a['line_id']
        if lid in owner:
            current = owner[lid]; continue
        if current is None:
            continue
        block = by_n[current]
        bb, lb = block.get('bbox'), a['bbox']
        if not bb:
            continue
        height = max(1, lb[3]-lb[1])
        vertical_gap = max(0, lb[1]-bb[3], bb[1]-lb[3])
        horizontal = min(bb[2], lb[2]) - max(bb[0], lb[0])
        if vertical_gap <= max_gap_lines*height and horizontal > 0:
            block['lines'].append(lid)
            block['bbox'] = [min(bb[0], lb[0]), min(bb[1], lb[1]), max(bb[2], lb[2]), max(bb[3], lb[3])]
            block.setdefault('attached_lines', []).append(lid)
            owner[lid] = current
            attached += 1
    return attached
