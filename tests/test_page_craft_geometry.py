from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_craft_geometry import crop_bbox, geometry_rows, native_detection, resize_geometry, score_native_support


def test_geometry_input_never_contains_transcription_or_auxiliary_ocr():
    rows = geometry_rows([dict(id='L1', bbox=[10, 20, 50, 40],
        text='never read', auxiliary_text='not passed', confidence=.9)])
    assert rows == [dict(id='L1', bbox=[10, 20, 50, 40])]
    with pytest.raises(ValueError, match='dupliqué'):
        geometry_rows(rows*2)


def test_crop_bbox_uses_native_half_open_bounds_and_only_available_context():
    assert crop_bbox([30, 40, 150, 60], (200, 100)) == [14, 20, 166, 80]
    assert crop_bbox([2, 1, 199, 99], (200, 100)) == [0, 0, 200, 100]
    assert crop_bbox([30.2, 40.1, 150.7, 59.9], (200, 100)) == [14, 20, 167, 80]
    with pytest.raises(ValueError, match='hors image'):
        crop_bbox([-1, 20, 50, 40], (200, 100))


def test_odd_resize_exposes_realized_scale_and_padding_separately():
    result = resize_geometry([73, 127, 3], [128, 192, 3], 1.5, [64, 96])
    assert result['resized_content_shape_yx'] == [109, 190]
    assert result['padding_ltrb'] == [0, 0, 2, 19]
    assert result['realized_resize_ratio_xy'] == [190/127, 109/73]
    assert result['official_score_to_crop_scale_xy'] == [4/3, 4/3]
    assert not result['score_cell_native_support_is_receptive_field']
    support = score_native_support(result)
    assert support.shape == (64, 96)
    assert np.count_nonzero(support == 1) == 54*95
    assert np.count_nonzero(support == .5) == 95
    assert np.all(support[:, 95] == 0)
    assert np.all(support[55:] == 0)


def test_partial_native_score_corner_is_quarter_cell_not_valid_whole_cell():
    result = resize_geometry([73, 73, 3], [128, 128, 3], 1.5, [64, 64])
    support = score_native_support(result)
    assert support[54, 54] == .25
    assert support[53, 54] == .5
    assert support[54, 53] == .5


@pytest.mark.parametrize(('input_shape','ratio','score_shape'), [
    ([128,192,3], float('nan'), [64,96]),
    ([128,192,3], 1.5, [128,192]),
    ([109,190,3], 1.5, [54,95]),
])
def test_inconsistent_network_geometry_is_refused(input_shape, ratio, score_shape):
    with pytest.raises(ValueError):
        resize_geometry([73,127,3], input_shape, ratio, score_shape)


def test_official_coordinate_mapping_adds_crop_origin_once_without_rounding():
    score = np.array([[3,6],[12,6],[12,15],[3,15]],dtype=float)
    original = score.copy()
    result = native_detection(score, 1.5, [100,200,200,300], [100,200,150,250], identifier='D')
    assert result['polygon'] == [[104,208],[116,208],[116,220],[104,220]]
    assert result['bbox'] == [104,208,116,220]
    assert result['within_source_crop'] and result['center_in_detector_bbox']
    assert np.array_equal(score, original)
    assert result['text'] is None and not result['geometry_certified']


def test_outside_quadrilateral_is_reported_without_clipping_or_certifying():
    result = native_detection([[-1,1],[80,1],[80,80],[-1,80]], 1.5,
        [100,200,200,300], [100,200,150,250], identifier='D')
    assert result['bbox'][0] < 100 and result['bbox'][2] > 200
    assert not result['within_source_crop']
    assert not result['geometry_certified']
    with pytest.raises(ValueError):
        native_detection([[0,0],[1,0],[1,float('nan')],[0,1]], 1.5,
                         [0,0,100,100], [1,1,20,20], identifier='bad')
