"""Appariement lexical conservateur, réservé à la notation indépendante.

La distance de Levenshtein porte sur les chaînes de mots joints par une espace.
Une paire de mots n'est mesurée que si tous ses caractères sont appariés aux
mêmes caractères, sans substitution, dans TOUS les chemins optimaux. Aucun
rectangle, numéro de ligne, ordre spatial ni texte de production n'est modifié.
Les scores historiques fondés sur SequenceMatcher restent indépendants.
"""
from __future__ import annotations

from array import array
from collections import defaultdict


VERSION = 'forced-exact-words-all-optimal-character-paths-v1'
DEFAULT_MAX_CELLS = 1_000_000


def _words(values, name):
    if isinstance(values, (str, bytes)):
        raise ValueError(name + ' doit être une séquence de mots')
    values = list(values)
    if any(not isinstance(word, str) or not word or any(c.isspace() for c in word)
           for word in values):
        raise ValueError(name + ' contient un mot vide, non textuel ou avec espaces')
    return values


def _joined(words):
    spans, position = [], 0
    for word in words:
        spans.append((position, position + len(word)))
        position += len(word) + 1
    return ' '.join(words), spans


def _forward(reference, prediction):
    """Coûts seuls, tableaux uint32 : pas de comptage exponentiel de chemins."""
    width = len(prediction) + 1
    rows = [array('I', range(width))]
    for i, rc in enumerate(reference, 1):
        previous = rows[-1]
        current = array('I', [i])
        for j, pc in enumerate(prediction, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (rc != pc)))
        rows.append(current)
    return rows


def match_exact_words(reference_words, prediction_words, *, max_cells=DEFAULT_MAX_CELLS):
    """Retourne des indices de mots exacts et non ambigus, jamais des boîtes.

    Les chaînes entrantes sont comparées telles quelles (casse, ponctuation,
    Unicode inclus). Les appelants qui chargent du NFC restent responsables de
    cette convention. Une ponctuation rattachée différemment rend le mot non
    exact ; elle peut toujours fournir du contexte à l'alignement caractère.

    Pour une lettre de référence, toutes les arêtes qui la consomment sur un
    chemin optimal sont trouvées par coûts avant/arrière. Si une suppression,
    substitution ou autre destination est possible, sa destination n'est pas
    forcée. Un mot ne passe que si toutes ses destinations sont forcées et
    couvrent exactement un mot identique de la prédiction.

    Deux matrices de coûts occupent environ 8 * cellules octets, sans compter
    les petits tableaux d'indices. Une ligne trop longue est explicitement
    refusée ; jamais tronquée et jamais notée par une méthode moins stricte.
    """
    reference_words = _words(reference_words, 'reference_words')
    prediction_words = _words(prediction_words, 'prediction_words')
    if not isinstance(max_cells, int) or isinstance(max_cells, bool) or max_cells < 1:
        raise ValueError('max_cells doit être un entier positif')
    reference, reference_spans = _joined(reference_words)
    prediction, prediction_spans = _joined(prediction_words)
    cells = (len(reference) + 1) * (len(prediction) + 1)
    base = dict(version=VERSION, method='unit_cost_character_levenshtein_all_optimal_paths',
                reference_words=len(reference_words), prediction_words=len(prediction_words),
                reference_characters=sum(map(len, reference_words)),
                prediction_characters=sum(map(len, prediction_words)),
                matrix_cells=cells, max_cells=max_cells, spatial_information_used=False,
                matches=[], ambiguous_reference_indices=[], ambiguous_prediction_indices=[],
                ambiguous_candidates=[], unmatched_reference_indices=list(range(len(reference_words))),
                unmatched_prediction_indices=list(range(len(prediction_words))),
                measured_words=0, measured_reference_characters=0,
                word_coverage=0.0 if reference_words else None,
                reference_character_coverage=0.0 if reference else None)
    if cells > max_cells:
        return dict(base, status='resource_limit_not_measured', edit_distance=None)

    forward = _forward(reference, prediction)
    # Retourner les deux axes permet de réutiliser exactement la récurrence.
    reverse = _forward(reference[::-1], prediction[::-1])
    n, m = len(reference), len(prediction)
    distance = forward[n][m]

    def after(i, j):
        return reverse[n - i][m - j]

    forced = [None] * n
    for i, rc in enumerate(reference):
        destination = None
        ambiguous = False
        for j in range(m + 1):
            prefix = forward[i][j]
            if prefix + 1 + after(i + 1, j) == distance:
                # La lettre peut disparaître dans un chemin optimal.
                ambiguous = True
                break
            if j < m:
                same = rc == prediction[j]
                if prefix + (not same) + after(i + 1, j + 1) == distance:
                    if not same or destination is not None and destination != j:
                        ambiguous = True
                        break
                    destination = j
        if not ambiguous:
            forced[i] = destination

    prediction_by_text = defaultdict(list)
    for index, word in enumerate(prediction_words):
        prediction_by_text[word].append(index)
    matches, ambiguities = [], []
    for ri, (start, end) in enumerate(reference_spans):
        possible = []
        fixed = None
        for pi in prediction_by_text[reference_words[ri]]:
            pstart, pend = prediction_spans[pi]
            # Ce segment diagonal exact appartient à au moins un chemin optimal.
            if forward[start][pstart] + after(end, pend) != distance:
                continue
            possible.append(pi)
            if all(forced[char] == pstart + char - start for char in range(start, end)):
                fixed = pi
        if fixed is not None:
            matches.append(dict(reference_index=ri, prediction_index=fixed))
        elif possible:
            ambiguities.append(dict(reference_index=ri, prediction_indices=possible,
                                    reason='exact_word_not_forced_in_every_optimal_character_path'))
    matched_reference = {pair['reference_index'] for pair in matches}
    matched_prediction = {pair['prediction_index'] for pair in matches}
    assert len(matched_reference) == len(matched_prediction) == len(matches)
    assert all(a['prediction_index'] < b['prediction_index'] for a, b in zip(matches, matches[1:]))
    measured_characters = sum(len(reference_words[i]) for i in matched_reference)
    return dict(base, status='measured', edit_distance=distance, matches=matches,
                ambiguous_reference_indices=[item['reference_index'] for item in ambiguities],
                ambiguous_prediction_indices=sorted({i for item in ambiguities for i in item['prediction_indices']}),
                ambiguous_candidates=ambiguities,
                unmatched_reference_indices=[i for i in range(len(reference_words)) if i not in matched_reference],
                unmatched_prediction_indices=[i for i in range(len(prediction_words)) if i not in matched_prediction],
                measured_words=len(matches), measured_reference_characters=measured_characters,
                word_coverage=len(matches) / len(reference_words) if reference_words else None,
                reference_character_coverage=measured_characters / base['reference_characters']
                    if base['reference_characters'] else None)
