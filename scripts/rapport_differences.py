#!/usr/bin/env python
"""Rapport complet des différences entre le texte Gemini et la VT d'une page.

Évaluation SEULEMENT : la référence n'est lue qu'ici, après coup, et rien de ce
rapport ne retourne dans la chaîne. Chaque différence est listée, classée et
illustrée par une vignette de l'image (boîtes VT en bleu, boîtes Gemini en
rouge). La lecture CTC kraken de la ligne, indépendante de Gemini et de la VT,
sert d'arbitre quand les deux textes divergent ; elle peut se tromper aussi,
d'où la catégorie « indéterminé ».

Ordre comparé : région par région (plan automatique figé), lignes de VT
rangées géométriquement dans chaque région — le même ordre que le CER
« ordre spatial commun ».
"""
import argparse
import bisect
import base64
from collections import Counter, defaultdict
import html
import io
import json
from pathlib import Path
import re
import sys
import unicodedata

from lxml import etree
from PIL import Image, ImageDraw
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))
from evaluation import _points, nfc
from evaluer_regions import geometric_order
from page_alignment import _block_regions
from page_anchors import save_json, sha256

VERSION = 'gemini-vt-differences-v1'

TYPO = str.maketrans({'’': "'", '‘': "'", 'ʼ': "'", '´': "'", '`': "'", '«': '"', '»': '"',
                      '“': '"', '”': '"', '„': '"', '—': '-', '–': '-', '‐': '-', '‑': '-',
                      '¬': '-', 'ſ': 's', 'º': '°', ' ': ' ', ' ': ' ', '…': '...'})
LIGATURES = {'œ': 'oe', 'Œ': 'OE', 'æ': 'ae', 'Æ': 'AE', 'ﬁ': 'fi', 'ﬂ': 'fl'}

CATEGORIES = [
    ('normalisation', 'Normalisation typographique', 'Apostrophe, guillemets, tirets, ligature, ſ, espace : même texte, autre graphie.'),
    ('casse', 'Casse', 'Majuscule/minuscule seulement.'),
    ('accent_majuscule', 'Accent sur majuscule', 'Convention d\'imprimerie (Etat/État) : pas une erreur de lecture.'),
    ('ponctuation', 'Ponctuation', 'Signe de ponctuation présent, absent ou différent.'),
    ('cesure', 'Césure / fin de ligne', 'Mot coupé en fin de ligne recollé ou non.'),
    ('balisage', 'Balisage Gemini', 'Barres de tableau Markdown ou marqueur ajouté par Gemini.'),
    ('illisible', 'Marqueur [illisible]', 'Gemini signale lui-même un passage illisible.'),
    ('vt_illisible', 'Passage illisible dans la VT', 'La VT marque elle-même un passage illisible (###) que Gemini a lu.'),
    ('exposant', 'Exposant / ordinal', 'Lettre supérieure (5e, 1er, 2°) notée ou omise : notation, pas lecture.'),
    ('ordre', 'Ordre de lecture', 'Même texte des deux côtés, à une autre place (dans la région ou une région voisine).'),
    ('correction_gemini', 'Gemini corrige l\'imprimé', 'kraken lit comme la VT (donc comme l\'imprimé), mais la forme Gemini est un mot courant et celle de la VT non : Gemini a normalisé une coquille ou une orthographe.'),
    ('erreur_gemini', 'Erreur de lecture Gemini', 'Gemini diffère de la VT ; la lecture kraken indépendante soutient la VT, et la forme Gemini n\'est pas plus courante.'),
    ('hallucination_substitution', 'Hallucination probable (mot remplacé)', 'Mot Gemini sans ressemblance avec la VT ; kraken soutient la VT.'),
    ('erreur_vt', 'Erreur probable de la VT', 'kraken (indépendant) soutient Gemini contre la VT : à vérifier sur l\'image.'),
    ('absent_vt', 'Texte sur l\'image absent de la VT', 'Ajout Gemini apparié à une ligne de pixels et confirmé par kraken : lacune de la VT.'),
    ('ajout_non_confirme', 'Ajout apparié mais non confirmé', 'Texte Gemini apparié à une ligne de pixels, absent de la VT, que kraken ne confirme pas : à regarder.'),
    ('hallucination_ajout', 'Ajout sans ligne détectée : à vérifier', 'Texte Gemini sans équivalent dans la VT et sans ligne détectée pour l\'arbitrer : hallucination possible tant qu\'une vérification visuelle ne l\'a pas écartée.'),
    ('omission', 'Omission Gemini', 'Texte de la VT que Gemini n\'a pas transcrit.'),
    ('indetermine', 'Indéterminé', 'Les deux textes diffèrent et kraken ne départage pas : regarder la vignette.'),
]
LABELS = {k: (label, help_) for k, label, help_ in CATEGORIES}


