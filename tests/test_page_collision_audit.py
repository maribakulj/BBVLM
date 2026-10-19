from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_collision_audit import collision_pairs, support_kind, NativeEvidence
from page_line_ink_v2 import PolygonBaselineInkV2


def test_white_envelope_intersection_is_not_called_shared_ink():
    a = np.array([[1, 0], [0, 0]], bool)
    b = np.array([[0, 0], [0, 1]], bool)
    assert support_kind(a, b) == ('disjoint_mask_pixels', [1, 1], 0)
    assert support_kind(a, a) == ('shared_mask_pixels', [1, 1], 1)
    assert support_kind(a, np.zeros_like(a)) == ('one_sided_mask_pixels', [1, 0], 0)
    assert support_kind(np.zeros_like(a), np.zeros_like(a))[0] == 'no_mask_pixels'


def test_inclusive_word_edges_are_counted_as_real_rectangle_collision():
    rows = [dict(id='A', words=[dict(x0=1, y0=1, x1=5, y1=5)]),
            dict(id='B', words=[dict(x0=5, y0=5, x1=8, y1=8)])]
    assert collision_pairs(rows)[0]['intersection'] == [5, 5, 6, 6]


def test_competing_polygon_support_remains_distinct_from_baseline_distance():
    gray = np.full((100, 100), 255, np.uint8)
    gray[20:41, 30:45] = 0
    rows = [dict(id=lid, bbox=[5, 5, 90, 80], baseline=[[5, baseline], [90, baseline]],
                 polygon=[[5, 5], [90, 5], [90, 80], [5, 80]], source='kraken-blla/full')
            for lid, baseline in [('A', 41), ('B', 79)]]
    model = PolygonBaselineInkV2(gray, rows)
    label = int(model.labels[30, 35])
    result = NativeEvidence(model).component(label)
    assert result['kind'] == 'overlapping_competing_polygons' and result['owner'] is None
    assert result['top_two_polygon_shared_ink_pixels'] > 0
    distances = {row['id']: row['baseline_distance_line_heights'] for row in result['candidates']}
    assert distances['A'] < .1 and distances['B'] > .5


def test_component_between_adjacent_polygons_is_not_mislabeled_as_simple_undercoverage():
    gray = np.full((100, 100), 255, np.uint8)
    gray[20:41, 30:45] = 0
    rows = [dict(id=lid, bbox=[left, 5, right, 80], baseline=[[left, baseline], [right, baseline]],
                 polygon=[[left, 5], [right, 5], [right, 80], [left, 80]], source='kraken-blla/full')
            for lid, baseline, left, right in [('A', 41, 5, 37), ('B', 79, 38, 90)]]
    model = PolygonBaselineInkV2(gray, rows)
    label = int(model.labels[30, 35])
    result = NativeEvidence(model).component(label)
    assert result['kind'] == 'component_spans_adjacent_polygons'
    assert result['top_two_polygon_shared_ink_pixels'] == 0
    assert result['best_polygon_undercoverage']
