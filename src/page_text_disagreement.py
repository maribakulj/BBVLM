"""Exposer les désaccords OCR/VT sans élire une lecture ni changer la VT.

L'ancre auxiliaire et la transcription peuvent chacune être fautives. Un
alignement de tokens est une piste pour revenir aux pixels, jamais un vote
pour l'OCR. Les cartes conservent les caractères source et les offsets exacts.
Le diagnostic réutilise la normalisation du localisateur pour distinguer ses
tolérances de présentation des substitutions de mots qu'il peut accepter.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

from page_alignment import VERSION as ALIGNMENT_VERSION, _search_text


VERSION = 'anchor-transcription-disagreement-diagnostic-v2'


def _tokens(text):
    normalized, positions = _search_text(text)
    tokens = []
    for match in re.finditer(r'\w+|[^\w\s]', normalized):
        start, end = positions[match.start()], positions[match.end()-1]+1
        while end < len(text) and unicodedata.category(text[end]).startswith('M'):
            end += 1
        tokens.append(dict(key=match.group(), start=start, end=end,
                           text=text[start:end], lexical=bool(re.search(r'\w', match.group()))))
    return normalized, tokens


def _span(text, tokens, start, end, offset=None):
    """Une opération vide pointe avant le token suivant (ou en fin de texte)."""
    a = tokens[start]['start'] if start < len(tokens) else len(text)
    b = tokens[end-1]['end'] if end > start else a
    result = dict(start=a, end=b, text=text[a:b], token_start=start,
                  token_end=end, tokens=tokens[start:end])
    if offset is not None:
        result.update(page_start=offset+a, page_end=offset+b)
    return result


def text_disagreements(anchor_text, vt_text, *, vt_start=0):
    """Décrire une édition minimale de tokens de l'ancre vers la VT exacte.

    Les mots et la ponctuation sont des tokens séparés ; apostrophes, marques
    combinatoires, ligatures, casse et espaces suivent la clé du localisateur.
    Les opérations indiquent un désaccord, sans dire quel côté a raison.
    Un second alignement des seuls tokens lexicaux empêche une ponctuation
    ajoutée de détourner la correspondance entre deux mots. Il ne supprime
    rien du texte : les deux cartes sont simplement des vues diagnostiques.
    Plusieurs alignements minimaux peuvent exister : celui renvoyé ne certifie
    pas la position des erreurs et n'est jamais employé comme critère de rejet.
    """
    from rapidfuzz.distance import Levenshtein

    if not isinstance(anchor_text, str) or not isinstance(vt_text, str):
        raise TypeError('Deux textes exacts sont requis')
    if type(vt_start) is not int or vt_start < 0:
        raise ValueError('Offset source non négatif requis')
    anchor_key, anchor_tokens = _tokens(anchor_text)
    vt_key, vt_tokens = _tokens(vt_text)
    anchor_keys = [token['key'] for token in anchor_tokens]
    vt_keys = [token['key'] for token in vt_tokens]
    operations, surface_differences = [], []
    for op in Levenshtein.opcodes(anchor_keys, vt_keys):
        if op.tag == 'equal':
            for a, b in zip(anchor_tokens[op.src_start:op.src_end], vt_tokens[op.dest_start:op.dest_end]):
                if a['text'] != b['text']:
                    surface_differences.append(dict(anchor=a, vt={**b,
                        'page_start': vt_start+b['start'], 'page_end': vt_start+b['end']}))
            continue
        anchor = _span(anchor_text, anchor_tokens, op.src_start, op.src_end)
        vt = _span(vt_text, vt_tokens, op.dest_start, op.dest_end, vt_start)
        lexical = any(token['lexical'] for token in anchor['tokens']+vt['tokens'])
        operations.append(dict(operation=op.tag, kind='lexical' if lexical else 'punctuation',
                               anchor=anchor, vt=vt))
    anchor_words = [token for token in anchor_tokens if token['lexical']]
    vt_words = [token for token in vt_tokens if token['lexical']]
    lexical_operations = []
    for op in Levenshtein.opcodes([t['key'] for t in anchor_words], [t['key'] for t in vt_words]):
        if op.tag != 'equal':
            lexical_operations.append(dict(operation=op.tag,
                anchor=_span(anchor_text, anchor_words, op.src_start, op.src_end),
                vt=_span(vt_text, vt_words, op.dest_start, op.dest_end, vt_start)))
    return dict(version=VERSION, anchor_text=anchor_text, vt_text=vt_text,
        vt_start=vt_start, vt_end=vt_start+len(vt_text),
        anchor_sha256=hashlib.sha256(anchor_text.encode('utf-8')).hexdigest(),
        vt_sha256=hashlib.sha256(vt_text.encode('utf-8')).hexdigest(),
        operations=operations, lexical_operations=lexical_operations,
        operation_counts={key: count for key, count in dict(
            lexical=len(lexical_operations),
            punctuation=sum(op['kind'] == 'punctuation' for op in operations)).items() if count},
        surface_differences=surface_differences,
        raw_equal=anchor_text == vt_text, normalized_equal=anchor_key == vt_key,
        normalized_token_sequences_equal=anchor_keys == vt_keys,
        comparison_direction='anchor_to_vt', normalization=f'{ALIGNMENT_VERSION}._search_text',
        alignment_algorithm='Levenshtein tokens, unit costs; one minimum-cost alignment',
        alignment_uniqueness_checked=False, source_only=True,
        correct_reading_selected=False, transcription_rewritten=False,
        automatic_acceptance_changed=False)


def page_disagreements(alignment):
    """Diagnostiquer chaque span retenu, sans toucher son statut ou sa géométrie."""
    plain = alignment['plain_text']
    rows = []
    for assignment in alignment['assignments']:
        start, end = assignment['start'], assignment['end']
        if not 0 <= start <= end <= len(plain) or plain[start:end] != assignment['text']:
            raise ValueError('Le span ne reconstruit pas la VT exacte')
        rows.append(dict(line_id=assignment['id'], bbox=assignment['bbox'],
            assignment_similarity=assignment['similarity'],
            **text_disagreements(assignment['auxiliary_text'], assignment['text'], vt_start=start)))
    return dict(version=VERSION, markdown_sha256=alignment['markdown_sha256'],
        plain_text_sha256=hashlib.sha256(plain.encode('utf-8')).hexdigest(),
        assignment_count=len(rows),
        lines_with_lexical_disagreement=sum(bool(r['operation_counts'].get('lexical')) for r in rows),
        lines_with_punctuation_disagreement=sum(bool(r['operation_counts'].get('punctuation')) for r in rows),
        lines_with_normalized_equal_tokens=sum(r['normalized_token_sequences_equal'] for r in rows),
        lines_with_raw_equal_text=sum(r['raw_equal'] for r in rows),
        rows=rows, source_only=True, correct_reading_selected=False,
        transcription_rewritten=False, automatic_acceptance_changed=False)