def typo(text):
    text = unicodedata.normalize('NFC', text).translate(TYPO)
    for a, b in LIGATURES.items():
        text = text.replace(a, b)
    return text


def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.category(c).startswith('M'))


def loose(token):
    """Clé d'appariement robuste : sans casse, accents, ponctuation."""
    key = re.sub(r'[\W_]+', '', strip_accents(typo(token)).casefold())
    return key or typo(token)


def is_punct(token):
    return not re.sub(r'[\W_]+', '', token)


def tokens_with_spans(text):
    return [(m.group(), m.start(), m.end()) for m in re.finditer(r'\S+', text)]


FINE = re.compile(r"\[illisible\]|\w*#{2,}\w*|\w(?:[\w'’\-]*\w)?|[^\w\s]+")


def fine_tokens(text):
    """Mots et ponctuation séparés : « résultats; » et « résultats ; » s'apparient."""
    return [(m.group(), m.start(), m.end()) for m in FINE.finditer(text)]


def load_reference_words(reference_path, regions):
    """Mots de la VT par région, en ordre géométrique ; boîtes de mots si présentes."""
    root = etree.parse(str(reference_path)).getroot()
    lines = []
    for line in root.findall('.//{*}TextLine'):
        box = _points(line)
        text = line.findtext('{*}TextEquiv/{*}Unicode')
        words = []
        for w in line.findall('{*}Word'):
            wt = w.findtext('{*}TextEquiv/{*}Unicode') or ''
            for t in wt.split():
                words.append(dict(text=nfc(t), bbox=_points(w) or box))
        if text is None:
            text = ' '.join(w['text'] for w in words)
        text = nfc((text or '').strip())
        if not text or box is None:
            continue
        if [w['text'] for w in words] != text.split():
            words = [dict(text=t, bbox=box) for t in text.split()]
        lines.append(dict(id=line.get('id'), text=text, bbox=box, words=words))
    grouped, unassigned = defaultdict(list), []
    for line in lines:
        x, y = (line['bbox'][0]+line['bbox'][2])/2, (line['bbox'][1]+line['bbox'][3])/2
        hits = [r['id'] for r in regions if r['bbox'][0] <= x < r['bbox'][2] and r['bbox'][1] <= y < r['bbox'][3]]
        if len(hits) == 1:
            grouped[hits[0]].append(line)
        else:
            unassigned.append(line)
    out, raw = {}, {}
    for rid, rows in grouped.items():
        ordered = geometric_order(rows)
        raw[rid] = '\n'.join(l['text'] for l in ordered)
        out[rid] = [dict(text=t, bbox=w['bbox'], line_id=l['id'], line_end=(k == len(l['words'])-1))
                    for l in ordered for k, w in enumerate(l['words']) for t, _, _ in fine_tokens(w['text'])]
    return out, unassigned, raw


def gemini_words(inspection, region_spans):
    """Mots Gemini par région, avec boîte si le mot a été posé sur l'image."""
    alignment = json.loads((inspection/'page-alignment.json').read_text())
    markdown = (inspection/'vt.gemini.md').read_text()
    plain = alignment['plain_text']
    block_region = _block_regions(markdown, alignment['blocks'], region_spans)
    boxes = {}  # début de mot -> boîte ; les sous-jetons cherchent leur mot englobant
    ranges = []
    for row in json.loads((inspection/'annotations.json').read_text()):
        if row.get('status') != 'retenue' or not row.get('words'):
            continue
        spans = row.get('source_spans')
        for (token, a, b), word in zip(tokens_with_spans(row['text']), row['words']):
            start = row['start']+(spans[a][0] if spans else a)
            end = row['start']+(spans[b-1][1] if spans else b)
            boxes[start] = dict(bbox=[word['x0'], word['y0'], word['x1'], word['y1']], line_id=row['id'])
            ranges.append((start, end, boxes[start]))
    ranges.sort(key=lambda r: r[0])
    range_starts = [r[0] for r in ranges]
    assigned = sorted((a['start'], a['end'], a['bbox'], a['line_id']) for a in alignment['assignments'])
    starts = [a[0] for a in assigned]

    def line_of(offset):
        k = bisect.bisect_right(starts, offset)-1
        if k >= 0 and assigned[k][0] <= offset < assigned[k][1]:
            return assigned[k]
        return None
    out = defaultdict(list)
    for block in alignment['blocks']:
        rid = block_region.get(block['id'])
        if rid is None:
            continue
        lines = block['text'].split('\n')
        offset = block['start']
        for k, line in enumerate(lines):
            toks = fine_tokens(line)
            for j, (token, a, b) in enumerate(toks):
                start = offset+a
                k = bisect.bisect_right(range_starts, start)-1
                placed = ranges[k][2] if k >= 0 and ranges[k][0] <= start < ranges[k][1] else None
                pixel_line = line_of(start)
                out[rid].append(dict(text=token, start=start, bbox=placed['bbox'] if placed else None,
                                     line_bbox=pixel_line[2] if pixel_line else None,
                                     line_id=placed['line_id'] if placed else (pixel_line[3] if pixel_line else None),
                                     line_end=(j == len(toks)-1)))
            offset += len(line)+1
    return out, plain


