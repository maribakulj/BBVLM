"""Prepare frozen A11 page 0010 using the shared blind coarse-role builder."""
import prepare_spiritualist_coarse_v4 as base

base.PAGE="0010"
base.SEED="bbvlm-semantic-v6-full-2026092711"
base.OUT=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v6-full-validation"
base.PROFILE=base.ROOT/"experiments/loop/spiritualist-v1/semantic-v6-typography/full-validation-profile.json"

if __name__=="__main__": base.main()
