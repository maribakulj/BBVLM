from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_rectified_mapping import map_rectified_box


def grid(height=5, width=7):
    y, x = np.mgrid[:height, :width]
    return np.stack((x, y), axis=2).astype(float)


def test_identity_integer_pixel_support_preserves_inclusive_to_half_open_edges():
    r = map_rectified_box(grid(), [2, 1, 6, 4], image_size=(7, 5))
    assert r['source_support_bbox'] == [2, 1, 7, 5]
    assert r['sample_count'] == 20
    assert r['eligible_for_geometric_comparison']
    assert not r['word_geometry_certified']


def test_subpixel_samples_cover_every_source_neighbor_needed_for_interpolation():
    r = map_rectified_box(grid()+[10.25, 20.75], [2, 1, 4, 3], image_size=(100, 100))
    assert r['source_center_envelope'] == [12.25, 21.75, 14.25, 23.75]
    assert r['source_support_bbox'] == [12, 21, 16, 25]


def test_curved_mapping_extremum_is_not_lost_by_only_mapping_four_corners():
    m = grid()+[10, 20]
    m[2, 3, 1] = 37
    r = map_rectified_box(m, [0, 0, 6, 4], image_size=(100, 100))
    assert r['source_support_bbox'] == [10, 20, 17, 38]


def test_out_of_page_is_explicit_and_never_clamped_into_accepted_geometry():
    r = map_rectified_box(grid()-[.125, 0], [0, 0, 6, 4], image_size=(7, 5))
    assert r['status'] == 'source_mapping_out_of_page'
    assert r['source_support_bbox'] is None
    assert r['unclipped_source_support_bbox'][0] == -1
    assert r['out_of_page_samples'] == 5
    assert not r['source_clipping_performed']


def test_nonfinite_sample_refuses_box_but_irrelevant_grid_area_does_not():
    m = grid()
    m[0, 0] = [np.nan, np.inf]
    bad = map_rectified_box(m, [0, 0, 2, 2], image_size=(7, 5))
    assert bad['status'] == 'nonfinite_source_mapping'
    assert bad['invalid_samples'] == 1
    good = map_rectified_box(m, [1, 1, 2, 2], image_size=(7, 5))
    assert good['source_support_bbox'] == [1, 1, 3, 3]


@pytest.mark.parametrize('bbox', [[0, 0, 7, 4], [0, 0, 1.5, 2], [True, 0, 1, 1], [3, 0, 1, 2]])
def test_invalid_local_boxes_cannot_be_truncated_or_reversed_silently(bbox):
    with pytest.raises(ValueError):
        map_rectified_box(grid(), bbox, image_size=(7, 5))