def lexicon(reference_dir, exclude):
    """Fréquence des mots dans les AUTRES pages de VT du même corpus."""
    counts = Counter()
    for path in sorted(Path(reference_dir).glob('*.xml')):
        if path.resolve() == Path(exclude).resolve():
            continue
        try:
            root = etree.parse(str(path)).getroot()
        except etree.XMLSyntaxError:
            continue
        for line in root.iter():
            if not isinstance(line.tag, str) or etree.QName(line).localname != 'TextLine':
                continue
            text = None
            for child in line:
                if isinstance(child.tag, str) and etree.QName(child).localname == 'TextEquiv':
                    text = ''.join(child.itertext())
            if text is None and etree.QName(root).localname.lower() == 'alto':
                text = ' '.join(s.get('CONTENT', '') for s in line if isinstance(s.tag, str) and etree.QName(s).localname == 'String')
            for token in (text or '').split():
                counts[word_key(token)] += 1
    return counts


def word_key(token):
    return re.sub(r'[\W_]+', '', typo(token)).casefold()


def kraken_reading(anchors, bbox):
    """Lecture CTC indépendante de la ligne détectée qui recouvre le plus la boîte."""
    if bbox is None:
        return '', None
    best, score = None, 0
    for line in anchors:
        b = line['bbox']
        w = max(0, min(b[2], bbox[2])-max(b[0], bbox[0]))
        h = max(0, min(b[3], bbox[3])-max(b[1], bbox[1]))
        if w*h > score:
            best, score = line, w*h
    return (best['auxiliary_text'], best['id']) if best else ('', None)


