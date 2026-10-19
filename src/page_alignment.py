"""Apparier une VT de page à des lignes automatiques sans réécrire la VT.

L'OCR auxiliaire sert exclusivement d'adresse dans le texte Gemini. Il ne
remplace aucun caractère de ce texte et ne fournit aucune boîte de mot. Les
boîtes de lignes sont celles du détecteur, en coordonnées PIL [x0,y0,x1,y1).
Les sorties restent des propositions de placement, pas des annotations
d'entraînement validées. L'ordre des entrées n'impose jamais l'ordre de page.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import Counter
import hashlib
from html.parser import HTMLParser
import importlib.metadata
import json
import math
import re
from pathlib import Path
import unicodedata


VERSION = 'page-markdown-source-alignment-v3'


class _PresentationHTML(HTMLParser):
    """Retirer les seules balises connues ; exposer le reste sans perte."""
    inline_tags = {'a', 'abbr', 'b', 'big', 'cite', 'code', 'del', 'em', 'font',
                   'i', 'ins', 'kbd', 'mark', 'q', 's', 'samp', 'small', 'span',
                   'strike', 'strong', 'sub', 'sup', 'time', 'tt', 'u', 'var', 'wbr'}
    block_tags = {'address', 'article', 'aside', 'blockquote', 'caption', 'center',
                  'dd', 'div', 'dl', 'dt', 'figcaption', 'figure', 'footer',
                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'li', 'main',
                  'ol', 'p', 'pre', 'section', 'table', 'tbody', 'td', 'tfoot',
                  'th', 'thead', 'tr', 'ul'}

    def __init__(self, unhandled):
        super().__init__(convert_charrefs=True)
        self.parts, self.unhandled = [], unhandled

    def handle_starttag(self, tag, attrs):
        if tag in self.block_tags or tag in {'br', 'hr'}:
            self.parts.append('\n')
        elif tag == 'img':
            self.parts.append(dict(attrs).get('alt') or '')
        elif tag not in self.inline_tags:
            self.unhandled.add(tag)
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in self.block_tags:
            self.parts.append('\n')
        elif tag not in self.inline_tags and tag not in {'br', 'hr', 'img'}:
            self.unhandled.add(tag)
            self.parts.append('</'+tag+'>')

    def handle_data(self, data):
        self.parts.append(data)


def markdown_document(markdown):
    """Contenu rendu et blocs CommonMark ; le Markdown original reste intact.

    Les offsets de la sortie portent sur ``plain_text``, jamais sur les octets
    du Markdown. Les cartes de lignes Markdown permettent de remonter au bloc
    source, sans prétendre que les positions des marqueurs sont des glyphes.
    """
    from markdown_it import MarkdownIt
    if not isinstance(markdown, str):
        raise TypeError('La VT Markdown doit être une chaîne')
    parser = MarkdownIt('commonmark').enable('table')
    chunks, blocks, stack, unhandled, unhandled_html = [], [], [], set(), set()

    def html_text(value):
        reader = _PresentationHTML(unhandled_html)
        reader.feed(value)
        reader.close()
        return ''.join(reader.parts)

    def inline_text(children):
        content = []
        for child in children or []:
            if child.type in {'text', 'text_special', 'code_inline'}:
                content.append(child.content)
            elif child.type == 'image':
                content.append(inline_text(child.children))
            elif child.type == 'html_inline':
                content.append(html_text(child.content))
            elif child.type in {'softbreak', 'hardbreak'}:
                content.append('\n')
            elif not child.type.endswith(('_open', '_close')):
                unhandled.add(child.type)
                content.append(child.content)
        return ''.join(content)

    length = 0
    for token in parser.parse(markdown):
        if token.type.endswith('_open'):
            stack.append(token.type.removesuffix('_open'))
            continue
        if token.type.endswith('_close'):
            if stack:
                stack.pop()
            continue
        if token.type == 'inline':
            text = inline_text(token.children)
        elif token.type == 'html_block':
            text = html_text(token.content).strip('\n')
        elif token.type in {'fence', 'code_block'}:
            text = token.content.rstrip('\n')
        elif token.type == 'hr':
            continue
        else:
            unhandled.add(token.type)
            text = token.content
        if chunks:
            chunks.append('\n')
            length += 1
        start = length
        chunks.append(text)
        length += len(text)
        role = ('heading' if 'heading' in stack else 'table_cell' if
                any(s in stack for s in ('th', 'td')) else 'paragraph')
        blocks.append(dict(id=f'M{len(blocks)+1:04d}', start=start, end=length,
                           text=text, role=role, markdown_lines=token.map,
                           structure=list(stack)))
    return ''.join(chunks), blocks, dict(parser='markdown-it-py',
        version=importlib.metadata.version('markdown-it-py'),
        preset='commonmark+table', converter='bbvlm-production-page-text',
        converter_revision=2, unhandled_token_types=sorted(unhandled),
        unhandled_html_tags=sorted(unhandled_html))


_TYPOGRAPHY = str.maketrans({'’': "'", '‘': "'", 'ʼ': "'", 'ſ': 's',
                            'œ': 'oe', 'Œ': 'OE', 'æ': 'ae', 'Æ': 'AE', '¬': '-'})


def _search_text(text):
    """Clé tolérante et carte vers le texte exact ; jamais une sortie de VT."""
    characters, positions = [], []
    for index, character in enumerate(text):
        # Les graphies canoniquement équivalentes gardent les mêmes ancres.
        value = unicodedata.normalize('NFKD', character.translate(_TYPOGRAPHY)).casefold()
        for value_character in value:
            if unicodedata.category(value_character).startswith('M'):
                continue
            if value_character.isspace():
                value_character = ' '
                if not characters or characters[-1] == ' ':
                    continue
            characters.append(value_character)
            positions.append(index)
    if characters and characters[-1] == ' ':
        characters.pop()
        positions.pop()
    return ''.join(characters), positions


def _overlap(a, b):
    return max(0, min(a['end'], b['end'])-max(a['start'], b['start']))


def _spatially_precedes(first, second):
    """Deux voisins observés sur une même ligne ou une même colonne locale."""
    x0, y0, x1, y1 = first
    a0, b0, a1, b1 = second
    height = max(y1-y0, b1-b0)
    vertical_overlap = max(0, min(y1, b1)-max(y0, b0))/min(y1-y0, b1-b0)
    horizontal_overlap = max(0, min(x1, a1)-max(x0, a0))/min(x1-x0, a1-a0)
    same_line = vertical_overlap >= .5 and 0 <= a0-x1 <= 3*height
    same_column = horizontal_overlap >= .5 and 0 < (b0+b1-y0-y1)/2 <= 3*height
    return same_line or same_column


def _short_anchor_support(candidate, strong, by_id, line, plain):
    """Une clé ≤3 caractères requiert deux ancres fortes locales et ordonnées.

    Un chiffre de folio isolé ou une fin de mot détectée séparément n'est pas
    une adresse textuelle assez discriminante. Le texte reste sans placement
    en l'absence de deux voisins établis ; ni largeur inventée, ni raccord à
    une colonne lointaine pour satisfaire une occurrence textuelle unique.
    """
    previous = [(lid, other) for lid, other in strong if other['end'] <= candidate['start']]
    following = [(lid, other) for lid, other in strong if other['start'] >= candidate['end']]
    if not previous or not following:
        return None
    previous_id, previous = max(previous, key=lambda row: row[1]['end'])
    next_id, following = min(following, key=lambda row: row[1]['start'])
    if plain[previous['end']:candidate['start']].strip() or \
            plain[candidate['end']:following['start']].strip():
        return None
    if not _spatially_precedes(by_id[previous_id]['bbox'], line['bbox']) or \
            not _spatially_precedes(line['bbox'], by_id[next_id]['bbox']):
        return None
    return [previous_id, next_id]


def _hyphen_boundary(text, index):
    """Frontière explicitement marquée entre deux fragments alphanumériques."""
    return (1 < index < len(text) and text[index-1] == '-'
            and text[index-2].isalnum() and text[index].isalnum())


CLIP_TO_PHYSICAL_LINES = True


def _candidates(query, blocks, minimum_similarity, max_candidates, hyphen_reflow=True):
    """Recherche locale indépendante des colonnes et de l'ordre du détecteur."""
    from rapidfuzz.distance import Levenshtein
    from rapidfuzz import fuzz
    normalized, _ = _search_text(query)
    if not normalized:
        return []
    candidates = {}
    for block in blocks:
        haystack, positions = block['_search'], block['_positions']
        if not haystack:
            continue

        def add(start, end, clip=True, must_exceed=None):
            if start >= end:
                return
            # Une césure imprimée peut rester collée dans un paragraphe remis
            # à plat : « préoc-cupations ». Le tiret OBSERVÉ permet de retrouver
            # deux fragments source, sans ajouter/retirer le moindre caractère.
            # Une fin après ce tiret exige aussi un tiret terminal dans l'ancre.
            # Les autres frontières restent des espaces, jamais une coupure
            # arbitraire dans un mot ou une dé-césure reconstruite.
            while start > 0 and haystack[start-1] != ' ':
                if hyphen_reflow and _hyphen_boundary(haystack, start):
                    break
                start -= 1
            while end < len(haystack) and haystack[end] != ' ':
                if hyphen_reflow and normalized.endswith('-') and _hyphen_boundary(haystack, end):
                    break
                end += 1
            while start < end and haystack[start] == ' ':
                start += 1
            while end > start and haystack[end-1] == ' ':
                end -= 1
            found = haystack[start:end]
            score = Levenshtein.normalized_similarity(normalized, found)
            if must_exceed is not None and score <= must_exceed:
                return
            # Une fenêtre floue peut déborder sur la fin de la ligne imprimée
            # précédente (« 3/4 Pacific Central… » dans un tableau). Proposer
            # aussi les morceaux bornés par les retours à la ligne de Gemini,
            # retenus seulement s'ils correspondent strictement mieux ; rien
            # n'est retiré du texte source.
            if clip and CLIP_TO_PHYSICAL_LINES:
                for a, b in block['_physical_spans']:
                    if a < end and b > start and (a > start or b < end):
                        add(max(start, a), min(end, b), clip=False, must_exceed=score)
            # Un caractère/nombre bref doit correspondre exactement. Un score
            # élevé sur un sous-fragment ne prouve pas le reste de la ligne.
            if score < minimum_similarity or (len(normalized) < 6 and score != 1):
                return
            original_start = positions[start]
            original_end = positions[end-1]+1
            while original_end < len(block['text']) and \
                    unicodedata.category(block['text'][original_end]).startswith('M'):
                original_end += 1
            candidate = dict(start=block['start']+original_start,
                             end=block['start']+original_end,
                             similarity=score, block_id=block['id'])
            if hyphen_reflow and _hyphen_boundary(haystack, start):
                candidate['start_after_observed_hyphen'] = True
            if hyphen_reflow and _hyphen_boundary(haystack, end):
                candidate['end_after_observed_hyphen'] = True
            key = candidate['start'], candidate['end']
            if key not in candidates or candidates[key]['similarity'] < score:
                candidates[key] = candidate

        # Les lignes imprimées conservées par Gemini sont des candidats forts.
        for a, b in block['_physical_spans']:
            add(a, b)

        # Chercher aussi des sous-chaînes de paragraphes remis à la ligne par
        # le Markdown. Les répétitions restent toutes candidates et ambiguës.
        start, exact_count = 0, 0
        while True:
            start = haystack.find(normalized, start)
            if start < 0:
                break
            add(start, start+len(normalized))
            start += max(1, len(normalized))
            exact_count += 1
        if exact_count:
            continue
        pending = [(0, len(haystack))]
        attempts = 0
        while pending and attempts < max_candidates:
            a, b = pending.pop()
            if b-a < max(1, len(normalized)*minimum_similarity):
                continue
            alignment = fuzz.partial_ratio_alignment(normalized, haystack[a:b],
                                                       score_cutoff=100*minimum_similarity)
            attempts += 1
            if alignment is None:
                continue
            start, end = a+alignment.dest_start, a+alignment.dest_end
            add(start, end)
            if start > a:
                pending.append((a, start))
            if end < b:
                pending.append((end, b))
    # Les variantes recouvrant la même adresse ne sont pas des alternatives
    # spatiales. Une autre occurrence disjointe, même identique, en est une.
    distinct = []
    for candidate in sorted(candidates.values(),
                            key=lambda c: (-c['similarity'], c['start'], c['end'])):
        if any(_overlap(candidate, old) >= .5*min(candidate['end']-candidate['start'],
                                                old['end']-old['start']) for old in distinct):
            continue
        distinct.append(candidate)
    return distinct[:max_candidates]


