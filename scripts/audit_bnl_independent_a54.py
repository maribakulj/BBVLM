#!/usr/bin/env python3
"""Open and audit the frozen A54 BnL sample after membership is sealed."""
from pathlib import Path

import audit_bnl_independent_a45 as base


ROOT = Path(__file__).resolve().parents[1]
base.BASE = ROOT / "experiments/loop/bnl-independent-a54"

if __name__ == "__main__":
    base.main()
