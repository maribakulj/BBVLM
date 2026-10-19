from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from baseline_ink import BaselineInk


def row(id,y):
    return dict(id=id,bbox=[5,y-30,195,y+8],baseline=[[5,y],[195,y]],source='kraken-blla/full')


def test_upper_neighbor_ink_does_not_enter_lower_line_mask():
    gray=np.full((140,200),255,np.uint8)
    gray[20:46,30:45]=0;gray[65:91,30:45]=0
    model=BaselineInk(gray,[row('L1',46),row('L2',91)])
    mask,x,y=model.mask('L2',[0,10,200,110])
    assert mask[65-y:91-y,30:45].any() and not mask[20-y:46-y,30:45].any()
    assert model.audit['promoted'] is False


def test_dot_above_stem_follows_its_letter_and_component_stays_whole():
    gray=np.full((140,200),255,np.uint8)
    gray[20:46,80:95]=0;gray[65:91,30:36]=0;gray[56:60,30:36]=0
    model=BaselineInk(gray,[row('L1',46),row('L2',91)])
    mask,_,_=model.mask('L2',[0,0,200,140])
    assert mask[56:60,30:36].all() and mask[65:91,30:36].all()


def test_long_vertical_rule_is_unassigned_instead_of_cut_into_letters():
    gray=np.full((140,200),255,np.uint8);gray[5:130,180:183]=0
    model=BaselineInk(gray,[row('L1',46),row('L2',91)])
    assert not model.mask('L1',[0,0,200,140])[0].any()
    assert not model.mask('L2',[0,0,200,140])[0].any()
    assert model.audit['unassigned_components']>=1


def test_reference_text_or_unknown_baseline_cannot_enter_owner_model():
    gray=np.full((140,200),255,np.uint8)
    with pytest.raises(ValueError,match='automatique'):
        BaselineInk(gray,[{**row('L1',46),'text':'reference'}])
    model=BaselineInk(gray,[row('L1',46)])
    with pytest.raises(ValueError,match='inconnu'):model.mask('other',[0,0,200,140])


def test_equally_plausible_baselines_do_not_invent_component_owner():
    gray=np.full((140,200),255,np.uint8);gray[40:66,30:45]=0
    model=BaselineInk(gray,[row('L1',65),row('L2',67)])
    assert not model.mask('L1',[0,0,200,140])[0].any()
    assert not model.mask('L2',[0,0,200,140])[0].any()
    assert model.audit['ambiguous_baseline_components']>=1


def test_component_box_includes_native_whole_accent_outside_source_crop():
    gray=np.full((140,200),255,np.uint8)
    gray[65:91,30:36]=0;gray[50:54,30:36]=0
    model=BaselineInk(gray,[row('L1',91)])
    box=model.component_box('L1',[5,60,195,100])
    assert box==[5,50,195,100]
    assert model.mask('L1',box)[0][0:4,25:31].all()


def test_conservative_filter_removes_foreign_component_and_preserves_own_ink():
    gray=np.full((140,200),255,np.uint8)
    gray[20:46,30:45]=0;gray[65:91,30:45]=0
    model=BaselineInk(gray,[row('L1',46),row('L2',91)])
    mask=(gray==0).astype(np.uint8)*255
    (result,_,_),audit=model.filter_mask('L2',mask,0,0)
    assert not result[20:46,30:45].any() and result[65:91,30:45].all()
    assert audit['removed_pixels']==26*15


def test_conservative_filter_preserves_ambiguous_or_mixed_components_whole():
    gray=np.full((140,200),255,np.uint8)
    gray[20:46,30:45]=0;gray[65:91,30:45]=0
    model=BaselineInk(gray,[row('L1',46),row('L2',91)])
    mixed=(gray==0).astype(np.uint8)*255;mixed[40:70,35:40]=255
    (result,_,_),audit=model.filter_mask('L2',mixed,0,0)
    assert np.array_equal(result,mixed) and not audit['removed']
    model.owners[:]=-1
    (result,_,_),audit=model.filter_mask('L2',mixed,0,0)
    assert np.array_equal(result,mixed) and not audit['removed']


def test_punctuation_near_own_baseline_does_not_follow_next_line_body():
    gray=np.full((140,200),255,np.uint8)
    gray[45:49,30:35]=0;gray[59:86,30:45]=0
    model=BaselineInk(gray,[row('L1',48),row('L2',86)])
    assert model.mask('L1',[0,0,200,140])[0][45:49,30:35].all()
    assert not model.mask('L2',[0,0,200,140])[0][45:49,30:35].any()


def test_horizontal_dash_keeps_its_baseline_when_lower_letters_are_near():
    gray=np.full((140,200),255,np.uint8)
    gray[43:46,20:65]=0;gray[59:86,30:45]=0
    model=BaselineInk(gray,[row('L1',48),row('L2',86)])
    assert model.mask('L1',[0,0,200,140])[0][43:46,20:65].all()


def test_vertical_detector_baseline_is_preserved_unresolved_without_fake_curve():
    gray=np.full((140,200),255,np.uint8);gray[20:91,30:34]=0
    vertical={**row('L1',91),'baseline':[[30,20],[30,91]]}
    model=BaselineInk(gray,[vertical]);mask=(gray==0).astype(np.uint8)*255
    assert model.audit['unsupported_baseline_ids']==['L1']
    assert not model.mask('L1',[0,0,200,140])[0].any()
    (filtered,_,_),audit=model.filter_mask('L1',mask,0,0)
    assert np.array_equal(filtered,mask) and audit['unsupported_baseline']
