from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_line_ink import PolygonBaselineInk
from page_line_ink_v2 import PolygonBaselineInkV2


def line(lid, baseline, top, bottom):
    return dict(id=lid, bbox=[5, top, 195, bottom], baseline=[[5, baseline], [195, baseline]],
                polygon=[[5, top], [195, top], [195, bottom], [5, bottom]], source='kraken-blla/full')


def fixture():
    gray = np.full((150, 200), 255, np.uint8)
    gray[25:46, 30:43] = 0
    gray[75:96, 30:43] = 0
    return gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)]


def test_only_one_pixel_foreign_body_fringe_exception_changes_v1():
    gray, rows = fixture()
    mask = (gray < 128).astype(np.uint8)*255
    mask[24, 30] = 255
    old, _ = PolygonBaselineInk(gray, rows).filter_mask('B', mask, 0, 0)
    new, audit = PolygonBaselineInkV2(gray, rows).filter_mask('B', mask, 0, 0)
    assert old[24:46, 30:43].any() and not new[24:46, 30:43].any()
    assert new[75:96, 30:43].all()
    assert audit['native_threshold_fringe_components'] == 1 and audit['native_threshold_fringe_pixels'] == 1


def test_two_pixel_extension_is_not_treated_as_threshold_fringe():
    gray, rows = fixture()
    mask = (gray < 128).astype(np.uint8)*255
    mask[23:25, 30] = 255
    new, audit = PolygonBaselineInkV2(gray, rows).filter_mask('B', mask, 0, 0)
    assert np.array_equal(new, mask) and audit['native_threshold_fringe_components'] == 0


def test_small_punctuation_never_gets_foreign_fringe_exception():
    gray, rows = fixture()
    gray[25:46, 30:43] = 255
    gray[43:47, 30:34] = 0
    mask = (gray < 128).astype(np.uint8)*255
    mask[42, 30] = 255
    new, audit = PolygonBaselineInkV2(gray, rows).filter_mask('B', mask, 0, 0)
    assert np.array_equal(new, mask) and audit['native_threshold_fringe_components'] == 0


def test_foreign_polygon_must_cover_every_local_pixel():
    gray, rows = fixture()
    rows[0]['polygon'] = [[5, 25], [195, 25], [195, 55], [5, 55]]
    mask = (gray < 128).astype(np.uint8)*255
    mask[24, 30] = 255
    new, audit = PolygonBaselineInkV2(gray, rows).filter_mask('B', mask, 0, 0)
    assert np.array_equal(new, mask) and audit['native_threshold_fringe_components'] == 0
