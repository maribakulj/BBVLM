from bbvlm.olr_continuation import horizontal_overlap, merge_conservative_streams


def test_horizontal_overlap_uses_narrower_box():
    assert horizontal_overlap((0, 0, 100, 10), (20, 20, 80, 30)) == 1.0
    assert horizontal_overlap((0, 0, 10, 10), (20, 0, 30, 10)) == 0.0


def test_merges_small_same_column_gap_only():
    boxes = {
        "a": (0, 0, 100, 100),
        "b": (5, 105, 95, 200),
        "c": (5, 250, 95, 300),
        "d": (200, 305, 300, 350),
    }
    got = merge_conservative_streams([["a"], ["b"], ["c"], ["d"]], boxes, 1000)
    assert got == [["a", "b"], ["c"], ["d"]]


def test_empty_and_invalid_inputs_fail_closed():
    assert merge_conservative_streams([], {}, 1000) == []
    try:
        merge_conservative_streams([["missing"]], {}, 1000)
    except KeyError:
        pass
    else:
        raise AssertionError("missing geometry must fail")
