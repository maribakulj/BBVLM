#!/usr/bin/env python3
"""Blind unchanged PERO plus A37 inference on the fresh A54 blocks."""
from pathlib import Path

import run_bnl_independent_a46 as base


ROOT = Path(__file__).resolve().parents[1]
base.A45 = ROOT / "experiments/loop/bnl-independent-a54"
base.EXP = base.A45

if __name__ == "__main__":
    base.main()
