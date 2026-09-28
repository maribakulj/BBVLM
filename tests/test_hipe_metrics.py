from bbvlm.hipe_metrics import alignment_counts, cmer, hipe_normalize


def test_upstream_normalization_order_and_boundaries():
    assert hipe_normalize("ŒUVRE_ſ —\nAͤ Oͤ Uͤ, Straße ꝛ æ") == "oeuvre ſ ä ö ü strasse r ae"
    assert hipe_normalize("A—\nB C¬\nD") == "ab cd"
    # The upstream uses lower(), not casefold(), and does not NFC-normalize.
    assert hipe_normalize("ẞ É e\u0301") == "ss é e"


def test_alignment_counts_cover_all_operation_types():
    assert alignment_counts("same", "same") == {
        "hits": 4, "substitutions": 0, "deletions": 0, "insertions": 0}
    assert alignment_counts("abc", "axdc") == {
        "hits": 2, "substitutions": 1, "deletions": 0, "insertions": 1}
    assert alignment_counts("abcd", "acd") == {
        "hits": 3, "substitutions": 0, "deletions": 1, "insertions": 0}


def test_mer_uses_alignment_length_not_reference_length():
    result = cmer("a", "abc")
    assert result["errors"] == 2
    assert result["denominator"] == 3
    assert result["cmer"] == 2 / 3
