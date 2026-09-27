"""Diagnostic of false confidence: read ALL six non-escalated A18 items.

The global experiment is motivated by consumed development results. No item is
selected by its reference disagreement; even exact lines enter this ablation.
"""
from pathlib import Path
from prepare_sbb_escalation_a18 import main

if __name__ == '__main__':
    main('not_uncertain', Path(__file__).resolve().parents[1]/
         'experiments/loop/routing-a21/input')
