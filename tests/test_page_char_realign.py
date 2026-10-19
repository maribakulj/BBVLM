from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_char_realign import repair


def annotation():
    return dict(id='L1', text='P. mot', status='retenue', training_eligible=True,
        reading_bbox=[0, 5, 100, 30], bbox=[10, 10, 70, 25],
        chars=[[10, 14, .8], [19, 21, .4], [20, 30, 0], [30, 40, .7], [40, 50, .8], [50, 60, .7]],
        words=[dict(text='P.', x0=10, y0=10, x1=19, y1=24), dict(text='mot', x0=30, y0=10, x1=69, y1=24)],
        alignment={'model_path': 'model', 'character_position_sources': ['word_ctc']*6})


def test_only_outside_word_is_realigned_text_boxes_and_other_chars_stay_identical():
    original = annotation()
    calls = []
    def align(model, text, crop):
        calls.append((model, text, crop))
        return dict(positions=[[10, 14, .9], [16, 19, .8]], alignment={'model_path': model})
    result = repair(np.full((40, 100), 255, np.uint8), [original], align)
    row = result['annotations'][0]
    assert calls == [('model', 'P.', [10, 5, 20, 30])]
    assert row['text'] == original['text'] and row['words'] == original['words']
    assert row['chars'][2:] == original['chars'][2:]
    assert original == annotation() and result['unresolved'] == []
    assert result['decisions'][0]['raw_input_shape'] == [25, 10]
    assert not result['promoted']


@pytest.mark.parametrize('positions', [[[10, 14, .9], [20, 20, .8]],
                                       [[10, 14, .9], [19, 21, .8]], [[10, 14, .9]]])
def test_zero_or_outside_positions_cannot_be_fabricated_to_pass(positions):
    original = annotation()
    result = repair(np.full((40, 100), 255, np.uint8), [original],
                    lambda model, text, crop: dict(positions=positions, alignment={'model_path': model}))
    row = result['annotations'][0]
    assert row['chars'] == original['chars'] and not row['training_eligible']
    assert row['status'] == 'repositionnement_caracteres_non_resolu'
    assert not result['decisions'][0]['accepted']


def test_model_change_is_refused_and_old_positions_preserved():
    original = annotation()
    result = repair(np.full((40, 100), 255, np.uint8), [original],
        lambda *args: dict(positions=[[10, 14, .9], [16, 19, .8]], alignment={'model_path': 'other'}))
    assert result['annotations'][0]['chars'] == original['chars']
    assert not result['decisions'][0]['accepted']


def test_visually_incomplete_word_crop_is_not_certified_by_a_forced_path():
    original = annotation()
    result = repair(np.full((40, 100), 255, np.uint8), [original],
                    lambda *args: pytest.fail('Incomplete source crop must not be aligned'),
                    [dict(line_id='L1', word_index=0, text='P.', reason='incomplete_native_component')])
    assert not result['decisions'][0]['accepted']
    assert result['annotations'][0]['chars'] == original['chars']
    assert not result['annotations'][0]['training_eligible']
