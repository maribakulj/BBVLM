"""Evaluate frozen A09 validation page 0050 using the shared strict evaluator."""
import evaluate_spiritualist_coarse_v4 as base

base.BASE=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v5-coarse-order-validation"

if __name__=="__main__":base.main()
