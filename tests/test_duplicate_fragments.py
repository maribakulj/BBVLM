import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from duplicate_fragments import detect,conserve_fragment_ink


def examples():
    image=Image.new('L',(200,150),255);draw=ImageDraw.Draw(image)
    for x in (15,35,55,95,115,135):draw.rectangle((x,24,x+7,55),fill=0)
    draw.rectangle((55,84,62,115),fill=0)
    parent=dict(id='P',text='abc def',bbox=[10,20,160,60],uncertain=False,
                chars=[[15,23,.9],[35,43,.9],[55,63,.9],[63,95,0],[95,103,.9],[115,123,.9],[135,143,.9]],
                words=[dict(text='abc',x0=15,y0=24,x1=62,y1=55),dict(text='def',x0=95,y0=24,x1=142,y1=55)])
    child=dict(id='C',text='c',bbox=[49,20,67,60],uncertain=False,chars=[[55,63,.9]],
               words=[dict(text='c',x0=55,y0=24,x1=62,y1=55)])
    return np.asarray(image),parent,child


def test_duplicate_fragment_needs_same_native_ink_and_preserves_every_original_record():
    gray,parent,child=examples();rows=[parent,child];result=detect(gray,rows)
    assert len(result['decisions'])==1
    d=result['decisions'][0]
    assert (d['child_id'],d['parent_id'],d['parent_text_offset'])==('C','P',[2,3])
    assert d['native_shared_fraction']==1 and d['max_ctc_center_distance']==0
    assert result['annotations']==rows and result['criteria_met'] is False


def test_repeated_printed_letter_on_another_baseline_or_incompatible_text_is_not_a_copy():
    gray,parent,child=examples();child['bbox']=[49,80,67,120]
    child['words'][0].update(y0=84,y1=115)
    assert not detect(gray,[parent,child])['decisions']


def test_global_observation_requires_conserving_native_fragment_ink_in_canonical_word():
    gray,parent,child=examples();parent['words'][0]['y0']=29  # truncated native glyph edge
    result=conserve_fragment_ink(detect(gray,[parent,child],mask_source='global_source'))
    assert result['decisions'][0]['native_shared_fraction']==1
    assert result['annotations'][0]['words'][0]['y0']==24
    assert parent['words'][0]['y0']==29  # original trial immutable
    assert result['ink_conservation_repairs'][0]['before'][1]==29
    gray,parent,child=examples();child['text']='x';child['words'][0]['text']='x'
    assert not detect(gray,[parent,child])['decisions']