def _validate_lines(lines, image_size):
    if image_size is None or len(image_size) != 2 or any(
            not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in image_size):
        raise ValueError('Dimensions source requises')
    width, height = image_size
    checked, ids = [], set()
    for line in lines:
        if not isinstance(line, dict) or not isinstance(line.get('id'), str) or not line['id']:
            raise ValueError('Identifiant de ligne automatique absent')
        if line['id'] in ids:
            raise ValueError('Identifiants de lignes dupliqués')
        ids.add(line['id'])
        bbox = line.get('bbox')
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4 or any(
                not isinstance(v, (int, float)) or not math.isfinite(v) for v in bbox):
            raise ValueError('Boîte de ligne automatique invalide')
        x0, y0, x1, y1 = bbox
        if not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height:
            raise ValueError('Boîte de ligne hors image source')
        detector_bbox = line.get('detector_bbox', bbox)
        if not isinstance(detector_bbox, (list, tuple)) or len(detector_bbox) != 4 or any(
                not isinstance(v, (int, float)) or not math.isfinite(v) for v in detector_bbox):
            raise ValueError('Boîte de détection invalide')
        x0, y0, x1, y1 = detector_bbox
        if not 0 <= x0 < x1 <= width or not 0 <= y0 < y1 <= height:
            raise ValueError('Boîte de détection hors image source')
        auxiliary = line.get('auxiliary_text', line.get('ocr_text', ''))
        if not isinstance(auxiliary, str):
            raise ValueError('Texte OCR auxiliaire invalide')
        checked.append({**line, 'bbox': list(bbox), 'detector_bbox': list(detector_bbox),
                        'auxiliary_text': auxiliary})
    return checked


