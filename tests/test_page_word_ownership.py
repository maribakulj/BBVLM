from copy import deepcopy
import numpy as np
import pytest

import alto
from page_collision_export import diagnostic_alto
from page_word_ownership import refine


def row(lid, y, box):
    return dict(id=lid, bbox=box, reading_bbox=box, baseline=[[5,y],[70,y]],
                text='mot', words=[dict(text='mot',x0=10,x1=60,y0=y-10,y1=y+2)])


def test_ownership_uses_pixels_without_changing_input_or_text():
    gray=np.full((70,80),255,np.uint8)
    gray[15:24,10:30]=0;gray[35:44,35:60]=0
    original=[row('a',25,[5,5,70,35]),row('b',45,[5,25,70,60])]
    before=deepcopy(original)
    result,audit=refine(gray,original)
    assert original==before
    assert [r['text'] for r in result]==['mot','mot']
    assert not audit['conflicts'] and not audit['failed_lines']
    for r in result:
        w=r['words'][0]
        assert w['ownership_status']=='observed'
        assert gray[w['y0']:w['y1']+1,w['x0']:w['x1']+1].min()==0
        assert 10<=w['x0']<=w['x1']<=60


def test_identical_duplicate_cannot_export_same_ink_twice():
    gray=np.full((70,80),255,np.uint8);gray[15:24,10:60]=0
    rows=[row('a',25,[5,5,70,35]),row('b',25,[5,5,70,35])]
    result,audit=refine(gray,rows)
    assert audit['failed_lines'] or audit['conflicts']
    assert sum(r['words'][0]['ownership_status']=='observed' for r in result)<=1


def test_alto_overlap_exception_is_explicit_and_pair_specific():
    rows=[dict(id='A',text='un',words=[dict(text='un',x0=10,y0=10,x1=30,y1=30)]),
          dict(id='B',text='deux',words=[dict(text='deux',x0=20,y0=20,x1=40,y1=40)])]
    xml=diagnostic_alto(rows,100,100,'source.png')
    with pytest.raises(ValueError,match='superposés'):alto.validate(xml)
    with pytest.raises(ValueError,match='superposés'):
        alto.validate(xml,permitted_word_overlaps=[['A_W01','C_W01']])
    assert alto.validate(xml,permitted_word_overlaps=[['A_W01','B_W01']])['valid']
