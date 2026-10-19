import numpy as np
from page_layout_auto import column_starts,horizontal_separators,separate_spanning_regions


def test_column_count_follows_observed_lines_without_manual_count():
    for count in (2,4,7):
        boxes=[[30+c*150,y,160+c*150,y+12] for c in range(count) for y in range(20,500,20)]
        assert len(column_starts(boxes,count*150+40,12))==count


def test_long_separator_survives_dense_character_edges():
    gray=np.full((500,800),255,np.uint8)
    for y in range(25,470,20):
        for x in range(20,780,9):gray[y:y+8,x:x+4]=0
    gray[298:301,20:780]=0
    lines=horizontal_separators(gray,[20,20,780,480],15)
    assert any(abs(y-300)<10 for y in lines)


def test_spanning_heading_is_not_transcribed_again_in_column_crops():
    regions=[dict(id='a',bbox=[0,0,100,300]),dict(id='b',bbox=[100,0,200,300])]
    result=separate_spanning_regions(regions,[[10,20,190,55]],20)
    spans=[r for r in result if r.get('kind')=='spanning_region']
    assert len(spans)==1
    _,top,_,bottom=spans[0]['bbox']
    for r in result:
        if r is spans[0]:continue
        assert r['bbox'][3]<=top or r['bbox'][1]>=bottom