def _block_regions(markdown, blocks, region_spans):
    """Région source de chaque bloc, par ses lignes Markdown ; jamais par le texte."""
    starts = sorted((markdown.count('\n', 0, a), markdown.count('\n', 0, max(a, b-1))+1, rid)
                    for rid, (a, b) in region_spans.items())
    out = {}
    for block in blocks:
        lines = block.get('markdown_lines')
        if not lines:
            continue
        inside = [rid for a, b, rid in starts if a <= lines[0] < b]
        if len(inside) == 1:
            out[block['id']] = inside[0]
    return out


def _region_reading_order(rows):
    """Lignes d'une région en ordre de lecture : y, puis x dans une même rangée."""
    rows = sorted(rows, key=lambda r: ((r['bbox'][1]+r['bbox'][3])/2, r['bbox'][0]))
    changed = True
    while changed:
        changed = False
        for i in range(len(rows)-1):
            a, b = rows[i]['bbox'], rows[i+1]['bbox']
            overlap = max(0, min(a[3], b[3])-max(a[1], b[1]))/max(1, min(a[3]-a[1], b[3]-b[1]))
            if overlap >= .5 and b[0] < a[0]:
                rows[i], rows[i+1] = rows[i+1], rows[i]
                changed = True
    return rows


def _column_reading_order(rows):
    """Ordre colonne par colonne : la région est coupée en bandes par les lignes
    qui traversent une gouttière verticale (titres, filets pleine largeur), et
    dans chaque bande les colonnes se lisent de gauche à droite, chacune de
    haut en bas. Gouttière = abscisse que ne croise aucune ligne d'au moins
    trois lignes de chaque côté, hors lignes qui la traversent (≤ 15 %)."""
    if len(rows) < 6:
        return list(rows)
    x0, x1 = min(r['bbox'][0] for r in rows), max(r['bbox'][2] for r in rows)
    step = max(1, (x1-x0)//200)
    gaps = []
    for x in range(x0+step, x1, step):
        crossing = sum(r['bbox'][0] < x < r['bbox'][2] for r in rows)
        left = sum(r['bbox'][2] <= x for r in rows)
        right = sum(r['bbox'][0] >= x for r in rows)
        if crossing <= .15*len(rows) and left >= 3 and right >= 3:
            if gaps and x-gaps[-1][-1] <= step:
                gaps[-1].append(x)
            else:
                gaps.append([x])
    if not gaps:
        return list(rows)
    cuts = [min(g, key=lambda x: sum(r['bbox'][0] < x < r['bbox'][2] for r in rows)) for g in gaps]
    by_y = sorted(rows, key=lambda r: ((r['bbox'][1]+r['bbox'][3])/2, r['bbox'][0]))
    out, band = [], []

    def flush():
        columns = [[] for _ in range(len(cuts)+1)]
        for r in band:
            centre = (r['bbox'][0]+r['bbox'][2])/2
            columns[sum(centre > c for c in cuts)].append(r)
        for column in columns:
            out.extend(_region_reading_order(column))
        band.clear()

    for r in by_y:
        if any(r['bbox'][0] < c < r['bbox'][2] for c in cuts):
            flush(); out.append(r)
        else:
            band.append(r)
    flush()
    return out


def _anchored_reading_order(rows, chosen):
    """Ordre de lecture d'une région choisi d'après les lignes déjà ancrées :
    rangée par rangée (défaut) ou colonne par colonne (tableaux côte à côte que
    Gemini lit colonne après colonne), selon celui qui garde le plus d'ancres
    dans l'ordre du texte. Aucun texte n'est lu ici : seules les ancres votent."""
    row_major = _region_reading_order(rows)
    column_major = _column_reading_order(rows)
    if [r['id'] for r in column_major] == [r['id'] for r in row_major]:
        return row_major

    def kept(order):
        return len(_increasing([chosen[r['id']]['start'] for r in order if r['id'] in chosen]))
    # marge : une ou deux ancres de plus peuvent tenir du hasard
    by_rows, by_columns = kept(row_major), kept(column_major)
    return column_major if by_columns >= by_rows + max(2, .05*by_rows) else row_major


def _increasing(values):
    """Indices d'une plus longue sous-suite strictement croissante."""
    import bisect
    tails, tail_index, parent = [], [], [None]*len(values)
    for i, v in enumerate(values):
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v); tail_index.append(i)
        else:
            tails[k] = v; tail_index[k] = i
        parent[i] = tail_index[k-1] if k else None
    out, i = [], tail_index[-1] if tail_index else None
    while i is not None:
        out.append(i); i = parent[i]
    return out[::-1]


