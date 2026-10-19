from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))


def test_descender_from_upper_line_does_not_hide_the_word_gap():
    from boxers.forcectc import body_white_columns
    mask = np.zeros((48, 120), np.uint8)
    mask[20:40, 10:50] = 255      # mot gauche, corps des lettres
    mask[20:40, 70:110] = 255     # mot droit
    mask[0:12, 45:75] = 255       # jambage de la ligne du dessus, au-dessus du blanc
    occ = (mask > 0).any(axis=0)
    assert occ[50:70].all()                       # aucun blanc plein-hauteur
    white = body_white_columns(mask)
    assert set(range(50, 70)) <= set(white.tolist())  # mais un blanc dans le corps
    assert not set(range(12, 48)) & set(white.tolist())


def test_dust_in_the_body_band_is_ignored_but_letters_are_not():
    from boxers.forcectc import body_white_columns
    mask = np.zeros((48, 120), np.uint8)
    mask[20:40, 10:50] = 255
    mask[20:40, 70:110] = 255
    mask[30:32, 60:62] = 255      # poussière de 4 px
    white = set(body_white_columns(mask).tolist())
    assert 60 in white and 61 in white and 30 not in white


def test_independent_ctc_reading_can_lift_an_ink_template_suspicion():
    from page_geometry_repair import _independent_reading_agreement
    assert _independent_reading_agreement(dict(text='NET DE TOUS IMPOTS',
                                               auxiliary_text='NETDE VOUS IMPOTS')) >= .85
    assert _independent_reading_agreement(dict(text='A sa vue, Maurice de découvrit :',
                                               auxiliary_text='s tnse Mfannien de degprggrmse')) < .85
    assert _independent_reading_agreement(dict(text='touche :', auxiliary_text='')) == 0


def test_visual_equivalent_only_after_exact_glyph_and_text_unchanged():
    from types import SimpleNamespace
    from boxers.forcectc import encode_text
    codec = SimpleNamespace(c2l={'9': [1], '0': [2], 'o': [3]})
    import pytest
    with pytest.raises(ValueError):
        encode_text(codec, '90º')
    codes, positions = encode_text(codec, '90º', visual_fallback=True)
    assert codes == [1, 2, 3] and positions == [(0,), (1,), (2,)]
    with pytest.raises(ValueError):
        encode_text(codec, '9€', visual_fallback=True)
