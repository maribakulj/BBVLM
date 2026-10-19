from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_word_boundaries import space_anchored_boundaries


def propose(text, positions, boundary, mask=None, **kwargs):
    if mask is None:
        mask = np.zeros((20, 80), np.uint8)
        mask[8:11,10:22] = 255
        mask[8:11,24:40] = 255
        mask[2:18,50:58] = 255
        mask[8:18,63:70] = 255
    return space_anchored_boundaries(text, [0,0,80,20], mask, positions, boundary, **kwargs)


def test_space_peak_avoids_a_false_boundary_between_parts_of_punctuation():
    positions = [[13,15,.99], [43,47,.99], [52,54,.99], [65,67,.99]]
    before = [positions.copy(), [23]]
    result = propose('— La', positions, [23])
    row = result['boundaries'][0]
    assert row['status'] == 'candidate'
    assert row['proposed_x'] == 45
    assert row['native_white_run'] == [40,50]
    assert row['transferred_ink_pixels'] == 16*3
    assert row['cuts_observed_ink'] is False
    assert row['native_support_deleted'] is False
    assert row['semantic_component_assignment_verified'] is False
    assert result['text'] == '— La' and result['annotations_modified'] is False
    assert positions == before[0]


def test_existing_boundary_in_same_white_gap_remains_exactly_unchanged():
    result = propose('— La', [[13,15,.99], [43,47,.99], [52,54,.99], [65,67,.99]], [41])
    assert result['boundaries'][0]['status'] == 'same_native_gap'
    assert result['boundaries'][0]['proposed_x'] == 41
    assert result['candidates'] == 0


def test_low_confidence_whitespace_never_moves_boundary():
    result = propose('— La', [[13,15,.99], [43,47,.05], [52,54,.99], [65,67,.99]], [23])
    assert result['boundaries'][0]['status'] == 'space_support_insufficient'
    assert result['boundaries'][0]['proposed_x'] == 23


def test_no_native_white_column_never_creates_a_gap():
    result = propose('— La', [[13,15,.99], [43,47,.99], [52,54,.99], [65,67,.99]], [23],
                     mask=np.full((20,80),255,np.uint8))
    assert result['boundaries'][0]['status'] == 'no_native_white_column'
    assert result['candidates'] == 0


def test_space_peak_outside_neighboring_characters_is_refused():
    result = propose('— La', [[13,15,.99], [60,64,.99], [52,54,.99], [65,67,.99]], [23])
    assert result['boundaries'][0]['status'] == 'space_anchor_outside_neighbors'


def test_empty_space_interval_is_not_turned_into_an_anchor():
    result = propose('— La', [[13,15,.99], [45,45,.99], [52,54,.99], [65,67,.99]], [23])
    assert result['boundaries'][0]['status'] == 'empty_space_anchor'


def test_multiple_whitespace_characters_are_preserved_and_all_require_support():
    result = propose('—\t La', [[13,15,.99], [42,44,.99], [46,48,.99], [52,54,.99], [65,67,.99]], [23])
    assert result['text'] == '—\t La'
    assert result['boundaries'][0]['whitespace_indices'] == [1,2]
    assert result['boundaries'][0]['proposed_x'] == 45


def test_native_global_coordinates_and_shape_must_match():
    mask = np.zeros((20,80),np.uint8)
    result = space_anchored_boundaries('a b',[100,200,180,220],mask,
        [[110,112,.9],[120,122,.95],[130,132,.9]], [119])
    assert result['boundaries'][0]['status'] == 'same_native_gap'
    with pytest.raises(ValueError,match='Masque'):
        space_anchored_boundaries('a b',[100,200,180,221],mask,
            [[110,112,.9],[120,122,.95],[130,132,.9]], [119])


@pytest.mark.parametrize('positions,boundaries', [([], [23]),
    ([[13,15,.99], [43,47,.99], [52,54,.99], [65,67,.99]], []),
    ([[13,15,.99], [43,47,.99], [52,54,.99], [65,67,.99]], [23.5])])
def test_inconsistent_inputs_are_rejected(positions, boundaries):
    with pytest.raises(ValueError):
        propose('— La', positions, boundaries)