def _gap_pairs(pixel_rows, text_rows, px_per_char, minimum_similarity):
    """Apparier dans l'ordre les lignes d'un intervalle encadré par deux ancres.

    Les deux suites sont ordonnées et bornées par des ancres textuelles sûres ;
    on cherche l'appariement monotone de score maximal. Une paire exige une
    largeur observée compatible avec la longueur du texte ET, sauf si
    l'intervalle ne contient qu'une ligne de chaque côté, une ressemblance
    minimale de la lecture auxiliaire. Le texte n'est jamais modifié.
    """
    from rapidfuzz.distance import Levenshtein
    n, m = len(pixel_rows), len(text_rows)
    if not n or not m:
        return []
    one_to_one = n == 1 and m == 1

    def score(p, t):
        key = _search_text(t['text'])[0]
        aux = _search_text(p['auxiliary_text'])[0]
        if not key:
            return None
        width = p['bbox'][2]-p['bbox'][0]
        ratio = width/(len(key)*px_per_char)
        if not .6 <= ratio <= 1.6:
            return None
        sim = Levenshtein.normalized_similarity(key, aux) if aux else 0.
        # Une ressemblance forte ici vient d'une ligne ambiguë ou concurrente :
        # c'est l'ordre entre deux ancres qui choisit l'occurrence, pas le score.
        if not one_to_one and sim < .4:
            return None
        return .5+sim
    table = [[score(p, t) for t in text_rows] for p in pixel_rows]
    best = [[0.]*(m+1) for _ in range(n+1)]
    for i in range(n-1, -1, -1):
        for j in range(m-1, -1, -1):
            options = [best[i+1][j], best[i][j+1]]
            if table[i][j] is not None:
                options.append(table[i][j]+best[i+1][j+1])
            best[i][j] = max(options)
    pairs, i, j = [], 0, 0
    while i < n and j < m:
        if table[i][j] is not None and abs(best[i][j]-(table[i][j]+best[i+1][j+1])) < 1e-12:
            pairs.append((i, j, table[i][j]-.5)); i += 1; j += 1
        elif best[i][j] == best[i+1][j]:
            i += 1
        else:
            j += 1
    return pairs


def _split_tokens(text, cells):
    """Répartit les mots de ``text`` (dans l'ordre) sur les cellules (dans l'ordre x)
    en maximisant la ressemblance à leur lecture CTC ; renvoie [(a, b, sim)] en
    offsets de ``text``."""
    from rapidfuzz.distance import Levenshtein
    tokens = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
    n, k = len(tokens), len(cells)
    if n < k or k == 0:
        return None
    keys = [_search_text(c['auxiliary_text'])[0] for c in cells]

    def sim(i, j, c):
        found = _search_text(text[tokens[i][0]:tokens[j-1][1]])[0]
        return Levenshtein.normalized_similarity(keys[c], found) if keys[c] else 0.

    best = {(0, 0): (0., [])}
    for c in range(k):
        for i in range(n):
            if (i, c) not in best:
                continue
            score, path = best[(i, c)]
            for j in range(i+1, n-(k-c-1)+1):
                value = sim(i, j, c)
                key = (j, c+1)
                if key not in best or best[key][0] < score+value:
                    best[key] = (score+value, path+[(tokens[i][0], tokens[j-1][1], value)])
    return best.get((n, k), (0., None))[1]


