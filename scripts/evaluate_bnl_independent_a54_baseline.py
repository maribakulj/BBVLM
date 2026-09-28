#!/usr/bin/env python3
"""Evaluate the sealed A54 PERO baseline after its blind outputs exist."""
from pathlib import Path

import evaluate_bnl_independent_a46 as base


ROOT = Path(__file__).resolve().parents[1]
base.A45 = ROOT / "experiments/loop/bnl-independent-a54"
base.EXP = base.A45

if __name__ == "__main__":
    base.main()
