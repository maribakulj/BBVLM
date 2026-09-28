import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/evaluate_bnl_vlm_a54.py"
SPEC = importlib.util.spec_from_file_location("evaluate_bnl_vlm_a54", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_guard_accepts_unique_declared_edit():
    answer = {"text": "le monde", "decision": "edit", "uncertain": False,
              "edits": [{"before": "monde.", "after": "monde", "visual_reason": "no dot"}]}
    text, audit = MODULE.validate_and_apply("le monde.", answer)
    assert text == "le monde"
    assert audit["accepted"]


def test_guard_rejects_unreported_lexical_rewrite():
    answer = {"text": "le monde", "decision": "keep", "uncertain": False, "edits": []}
    text, audit = MODULE.validate_and_apply("la monde", answer)
    assert text == "la monde"
    assert not audit["accepted"]


def test_guard_rejects_ambiguous_before_span():
    answer = {"text": "la bb", "decision": "edit", "uncertain": False,
              "edits": [{"before": "a", "after": "b", "visual_reason": "glyph"}]}
    text, audit = MODULE.validate_and_apply("la aa", answer)
    assert text == "la aa"
    assert not audit["accepted"]