def _complete_table_rows(lines, states, proposals, plain, blocks, line_regions, posteriors=None):
    """Rangées de tableau : Gemini écrit la rangée sur UNE ligne, le détecteur la
    coupe en cellules. Quand une cellule de la rangée est appariée, le reste de
    la MÊME ligne imprimée de Gemini est réparti, dans l'ordre gauche-droite, sur
    les cellules non appariées situées à la même hauteur (même région). Chaque
    morceau doit ressembler (>= .4) à la lecture CTC de sa cellule et en avoir
    à peu près la longueur (rapport .6-1.6 hors espaces). Aucun texte
    source n'est modifié."""
    by_id = {l['id']: l for l in lines}
    chosen = {lid: proposals[lid][0] for lid in states if states[lid] == 'candidate'}
    used = [(c['start'], c['end']) for c in chosen.values()]
    support = {}

    def physical(offset):
        end = plain.find('\n', offset)
        return plain.rfind('\n', 0, offset)+1, end if end >= 0 else len(plain)

    def same_row(a, b):
        overlap = min(a[3], b[3]) - max(a[1], b[1])
        return overlap >= .5*min(a[3]-a[1], b[3]-b[1])

    seen = set()
    for lid, candidate in sorted(chosen.items(), key=lambda kv: kv[1]['start']):
        p0, p1 = physical(candidate['start'])
        if (p0, p1) in seen or candidate['end'] > p1:
            continue
        seen.add((p0, p1))
        members = [(m, chosen[m]) for m in chosen if p0 <= chosen[m]['start'] and chosen[m]['end'] <= p1]
        box = by_id[lid]['bbox']
        region = line_regions.get(lid) if line_regions else None
        cells = [l for l in lines if states[l['id']] != 'candidate' and l.get('auxiliary_text')
                 and same_row(box, l['bbox'])
                 and (line_regions is None or line_regions.get(l['id']) == region)]
        if not cells:
            continue
        items = sorted([('m', by_id[m]['bbox'][0], m) for m, _ in members] +
                       [('c', l['bbox'][0], l['id']) for l in cells], key=lambda t: t[1])
        # intervalles de texte libres entre membres consécutifs (ordre du texte = ordre x)
        member_spans = sorted((c['start'], c['end'], m) for m, c in members)
        if [m for _, _, m in member_spans] != [t[2] for t in items if t[0] == 'm']:
            continue  # ordre du texte et ordre spatial en désaccord : ne rien supposer
        bounds = [p0] + [x for a, b, _ in member_spans for x in (a, b)] + [p1]
        groups, current = [], []
        for kind, _, ident in items:
            if kind == 'm':
                groups.append(current); current = []
            else:
                current.append(by_id[ident])
        groups.append(current)
        for g, group in enumerate(groups):
            if not group:
                continue
            a, b = bounds[2*g], bounds[2*g+1]
            text = plain[a:b]
            if not text.strip():
                continue
            if posteriors is not None and all(posteriors.logp(c['id']) is not None for c in group):
                # répartition choisie par l'image : vraisemblance CTC de chaque
                # morceau sur sa cellule ; texte sans cellule laissé libre
                from block_ctc import solve_gap
                left = member_spans[g-1] if g > 0 else None
                if left is not None and posteriors.logp(left[2]) is not None:
                    # La ligne ancrée à gauche (le nom de la rangée) entre dans le
                    # même calcul : sa fin peut avoir avalé le début de la cellule
                    # suivante (« Café fair Rio…… 12 » + « 1/4 »).
                    m0, m1, mid = left
                    joint = solve_gap([by_id[mid]] + group, plain[m0:b], posteriors)
                    first = next((p for p in joint if p[0] == 0), None)
                    if first is not None and first[3] >= -3.0 and first[1] == 0 and first[2] > 0:
                        new_end = m0 + first[2]
                        if new_end != m1:
                            if (m0, m1) in used:
                                used.remove((m0, m1))
                            used.append((m0, new_end))
                            proposals[mid][0].update(end=new_end)
                            support[mid] = dict(method='row_anchor_end_adjusted_by_ctc', old_end=m1, new_end=new_end,
                                                mean_log_likelihood_per_character=round(float(first[3]), 3))
                        a = new_end
                        text = plain[a:b]
                        pieces = {k-1: (x0 + m0 - a, x1 + m0 - a, score) for k, x0, x1, score in joint if k > 0}
                    else:
                        pieces = {k: (x0, x1, score) for k, x0, x1, score in solve_gap(group, text, posteriors)}
                else:
                    pieces = {k: (x0, x1, score) for k, x0, x1, score in solve_gap(group, text, posteriors)}
                for k, cell in enumerate(group):
                    if k not in pieces or pieces[k][2] < -3.0:
                        continue
                    x0, x1, score = pieces[k]
                    start, end = a+x0, a+x1
                    if end <= start or any(u0 < end and start < u1 for u0, u1 in used):
                        continue
                    block = next((blk for blk in blocks if blk['start'] <= start and end <= blk['end']), None)
                    if block is None:
                        continue
                    proposals[cell['id']] = [dict(start=start, end=end, similarity=round(math.exp(score), 3),
                                                  block_id=block['id'])]
                    states[cell['id']] = 'candidate'
                    used.append((start, end))
                    support[cell['id']] = dict(method='same_row_ctc_likelihood', row_anchor=lid,
                                               mean_log_likelihood_per_character=round(score, 3))
                continue
            split = _split_tokens(text, group)
            if not split:
                continue
            for cell, (x0, x1, value) in zip(group, split):
                start, end = a+x0, a+x1
                piece = sum(not ch.isspace() for ch in plain[start:end])
                seen_chars = max(1, sum(not ch.isspace() for ch in cell['auxiliary_text']))
                if value < .4 or not .6 <= piece/seen_chars <= 1.6 or \
                        any(u0 < end and start < u1 for u0, u1 in used):
                    continue
                block = next((blk for blk in blocks if blk['start'] <= start and end <= blk['end']), None)
                if block is None:
                    continue
                proposals[cell['id']] = [dict(start=start, end=end, similarity=value, block_id=block['id'])]
                states[cell['id']] = 'candidate'
                used.append((start, end))
                support[cell['id']] = dict(method='same_row_rest_of_gemini_line', row_anchor=lid,
                                           auxiliary_similarity=value)
    return support


def _ctc_gap_fill(lines, states, proposals, plain, blocks, line_regions, posteriors,
                  minimum_score=-3.0):
    """Entre deux ancres d'une région, découper le texte Gemini libre entre les
    lignes restantes par vraisemblance CTC (``block_ctc.solve_gap``) : c'est
    l'image, pas une lecture intermédiaire, qui choisit les coupures. Morceau
    retenu si sa log-vraisemblance moyenne par caractère >= ``minimum_score``."""
    from block_ctc import solve_gap
    support = {}
    if line_regions is None or posteriors is None:
        return support
    chosen = {lid: proposals[lid][0] for lid in states if states[lid] == 'candidate'}
    used = sorted((c['start'], c['end']) for c in chosen.values())
    for rid in sorted(set(line_regions.values())):
        rows = _anchored_reading_order([l for l in lines if line_regions.get(l['id']) == rid], chosen)
        anchored = [(k, chosen[r['id']]) for k, r in enumerate(rows) if r['id'] in chosen]
        keep = _increasing([c['start'] for _, c in anchored])
        anchored = [anchored[k] for k in keep]
        if not anchored:
            continue
        region_blocks = sorted({c['block_id'] for _, c in anchored})
        members = [b for b in blocks if b['id'] in region_blocks]
        r0, r1 = min(b['start'] for b in members), max(b['end'] for b in members)
        bounds = [(-1, r0)] + [(k, c['end']) for k, c in anchored] + [(len(rows), None)]
        starts = [c['start'] for _, c in anchored] + [r1]
        for g, ((k0, t0), (k1, _)) in enumerate(zip(bounds, bounds[1:])):
            t1 = starts[g]
            pixel = [r for r in rows[k0+1:k1] if states[r['id']] != 'candidate']
            if not pixel or t1 <= t0 or len(pixel) > 40 or t1-t0 > 4000:
                continue
            free, where = [], []
            for i in range(t0, t1):
                if not any(u0 <= i < u1 for u0, u1 in used):
                    free.append(plain[i]); where.append(i)
            text = ''.join(free)
            if not text.strip():
                continue
            for k, a, b, score in solve_gap(pixel, text, posteriors):
                if score < minimum_score or b <= a:
                    continue
                start, end = where[a], where[b-1]+1
                if end-start != b-a or any(u0 < end and start < u1 for u0, u1 in used):
                    continue  # le morceau enjamberait du texte déjà attribué
                block = next((blk for blk in blocks if blk['start'] <= start and end <= blk['end']), None)
                if block is None:
                    continue
                line = pixel[k]
                proposals[line['id']] = [dict(start=start, end=end, similarity=round(math.exp(score), 3),
                                              block_id=block['id'])]
                states[line['id']] = 'candidate'
                used.append((start, end))
                support[line['id']] = dict(method='ctc_likelihood_between_anchors',
                                           mean_log_likelihood_per_character=round(score, 3),
                                           previous_anchor=rows[k0]['id'] if k0 >= 0 else None,
                                           next_anchor=rows[k1]['id'] if k1 < len(rows) else None)
    return support


