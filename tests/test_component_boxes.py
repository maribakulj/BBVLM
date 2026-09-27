import numpy as np

from bbvlm.component_boxes import (
    TRAILING_PUNCTUATION,
    refine_cells,
    refine_cells_text,
    selected_ink,
)


def test_whole_stem_and_detached_accent_survive_satellites():
    ink = np.zeros((60, 100), dtype="uint8")
    ink[25:45, 10:80] = 255
    ink[8:30, 30:36] = 255  # connected tall stem
    ink[17:20, 60:65] = 255  # detached accent
    ink[0:2, 90:95] = 255  # distant top noise
    mask, _ = selected_ink(ink, "satellites")
    assert mask[8:30, 30:36].all()
    assert mask[17:20, 60:65].all()
    assert not mask[0:2, 90:95].any()


def test_blank_and_punctuation_do_not_drop_tokens():
    blank = np.full((60, 100), 255, dtype="uint8")
    boxes = [[0, 0, 45, 60], [50, 0, 100, 60]]
    result, diag = refine_cells(blank, [0, 0, 100, 60], boxes, "body")
    assert result == boxes
    assert diag["fallback_cells"] == 2
    blank[30:33, 10:30] = 0
    result, diag = refine_cells(blank, [0, 0, 100, 60], boxes, "body")
    assert len(result) == 2
    assert result[0] == [10, 30, 30, 33]


def test_text_guided_terminal_rescue_is_selective():
    gray = np.full((60, 120), 255, dtype="uint8")
    gray[25:45, 10:70] = 0
    gray[53:56, 90:93] = 0  # detached terminal period, outside A32 radius/band
    gray[2:5, 105:108] = 0  # unrelated high noise
    plain = [{"text": "mot", "bbox": [8, 10, 98, 55]}]
    punct = [{"text": "mot.", "bbox": [8, 10, 98, 55]}]
    without, d0 = refine_cells_text(gray, [0, 0, 120, 60], plain)
    with_punct, d1 = refine_cells_text(gray, [0, 0, 120, 60], punct)
    assert without[0][2] == 70
    assert with_punct[0][2] == 93
    assert len(d0["rescues"]) == 0 and len(d1["rescues"]) == 1


def test_conservative_text_rescue_rejects_small_blob_and_star_trigger():
    gray = np.full((60, 120), 255, dtype="uint8")
    gray[25:45, 10:70] = 0
    gray[53:56, 90:93] = 0  # 9 px: below the frozen A34 minimum
    punctuation = set(TRAILING_PUNCTUATION) - {"*"}
    for token in ("mot.", "mot*"):
        result, diagnostic = refine_cells_text(
            gray,
            [0, 0, 120, 60],
            [{"text": token, "bbox": [8, 10, 98, 55]}],
            minimum_rescue_area=20,
            trailing_punctuation=punctuation,
        )
        assert result[0][2] == 70
        assert diagnostic["rescues"] == []
