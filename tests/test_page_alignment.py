from pathlib import Path
import hashlib
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_alignment import align_page, markdown_document, write_alignment


def line(lid, text, bbox=(1, 1, 200, 20)):
    return dict(id=lid, bbox=list(bbox), auxiliary_text=text, source='kraken-blla/full')


def match(markdown, lines, **kwargs):
    return align_page(markdown, lines, image_size=(1000, 1000), **kwargs)


def test_markdown_is_preserved_and_ocr_never_replaces_visible_text(tmp_path):
    markdown = '# Un titre\r\n\r\nL’e\u0301té, **œuvres** et ſoleil.\r\n'
    source = tmp_path/'vt.gemini.md'
    source.write_bytes(markdown.encode())
    before = source.read_bytes()
    result = write_alignment(source, [line('title', 'Un titre'),
        line('body', "L'ete, oeuvres et soleil.")], tmp_path/'output', image_size=(1000, 1000))
    assert source.read_bytes() == before
    assert result['markdown'] == markdown
    assert result['markdown_sha256'] == hashlib.sha256(before).hexdigest()
    assert result['assignments'][1]['text'] == 'L’e\u0301té, œuvres et ſoleil.'
    assert result['text_coverage']['fraction'] == 1
    assert result['auxiliary_ocr_replaces_transcription'] is False
    assert json.loads((tmp_path/'output/page-alignment.json').read_text())['markdown'] == markdown


def test_assignment_uses_page_text_order_and_source_geometry_across_columns():
    rows = [line('right', 'Deuxième colonne.', (600, 10, 900, 30)),
            line('left', 'Première colonne.', (10, 100, 400, 120))]
    result = match('Première colonne.\n\nDeuxième colonne.', rows)
    assert result['reading_order'] == ['left', 'right']
    assert [a['bbox'] for a in result['assignments']] == [rows[1]['bbox'], rows[0]['bbox']]
    assert all(a['training_eligible'] is False and 'words' not in a for a in result['assignments'])


def test_reflowed_paragraph_can_map_to_multiple_physical_lines_without_cutting_words():
    markdown = 'Le premier segment se termine ici. Le deuxième poursuit cette phrase.'
    result = match(markdown, [line('one', 'Le premier segment se termine ici.'),
                              line('two', 'Le deuxième poursuit cette phrase.')])
    assert result['text_coverage']['fraction'] == 1
    assert [a['text'] for a in result['assignments']] == [
        'Le premier segment se termine ici.', 'Le deuxième poursuit cette phrase.']
    assert ''.join(s['text'] for s in result['segments']) == result['plain_text']


def test_missing_or_bad_ocr_keeps_complete_unplaced_text_and_original_ids():
    result = match('Texte essentiel omis du détecteur.\n\nUne bonne ligne.',
                   [line('known', 'Une bonne ligne.'), line('noise', 'zzzzzzzz'), line('empty', '')])
    assert result['assignments'][0]['text'] == 'Une bonne ligne.'
    assert result['segments'][0]['status'] == 'unmatched_text'
    assert result['segments'][0]['text'].startswith('Texte essentiel')
    assert {a['id']: a['status'] for a in result['unmatched_lines']} == {
        'noise': 'no_text_match', 'empty': 'no_auxiliary_text'}
    assert ''.join(s['text'] for s in result['segments']) == result['plain_text']


def test_repeated_text_and_duplicate_detections_remain_ambiguous():
    repeated = match('Même annonce.\n\nMême annonce.', [line('one', 'Même annonce.')])
    assert not repeated['assignments']
    assert repeated['unmatched_lines'][0]['status'] == 'ambiguous_text_match'
    duplicate = match('Une seule occurrence.', [line('one', 'Une seule occurrence.'),
                                               line('two', 'Une seule occurrence.')])
    assert not duplicate['assignments']
    assert {a['status'] for a in duplicate['unmatched_lines']} == {'competing_line_match'}


def test_fuzzy_matching_retains_punctuation_and_lexical_difference_from_gemini():
    result = match('Bonjour madame, voici votre journal.',
                   [line('one', 'Bonjour madarne, voici votre journal.')])
    assert result['assignments'][0]['text'] == 'Bonjour madame, voici votre journal.'
    assert result['assignments'][0]['similarity'] < 1


def test_tables_lists_emphasis_and_code_keep_all_content_without_marker_words():
    text, blocks, metadata = markdown_document(
        '# Titre\n\n- **alpha**\n- `bêta`\n\n| Un | Deux |\n|---|---|\n| Trois | Quatre |')
    assert text == 'Titre\nalpha\nbêta\nUn\nDeux\nTrois\nQuatre'
    assert sum(b['role'] == 'table_cell' for b in blocks) == 4
    assert metadata['unhandled_token_types'] == []


