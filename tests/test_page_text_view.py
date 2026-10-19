from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_text_view import compact_line_text_view, line_text_view


def test_reflow_whitespace_maps_one_for_one_without_changing_words():
    source = "Son mari,\nqui\test inculpé\r\ndans l'affaire."
    result = line_text_view(source)
    assert result['source_text'] == source
    assert result['text'] == "Son mari, qui est inculpé  dans l'affaire."
    assert result['source_offsets'] == list(range(len(source)))
    assert result['transform']['mapping'] == 'one_to_one'
    assert result['transform']['crlf'] == 'two_ascii_spaces'
    assert result['text'].split() == source.split()
    assert ''.join(source[i] for i in result['source_offsets']) == source


def test_punctuation_apostrophes_case_and_unicode_composition_remain_exact():
    source = "L’été, l'e\u0301té ; ﬁancé ſœur Æneas."
    result = line_text_view(source)
    assert result['text'] == source
    assert result['source_text'] == source
    assert result['transform']['changed_indices'] == []


def test_hyphenated_word_is_never_joined_or_corrected():
    result = line_text_view('Républi-\nque et inter¬\nnational')
    assert result['text'] == 'Républi- que et inter¬ national'
    assert result['text'].split() == ['Républi-', 'que', 'et', 'inter¬', 'national']


@pytest.mark.parametrize('whitespace', ['\t', '\n', '\r', '\v', '\f', '\u0085', '\u00a0',
                                       '\u1680', '\u2003', '\u2028', '\u2029', '\u202f', '\u3000'])
def test_unicode_whitespace_uses_explicit_character_mapping(whitespace):
    source = 'a'+whitespace+'b'
    result = line_text_view(source)
    assert result['text'] == 'a b'
    assert result['source_text'] == source
    assert result['source_offsets'] == [0, 1, 2]
    assert result['transform']['changed_indices'] == [1]


def test_existing_spaces_and_leading_trailing_blank_characters_are_not_collapsed():
    result = line_text_view('\n  Texte\t \r\n')
    assert result['text'] == '   Texte    '
    assert len(result['text']) == len(result['source_text'])
    assert result['transform']['changed_indices'] == [0, 8, 10, 11]


def test_offsets_are_unicode_codepoints_even_for_non_bmp_and_combining_characters():
    source = '𝔄e\u0301\nœ'
    result = line_text_view(source)
    assert result['text'] == '𝔄e\u0301 œ'
    assert result['source_offsets'] == [0, 1, 2, 3, 4]
    assert result['transform']['offset_unit'] == 'unicode_codepoints'


def test_zero_width_space_is_not_silently_removed_or_treated_as_a_word_break():
    source = 'avant\u200baprès'
    result = line_text_view(source)
    assert result['text'] == source
    assert result['transform']['changed_indices'] == []
    assert len(result['text'].split()) == 1


def test_empty_and_whitespace_only_sources_preserve_all_indices():
    assert line_text_view('')['source_offsets'] == []
    result = line_text_view('\r\n\t')
    assert result['text'] == '   '
    assert result['source_offsets'] == [0, 1, 2]
    assert result['source_text'] == '\r\n\t'


@pytest.mark.parametrize('invalid', [None, b'text', ['text'], 42])
def test_nontext_input_is_rejected(invalid):
    with pytest.raises(TypeError):
        line_text_view(invalid)


def test_compact_crlf_maps_to_one_space_and_its_complete_source_span():
    source = 'Un\r\nmot'
    result = compact_line_text_view(source)
    assert result['text'] == 'Un mot'
    assert result['source_text'] == source
    assert result['source_spans'] == [[0, 1], [1, 2], [2, 4], [4, 5], [5, 6], [6, 7]]
    assert result['source_offsets'] == [0, 1, 2, 4, 5, 6]
    assert result['transform']['trimmed_source_spans'] == []
    # L'ancienne API demeure une vue distincte, strictement un pour un.
    assert line_text_view(source)['text'] == 'Un  mot'


def test_compact_consecutive_unicode_blanks_and_boundary_trims_are_explicit():
    source = '\t\nA\t\u00a0 \r\nB\u202f\n'
    result = compact_line_text_view(source)
    assert result['text'] == 'A B'
    assert result['source_text'] == source
    assert result['source_spans'] == [[2, 3], [3, 8], [8, 9]]
    assert result['source_offsets'] == [2, 3, 8]
    assert result['transform']['trimmed_source_spans'] == [[0, 2], [9, 11]]
    assert result['transform']['whitespace_runs'] == [[0, 2], [3, 8], [9, 11]]
    assert result['transform']['boundary_whitespace'] == 'trimmed_in_view_only'


def test_compact_combining_marks_ligatures_and_punctuation_keep_their_exact_source_indices():
    source = "\ne\u0301,\tL’été\r\nﬁancé.\t"
    result = compact_line_text_view(source)
    assert result['text'] == 'e\u0301, L’été ﬁancé.'
    assert result['source_text'] == source
    for character, (start, end) in zip(result['text'], result['source_spans']):
        if character == ' ':
            assert source[start:end] and all(c.isspace() for c in source[start:end])
        else:
            assert end == start+1
            assert source[start:end] == character
    assert result['text'].split() == source.split()


def test_compact_word_offsets_recover_exact_source_words():
    import re
    source = '\r\nRépubli-\nque\t\u00a0et\r\ninter¬\nnational.  '
    result = compact_line_text_view(source)
    recovered = []
    for token in re.finditer(r'\S+', result['text']):
        start = result['source_spans'][token.start()][0]
        end = result['source_spans'][token.end()-1][1]
        recovered.append(source[start:end])
        assert source[start:end] == token.group()
    assert recovered == source.split()
    assert recovered == ['Républi-', 'que', 'et', 'inter¬', 'national.']


@pytest.mark.parametrize('source', ['', '\r\n\t\u00a0'])
def test_compact_empty_or_blank_source_keeps_original_without_fake_characters(source):
    result = compact_line_text_view(source)
    assert result['text'] == ''
    assert result['source_text'] == source
    assert result['source_spans'] == result['source_offsets'] == []
    assert result['transform']['trimmed_source_spans'] == ([[0, len(source)]] if source else [])


def test_compact_already_compact_text_has_identity_character_spans():
    source = 'Texte déjà compact.'
    result = compact_line_text_view(source)
    assert result['text'] == source
    assert result['source_spans'] == [[i, i+1] for i in range(len(source))]
    assert result['transform']['trimmed_source_spans'] == []


@pytest.mark.parametrize('invalid', [None, b'text', ['text'], 42])
def test_compact_nontext_input_is_rejected(invalid):
    with pytest.raises(TypeError):
        compact_line_text_view(invalid)
