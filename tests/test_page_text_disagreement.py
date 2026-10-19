from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_text_disagreement import page_disagreements, text_disagreements


def test_word_substitution_has_exact_source_spans_and_no_preferred_reading():
    anchor, vt = 'La maison demeure ouverte.', 'La boutique demeure ouverte.'
    result = text_disagreements(anchor, vt, vt_start=150)
    op, = result['operations']
    assert op['operation'] == 'replace'
    assert op['kind'] == 'lexical'
    assert op['anchor']['text'] == 'maison'
    assert op['vt']['text'] == 'boutique'
    assert vt[op['vt']['start']:op['vt']['end']] == op['vt']['text']
    assert op['vt']['page_start'] == 153
    assert result['anchor_text'] == anchor and result['vt_text'] == vt
    assert not result['correct_reading_selected']
    assert not result['transcription_rewritten']
    assert not result['automatic_acceptance_changed']


@pytest.mark.parametrize(('anchor','vt','tag'), [
    ('Il faut attendre.', 'Il attendre.', 'delete'),
    ('Il attendre.', 'Il faut attendre.', 'insert'),
    ('', 'Texte.', 'insert'),
    ('Texte.', '', 'delete'),
])
def test_insertions_and_deletions_preserve_both_sides(anchor, vt, tag):
    result = text_disagreements(anchor, vt)
    assert result['operations'][0]['operation'] == tag
    assert result['anchor_text'] == anchor and result['vt_text'] == vt
    for op in result['operations']:
        assert anchor[op['anchor']['start']:op['anchor']['end']] == op['anchor']['text']
        assert vt[op['vt']['start']:op['vt']['end']] == op['vt']['text']


def test_punctuation_differences_are_separate_from_lexical_substitutions():
    result = text_disagreements('Vraiment ;', 'Vraiment:')
    assert result['operation_counts'] == {'punctuation': 1}
    assert result['operations'][0]['anchor']['text'] == ';'
    assert result['operations'][0]['vt']['text'] == ':'
    assert result['lexical_operations'] == []


def test_word_alignment_is_not_distracted_by_an_added_comma():
    result = text_disagreements("La maison de l'ancien quartier. Des gens", 
                                "La boutique de l'autre quartier, des gens")
    assert [(op['anchor']['text'],op['vt']['text']) for op in result['lexical_operations']] == [
        ('maison','boutique'), ('ancien','autre')]


def test_presentation_normalization_is_visible_without_changing_sources():
    anchor = "L'ETE\t oeuvres et soleil préoc¬"
    vt = 'L’été\u00a0œuvres et ſoleil préoc-'
    result = text_disagreements(anchor, vt)
    assert result['operations'] == []
    assert result['surface_differences']
    assert result['normalized_equal']
    assert not result['raw_equal']
    assert result['anchor_text'] == anchor and result['vt_text'] == vt


def test_combining_mark_and_ligature_offsets_reconstruct_exact_substitutions():
    anchor, vt = 'Un cafe\u0301 ferme.', 'Un œillet ferme.'
    result = text_disagreements(anchor, vt, vt_start=17)
    op, = result['operations']
    assert op['anchor']['text'] == 'cafe\u0301'
    assert op['vt']['text'] == 'œillet'
    assert op['anchor']['end'] == 8
    assert op['vt']['page_start'] == 20


def test_whitespace_before_punctuation_does_not_create_lexical_disagreement():
    result = text_disagreements('Oui\r\n ?', 'Oui?')
    assert not result['normalized_equal']
    assert result['normalized_token_sequences_equal']
    assert result['operations'] == []


def test_word_order_disagreement_is_reported_without_claiming_unique_alignment():
    result = text_disagreements('on dit oui oui', 'oui on dit oui')
    assert result['operation_counts']['lexical'] >= 1
    assert result['alignment_uniqueness_checked'] is False


def test_page_diagnostic_is_read_only_and_checks_exact_vt_offsets():
    alignment = dict(plain_text='Titre\nUne boutique.', markdown_sha256='example',
        assignments=[dict(id='L1',bbox=[0,0,100,20],similarity=.8,
                          start=6,end=19,text='Une boutique.',auxiliary_text='Une maison.')])
    original = deepcopy(alignment)
    result = page_disagreements(alignment)
    assert alignment == original
    assert result['lines_with_lexical_disagreement'] == 1
    assert result['rows'][0]['operations'][0]['vt']['page_start'] == 10
    alignment['assignments'][0]['start'] += 1
    with pytest.raises(ValueError, match='span'):
        page_disagreements(alignment)


@pytest.mark.parametrize('offset', [-1, True, .5])
def test_invalid_source_offsets_refused(offset):
    with pytest.raises(ValueError):
        text_disagreements('a', 'b', vt_start=offset)
