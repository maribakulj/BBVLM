from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_line_ink import PolygonBaselineInk, refine_words


def line(lid, baseline, top, bottom):
    return dict(id=lid, bbox=[5, top, 195, bottom], baseline=[[5, baseline], [195, baseline]],
                polygon=[[5, top], [195, top], [195, bottom], [5, bottom]], source='kraken-blla/full')


def page():
    gray = np.full((150, 200), 255, np.uint8)
    gray[25:46, 30:43] = 0
    gray[75:96, 30:43] = 0
    return gray


def test_foreign_whole_component_needs_polygon_and_baseline_evidence():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)])
    mask = (gray < 128).astype(np.uint8)*255
    filtered, audit = model.filter_mask('B', mask, 0, 0)
    assert not filtered[25:46, 30:43].any() and filtered[75:96, 30:43].all()
    assert audit['removed_pixels'] == 21*13 and audit['component_cut_pixels'] == 0
    assert audit['removed'][0]['foreign_line'] == 'A'


def test_polygon_overlap_is_not_resolved_by_cutting_component():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 25, 110)])
    mask = (gray < 128).astype(np.uint8)*255
    filtered, audit = model.filter_mask('B', mask, 0, 0)
    assert np.array_equal(filtered, mask) and not audit['removed']


def test_polygon_alone_cannot_assign_a_component_far_from_its_baseline():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 90, 10, 55), line('B', 96, 60, 110)])
    filtered, audit = model.filter_mask('B', (gray < 128).astype(np.uint8)*255, 0, 0)
    assert filtered[25:46, 30:43].all() and not audit['removed']


def test_ambiguous_accent_and_punctuation_survive_whole():
    gray = page()
    gray[62:66, 60:64] = 0  # petite marque entre deux lignes, sans preuve de baseline
    gray[94:98, 70:74] = 0  # ponctuation au pied de B
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)])
    filtered, _ = model.filter_mask('B', (gray < 128).astype(np.uint8)*255, 0, 0)
    assert filtered[62:66, 60:64].all() and filtered[94:98, 70:74].all()


def test_mixed_connected_component_cannot_lose_own_punctuation():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)])
    mask = (gray < 128).astype(np.uint8)*255
    mask[40:80, 34:38] = 255  # connexion locale absente de la preuve native
    filtered, audit = model.filter_mask('B', mask, 0, 0)
    assert np.array_equal(filtered, mask) and not audit['removed']


def test_unknown_native_pixels_prevent_foreign_removal():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)])
    mask = (gray < 128).astype(np.uint8)*255
    mask[24, 30] = 255  # un seul pixel non prouvé, la composante entière reste
    filtered, _ = model.filter_mask('B', mask, 0, 0)
    assert filtered[24:46, 30:43].sum() == mask[24:46, 30:43].sum()


def test_text_and_nonautomatic_sources_are_not_owner_inputs():
    gray = page()
    for row in [{**line('A', 46, 10, 55), 'text': 'forbidden'},
                {**line('A', 46, 10, 55), 'source': 'manual'}]:
        with pytest.raises(ValueError, match='automatique'):
            PolygonBaselineInk(gray, [row])


def test_refinement_removes_neighbor_envelope_without_touching_text_or_ctc():
    gray = page()
    model = PolygonBaselineInk(gray, [line('A', 46, 10, 55), line('B', 96, 60, 110)])
    original = dict(id='B', status='placee', text='Mot', reading_bbox=[5, 10, 195, 110],
        chars=[[30, 31, .5], [35, 36, .5], [40, 41, .5]],
        words=[dict(text='Mot', x0=30, y0=25, x1=42, y1=95, synthetic=False)],
        alignment={'word_geometry': {'version': 'ctc-ink-whitespace-v4', 'boundaries': []}})
    result, audit = refine_words(gray, original, model)
    assert audit['changed'] and result['words'][0]['y0'] == 75
    assert result['words'][0]['y1'] == 95
    assert result['text'] == original['text'] and result['chars'] == original['chars']
    assert result['alignment'] == original['alignment']
    assert original['words'][0]['y0'] == 25
    assert not result['line_ink_diagnostic']['promoted']
