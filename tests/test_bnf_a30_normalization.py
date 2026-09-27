from audit_bnf_region_ocr_a30 import retrieval


def test_retrieval_unifies_nonbreaking_hyphen_before_joining_line_break():
    assert retrieval("réu\u2011\nnie") == "réunie"
    assert retrieval("Henri\u2011Martin") == "henri-martin"


def test_retrieval_keeps_diplomatic_punctuation_as_search_punctuation():
    assert retrieval("« L’affaire — continue. »") == "« l'affaire - continue. »"