@pytest.mark.parametrize('rows', [[line('one', 'hello', (-1, 0, 4, 5))],
                                  [line('one', 'hello'), line('one', 'hello')],
                                  [line('one', 'hello', (1, 1, float('nan'), 4))]])
def test_geometry_and_ids_are_checked_before_any_match(rows):
    with pytest.raises(ValueError):
        match('hello', rows)


def test_missing_geometry_and_no_auxiliary_text_do_not_create_coordinates():
    with pytest.raises(ValueError):
        match('Texte.', [dict(id='one', auxiliary_text='Texte.')])
    result = match('Texte.', [dict(id='one', bbox=[1, 2, 30, 40])])
    assert not result['assignments']
    assert result['text_coverage']['fraction'] == 0
    assert result['segments'][0]['text'] == 'Texte.'


def test_short_partial_word_and_dehyphenated_word_are_not_forced():
    result = match('République.', [line('one', 'Républi-'), line('two', 'que.')])
    assert not result['assignments']
    assert result['text_coverage']['fraction'] == 0


def test_combining_mark_at_end_of_match_is_not_dropped():
    result = match('cafe\u0301', [line('one', 'café')])
    assert result['assignments'][0]['text'] == 'cafe\u0301'
    assert result['text_coverage']['fraction'] == 1


@pytest.mark.parametrize(('markdown', 'expected'), [
    ('![Une **légende** &amp; fin](image.png)', 'Une légende & fin'),
    ('Mot <em>important</em><br>suite &amp; fin.', 'Mot important\nsuite & fin.'),
    ('<div>Texte <strong>fort</strong><br>suite &amp; fin.</div>', 'Texte fort\nsuite & fin.'),
    (r'\# Titre \*visible\*', '# Titre *visible*'),
    ('Du `# code`\n\n```text\n**littéral**\n```', 'Du # code\n**littéral**'),
])
def test_inline_html_alt_and_escaped_text_are_content_not_marker_coordinates(markdown, expected):
    plain, blocks, conversion = markdown_document(markdown)
    assert plain == expected
    assert conversion['unhandled_token_types'] == []
    assert conversion['unhandled_html_tags'] == []
    assert all(plain[b['start']:b['end']] == b['text'] for b in blocks)


def test_unknown_markup_is_retained_and_reported():
    plain, _, conversion = markdown_document('Texte <inconnu>visible</inconnu>.')
    assert plain == 'Texte <inconnu>visible</inconnu>.'
    assert conversion['unhandled_html_tags'] == ['inconnu']


def test_zero_ambiguity_margin_still_refuses_ties():
    result = match('Même annonce.\n\nMême annonce.', [line('one', 'Même annonce.')], ambiguity_margin=0)
    assert not result['assignments']
    assert result['unmatched_lines'][0]['status'] == 'ambiguous_text_match'


def test_detector_crop_is_preserved_separately_from_refined_line_geometry():
    row = {**line('one', 'Texte', (10, 10, 190, 18)), 'detector_bbox': [1, 1, 200, 20]}
    result = match('Texte', [row])
    assert result['assignments'][0]['bbox'] == row['bbox']
    assert result['assignments'][0]['detector_bbox'] == row['detector_bbox']
    row['detector_bbox'] = [1, 1, 2000, 20]
    with pytest.raises(ValueError, match='détection hors image'):
        match('Texte', [row])


def test_short_fragment_cannot_move_into_an_unrelated_column():
    markdown = 'Un passage avant.\nE.\nUn passage après.'
    result = match(markdown, [line('before', 'Un passage avant.', (600, 100, 900, 120)),
        line('fragment', 'e.', (400, 125, 420, 145)),
        line('after', 'Un passage après.', (600, 150, 900, 170))])
    assert result['reading_order'] == ['before', 'after']
    assert result['status_counts']['short_anchor_without_spatial_context'] == 1
    assert result['unmatched_lines'][0]['id'] == 'fragment'
    assert result['unmatched_lines'][0]['candidates'][0]['similarity'] == 1
    assert any('E.' in s['text'] and s['status'] == 'unmatched_text' for s in result['segments'])
    assert ''.join(s['text'] for s in result['segments']) == result['plain_text']


def test_isolated_folio_has_text_but_no_proven_spatial_address():
    result = match('12', [line('folio', '12', (50, 20, 75, 40))])
    assert not result['assignments']
    assert result['unmatched_lines'][0]['status'] == 'short_anchor_without_spatial_context'
    assert result['segments'] == [dict(start=0, end=2, text='12', status='unmatched_text')]


