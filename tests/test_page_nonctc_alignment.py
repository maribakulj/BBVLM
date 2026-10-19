from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_nonctc_alignment import align_crop, tokens_with_offsets


class Boxes:
    def __init__(self, boxes):
        self.value = boxes

    def boxes(self, gray, line):
        return self.value


def image():
    a = np.full((50, 160), 255, np.uint8)
    a[15:36, 10:30] = 0
    a[15:36, 90:115] = 0
    return a


def test_whitespace_and_apostrophe_offsets_are_exact():
    text = "l’autre\n  mot\tfin."
    assert [text[t['start']:t['end']] for t in tokens_with_offsets(text)] == ['l’autre', 'mot', 'fin.']
    result = align_crop(image(), 'l’autre\n  mot', 'dtw_snap', backend=Boxes([(10, 15, 29, 35), (90, 15, 114, 35)]))
    assert result['text'] == 'l’autre\n  mot'
    assert result['status'] == 'geometry_observed_unvalidated'
    assert not result['training_eligible'] and not result['glyphs_certified']


def test_inkgap_proportional_fallback_is_refused_before_algorithm():
    class MustNotRun:
        def boxes(self, *args):
            raise AssertionError('proportional fallback must be blocked first')
    result = align_crop(image(), 'one two three', 'inkgap_dp', backend=MustNotRun())
    assert result['status'] == 'proportional_fallback_forbidden' and not result['fallback_used']


def test_dtw_box_without_ink_is_not_reported_as_observed_geometry():
    result = align_crop(image(), 'one two', 'dtw_snap', backend=Boxes([(10, 15, 29, 35), (40, 15, 50, 35)]))
    assert result['status'] == 'word_interval_without_observed_ink' and result['words'] == []
    assert align_crop(np.full((40, 100), 255, np.uint8), 'one', 'dtw_snap')['status'] == 'no_observed_ink'


def test_invalid_cell_does_not_pass_as_success():
    result = align_crop(image(), 'one two', 'dtw_snap', backend=Boxes([(10, 15, 30, 35), (30, 15, 115, 35)]))
    assert result['status'] == 'invalid_or_overlapping_word_geometry'
