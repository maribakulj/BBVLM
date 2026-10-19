"""Propositions de frontières guidées par les espaces CTC, sans les appliquer.

Le milieu de deux lettres n'est pas toujours l'espace imprimé : un signe en
plusieurs fragments peut contenir un blanc plus proche de ce milieu. Ce
diagnostic compare la frontière historique au pic CTC du blanc transcrit.
Il propose seulement des colonnes effectivement vides du masque fourni,
entre les caractères voisins. Il ne valide ni une transcription ni un glyphe
et ne change aucune annotation : la sémantique des composantes transférées
doit être contrôlée séparément avant une éventuelle application.
"""
from __future__ import annotations

import math
import re

import numpy as np


VERSION = 'native-white-columns-ctc-space-proposals-v1'


def space_anchored_boundaries(text, source_box, mask, char_positions, boundaries,
                              minimum_space_support=.9):
    """Comparer des frontières de mots à des pics d'espaces CTC déjà calculés.

    ``mask`` est un masque natif du rectangle source demi-ouvert.
    ``char_positions`` contient une triple [x0,x1,support] par caractère du
    texte exact ; prendre les positions CTC de *ligne*, avant leur éventuel
    remplacement par des espaces déduits des boîtes. ``boundaries`` contient
    un ``x`` (ou un dict avec ce champ) entre chaque paire de mots consécutifs.
    Le seuil est un filtre expérimental, pas une probabilité de conformité.
    """
    if not isinstance(text, str):
        raise TypeError('Texte exact requis')
    if not 0 <= minimum_space_support <= 1:
        raise ValueError('Seuil de support invalide')
    if len(source_box) != 4 or any(not isinstance(v, (int, float)) or
            not math.isfinite(v) or int(v) != v for v in source_box):
        raise ValueError('Rectangle source entier requis')
    x0, y0, x1, y1 = map(int, source_box)
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0 or \
            not isinstance(mask, np.ndarray) or mask.ndim != 2 or mask.shape != (y1-y0, x1-x0):
        raise ValueError('Masque et coordonnées source incohérents')
    if len(char_positions) != len(text) or any(
            len(p) != 3 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in p)
            or not x0 <= p[0] <= p[1] <= x1 or not 0 <= p[2] <= 1 for p in char_positions):
        raise ValueError('Positions CTC incohérentes avec le texte et la source')
    words = list(re.finditer(r'\S+', text))
    if len(boundaries) != max(0, len(words)-1):
        raise ValueError('Compte de frontières incohérent')
    old = [value['x'] if isinstance(value, dict) else value for value in boundaries]
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) or int(value) != value
           or not x0 < value < x1 for value in old) or any(b <= a for a,b in zip(old, old[1:])):
        raise ValueError('Frontières historiques invalides')
    old = [int(value) for value in old]
    occupied = np.any(mask > 0, axis=0)
    white = np.flatnonzero(~occupied)+x0
    records = []
    for wi, (left, right) in enumerate(zip(words, words[1:])):
        left_position, right_position = char_positions[left.end()-1], char_positions[right.start()]
        a = (left_position[0]+left_position[1])/2
        b = (right_position[0]+right_position[1])/2
        indexes = list(range(left.end(), right.start()))
        record = dict(left_word_index=wi, right_word_index=wi+1,
            left_word=left.group(), right_word=right.group(), whitespace_indices=indexes,
            previous_x=old[wi], proposed_x=old[wi], left_anchor=a, right_anchor=b,
            status='unchanged', applied=False)
        records.append(record)
        if not indexes or any(not text[i].isspace() for i in indexes) or not a < b:
            record['status'] = 'invalid_neighbor_anchors'
            continue
        if any(char_positions[i][0] >= char_positions[i][1] for i in indexes):
            record['status'] = 'empty_space_anchor'
            continue
        support = min(char_positions[i][2] for i in indexes)
        center = float(np.median([(char_positions[i][0]+char_positions[i][1])/2 for i in indexes]))
        record.update(space_support=support, space_anchor=center)
        if support < minimum_space_support:
            record['status'] = 'space_support_insufficient'
            continue
        if not a < center < b:
            record['status'] = 'space_anchor_outside_neighbors'
            continue
        choices = white[(white > a) & (white < b)]
        if not len(choices):
            record['status'] = 'no_native_white_column'
            continue
        proposal = int(choices[np.argmin(np.abs(choices-center))])
        begin, end = proposal-x0, proposal-x0+1
        while begin > 0 and not occupied[begin-1]:
            begin -= 1
        while end < len(occupied) and not occupied[end]:
            end += 1
        record['native_white_run'] = [x0+begin, x0+end]
        if x0+begin <= old[wi] < x0+end:
            # Déplacer une coupure dans le même blanc ne change aucun mot.
            record['status'] = 'same_native_gap'
            continue
        lo, hi = sorted((old[wi], proposal))
        record.update(proposed_x=proposal, status='candidate',
            displacement=proposal-old[wi], transferred_ink_pixels=int(np.count_nonzero(mask[:,lo-x0:hi-x0])),
            transfer_direction='right_word_to_left_word' if proposal > old[wi] else 'left_word_to_right_word',
            native_support_deleted=False, cuts_observed_ink=bool(occupied[proposal-x0]),
            semantic_component_assignment_verified=False)
    proposed = [record['proposed_x'] for record in records]
    if any(b <= a for a,b in zip(proposed, proposed[1:])):
        for record in records:
            if record['status'] == 'candidate':
                record.update(status='conflicting_boundary_proposals', proposed_x=record['previous_x'])
    return dict(version=VERSION, text=text, source_box=list(source_box),
        boundaries=records, candidates=sum(r['status'] == 'candidate' for r in records),
        minimum_space_support=minimum_space_support, text_changed=False,
        annotations_modified=False, promoted=False, criteria_met=False,
        scope='diagnostic source-only proposals; CTC space peaks are not glyph geometry certificates')
