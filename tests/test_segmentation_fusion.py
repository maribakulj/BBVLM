import sys
from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from segmentation_fusion import fuse


def row(id,bbox):return dict(id=id,bbox=bbox,source='kraken-blla/full')


def image():
    gray=np.full((160,240),255,np.uint8)
    for y in (30,90):
        for x in range(20,200,18):gray[y:y+10,x:x+8]=0
    return gray


def test_complement_preserves_primary_pixels_and_audits_duplicate():
    first=[row('L0001',[15.2,25.3,202.4,44.5])]
    second=[row('L0001',[16,26,204,45]),row('L0002',[15,85,205,106])]
    original=deepcopy(first)
    rows,audit=fuse(image(),first,second)
    assert first==original
    assert len(rows)==2 and audit['added']==1
    assert rows[0]['bbox']==original[0]['bbox']
    assert audit['decisions'][0]['reason']=='same_line_geometry'
    assert audit['decisions'][1]['novel_fraction']==1


def test_partial_fragment_does_not_double_count_existing_ink():
    first=[row('L0001',[10,24,210,46])]
    # La moitié droite est déjà couverte ; aucune ligne supplémentaire.
    rows,audit=fuse(image(),first,[row('S1',[130,18,220,60])])
    assert len(rows)==1 and not audit['decisions'][0]['accepted']
    assert audit['decisions'][0]['novel_pixels']==0


def test_blank_or_invalid_candidate_never_creates_a_line():
    rows,audit=fuse(image(),[],[row('S1',[0,0,10,10])])
    assert not rows and audit['decisions'][0]['reason']=='insufficient_native_ink'
    with pytest.raises(ValueError,match='hors page'):
        fuse(image(),[],[row('S1',[-1,0,10,10])])


def test_added_candidate_cannot_be_added_a_second_time():
    rows,audit=fuse(image(),[],[row('S1',[15,25,205,45]),row('S2',[15,25,205,45])])
    assert len(rows)==1 and audit['added']==1
    assert audit['decisions'][1]['canonical_origin']=={'pass':'supplement','id':'S1'}
