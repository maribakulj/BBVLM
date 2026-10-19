from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np
import pytest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parents[1]/'src/boxers')]
from native_frame_ctc import native_frames,constrain,source_frame_alignment
from forcectc import viterbi,graphe_ctc


def test_best_nonblank_in_padding_cannot_become_zero_width_source_character():
    logp=np.full((10,2),-8.);logp[:,0]=-1.;logp[-1,1]=0.;logp[6,1]=-2.
    masked,valid=constrain(logp,100,16)
    states=graphe_ctc([1]);old=viterbi(logp,states);new=viterbi(masked,states)
    assert old[1]==9 and new[1]==6 and valid[new[1]]
    assert masked[9,0]==logp[9,0] and masked[9,1]==-1e30


def test_partially_native_cells_remain_valid_even_when_center_is_in_padding():
    assert native_frames(5,36,16).tolist()==[False,False,True,False,False]
    assert native_frames(4,34,16).tolist()==[False,True,True,False]
    with pytest.raises(ValueError):native_frames(4,32,16)


def test_center_and_contained_policies_are_distinct_and_do_not_invent_admissible_cells():
    assert native_frames(4,34,16,'center').tolist()==[False]*4
    assert native_frames(4,34,16,'contained').tolist()==[False]*4
    assert native_frames(10,100,16,'center').tolist()==[False,False,True,True,True,True,True,True,False,False]
    assert native_frames(10,100,16,'contained').tolist()==[False,False,True,True,True,True,True,True,False,False]
    assert native_frames(10,100,10,'contained').sum()==8
    with pytest.raises(ValueError):native_frames(10,100,16,'unknown')


def test_impossible_repeat_alignment_is_refused_and_context_restores_callbacks():
    tensor=lambda *args,**kwargs:SimpleNamespace(shape=(1,1,10,34))
    module=SimpleNamespace(_ligne_tenseur=tensor,viterbi=viterbi,PAD=16)
    with source_frame_alignment(module) as audit:
        module._ligne_tenseur()
        assert module.viterbi(np.zeros((4,2)),graphe_ctc([1,1])) is None
        assert audit[0]['required_frames']==3 and audit[0]['native_frames']==2
    assert module._ligne_tenseur is tensor and module.viterbi is viterbi
    with pytest.raises(RuntimeError):
        with source_frame_alignment(module):raise RuntimeError('incident')
    assert module._ligne_tenseur is tensor and module.viterbi is viterbi
