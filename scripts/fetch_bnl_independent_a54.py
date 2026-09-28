#!/usr/bin/env python3
"""Fetch only the pre-frozen A54 BnL members via verified ZIP ranges."""
from pathlib import Path

import fetch_bnl_independent_a45 as base


ROOT = Path(__file__).resolve().parents[1]
base.EXPERIMENT = ROOT / "experiments/loop/bnl-independent-a54"
base.SPLIT = base.EXPERIMENT / "split.json"
base.SOURCE = base.EXPERIMENT / "source"

if __name__ == "__main__":
    base.main()
