import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from char_geometry import repair_terminal


def source(ambiguous=False):
    image=Image.new('L',(220,80),255);draw=ImageDraw.Draw(image)
    draw.rectangle((150,20,169,59),fill=0)
    draw.rectangle((180,50,185,65),fill=0)
    draw.rectangle((191,50,196,65) if ambiguous else (195,25,196,26),fill=0)
    annotation=dict(id='L1',text='x,',bbox=[10,10,200,70],chars=[[150,160,.99],[200,200,.98]],
                    words=[dict(text='x,',x0=10,y0=10,x1=199,y1=69)])
    return np.asarray(image),annotation


def test_zero_width_punctuation_uses_native_ink_and_does_not_select_rightmost_noise():
    gray,a=source();result=repair_terminal(gray,[a]);row=result['annotations'][0]
    assert row['chars'][1]==[180.,186.,0.]
    assert row['text']==a['text'] and row['words']==a['words']
    assert a['chars'][1]==[200,200,.98]  # immutable source trial
    assert result['decisions'][0]['previous']==[200,200,.98]
    assert row['alignment']['character_position_sources'][1]=='native_terminal_component; ctc_support_unknown'
    assert not result['unresolved'] and result['criteria_met'] is False


def test_competing_terminal_components_remain_unresolved_instead_of_fabricating_a_position():
    gray,a=source(True);result=repair_terminal(gray,[a])
    assert not result['decisions'][0]['accepted'] and len(result['unresolved'])==1
    assert result['annotations'][0]['chars']==a['chars']


def test_upper_neighbor_period_is_never_credited_as_terminal_punctuation():
    gray,a=source();gray=gray.copy();gray[:]=255
    gray[20:60,150:170]=0;gray[21:25,181:185]=0  # point de la ligne précédente
    a['text']='x.';a['words'][0]['text']='x.'
    result=repair_terminal(gray,[a])
    assert not result['decisions'][0]['accepted'] and len(result['unresolved'])==1
    assert result['annotations'][0]['chars']==a['chars']
