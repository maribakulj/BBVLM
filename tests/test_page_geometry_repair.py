import json
from pathlib import Path
from PIL import Image

import page_geometry_repair as module
from page_anchors import save_json
from page_text_view import compact_line_text_view


def test_ambiguous_middle_word_preserves_surrounding_words_and_full_source(tmp_path,monkeypatch):
    image=tmp_path/'image.png';Image.new('L',(100,60),255).save(image)
    source='Un\nmot\nfinal';view=compact_line_text_view(source)
    assignment=dict(line_id='L1',start=0,end=len(source),text=source,bbox=[0,0,100,50])
    row=dict(id='L1',text=view['text'],source_text=source,source_spans=view['source_spans'],
             bbox=[0,0,100,50],assignment_resolved=True,cout=0,status='collision',
             chars=[[i,i+1,1] for i in range(len(view['text']))],
             alignment={'character_position_sources':['ctc']*len(view['text'])},
             words=[dict(text=w,x0=i*30,y0=10,x1=i*30+20,y1=30,
                         ownership_status='no_owned_ink' if i==1 else 'observed')
                    for i,w in enumerate(['Un','mot','final'])])
    alignment=dict(plain_text=source,assignments=[assignment],blocks=[dict(line_ids=['L1'])],
                   text_coverage={'nonspace_characters':10})
    save_json(tmp_path/'annotations.json',[row]);save_json(tmp_path/'page-alignment.json',alignment)
    save_json(tmp_path/'geometry-report.json',dict(ink_suspicion_threshold=1,statuses={'collision':1}))
    monkeypatch.setattr(module,'refine',lambda *args,**kwargs:([row],dict(conflicts=[],safe_overlaps=[])))
    result,rows=module.repair(image,tmp_path)
    assert [r['text'] for r in rows]==['Un','final']
    assert [r['id'] for r in rows]==['L1_G1','L1_G2']
    assert ''.join(s['text'] for s in result['segments'])==source
    assert any(s['status']=='unmatched_text' and 'mot' in s['text'] for s in result['segments'])
    for r in rows:
        assert len(r['text'])==len(r['chars'])==len(r['alignment']['character_position_sources'])
        assert source[r['start']:r['end']]==r['source_text']
    audit=json.loads((tmp_path/'ownership-audit.json').read_text())
    assert audit['retained_words']==2 and audit['excluded_words'][0]['text']=='mot'
