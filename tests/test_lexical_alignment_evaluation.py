"""Correspondances d'évaluation : contexte textuel, répétitions et abstention."""
from pathlib import Path
from itertools import product
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from lexical_alignment_evaluation import match_exact_words


def pairs(reference, prediction, **kwargs):
    result = match_exact_words(reference, prediction, **kwargs)
    return [(p['reference_index'], p['prediction_index']) for p in result['matches']]


def test_identical_text_keeps_each_repeated_occurrence():
    words = ['A.', 'mot;', 'A.', 'mot;']
    assert pairs(words, words) == list(enumerate(range(4)))


def test_character_context_locates_last_repeat_despite_tokenization_changes():
    reference = ['X,', 'Alpha', 'premier', 'instrument', ';', 'X.', 'Beta', ';', 'second', 'instrument;']
    prediction = ['X.', 'Omega,', 'instrument;', 'X.', 'Beta;', 'second', 'instrument;']
    result = pairs(reference, prediction)
    assert (5, 3) in result
    assert (9, 6) in result
    assert (5, 0) not in result
    assert (9, 2) not in result


@pytest.mark.parametrize(('reference', 'prediction', 'expected'), [
    (['avant', 'de', 'milieu', 'de', 'apres'], ['avant', 'milieu', 'de', 'apres'], [(0, 0), (2, 1), (3, 2), (4, 3)]),
    (['avant', 'milieu', 'de', 'apres'], ['avant', 'de', 'milieu', 'de', 'apres'], [(0, 0), (1, 2), (2, 3), (3, 4)]),
    (['haut', 'echo', 'bleu', 'echo', 'fin'], ['haut', 'echo', 'rouge', 'echo', 'fin'], [(0, 0), (1, 1), (3, 3), (4, 4)]),
])
def test_omission_insertion_and_substitution_keep_unambiguous_context(reference, prediction, expected):
    assert pairs(reference, prediction) == expected


@pytest.mark.parametrize(('reference', 'prediction', 'ambiguous_reference', 'ambiguous_prediction'), [
    (['de', 'de'], ['de'], [0, 1], [0]),
    (['de'], ['de', 'de'], [0], [0, 1]),
])
def test_equally_good_repeated_occurrences_are_refused(reference, prediction, ambiguous_reference, ambiguous_prediction):
    result = match_exact_words(reference, prediction)
    assert result['matches'] == []
    assert result['ambiguous_reference_indices'] == ambiguous_reference
    assert result['ambiguous_prediction_indices'] == ambiguous_prediction
    assert result['word_coverage'] == 0
    assert result['unmatched_reference_indices'] == list(range(len(reference)))


def test_ambiguity_does_not_erase_other_forced_words():
    result = match_exact_words(['a', 'b'], ['a', 'a', 'b'])
    assert result['matches'] == [dict(reference_index=1, prediction_index=2)]
    assert result['ambiguous_reference_indices'] == [0]
    assert result['word_coverage'] == .5


def test_a_single_exact_token_candidate_is_not_enough_when_partial_alignment_is_also_optimal():
    result = match_exact_words(['a'], ['a', 'aa'])
    assert result['matches'] == []
    assert result['ambiguous_candidates'][0]['prediction_indices'] == [0]
    assert result['ambiguous_reference_indices'] == [0]


def test_exact_word_contract_does_not_silently_normalize_punctuation_case_or_unicode():
    assert pairs(['A', 'été', 'fin;'], ['a', 'été', 'fin', ';']) == []
    assert pairs(['été'], ['été']) == [(0, 0)]
    assert pairs(['fin', ';', 'suite'], ['fin;', 'suite']) == [(2, 1)]


@pytest.mark.parametrize(('reference', 'prediction'), [([], []), (['mot'], []), ([], ['mot'])])
def test_empty_sequences_never_create_a_measurement(reference, prediction):
    result = match_exact_words(reference, prediction)
    assert result['matches'] == []
    assert result['measured_words'] == 0
    assert result['status'] == 'measured'
    assert result['edit_distance'] == len(' '.join(reference)) + len(' '.join(prediction))


def test_resource_limit_refuses_the_whole_line_without_truncation():
    result = match_exact_words(['a' * 1000], ['a' * 1000], max_cells=100)
    assert result['status'] == 'resource_limit_not_measured'
    assert result['matrix_cells'] == 1002001
    assert result['matches'] == [] and result['edit_distance'] is None
    assert result['unmatched_reference_indices'] == result['unmatched_prediction_indices'] == [0]


@pytest.mark.parametrize('words', [[''], ['a b'], [None], 'abc'])
def test_invalid_tokens_are_explicitly_rejected(words):
    with pytest.raises(ValueError):
        match_exact_words(words, ['mot'])


def test_small_cases_agree_with_exhaustive_optimal_edit_path_oracle():
    """Oracle par énumération de chemins, distinct du calcul d'arêtes forcées."""
    from rapidfuzz.distance import Levenshtein

    def exhaustive(reference_words, prediction_words):
        a, b = ' '.join(reference_words), ' '.join(prediction_words)
        distance = Levenshtein.distance(a, b)
        reference_starts, prediction_starts = [], []
        for words, starts in [(reference_words, reference_starts), (prediction_words, prediction_starts)]:
            offset = 0
            for word in words:
                starts.append(offset)
                offset += len(word)+1
        intersection = None

        def visit(i, j, cost, exact_chars):
            nonlocal intersection
            if cost > distance or cost + abs((len(a)-i)-(len(b)-j)) > distance:
                return
            if i == len(a) and j == len(b):
                word_pairs = {(ri, pi) for ri, rw in enumerate(reference_words)
                              for pi, pw in enumerate(prediction_words) if rw == pw and all(
                                  (reference_starts[ri]+k, prediction_starts[pi]+k) in exact_chars
                                  for k in range(len(rw)))}
                intersection = word_pairs if intersection is None else intersection & word_pairs
                return
            if i < len(a):
                visit(i+1, j, cost+1, exact_chars)
            if j < len(b):
                visit(i, j+1, cost+1, exact_chars)
            if i < len(a) and j < len(b):
                visit(i+1, j+1, cost+(a[i] != b[j]),
                      exact_chars | {(i, j)} if a[i] == b[j] else exact_chars)

        visit(0, 0, 0, set())
        return intersection or set()

    sequences = [list(words) for size in range(3) for words in product(['a', 'b', 'aa'], repeat=size)]
    for reference in sequences:
        for prediction in sequences:
            assert set(pairs(reference, prediction)) == exhaustive(reference, prediction), (reference, prediction)
