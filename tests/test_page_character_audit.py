from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_character_audit import audit


def row():
    return dict(text='Un mot', words=[dict(text='Un', x0=10, x1=29), dict(text='mot', x0=40, x1=69)],
                chars=[[10, 20, .9], [20, 30, .9], [30, 40, 0],
                       [40, 50, .9], [50, 60, .9], [60, 70, .9]])


def test_consistent_intervals_do_not_claim_glyph_certification_or_mutate():
    annotation = row()
    before = deepcopy(annotation)
    result = audit(annotation)
    assert result['consistent'] and not result['certified']
    assert result['nonspace_characters_checked'] == 5 and not result['issues']
    assert annotation == before


def test_zero_and_outside_and_overlapping_are_separate_observable_defects():
    annotation = row()
    annotation['chars'][0] = [10, 10, .9]
    annotation['chars'][3] = [39, 51, .9]
    result = audit(annotation)
    assert not result['consistent']
    assert result['issue_counts'] == dict(nonpositive_character_width=1,
        character_outside_word=1, overlapping_character_intervals=1)
    assert [i['index'] for i in result['issues']] == [0, 3, 4]


def test_whitespace_has_no_glyph_width_requirement():
    annotation = row()
    annotation['chars'][2] = [30, 30, 0]
    assert audit(annotation)['consistent']


def test_missing_or_nonfinite_intervals_are_not_consistent():
    annotation = row()
    annotation['chars'].pop()
    assert audit(annotation)['issue_counts'] == {'missing_or_inconsistent_character_count': 1}
    annotation = row()
    annotation['chars'][0][0] = float('nan')
    assert audit(annotation)['issue_counts'] == {'invalid_character_interval': 1}


def test_truncated_ctc_cell_cannot_pass_just_because_it_is_inside_word():
    annotation = row()
    annotation['chars'][1] = [29.5, 30, .99]
    annotation['character_realignments'] = [dict(accepted=True, start=0, end=2,
        word_index=0, source_box=[10, 0, 30, 20], ctc_attempt=dict(alignment=dict(
            frames=10, input_width=100, padding=10)))]
    result = audit(annotation)
    assert result['issue_counts'] == {'partially_native_ctc_frame': 1}
    assert not result['consistent'] and result['issues'][0]['index'] == 1


def test_invalid_character_with_repair_history_is_reported_without_unpacking_it():
    annotation = row()
    annotation['chars'][1] = None
    annotation['character_realignments'] = [dict(accepted=True, start=0, end=2,
        word_index=0, source_box=[10, 0, 30, 20], ctc_attempt=dict(alignment=dict(
            frames=10, input_width=100, padding=10)))]
    result = audit(annotation)
    assert result['issue_counts'] == {'invalid_character_interval': 1}
    assert not result['transportable'] and not result['consistent']
