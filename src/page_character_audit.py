"""Contrôles de cohérence des caractères, distincts des boîtes de mots.

Un intervalle positif contenu dans son mot n'est pas une certification du
glyphe : ces contrôles signalent seulement des défauts démontrables sans VT.
Ils ne déplacent aucune coordonnée et ne retirent aucun mot de l'ALTO.
"""
from __future__ import annotations

from collections import Counter
import math
import re


VERSION = 'page-character-geometry-consistency-v2'


def audit(annotation, page_width=None):
    text = annotation['text']
    chars = annotation.get('chars')
    tokens = list(re.finditer(r'\S+', text))
    words = annotation.get('words') or []
    issues = []
    checked = 0
    transportable = True
    invalid = set()
    if not isinstance(chars, (list, tuple)) or len(chars) != len(text):
        issues.append(dict(reason='missing_or_inconsistent_character_count'))
        transportable = False
    elif [w.get('text') for w in words] != [t.group() for t in tokens]:
        issues.append(dict(reason='inconsistent_word_text'))
        transportable = False
    else:
        for index, char in enumerate(chars):
            context = dict(index=index, character=text[index])
            if (not isinstance(char, (list, tuple)) or len(char) != 3
                    or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in char)):
                issues.append(dict(context, reason='invalid_character_interval'))
                invalid.add(index)
                continue
            left, right, confidence = char
            if not 0 <= left <= right or page_width is not None and right > page_width:
                issues.append(dict(context, reason='character_interval_outside_page_or_reversed'))
                invalid.add(index)
            if not 0 <= confidence <= 1:
                issues.append(dict(context, reason='invalid_character_confidence'))
                invalid.add(index)
        transportable = not invalid
        for wi, (word, token) in enumerate(zip(words, tokens)):
            previous_end = None
            for index in range(token.start(), token.end()):
                checked += 1
                char = chars[index]
                context = dict(index=index, word_index=wi, character=text[index])
                if index in invalid:
                    previous_end = None
                    continue
                left, right, confidence = char
                if right <= left:
                    issues.append(dict(context, reason='nonpositive_character_width'))
                if left < word['x0'] or right > word['x1'] + 1:
                    issues.append(dict(context, reason='character_outside_word'))
                if previous_end is not None and left < previous_end:
                    issues.append(dict(context, reason='overlapping_character_intervals'))
                previous_end = right
        # Un alignement local peut sembler contenu dans son mot parce que le
        # boxer a tronqué une cellule CTC qui déborde dans le padding. Une
        # cellule partielle ne démontre pas un support natif du caractère.
        for repair in annotation.get('character_realignments', []):
            if not repair.get('accepted'):
                continue
            details = (repair.get('ctc_attempt') or {}).get('alignment') or {}
            crop = repair.get('source_box')
            frames, width, padding = (details.get(k) for k in ('frames', 'input_width', 'padding'))
            if not crop or not frames or not width or padding is None or width <= 2 * padding:
                continue
            frame_width = width / frames * (crop[2] - crop[0]) / (width - 2 * padding)
            for index in range(repair['start'], repair['end']):
                if index in invalid:
                    continue
                left, right, _ = chars[index]
                if ((abs(left - crop[0]) < 1e-6 or abs(right - crop[2]) < 1e-6)
                        and 0 < right - left < frame_width - 1e-6):
                    issues.append(dict(index=index, word_index=repair['word_index'], character=text[index],
                                       reason='partially_native_ctc_frame'))
    sources = (annotation.get('alignment') or {}).get('character_position_sources')
    if sources is not None and (not isinstance(sources, (list, tuple)) or len(sources) != len(text)
                                or any(not isinstance(value, str) for value in sources)):
        issues.append(dict(reason='inconsistent_character_provenance'))
    return dict(version=VERSION, consistent=not issues, transportable=transportable, certified=False,
                nonspace_characters_checked=checked,
                issue_counts=dict(Counter(item['reason'] for item in issues)), issues=issues,
                scope='coordinate consistency only; glyph accuracy not independently certified')
