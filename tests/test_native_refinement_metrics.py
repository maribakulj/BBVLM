import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate_native_refinement_a35 import joint_metrics


def test_perfect_geometry_does_not_hide_wrong_text_or_missing_words():
    rows = [{'id': 'r', 'words': [{'text': 'one', 'bbox': [0, 0, 10, 10]},
                                 {'text': 'two', 'bbox': [20, 0, 30, 10]}]}]
    predicted = {'r': [{'text': 'wrong', 'bbox': [0, 0, 10, 10]}]}
    score = joint_metrics(rows, predicted)
    assert score['reference_words'] == 2
    assert score['recall_exact_text_and_iou80'] == 0
    assert joint_metrics(rows, {'r': []})['recall_exact_text_and_iou80'] == 0


def test_joint_metric_fails_closed_on_empty_reference():
    with pytest.raises(ValueError, match='empty reference'):
        joint_metrics([], {})