def test_short_anchor_can_use_two_strong_nearby_neighbors_in_same_column():
    result = match('Passage précédent.\nII\nPassage suivant.', [
        line('before', 'Passage précédent.', (10, 10, 300, 30)),
        line('short', 'II', (120, 45, 155, 65)),
        line('after', 'Passage suivant.', (10, 80, 300, 100))])
    assert result['reading_order'] == ['before', 'short', 'after']
    assert result['assignments'][1]['spatial_context_line_ids'] == ['before', 'after']
    assert result['text_coverage']['fraction'] == 1


def test_short_anchor_requires_both_neighbors_and_cannot_jump_unmatched_text():
    result = match('Passage précédent.\nTexte sans ancre.\nII\nPassage suivant.', [
        line('before', 'Passage précédent.', (10, 10, 300, 30)),
        line('short', 'II', (120, 45, 155, 65)),
        line('after', 'Passage suivant.', (10, 80, 300, 100))])
    assert 'short' not in result['reading_order']
    assert result['unmatched_lines'][0]['status'] == 'short_anchor_without_spatial_context'


def test_joined_printed_hyphenation_maps_two_lines_without_changing_one_character():
    markdown = '# Article\n\nLes préoc-cupations restent nombreuses.'
    result = match(markdown, [line('title', 'Article'),
        line('first', 'Les préoc¬'), line('second', 'cupations restent nombreuses.')])
    assert result['reading_order'] == ['title', 'first', 'second']
    first, second = result['assignments'][1:]
    assert first['text'] == 'Les préoc-'
    assert second['text'] == 'cupations restent nombreuses.'
    assert first['end'] == second['start']
    assert first['end_after_observed_hyphen'] is True
    assert second['start_after_observed_hyphen'] is True
    assert result['markdown'] == markdown
    assert result['text_coverage']['fraction'] == 1
    assert ''.join(s['text'] for s in result['segments']) == result['plain_text']


def test_end_inside_joined_hyphenated_word_requires_terminal_hyphen_in_anchor():
    result = match('Les préoc-cupations demeurent.', [line('first', 'Les préoc')], minimum_similarity=.9)
    assert not result['assignments']
    assert result['plain_text'] == 'Les préoc-cupations demeurent.'


def test_complete_compound_word_keeps_its_hyphen_in_the_same_assignment():
    markdown = 'Un porte-monnaie demeure ici.'
    result = match(markdown, [line('one', markdown)])
    assert result['assignments'][0]['text'] == markdown
    assert 'start_after_observed_hyphen' not in result['assignments'][0]
    assert 'end_after_observed_hyphen' not in result['assignments'][0]
    assert result['text_coverage']['fraction'] == 1


def test_no_hyphen_is_added_to_an_unhyphenated_word_or_missing_source_fragment():
    result = match('Les préoccupations demeurent.',
        [line('first', 'Les préoc¬'), line('second', 'cupations demeurent.')], minimum_similarity=.9)
    assert not result['assignments']
    assert result['plain_text'] == 'Les préoccupations demeurent.'
    assert result['markdown'] == 'Les préoccupations demeurent.'


def test_hyphen_reflow_can_be_disabled_for_comparison_without_touching_source():
    source = 'Les préoc-cupations demeurent.'
    rows = [line('first', 'Les préoc¬'), line('second', 'cupations demeurent.')]
    before = match(source, rows, hyphen_reflow=False, minimum_similarity=.9)
    after = match(source, rows, hyphen_reflow=True, minimum_similarity=.9)
    assert before['markdown'] == after['markdown'] == source
    assert before['markdown_sha256'] == after['markdown_sha256']
    assert before['plain_text'] == after['plain_text']
    assert before['text_coverage']['fraction'] < after['text_coverage']['fraction'] == 1


def test_linewise_v1_transcription_and_source_offsets_remain_identical(tmp_path):
    source = "# Titre\r\n\r\nLa préoc-\r\ncupation est l'été.\r\n"
    path = tmp_path/'vt.gemini.md'
    path.write_bytes(source.encode('utf-8'))
    rows = [line('title', 'Titre'), line('first', 'La préoc-'), line('second', "cupation est l'été.")]
    before = match(source, rows, hyphen_reflow=False)
    after = write_alignment(path, rows, tmp_path/'out', image_size=(1000, 1000))
    assert path.read_bytes() == source.encode('utf-8')
    assert before['markdown'] == after['markdown'] == source
    assert before['markdown_sha256'] == after['markdown_sha256']
    assert before['plain_text'] == after['plain_text']
    assert [(a['id'], a['start'], a['end'], a['text']) for a in before['assignments']] == [
        (a['id'], a['start'], a['end'], a['text']) for a in after['assignments']]