def _character_gap_fill(lines, states, proposals, plain, blocks, line_regions):
    """Dernier passage, purement positionnel : entre deux lignes ancrées d'une
    région (ordre de lecture géométrique), aligner caractère par caractère la
    lecture CTC concaténée des lignes restantes sur le texte Gemini encore libre.
    Résout les en-têtes répétés (« Jeudi Vendr. » ×3), les fractions mal lues
    par le CTC et le texte espacé (« T R I B U N A U X »), dont la recherche
    ligne par ligne ne peut pas trancher. Chaque morceau doit garder une
    longueur compatible (rapport .5-2 hors espaces) et une ressemblance hors
    espaces >= .4. Aucun texte source n'est modifié ni déplacé."""
    from rapidfuzz.distance import Levenshtein
    support = {}
    if line_regions is None:
        return support
    chosen = {lid: proposals[lid][0] for lid in states if states[lid] == 'candidate'}
    used = sorted((c['start'], c['end']) for c in chosen.values())

    def squeeze(text):
        return ''.join(ch for ch in text.lower() if not ch.isspace())

    for rid in sorted(set(line_regions.values())):
        rows = _anchored_reading_order([l for l in lines if line_regions.get(l['id']) == rid], chosen)
        anchored = [(k, chosen[r['id']]) for k, r in enumerate(rows) if r['id'] in chosen]
        keep = _increasing([c['start'] for _, c in anchored])
        anchored = [anchored[k] for k in keep]
        if not anchored:
            continue
        region_blocks = sorted({c['block_id'] for _, c in anchored})
        members = [b for b in blocks if b['id'] in region_blocks]
        r0, r1 = min(b['start'] for b in members), max(b['end'] for b in members)
        bounds = [(-1, r0)] + [(k, c['end']) for k, c in anchored] + [(len(rows), None)]
        starts = [c['start'] for _, c in anchored] + [r1]
        for g, ((k0, t0), (k1, _)) in enumerate(zip(bounds, bounds[1:])):
            t1 = starts[g]
            pixel = [r for r in rows[k0+1:k1] if states[r['id']] != 'candidate'
                     and len(r['auxiliary_text'].strip()) >= 2]
            if not pixel or t1 <= t0:
                continue
            # texte libre de l'intervalle, avec correspondance vers ``plain``
            free, where = [], []
            for i in range(t0, t1):
                if not any(u0 <= i < u1 for u0, u1 in used):
                    free.append(plain[i]); where.append(i)
            text = ''.join(free)
            if not squeeze(text):
                continue
            aux, ranges = '', []
            for r in pixel:
                if aux:
                    aux += ' '
                ranges.append((len(aux), len(aux)+len(r['auxiliary_text'])))
                aux += r['auxiliary_text']
            mapping = [None]*len(aux)
            for op in Levenshtein.opcodes(aux.lower(), text.lower()):
                if op.tag == 'insert':
                    continue
                span_src = op.src_end-op.src_start
                span_dst = op.dest_end-op.dest_start
                for i in range(op.src_start, op.src_end):
                    mapping[i] = (op.dest_start + (i-op.src_start)*span_dst//max(1, span_src)
                                  if span_dst else op.dest_start)
            pieces = []
            for r, (a0, a1) in zip(pixel, ranges):
                mapped = [mapping[i] for i in range(a0, a1) if mapping[i] is not None]
                if not mapped:
                    pieces.append(None); continue
                pieces.append([min(mapped), max(mapped)+1])
            # bornes aux espaces ; pas de chevauchement entre lignes voisines
            last_end = 0
            for piece in pieces:
                if piece is None:
                    continue
                b = min(piece[1], len(text))
                a = min(max(piece[0], last_end), b)
                while a > last_end and not text[a-1].isspace():
                    a -= 1
                while b < len(text) and not text[b].isspace():
                    b += 1
                while a < b and text[a].isspace():
                    a += 1
                while b > a and text[b-1].isspace():
                    b -= 1
                piece[0], piece[1] = a, b
                if b > a:
                    last_end = b
            for r, piece in zip(pixel, pieces):
                if piece is None or piece[1] <= piece[0]:
                    continue
                a, b = where[piece[0]], where[piece[1]-1]+1
                if any(u0 < b and a < u1 for u0, u1 in used) or b-a != piece[1]-piece[0]:
                    continue  # le morceau enjamberait du texte déjà attribué
                found, seen = squeeze(plain[a:b]), squeeze(r['auxiliary_text'])
                if not seen or not .5 <= len(found)/len(seen) <= 2:
                    continue
                similarity = Levenshtein.normalized_similarity(seen, found)
                if similarity < .4:
                    continue
                block = next((blk for blk in blocks if blk['start'] <= a and b <= blk['end']), None)
                if block is None:
                    continue
                proposals[r['id']] = [dict(start=a, end=b, similarity=similarity, block_id=block['id'])]
                states[r['id']] = 'candidate'
                used.append((a, b))
                support[r['id']] = dict(method='character_alignment_between_anchors',
                                        previous_anchor=rows[k0]['id'] if k0 >= 0 else None,
                                        next_anchor=rows[k1]['id'] if k1 < len(rows) else None,
                                        auxiliary_similarity_without_spaces=similarity)
    return support


