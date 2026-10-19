from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from terminal_geometry import repair


def annotation(text='x,'):
    return dict(id='L1',text=text,bbox=[5,10,71,55],reading_bbox=[5,10,100,65],
                chars=[[50,69,.99],[71,71,.2]],words=[dict(text=text,x0=10,y0=20,x1=70,y1=54)])


def test_detached_comma_extends_to_real_ink_and_keeps_original_boxes():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0;gray[51:62,75:79]=0
    a=annotation();result=repair(gray,[a]);out=result['annotations'][0]
    assert out['words'][0]['x1']==78 and out['words'][0]['y1']==61
    assert out['chars'][1]==[75.,79.,0.] and out['bbox']==[5,10,79,62]
    assert a['words'][0]['x1']==70 and out['text']==a['text']
    decision=next(d for d in result['decisions'] if d['reason']=='isolated_native_terminal_ink')
    assert decision['previous_word_bbox']==[10,20,71,55] and decision['previous']==[71,71,.2]


def test_terminal_hyphen_does_not_take_vertical_column_rule():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0
    gray[36:39,75:86]=0;gray[8:70,91:94]=0
    a=annotation('x-');a['linebreak']=dict(raw='-',role='hyphenation')
    out=repair(gray,[a])
    assert out['annotations'][0]['chars'][1]==[75.,86.,0.] and not out['unresolved']


def test_two_stroke_hyphen_marker_keeps_both_native_components():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0
    gray[33:36,75:86]=0;gray[41:44,75:86]=0
    a=annotation('x-');a['linebreak']=dict(raw='=',role='hyphenation')
    out=repair(gray,[a]);decision=next(d for d in out['decisions'] if d['accepted'])
    assert decision['native_bbox']==[75,33,86,44] and len(decision['native_components'])==2
    assert out['annotations'][0]['text']=='x-'


def test_parenthesis_or_competing_dots_remain_unresolved():
    for ambiguous in (False,True):
        gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0
        if ambiguous:
            gray[51:56,75:79]=0;gray[51:56,82:86]=0
        else:gray[20:59,75:79]=0
        a=annotation();out=repair(gray,[a])
        assert len(out['unresolved'])==1 and out['annotations'][0]['words']==a['words']


def test_explicit_bold_stroke_variant_preserves_square_components_as_unresolved():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0;gray[35:42,75:86]=0
    a=annotation('x-');a['linebreak']=dict(raw='-',role='hyphenation')
    assert len(repair(gray,[a])['unresolved'])==1
    assert not repair(gray,[a],hyphen_min_aspect=1.4)['unresolved']
    gray[35:46,75:86]=0
    assert len(repair(gray,[a],hyphen_min_aspect=1.4)['unresolved'])==1


def test_extension_updates_observed_space_without_overlapping_next_word():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0
    gray[51:62,75:79]=0;gray[20:55,110:125]=0
    a=annotation();a['text']='x, y';a['words'][0]['text']='x,'
    a['words'].append(dict(text='y',x0=110,y0=20,x1=124,y1=54))
    a['chars'].extend([[71,110,0],[110,125,.99]])
    out=repair(gray,[a])['annotations'][0]
    assert out['chars'][2]==[79.,110.,0.] and out['words'][0]['x1']<out['words'][1]['x0']
    assert out['character_position_repairs'][-1]['previous_gaps']==[dict(index=2,position=[71,110,0])]


def test_neighbor_upper_dot_does_not_override_actual_lower_terminal_outside_box():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0
    gray[22:26,75:80]=0;gray[51:55,96:100]=0
    a=annotation('x.');a['words'][0]['x1']=90;a['bbox'][2]=91;a['chars'][1]=[91,91,.2]
    out=repair(gray,[a])['annotations'][0]
    assert out['chars'][1]==[96.,100.,0.] and out['words'][0]['x1']==99


def test_dot_crossing_word_edge_is_observed_as_one_whole_native_component():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0;gray[51:56,88:96]=0
    a=annotation('x.');a['words'][0]['x1']=90;a['bbox'][2]=91;a['chars'][1]=[91,91,.2]
    out=repair(gray,[a])['annotations'][0]
    assert out['chars'][1]==[88.,96.,0.] and out['words'][0]['x1']==95


def test_mark_connected_to_previous_letter_is_not_fabricated_by_clipping_that_letter():
    gray=np.full((80,160),255,np.uint8);gray[20:55,50:70]=0;gray[51:56,66:75]=0
    a=annotation('x.');a['chars'][0][1]=70
    out=repair(gray,[a])
    assert len(out['unresolved'])==1 and out['annotations'][0]['chars']==a['chars']


def test_single_pipe_keeps_its_id_and_text_with_explicit_unresolved_decision():
    gray=np.full((80,160),255,np.uint8);gray[8:70,75:79]=0
    a=dict(id='L1',text='|',bbox=[75,8,79,70],chars=[[79,79,.001]],
           words=[dict(text='|',x0=75,y0=8,x1=78,y1=69)])
    out=repair(gray,[a])
    assert out['annotations'][0]==a and len(out['unresolved'])==1
    assert out['decisions'][0]['reason']=='unsupported_terminal_or_word_correspondence'