def union(boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def moved(keys, counters):
    """Texte retrouvé ailleurs : sur la page si le passage est substantiel
    (≥ 2 mots ou ≥ 5 lettres), sinon seulement dans la même région."""
    page, region = counters
    pool = page if (len(keys) >= 2 or sum(map(len, keys)) >= 5) else region
    return all(pool[k] > 0 for k in keys)


SUPERSCRIPT = re.compile(r'^(\d+)(e|er|ère|re|ème|me|°|o|bis)?$', re.I)


def classify(ref, hyp, region_ref_keys, region_hyp_keys, aux, lexicon_counts=None):
    """Catégorie d'une différence ; ref/hyp sont des listes de mots."""
    rt, ht = ' '.join(w['text'] for w in ref), ' '.join(w['text'] for w in hyp)
    if hyp and all(w['text'] in ('|', '||') or re.fullmatch(r'\|+', w['text']) for w in hyp) and not ref:
        return 'balisage', None
    if re.search(r'\[\s*illisible', ht):
        return 'illisible', None
    if '###' in rt:
        return 'vt_illisible', None
    if not ref:
        if all(is_punct(w['text']) for w in hyp):
            return 'ponctuation', None
        keys = [loose(w['text']) for w in hyp]
        if moved(keys, region_ref_keys):
            return 'ordre', None
        placed = sum((w['bbox'] or w.get('line_bbox')) is not None for w in hyp)/len(hyp)
        support = fuzz.partial_ratio(loose(ht), loose(aux)) if aux else 0
        if placed >= .5 and support >= 75:
            return 'absent_vt', support
        if placed >= .5:
            return 'ajout_non_confirme', support
        return 'hallucination_ajout', support
    if not hyp:
        if all(is_punct(w['text']) for w in ref):
            return 'ponctuation', None
        keys = [loose(w['text']) for w in ref]
        if moved(keys, region_hyp_keys):
            return 'ordre', None
        return 'omission', None
    # Les deux côtés existent.
    joined = lambda s: re.sub(r'[-¬]\s*', '', s)
    if typo(rt) == typo(ht) or re.sub(r'\s+', '', typo(rt)) == re.sub(r'\s+', '', typo(ht)):
        return 'normalisation', None
    if typo(rt).casefold() == typo(ht).casefold():
        return 'casse', None
    if joined(typo(rt)).replace(' ', '') == joined(typo(ht)).replace(' ', ''):
        return 'cesure', None
    a, b = re.sub(r'[\W_]+', '', typo(rt)), re.sub(r'[\W_]+', '', typo(ht))
    if a == b:
        return 'ponctuation', None
    if a.casefold() == b.casefold():
        return 'casse', None
    if strip_accents(a) == strip_accents(b):
        diff_upper = all(x == y or (strip_accents(x) == strip_accents(y) and x.isupper())
                         for x, y in zip(a, b)) if len(a) == len(b) else False
        if diff_upper:
            return 'accent_majuscule', None
    ma, mb = SUPERSCRIPT.match(a), SUPERSCRIPT.match(b)
    if ma and mb and ma.group(1) == mb.group(1):
        return 'exposant', None
    # Vraie divergence : arbitrage par la lecture kraken indépendante, AVEC
    # accents (une clé sans accents rendrait « a/à » toujours ex aequo).
    if not aux:
        return 'indetermine', None
    exact = lambda x: re.sub(r'[\W_]+', '', typo(x)).casefold()
    sr = fuzz.partial_ratio(exact(rt), exact(aux))
    sh = fuzz.partial_ratio(exact(ht), exact(aux))
    if len(a) <= 2 and not a.isdigit() and abs(sr-sh) < 30:
        return 'indetermine', (sr, sh)  # mot trop court pour un arbitrage fiable
    if sr == 100 and sh < 100 and len(a) >= 4:
        sh = min(sh, 100-8)  # kraken contient exactement la forme VT, pas la forme Gemini
    elif sh == 100 and sr < 100 and len(b) >= 4:
        sr = min(sr, 100-8)
    if sr >= sh+8:
        similarity = Levenshtein.normalized_similarity(loose(rt), loose(ht))
        if similarity < .4 and len(a) >= 3 and len(b) >= 3:
            return 'hallucination_substitution', (sr, sh)
        if lexicon_counts is not None and len(ref) == len(hyp) == 1:
            fr, fh = lexicon_counts[word_key(rt)], lexicon_counts[word_key(ht)]
            if fh >= 3 and fh >= 10*fr:
                return 'correction_gemini', (sr, sh)
        return 'erreur_gemini', (sr, sh)
    if sh >= sr+8:
        return 'erreur_vt', (sr, sh)
    return 'indetermine', (sr, sh)


def align_region(ref, hyp):
    """Blocs d'opérations mot à mot (clé robuste), puis sous-écarts bruts."""
    rk, hk = [loose(w['text']) for w in ref], [loose(w['text']) for w in hyp]
    items = []
    # Regrouper les opérations non égales contiguës (insertion + suppression
    # voisines = un remplacement) avant de les apparier.
    blocks = []
    for op in Levenshtein.opcodes(rk, hk):
        tag = 'equal' if op.tag == 'equal' else 'replace'
        if blocks and tag == 'replace' and blocks[-1][0] == 'replace':
            blocks[-1][2] = op.src_end; blocks[-1][4] = op.dest_end
        else:
            blocks.append([tag, op.src_start, op.src_end, op.dest_start, op.dest_end])
    for tag, s0, s1, d0, d1 in blocks:
        op = type('Op', (), dict(tag=tag if (s1 > s0 and d1 > d0) or tag == 'equal' else ('delete' if s1 > s0 else 'insert')))
        R, H = ref[s0:s1], hyp[d0:d1]
        if op.tag == 'equal':
            for r, h in zip(R, H):
                if r['text'] != h['text']:
                    items.append(([r], [h]))
            continue
        if op.tag == 'replace':
            # Ne jamais apparier un signe de ponctuation à un mot : mots avec
            # mots, signes avec signes, le reste en ajout/omission.
            rw, hw = [r for r in R if not is_punct(r['text'])], [h for h in H if not is_punct(h['text'])]
            rp, hp = [r for r in R if is_punct(r['text'])], [h for h in H if is_punct(h['text'])]
            for side_r, side_h in ((rw, hw), (rp, hp)):
                if len(side_r) == len(side_h):
                    items.extend(([r], [h]) for r, h in zip(side_r, side_h))
                elif side_r or side_h:
                    items.append((side_r, side_h))
        else:
            items.append((list(R), list(H)))
    return items


def crop(image, ref, hyp, margin=18, max_width=760):
    box = (union([w['bbox'] for w in ref+hyp]) or union([w.get('line_bbox') for w in hyp])
           or union([w.get('context_bbox') for w in hyp]))
    if box is None:
        return None
    x0, y0 = max(0, box[0]-margin*3), max(0, box[1]-margin)
    x1, y1 = min(image.width, box[2]+margin*3), min(image.height, box[3]+margin)
    tile = image.crop((x0, y0, x1, y1)).copy()
    draw = ImageDraw.Draw(tile)
    for w in ref:
        b = w['bbox']; draw.rectangle([b[0]-x0-2, b[1]-y0-2, b[2]-x0+2, b[3]-y0+2], outline=(30, 90, 230), width=2)
    for w in hyp:
        if not w['bbox'] and not w.get('line_bbox') and w.get('context_bbox'):
            b = w['context_bbox']; draw.rectangle([b[0]-x0, b[1]-y0, b[2]-x0, b[3]-y0], outline=(20, 160, 60), width=2)
        if not w['bbox'] and w.get('line_bbox'):
            b = w['line_bbox']; draw.rectangle([b[0]-x0, b[1]-y0, b[2]-x0, b[3]-y0], outline=(230, 140, 0), width=1)
        if w['bbox']:
            b = w['bbox']; draw.rectangle([b[0]-x0, b[1]-y0, b[2]-x0, b[3]-y0], outline=(220, 30, 30), width=2)
    if tile.width > max_width:
        tile = tile.resize((max_width, max(1, int(tile.height*max_width/tile.width))))
    buf = io.BytesIO(); tile.save(buf, 'JPEG', quality=72)
    return base64.b64encode(buf.getvalue()).decode()


def verification_key(item):
    return f"{item['region']}|{item['ref']}|{item['hyp']}"


def loose_key(key):
    """Clé tolérante au découpage des jetons (« triels. » ou « triels . »)."""
    region, ref, hyp = key.split('|', 2)
    clean = lambda t: re.sub(r'[\W_]+', '', t).casefold()
    return f"{region}|{clean(ref)}|{clean(hyp)}"


def build(manifest, transcription, inspection, output, title=None, verifications=None):
    transcription, inspection, output = Path(transcription), Path(inspection), Path(output)
    provenance = json.loads((transcription/'vt-provenance.json').read_text())
    regions = json.loads((transcription/'regions.json').read_text())['regions']
    pages = [p for p in json.loads(Path(manifest).read_text())['pages'] if p['image_sha256'] == provenance['image_sha256']]
    if len(pages) != 1:
        raise ValueError('Référence unique requise')
    page = pages[0]
    if sha256(page['reference']) != page['reference_sha256']:
        raise ValueError('Référence modifiée')
    if sha256(inspection/'vt.gemini.md') != provenance['artifact_sha256']:
        raise ValueError('Le dossier d\'inspection ne porte pas cette transcription')
    spans = {p['id']: p['span'] for p in provenance['parts']}
    ref_words, unassigned, ref_raw = load_reference_words(page['reference'], regions)
    hyp_words, _ = gemini_words(inspection, spans)
    lex = lexicon(Path(page['reference']).parent, page['reference'])
    anchor_file = inspection/'anchors.json'
    if not anchor_file.exists():  # variante raffinée : ancres du dossier initial voisin
        anchor_file = inspection.parent/'inspection'/'anchors.json'
    anchors = json.loads(anchor_file.read_text())['lines']
    image = Image.open(next(p for p in inspection.glob('*.jpg') if sha256(p) == page['image_sha256'])).convert('RGB')
    items = []
    region_lines = defaultdict(list)
    for line in anchors:
        x, y = (line['bbox'][0]+line['bbox'][2])/2, (line['bbox'][1]+line['bbox'][3])/2
        for r in regions:
            if r['bbox'][0] <= x < r['bbox'][2] and r['bbox'][1] <= y < r['bbox'][3]:
                region_lines[r['id']].append(line)
    pipes = Counter()
    page_ref = Counter(loose(w['text']) for ws in ref_words.values() for w in ws)
    page_hyp = Counter(loose(w['text']) for ws in hyp_words.values() for w in ws)
    for region in regions:
        ref, hyp = ref_words.get(region['id'], []), hyp_words.get(region['id'], [])
        pipes[region['id']] = sum(bool(re.fullmatch(r'\|+', w['text'])) for w in hyp)
        hyp = [w for w in hyp if not re.fullmatch(r'\|+', w['text'])]
        # Le texte peut avoir été lu dans une région voisine (titre à cheval) :
        # l'ordre se juge sur la page entière, pas seulement sur la région.
        rkeys = (page_ref, Counter(loose(w['text']) for w in ref))
        hkeys = (page_hyp, Counter(loose(w['text']) for w in hyp))
        if not ref and hyp:
            items.append(dict(region=region['id'], category='absent_vt', ref='', hyp=' '.join(w['text'] for w in hyp)[:400],
                              note='Région entière sans texte de référence', aux='', score=None,
                              crop=None, edits=0))
            continue
        position = {id(w): k for k, w in enumerate(hyp)}

        def context_box(H):
            """Zone entre les mots Gemini posés juste avant et juste après."""
            k0, k1 = position[id(H[0])], position[id(H[-1])]
            before = next((hyp[k] for k in range(k0-1, -1, -1) if hyp[k]['bbox'] or hyp[k].get('line_bbox')), None)
            after = next((hyp[k] for k in range(k1+1, len(hyp)) if hyp[k]['bbox'] or hyp[k].get('line_bbox')), None)
            boxes = [w.get('line_bbox') or w['bbox'] for w in (before, after) if w]
            return union(boxes)
        for R, H in align_region(ref, hyp):
            box = (union([w['bbox'] for w in H]) or union([w.get('line_bbox') for w in H])
                   or union([w['bbox'] for w in R]))
            aux, aux_line = kraken_reading(anchors, box)
            if box is None and H and not R:
                # Ligne Gemini non rattachée : la chercher parmi les lectures kraken
                # de SA région (ligne entière, pas un fragment d'une autre ligne).
                target = loose(' '.join(w['text'] for w in H))
                best = max(region_lines[region['id']], key=lambda l: fuzz.ratio(target, loose(l['auxiliary_text'])), default=None)
                if best is not None and fuzz.ratio(target, loose(best['auxiliary_text'])) >= 75:
                    aux, aux_line = best['auxiliary_text'], best['id']
                    for w in H:
                        w['line_bbox'] = best['bbox']
            category, score = classify(R, H, rkeys, hkeys, aux, lex)
            rt, ht = ' '.join(w['text'] for w in R), ' '.join(w['text'] for w in H)
            note = None
            if H and not R and union([w['bbox'] or w.get('line_bbox') for w in H]) is None:
                zone = context_box(H)
                if zone:
                    note = 'Vignette : zone entre les mots Gemini voisins (en vert), le texte n\'ayant pas été rattaché à une ligne.'
                    for w in H:
                        w['context_bbox'] = zone
            items.append(dict(region=region['id'], category=category, ref=rt, hyp=ht, aux=aux,
                              aux_line=aux_line, score=score, ref_line=R[0]['line_id'] if R else None,
                              gemini_offset=H[0]['start'] if H else None,
                              edits=Levenshtein.distance(rt, ht), crop=crop(image, R, H), note=note))
    # Espacement seul (« résultats ; » / « résultats; ») : invisible au niveau
    # des jetons, compté ici globalement pour ne rien perdre du décompte.
    from page_text_evaluation import markdown_text
    spacing = 0
    for region in regions:
        path = transcription/region['id']/'vt.gemini.md'
        if not path.exists() or region['id'] not in ref_raw:
            continue
        r, h = typo(ref_raw[region['id']]), typo(markdown_text(path.read_text())[0])
        r, h = re.sub(r'\s+', ' ', r), re.sub(r'\s+', ' ', h)
        spacing += max(0, Levenshtein.distance(r, h)-Levenshtein.distance(r.replace(' ', ''), h.replace(' ', '')))
    manual = json.loads(Path(verifications).read_text()) if verifications else {}
    manual_loose = {loose_key(k): v for k, v in manual.items()}
    for k, item in enumerate(items, 1):
        item['id'] = f'd{k:04d}'
        verdict = manual.get(verification_key(item)) or manual_loose.get(loose_key(verification_key(item)))
        if verdict:
            # Vérification visuelle humaine/Claude, tracée : la catégorie
            # automatique reste visible à côté du verdict.
            item.update(automatic_category=item['category'], category=verdict['category'],
                        verified=verdict['note'])
    counts = Counter(i['category'] for i in items)
    edits = Counter()
    for i in items:
        edits[i['category']] += i['edits']
    summary = dict(version=VERSION, page=page['id'], reference_sha256=page['reference_sha256'],
                   markdown_sha256=provenance['artifact_sha256'], inspection=str(inspection),
                   differences=len(items), by_category={k: counts[k] for k, _, _ in CATEGORIES if counts[k]},
                   raw_character_edits_by_category={k: edits[k] for k, _, _ in CATEGORIES if edits[k]},
                   unassigned_reference_lines=[l['id'] for l in unassigned],
                   visually_verified=sum('verified' in i for i in items),
                   spacing_only_character_edits=spacing,
                   gemini_table_pipes_ignored=sum(pipes.values()),
                   arbiter='kraken CTC (catmus-print-fondue-large), lecture indépendante de Gemini et de la VT',
                   lexicon=f'{sum(lex.values())} occurrences, {len(lex)} formes, des autres pages de VT du corpus (page évaluée exclue)',
                   order='région par région, lignes de VT en ordre géométrique')
    output.mkdir(parents=True, exist_ok=True)
    save_json(output/'differences.json', dict(summary=summary, items=[{k: v for k, v in i.items() if k != 'crop'} for i in items]))
    (output/'differences.html').write_text(render(summary, items, title or page['id']), encoding='utf-8')
    (output/'differences.artifact.html').write_text(render(summary, items, title or page['id'], document=False), encoding='utf-8')
    return summary


FAMILY = {'normalisation': 'forme', 'casse': 'forme', 'accent_majuscule': 'forme', 'ponctuation': 'forme',
          'cesure': 'forme', 'balisage': 'forme', 'exposant': 'forme', 'ordre': 'forme',
          'illisible': 'signal', 'vt_illisible': 'vt', 'correction_gemini': 'forme',
          'erreur_gemini': 'gemini', 'hallucination_substitution': 'gemini', 'omission': 'gemini',
          'erreur_vt': 'vt', 'absent_vt': 'vt', 'ajout_non_confirme': 'doute',
          'hallucination_ajout': 'doute', 'indetermine': 'doute'}
FAMILY_LABEL = {'forme': 'Forme, pas lecture', 'gemini': 'Faute de Gemini', 'vt': 'Faute ou lacune de la VT',
                'doute': 'À vérifier', 'signal': 'Signalé par Gemini'}


def render(summary, items, title, document=True):
    esc = html.escape
    by = defaultdict(list)
    for i in items:
        by[i['category']].append(i)
    families = Counter()
    for i in items:
        families[FAMILY[i['category']]] += 1
    chips = ''.join(f'<li class="fam f-{k}"><span class="n">{families[k]}</span> {esc(FAMILY_LABEL[k])}</li>'
                    for k in ('gemini', 'vt', 'doute', 'forme', 'signal') if families[k])
    rows = []
    for key, label, help_ in CATEGORIES:
        n = summary['by_category'].get(key, 0)
        if n:
            rows.append(f'<tr><td><span class="dot f-{FAMILY[key]}"></span><a href="#cat-{key}">{esc(label)}</a></td><td class="n">{n}</td>'
                        f'<td class="n">{summary["raw_character_edits_by_category"].get(key, 0)}</td><td class="muted">{esc(help_)}</td></tr>')
    sections = []
    for key, label, help_ in CATEGORIES:
        if not by[key]:
            continue
        cards = []
        for i in by[key]:
            img = f'<img loading="lazy" alt="vignette {i["id"]}" src="data:image/jpeg;base64,{i["crop"]}">' if i['crop'] else '<p class="muted">(pas de boîte sur l\'image)</p>'
            score = ''
            if isinstance(i.get('score'), (list, tuple)):
                score = f'<span class="muted">kraken proche VT {i["score"][0]:.0f} · proche Gemini {i["score"][1]:.0f}</span>'
            elif i.get('score') is not None:
                score = f'<span class="muted">appui kraken {i["score"]:.0f}</span>'
            extra = ''
            if i.get('note'):
                extra += f'<dt>note</dt><dd class="plain">{esc(i["note"])}</dd>'
            if i.get('verified'):
                extra += (f'<dt>vérifié</dt><dd class="plain">{esc(i["verified"])} '
                          f'(classement automatique : {esc(LABELS[i["automatic_category"]][0])})</dd>')
            cards.append(f'''<article id="{i["id"]}"><header><a href="#{i["id"]}">{i["id"]}</a><span>{esc(i["region"])}{(" · VT " + esc(i["ref_line"])) if i.get("ref_line") else ""}</span>{score}</header>
<dl><dt>VT</dt><dd class="ref">{esc(i["ref"]) or "<em>rien</em>"}</dd><dt>Gemini</dt><dd class="hyp">{esc(i["hyp"]) or "<em>rien</em>"}</dd>
<dt>kraken</dt><dd class="aux">{esc(i.get("aux") or "")}</dd>{extra}</dl>{img}</article>''')
        sections.append(f'<section id="cat-{key}"><h2><span class="dot f-{FAMILY[key]}"></span>{esc(label)} <small>{len(by[key])}</small></h2><p class="muted">{esc(help_)}</p><div class="cards">{"".join(cards)}</div></section>')
    style = '''<style>
/* Relevé d'écarts : en-tête de synthèse, puis une fiche par écart, groupées par catégorie. */
:root{--bg:#f7f7f4;--surface:#ffffff;--fg:#1c1d1f;--muted:#64666b;--line:#d9dad5;--ref:#1f55c9;--hyp:#b3261e;--vt:#1f55c9;--gemini:#b3261e;--doute:#a35d00;--forme:#7b7f86;--signal:#5b3fa6;
--display:"Literata",Georgia,serif;--body:"Atkinson Hyperlegible",system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141518;--surface:#1c1d21;--fg:#e9e9e6;--muted:#a1a3a8;--line:#33353a;--ref:#86a8ff;--hyp:#ff8a80;--vt:#86a8ff;--gemini:#ff8a80;--doute:#f0b45a;--forme:#9a9ea6;--signal:#b8a3f0;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141518;--surface:#1c1d21;--fg:#e9e9e6;--muted:#a1a3a8;--line:#33353a;--ref:#86a8ff;--hyp:#ff8a80;--vt:#86a8ff;--gemini:#ff8a80;--doute:#f0b45a;--forme:#9a9ea6;--signal:#b8a3f0;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font:15px/1.5 var(--body)}
.wrap{max-width:62rem;margin:0 auto;padding-inline:16px;padding-block:20px 48px}
h1,h2{font-family:var(--display);text-wrap:balance;line-height:1.2}h1{font-size:1.7rem;margin:0 0 .4rem}h2{font-size:1.25rem;margin:2.2rem 0 .3rem;display:flex;align-items:center;gap:.5rem}
h2 small{font:600 .85rem var(--body);color:var(--muted)}
.muted{color:var(--muted);font-size:.85rem}a{color:inherit}a:focus-visible{outline:2px solid var(--ref);outline-offset:2px}
.fams{list-style:none;padding:0;margin:1rem 0;display:flex;flex-wrap:wrap;gap:.5rem}.fam{border:1px solid var(--line);border-radius:999px;padding:.25rem .75rem;background:var(--surface);font-size:.9rem}.fam .n{font-weight:700;font-variant-numeric:tabular-nums}
.fam.f-gemini{border-color:var(--gemini)}.fam.f-vt{border-color:var(--vt)}.fam.f-doute{border-color:var(--doute)}
.dot{display:inline-block;width:.65rem;height:.65rem;border-radius:50%;margin-right:.4rem;flex:none}.dot.f-gemini{background:var(--gemini)}.dot.f-vt{background:var(--vt)}.dot.f-doute{background:var(--doute)}.dot.f-forme{background:var(--forme)}.dot.f-signal{background:var(--signal)}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;min-width:36rem}td,th{border-bottom:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}th{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.n{text-align:right;font-variant-numeric:tabular-nums}
.cards{display:grid;gap:.75rem}article{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:.7rem .8rem;min-width:0}
article header{display:flex;flex-wrap:wrap;gap:.3rem .8rem;font:.8rem var(--mono);color:var(--muted)}article header a{color:var(--fg);font-weight:700}
article img{max-width:100%;display:block;margin-top:.5rem;border-radius:3px}
dl{display:grid;grid-template-columns:4.5rem minmax(0,1fr);gap:.15rem .6rem;margin:.5rem 0 0}dt{color:var(--muted);font-size:.8rem;padding-top:.15rem}dd{margin:0;font-family:var(--mono);font-size:.9rem;overflow-wrap:anywhere}
dd.plain{font-family:var(--body)}.ref{color:var(--ref)}.hyp{color:var(--hyp)}
</style>'''
    fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=JetBrains+Mono:wght@400;700&family=Literata:opsz,wght@7..72,600&display=swap">'
    head = f'<title>Écarts Gemini VT {esc(title)}</title>{fonts}{style}'
    body = f'''<div class="wrap">
<h1>Écarts entre Gemini et la VT · {esc(title)}</h1>
<p class="muted">{summary["differences"]} différences, toutes listées ci-dessous. Comparaison {esc(summary["order"])}. Arbitre : {esc(summary["arbiter"])}. Lexique : {esc(summary.get("lexicon",""))}. {summary.get("visually_verified",0)} écarts vérifiés à l'œil (indiqué sur la fiche). Vignettes : boîtes VT en bleu, mots Gemini en rouge, ligne appariée sans mot exporté en orange, zone voisine en vert.</p>
<ul class="fams">{chips}</ul>
<p class="muted">Écarts d'espacement seul (espace avant « ; », espaces doubles…), non listés un par un : environ {summary.get("spacing_only_character_edits",0)} caractères.</p>
<div class="table"><table><thead><tr><th>Catégorie</th><th class="n">Écarts</th><th class="n">Caractères</th><th>Sens</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
{"".join(sections)}
</div>'''
    if document:
        return f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{head}</head><body>{body}</body></html>'
    return head+body


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('transcription')
    parser.add_argument('inspection')
    parser.add_argument('output')
    parser.add_argument('--title')
    parser.add_argument('--verifications', help='JSON {région|VT|Gemini: {category, note}} de vérifications visuelles')
    args = parser.parse_args()
    print(json.dumps(build(args.manifest, args.transcription, args.inspection, args.output, args.title, args.verifications),
                     ensure_ascii=False, indent=2))
