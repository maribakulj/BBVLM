import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_bnf_olr_a27 import prf,order_accuracy

def test_empty_reference_never_scores_as_perfect():
    assert prf(set(),set())['f1']==0.0
    assert order_accuracy([],[])['accuracy_on_covered']==0.0