def align_page(markdown, lines, *, image_size, minimum_similarity=.72,
               ambiguity_margin=.06, max_candidates=12, hyphen_reflow=True,
               line_regions=None, region_spans=None, ctc_posteriors=None):
    """Proposer des correspondances entre VT et lignes détectées sur la source.

    ``lines`` contient ``id``, ``bbox`` et ``auxiliary_text`` (ou ``ocr_text``).
    L'appelant fournit exclusivement des sorties automatiques image-only. Les
    champs optionnels ``source``, ``baseline`` et ``polygon`` sont conservés.
    Aucune lecture de fichier, reconnaissance ou utilisation d'une référence.
    Un appariement exact n'est pas une validation de géométrie ou du texte.
    """
    if not 0 < minimum_similarity <= 1 or not 0 <= ambiguity_margin < 1 or max_candidates < 2:
        raise ValueError('Seuils d’appariement invalides')
    if type(hyphen_reflow) is not bool:
        raise ValueError('Option de césure invalide')
    lines = _validate_lines(list(lines), image_size)
    plain, blocks, conversion = markdown_document(markdown)
    indexed = []
    for block in blocks:
        normalized, positions = _search_text(block['text'])
        physical_spans, offset = [], 0
        for physical in block['text'].splitlines(keepends=True):
            physical_spans.append((bisect_left(positions, offset),
                bisect_left(positions, offset+len(physical.rstrip('\r\n')))))
            offset += len(physical)
        indexed.append({**block, '_search': normalized, '_positions': positions,
                        '_physical_spans': physical_spans})
    # Option régionale : une ligne de pixels n'est cherchée que dans le texte
    # que Gemini a lu sur le recadrage de SA région (plan automatique figé).
    regional = line_regions is not None and region_spans is not None
    block_region = _block_regions(markdown, blocks, region_spans) if regional else {}
    proposals = {}
    states = {}
    for line in lines:
        searched = indexed
        if regional and line['id'] in line_regions:
            searched = [b for b in indexed if block_region.get(b['id']) == line_regions[line['id']]]
        candidates = _candidates(line['auxiliary_text'], searched,
                                 minimum_similarity, max_candidates, hyphen_reflow)
        proposals[line['id']] = candidates
        if not line['auxiliary_text'].strip():
            states[line['id']] = 'no_auxiliary_text'
        elif not candidates:
            states[line['id']] = 'no_text_match'
        elif len(candidates) > 1 and candidates[0]['similarity']-candidates[1]['similarity'] <= ambiguity_margin:
            states[line['id']] = 'ambiguous_text_match'
        else:
            states[line['id']] = 'candidate'

    # Un caractère de la VT ne peut pas servir à deux lignes. Les conflits
    # comparables sont exposés, même si le détecteur a dupliqué une boîte.
    candidates = [(line['id'], proposals[line['id']][0]) for line in lines
                  if states[line['id']] == 'candidate']
    conflicts = set()
    for index, (lid, candidate) in enumerate(candidates):
        for other_id, other in candidates[index+1:]:
            if not _overlap(candidate, other):
                continue
            difference = candidate['similarity']-other['similarity']
            if abs(difference) <= ambiguity_margin:
                conflicts.update((lid, other_id))
            else:
                conflicts.add(other_id if difference > 0 else lid)
    for lid in conflicts:
        states[lid] = 'competing_line_match'

    # Une occurrence textuelle unique ne suffit pas pour un micro-fragment.
    # Les ancres de contexte sont toutes longues, déjà non ambiguës, sans
    # conflit et de similarité ≥.9 ; elles ne dépendent pas de cette décision.
    by_id = {line['id']: line for line in lines}
    key_lengths = {line['id']: len(_search_text(line['auxiliary_text'])[0]) for line in lines}
    strong = [(lid, candidate) for lid, candidate in candidates if states[lid] == 'candidate'
              and key_lengths[lid] > 3 and candidate['similarity'] >= .9]
    context_support = {}
    for lid, candidate in candidates:
        if states[lid] != 'candidate' or key_lengths[lid] > 3:
            continue
        support = _short_anchor_support(candidate, strong, by_id, by_id[lid], plain)
        if support is None:
            states[lid] = 'short_anchor_without_spatial_context'
        else:
            context_support[lid] = support

    gap_support = {}
    if regional:
        chosen = {lid: proposals[lid][0] for lid in states if states[lid] == 'candidate'}
        used = sorted((c['start'], c['end']) for c in chosen.values())
        for rid in sorted(set(line_regions.values())):
            members = [b for b in blocks if block_region.get(b['id']) == rid]
            if not members:
                continue
            r0, r1 = min(b['start'] for b in members), max(b['end'] for b in members)
            rows = _anchored_reading_order([l for l in lines if line_regions.get(l['id']) == rid], chosen)
            anchored = [(k, chosen[r['id']]) for k, r in enumerate(rows)
                        if r['id'] in chosen and r0 <= chosen[r['id']]['start'] < r1]
            keep = _increasing([c['start'] for _, c in anchored])
            anchored = [anchored[k] for k in keep]
            widths = [(rows[k]['bbox'][2]-rows[k]['bbox'][0])/max(1, len(_search_text(c and plain[c['start']:c['end']])[0]))
                      for k, c in anchored if c['end']-c['start'] >= 12]
            if len(widths) < 5:
                continue
            px_per_char = sorted(widths)[len(widths)//2]
            bounds = [(-1, None, r0)] + [(k, c['start'], c['end']) for k, c in anchored] + [(len(rows), r1, None)]
            for (k0, _, t0), (k1, t1, _) in zip(bounds, bounds[1:]):
                pixel_rows = [r for r in rows[k0+1:k1] if states[r['id']] != 'candidate']
                text_rows, offset = [], t0
                for physical in plain[t0:t1].split('\n'):
                    a, b = offset, offset+len(physical)
                    offset = b+1
                    while a < b and plain[a].isspace(): a += 1
                    while b > a and plain[b-1].isspace(): b -= 1
                    if a < b and not any(u0 < b and a < u1 for u0, u1 in used) and \
                            any(blk['start'] <= a and b <= blk['end'] for blk in members):
                        text_rows.append(dict(start=a, end=b, text=plain[a:b]))
                for i, j, sim in _gap_pairs(pixel_rows, text_rows, px_per_char, minimum_similarity):
                    row, t = pixel_rows[i], text_rows[j]
                    block = next(blk for blk in members if blk['start'] <= t['start'] and t['end'] <= blk['end'])
                    proposals[row['id']] = [dict(start=t['start'], end=t['end'], similarity=sim,
                                                 block_id=block['id'])]
                    states[row['id']] = 'candidate'
                    gap_support[row['id']] = dict(method='regional_order_between_anchors',
                        previous_anchor=rows[k0]['id'] if k0 >= 0 else None,
                        next_anchor=rows[k1]['id'] if k1 < len(rows) else None,
                        auxiliary_similarity=sim, pixel_rows_in_gap=len(pixel_rows),
                        text_rows_in_gap=len(text_rows))
                    used.append((t['start'], t['end']))

    row_support = _complete_table_rows(lines, states, proposals, plain, blocks,
                                       line_regions if regional else None, ctc_posteriors)
    ctc_support = _ctc_gap_fill(lines, states, proposals, plain, blocks,
                                line_regions if regional else None, ctc_posteriors)
    character_support = _character_gap_fill(lines, states, proposals, plain, blocks,
                                            line_regions if regional else None)

    assignments, unmatched = [], []
    for line in lines:
        lid = line['id']
        if states[lid] != 'candidate':
            unmatched.append(dict(id=lid, bbox=line['bbox'], detector_bbox=line['detector_bbox'], status=states[lid],
                auxiliary_text=line['auxiliary_text'], candidates=proposals[lid]))
            continue
        candidate = proposals[lid][0]
        assignments.append(dict(id=lid, line_id=lid, **candidate,
            text=plain[candidate['start']:candidate['end']], bbox=line['bbox'],
            detector_bbox=line['detector_bbox'],
            source=line.get('source'), baseline=line.get('baseline', []),
            polygon=line.get('polygon', []), auxiliary_text=line['auxiliary_text'],
            status='matched', geometry_status='detected_line_only',
            training_eligible=False))
        if lid in context_support:
            assignments[-1]['spatial_context_line_ids'] = context_support[lid]
        if lid in gap_support:
            assignments[-1]['regional_order_support'] = gap_support[lid]
        if lid in row_support:
            assignments[-1]['table_row_support'] = row_support[lid]
        if lid in ctc_support:
            assignments[-1]['ctc_gap_support'] = ctc_support[lid]
        if lid in character_support:
            assignments[-1]['character_gap_support'] = character_support[lid]
    assignments.sort(key=lambda row: row['start'])
    segments, offset = [], 0
    for assignment in assignments:
        if offset < assignment['start']:
            text = plain[offset:assignment['start']]
            segments.append(dict(start=offset, end=assignment['start'], text=text,
                status='unmatched_text' if text.strip() else 'formatting_whitespace'))
        segments.append(dict(start=assignment['start'], end=assignment['end'],
                             text=assignment['text'], status='matched',
                             line_id=assignment['line_id']))
        offset = assignment['end']
    if offset < len(plain):
        text = plain[offset:]
        segments.append(dict(start=offset, end=len(plain), text=text,
            status='unmatched_text' if text.strip() else 'formatting_whitespace'))
    total = sum(not c.isspace() for c in plain)
    matched = sum(sum(not c.isspace() for c in a['text']) for a in assignments)
    for block in blocks:
        members = [a for a in assignments if a['block_id'] == block['id']]
        block.update(line_ids=[a['line_id'] for a in members],
            matched_nonspace_characters=sum(sum(not c.isspace() for c in a['text']) for a in members),
            article_id=None, semantic_status='markdown_structure_only')
    assert ''.join(segment['text'] for segment in segments) == plain
    return dict(version=VERSION, markdown=markdown,
        markdown_sha256=hashlib.sha256(markdown.encode('utf-8')).hexdigest(),
        plain_text=plain, markdown_conversion=conversion, image_size=list(image_size),
        status='full_text_matched' if total and total == matched else 'partially_matched',
        assignments=assignments, segments=segments, unmatched_lines=unmatched,
        status_counts=dict(Counter(['matched']*len(assignments)+[line['status'] for line in unmatched])),
        blocks=blocks, reading_order=[a['line_id'] for a in assignments],
        text_coverage=dict(nonspace_characters=total, matched_nonspace_characters=matched,
                           fraction=matched/total if total else None),
        criteria=dict(minimum_similarity=minimum_similarity, ambiguity_margin=ambiguity_margin,
                      max_candidates=max_candidates, short_anchor_max_characters=3,
                      short_anchor_minimum_neighbor_similarity=.9,
                      hyphen_reflow=hyphen_reflow,
                      hyphen_matching_normalization='¬ and - equivalent in search keys only',
                      short_anchor_spatial_context='two strong adjacent text anchors; same row/column within 3 line heights',
                      regional_constraint=('line searched only in the Gemini text of its automatic layout region; '
                          'monotone gap filling between ordered anchors, width/length ratio .6-1.6, '
                          'auxiliary similarity >= .4 unless the gap holds exactly one line on each side')
                          if regional else None),
        source_only=True, auxiliary_ocr_replaces_transcription=False,
        word_geometry_generated=False, complete_pipeline_certified=False)


def write_alignment(markdown_path, lines, output, *, image_size, **options):
    """Écrire page-alignment.json ; vérifier que l'artefact VT n'a pas changé."""
    markdown_path, output = Path(markdown_path), Path(output)
    raw = markdown_path.read_bytes()
    result = align_page(raw.decode('utf-8'), lines, image_size=image_size, **options)
    if markdown_path.read_bytes() != raw:
        raise ValueError('VT modifiée pendant l’appariement')
    output.mkdir(parents=True, exist_ok=True)
    result['markdown_artifact'] = str(markdown_path.resolve())
    target = output/'page-alignment.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)
    return result
