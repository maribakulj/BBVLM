"""Prepare frozen A09 validation page 0050 using the shared blind builder."""
from pathlib import Path
import prepare_spiritualist_coarse_v4 as base

base.PAGE="0050"
base.SEED="bbvlm-semantic-v5-coarse-order-2026092709"
base.OUT=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v5-coarse-order-validation"
base.PROFILE=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v5-coarse-order/profile.json"

if __name__=="__main__":base.main()
