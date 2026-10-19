import sys,json
from pathlib import Path
from PIL import Image,ImageDraw
from lxml import etree
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import alto
from olr import validate
from lecture import ResponseError
from export_training import export
from segmentation import deduplicate,tile_starts


def envelope():
    return dict(job_id='job',provider='gemini',model='test',
                blocks=[dict(id='B_1',type='text',line_ids=['L1'],article_id='A_1',uncertain=False)],
                reading_order=['B_1'],articles=[dict(id='A_1',block_ids=['B_1'],uncertain=False)])


def test_olr_coordinates_are_computed_and_missing_ids_cannot_pass():
    ann=[dict(id='L1',bbox=[1,2,21,22])]
    result=validate(envelope(),ann,'job')
    assert result['blocks'][0]['bbox'] == [1,2,21,22]
    value=envelope();value['blocks'][0]['line_ids']=['unknown']
    with pytest.raises(ResponseError):validate(value,ann,'job')
    value=envelope();value['blocks'][0]['bbox']=[0,0,999,999]
    with pytest.raises(ResponseError):validate(value,ann,'job')


def test_alto_empty_and_tagged_outputs_pass_the_real_xsd():
    assert alto.validate(alto.build(100,100,'p.png',[],'test','test'))['valid']
    block=dict(id='B_1',type='heading',article_id='A_1',x0=1,y0=2,x1=20,y1=21,
               lines=[dict(id='L1',bbox=[1,2,20,21],words=[dict(text='Été',x0=1,y0=2,x1=20,y1=21)])])
    data=alto.build(100,100,'p.png',[block],'test','test')
    assert alto.validate(data)['valid']
    root=etree.fromstring(data)
    assert root.xpath('//*[local-name()="ElementRef"]/@REF') == ['B_1']
    assert root.xpath('//*[local-name()="TextBlock"]/@TAGREFS') == ['TYPE_heading ART_A_1']


def test_export_preserves_nfc_character_positions_and_word_offsets(tmp_path):
    image=tmp_path/'p.png';Image.new('RGB',(100,100),'white').save(image)
    ann=[dict(id='L1',bbox=[1,2,22,23],text='Été',uncertain=False,status='retenue',
              training_eligible=True,chars=[[2,3,.8],[8,9,.7],[16,17,.9]],
              words=[dict(text='Été',x0=2,y0=3,x1=20,y1=21)])]
    (tmp_path/'annotations.json').write_text(json.dumps(ann))
    (tmp_path/'provenance.json').write_text(json.dumps(dict(taille=[100,100],lecture='gemini',geometrie='ctc')))
    (tmp_path/'olr.json').write_text(json.dumps(validate(envelope(),ann,'job')))
    (tmp_path/'segmentation.json').write_text(json.dumps([dict(id='L1',baseline=[[1,20],[21,20]])]))
    result=export(image,tmp_path)
    assert result['coverage'] == 1 and result['page_validation']
    ir=json.loads((tmp_path/'axel-ir.json').read_text())
    assert ir['blocks'][0]['lines'][0]['text'] == 'Été'
    assert len(ir['blocks'][0]['lines'][0]['chars']) == 3
    assert all(isinstance(v,str) for v in ir['provenance'].values())
    assert json.loads(ir['provenance']['block_articles'])=={'B_1':'A_1'}
    row=json.loads((tmp_path/'training.jsonl').read_text())
    assert row['page_id']==ir['id'] and ir['id'].startswith('P_') and ir['id']!='P1'
    assert row['words'][0]['start'] == 0 and row['words'][0]['end'] == 3
    root=etree.parse(str(tmp_path/'training.alto.xml'))
    assert root.xpath('//*[local-name()="TextLine"]/@BASELINE') == ['1.000,20.000 21.000,20.000']
    assert root.xpath('//*[local-name()="TextLine"]/*[local-name()="Shape"]/*[local-name()="Polygon"]/@POINTS')


def test_tiles_cover_page_and_do_not_merge_neighbor_columns():
    assert tile_starts(5891,2400,1200) == [0,1200,2400,3491]
    candidates=[dict(bbox=[0,0,100,20],interior=True),
                dict(bbox=[50,0,100,20],interior=False),
                dict(bbox=[110,0,210,20],interior=True)]
    kept=deduplicate(candidates)
    assert [r['bbox'] for r in kept] == [[0,0,100,20],[110,0,210,20]]


def test_olr_splits_disjoint_columns_without_changing_articles_or_line_order():
    ann=[dict(id='L1',bbox=[10,10,50,20]),dict(id='L2',bbox=[10,30,50,40]),
         dict(id='L3',bbox=[70,10,110,20])]
    value=envelope();value['blocks'][0]['line_ids']=['L1','L2','L3']
    result=validate(value,ann,'job')
    assert [b['bbox'] for b in result['blocks']] == [[10,10,50,40],[70,10,110,20]]
    assert [lid for b in result['blocks'] for lid in b['line_ids']] == ['L1','L2','L3']
    assert result['articles'][0]['block_ids'] == result['reading_order']
    assert all(b['article_id']=='A_1' for b in result['blocks'])


def test_olr_does_not_fill_distant_gaps_or_bridge_columns_with_a_wide_title():
    ann=[dict(id='H',bbox=[0,0,220,20]),dict(id='L1',bbox=[0,25,100,45]),
         dict(id='L2',bbox=[0,50,100,70]),dict(id='L3',bbox=[120,25,220,45]),
         dict(id='L4',bbox=[120,50,220,70]),dict(id='L5',bbox=[0,300,100,320])]
    value=envelope();value['blocks'][0]['line_ids']=[a['id'] for a in ann]
    result=validate(value,ann,'job')
    assert [b['bbox'] for b in result['blocks']]==[[0,0,220,20],[0,25,100,70],[120,25,220,70],[0,300,100,320]]
    assert result['articles'][0]['block_ids']==result['reading_order']


def test_compact_olr_covers_a_dense_page_and_expands_source_ids_without_coordinates(tmp_path):
    from olr_groups import groups,expand,write_inputs
    ann=[dict(id=f'L{i:04d}',bbox=[10+(i%2)*120,(i//2)*12,110+(i%2)*120,(i//2)*12+10],
              text=f'production {i}',uncertain=False,status='placee',secret_reference='must not be sent') for i in range(1000)]
    geometry=groups(ann)
    assert len(geometry)<100
    assert sorted(i for g in geometry for i in g['line_ids'])==sorted(a['id'] for a in ann)
    image=tmp_path/'p.png';Image.new('RGB',(250,6100),'white').save(image)
    files,overview=write_inputs(image,ann,geometry,[],tmp_path)
    assert 'must not be sent' not in ''.join(Path(p).read_text() for p in files)
    assert Path(overview).exists()
    value=dict(job_id='job',provider='gemini',model='test',blocks=[dict(id='B_1',type='text',
                group_ids=[g['id'] for g in geometry],segments=[],article_id='A_1',uncertain=False)],
               reading_order=['B_1'],articles=[dict(id='A_1',block_ids=['B_1'],uncertain=False)])
    result=validate(expand(value,geometry),ann,'job')
    assert len([i for b in result['blocks'] for i in b['line_ids']])==1000
    value['blocks'][0]['group_ids'].append(geometry[0]['id'])
    with pytest.raises(ResponseError):validate(expand(value,geometry),ann,'job')
    value['blocks'][0]['group_ids']=['UNKNOWN']
    with pytest.raises(ResponseError):expand(value,geometry)


def test_compact_olr_can_split_groups_but_cannot_omit_invent_or_reverse_endpoints():
    from olr_groups import expand
    geometry=[dict(id='G_1',line_ids=['L1','L2','L3'])]
    ann=[dict(id=f'L{i}',bbox=[0,i*10,50,i*10+8]) for i in range(1,4)]
    value=envelope();value['blocks'][0].pop('line_ids');value['blocks'][0].update(group_ids=[],
                        segments=[dict(group_id='G_1',first='L1',last='L3')])
    assert validate(expand(value,geometry),ann,'job')['blocks'][0]['line_ids']==['L1','L2','L3']
    value['blocks'][0]['segments'][0]['last']='L2'
    with pytest.raises(ResponseError):validate(expand(value,geometry),ann,'job')
    value['blocks'][0]['segments'][0]['first']='L3'
    with pytest.raises(ResponseError):expand(value,geometry)
    value['blocks'][0]['segments'][0]['first']='invented'
    with pytest.raises(ResponseError):expand(value,geometry)


def test_geometry_groups_do_not_fragment_columns_when_font_heights_alternate():
    from olr_groups import groups
    ann=[dict(id=f'L{i}',bbox=[2000+(i%2)*700,(i//2)*40,
                             2600+(i%2)*700,(i//2)*40+(18 if i%3 else 30)]) for i in range(40)]
    value=groups(ann)
    assert len(value)==2
    assert sorted(g['line_ids'] for g in value)==sorted([[f'L{i}' for i in range(0,40,2)],
                                                       [f'L{i}' for i in range(1,40,2)]])


def test_olr_invalid_identified_reply_keeps_contract_error_and_native_model():
    from olr import response_in_terminal
    from lecture import MalformedResponse
    ann=[dict(id='L1',bbox=[0,0,50,10]),dict(id='L2',bbox=[0,12,50,22])]
    invalid=envelope();invalid['blocks'][0]['line_ids']=['L1']
    with pytest.raises(MalformedResponse,match='omet ou duplique') as caught:
        response_in_terminal(json.dumps(invalid),'job',lambda v:validate(v,ann,'job'))
    assert caught.value.value['job_id']=='job'
    valid=envelope();valid['model']='self claim';valid['blocks'][0]['line_ids']=['L1','L2']
    raw,result=response_in_terminal(json.dumps(invalid)+'\n'+json.dumps(valid)+'\nGemini 3.1 Pro · high',
                                   'job',lambda v:validate(v,ann,'job'))
    assert raw['model']=='self claim' and result['model_display_terminal']=='Gemini 3.1 Pro · high'


def test_olr_format_repair_requires_settled_identified_response_and_is_not_repeated(tmp_path,monkeypatch):
    from olr import repair_response
    from lecture import HerdrGeminiReader,MalformedResponse,ReaderUnavailable
    reader=HerdrGeminiReader('pane',tmp_path)
    reader.last_terminal='job\nidentified native JSON'
    (tmp_path/'prompt.txt').write_text('Only automatic image and IDs; no reference')
    (tmp_path/'state.json').write_text(json.dumps(dict(phase='submission_intent')))
    monkeypatch.setattr(reader,'_resume_after_native_auth_refresh',lambda *a,**k:None)
    monkeypatch.setattr(reader,'_resume_after_cancelled_shell',lambda *a,**k:None)
    calls=[];status='done'
    def call(*args):
        calls.append(args)
        return 0,dict(result=dict(agent=dict(agent='agy',agent_status=status))),''
    monkeypatch.setattr(reader,'_call',call)
    error=MalformedResponse('missing automatic ID',dict(job_id='job',provider='gemini',model='test',blocks=[]))
    assert repair_response(reader,tmp_path,'job',lambda:('raw','validated'),error)==('raw','validated')
    assert len([c for c in calls if c[0]=='prompt'])==1
    assert json.loads((tmp_path/'olr-format-recovery.json').read_text())['blind_timeout_retry'] is False
    with pytest.raises(ReaderUnavailable,match='déjà tentée'):
        repair_response(reader,tmp_path,'job',lambda:None,error)
    assert len([c for c in calls if c[0]=='prompt'])==1
    status='working'
    with pytest.raises(ReaderUnavailable,match='encore active'):
        repair_response(reader,tmp_path,'job',lambda:None,error)


def test_compact_olr_declares_order_articles_and_regions_without_large_redundant_arrays():
    from olr_groups import expand
    geometry=[dict(id='G_1',line_ids=['L1','L2'])]
    ann=[dict(id='L1',bbox=[0,0,50,10]),dict(id='L2',bbox=[0,12,50,22])]
    value=dict(job_id='job',provider='gemini',model='test',format='bb-olr-tuples-v1',order_is_blocks=True,
               blocks=[['B_T','text',['G_1'],[],[],'A_1',False],
                       ['B_S','separator',[],[],['S1'],None,False]],articles=[['A_1',False]],rejected_regions=[])
    result=validate(expand(value,geometry,True),ann,'job',[dict(id='S1',bbox=[0,30,100,32])])
    assert result['reading_order']==['B_T','B_S']
    assert result['articles'][0]['block_ids']==['B_T']
    assert result['blocks'][0]['line_ids']==['L1','L2']
    value['blocks'][0][3]=[['G_1','L1','L2']];value['blocks'][0][2]=[]
    assert validate(expand(value,geometry,True),ann,'job',[dict(id='S1',bbox=[0,30,100,32])])['complete']
    value['reading_order']=['B_S','B_T']
    with pytest.raises(ResponseError,match='ambigus'):expand(value,geometry,True)


def test_settled_native_prompt_return_can_recover_a_clipped_olr_header(tmp_path,monkeypatch):
    from olr import repair_response
    from lecture import HerdrGeminiReader,ReaderUnavailable
    reader=HerdrGeminiReader('pane',tmp_path);reader.last_terminal='last1000 terminal rows; request header clipped'
    (tmp_path/'prompt.txt').write_text('saved production-only request job')
    completion=dict(result=dict(agent=dict(agent='agy',agent_status='done')))
    (tmp_path/'state.json').write_text(json.dumps(dict(phase='submitted',code=0,result=completion)))
    monkeypatch.setattr(reader,'_resume_after_native_auth_refresh',lambda *a,**k:None)
    monkeypatch.setattr(reader,'_resume_after_cancelled_shell',lambda *a,**k:None)
    calls=[]
    def call(*args):calls.append(args);return 0,completion,''
    monkeypatch.setattr(reader,'_call',call)
    assert repair_response(reader,tmp_path,'job',lambda:'validated',ResponseError('clipped'),'compact output')=='validated'
    assert len([c for c in calls if c[0]=='prompt'])==1
    (tmp_path/'olr-format-recovery.json').unlink()
    (tmp_path/'state.json').write_text(json.dumps(dict(phase='submission_intent')))
    with pytest.raises(ReaderUnavailable,match='non établie'):
        repair_response(reader,tmp_path,'job',lambda:None,ResponseError('unknown timeout'))
    assert len([c for c in calls if c[0]=='prompt'])==1


def test_completed_compact_reply_can_receive_one_identified_contract_repair(tmp_path,monkeypatch):
    from olr import repair_response
    from lecture import HerdrGeminiReader,MalformedResponse,ReaderUnavailable
    reader=HerdrGeminiReader('pane',tmp_path);reader.last_terminal='job compact JSON completed'
    (tmp_path/'prompt.txt').write_text('production-only image and groups')
    (tmp_path/'olr-format-recovery.json').write_text('{}')
    completion=dict(result=dict(agent=dict(agent='agy',agent_status='done')))
    (tmp_path/'state.json').write_text(json.dumps(dict(phase='olr_format_requested',code=0,result=completion)))
    monkeypatch.setattr(reader,'_resume_after_native_auth_refresh',lambda *a,**k:None)
    monkeypatch.setattr(reader,'_resume_after_cancelled_shell',lambda *a,**k:None)
    calls=[]
    def call(*args):calls.append(args);return 0,completion,''
    monkeypatch.setattr(reader,'_call',call)
    bad=dict(job_id='job',format='bb-olr-tuples-v1',blocks=[['B_1'],['B_1']])
    error=MalformedResponse('duplicate',bad)
    assert repair_response(reader,tmp_path,'job',lambda:'validated',error)=='validated'
    assert len([c for c in calls if c[0]=='prompt'])==1
    assert 'B_1' in (tmp_path/'olr-contract-prompt.txt').read_text()
    assert json.loads((tmp_path/'olr-contract-invalid-response.json').read_text())==bad
    with pytest.raises(ReaderUnavailable,match='déjà tentée'):
        repair_response(reader,tmp_path,'job',lambda:None,error)
    assert len([c for c in calls if c[0]=='prompt'])==1


def test_blind_word_verification_never_sends_the_expected_transcription(tmp_path):
    from verify_words import WordReader
    from lecture import LineRequest
    image=Image.new('RGB',(200,50),'white')
    reader=WordReader('pane',tmp_path)
    manifest,prompt=reader._prepare(image,[LineRequest('W_L1_000',(10,5,100,45))],tmp_path/'job',1)
    source=(tmp_path/'job/request.json').read_text()
    assert 'expected' not in source and 'transcription' not in source
    assert 'AUCUN texte attendu' in prompt and 'Ne complète aucun mot tronqué' in prompt
    assert manifest['lines'][0]['bbox']==[10,5,100,45]


def test_word_verification_cannot_rescue_missing_or_unbounded_character_positions():
    from verify_words import geometry_support
    a=dict(text='é',words=[dict(text='é',x0=10,x1=30)],chars=[[11,29,.2]],
           alignment=dict(character_scope='word',word_geometry=dict(boundaries=[]),
                          word_alignments=[dict(alignment=dict(support_min=.2))]))
    assert geometry_support(a)[0]  # posterior publié, pas un seuil non calibré
    a['chars'][0][1]=40
    assert not geometry_support(a)[0]
    a['chars']=[]
    assert not geometry_support(a)[0]


def test_word_review_commit_recovers_the_gap_between_two_atomic_files(tmp_path):
    import hashlib
    from verify_words import restore_checked_annotations
    path=tmp_path/'annotations.json';before=b'[{"status":"refused"}]';path.write_bytes(before)
    after=[dict(status='verified')];content=json.dumps(after,ensure_ascii=False,indent=2).encode()
    record=dict(annotations=after,input_annotations_sha256=hashlib.sha256(before).hexdigest(),
                output_annotations_sha256=hashlib.sha256(content).hexdigest())
    restore_checked_annotations(path,record)
    assert path.read_bytes()==content
    restore_checked_annotations(path,record)  # déjà appliqué, aucune nouvelle lecture
    path.write_bytes(b'user change')
    with pytest.raises(ValueError,match='modifiées'):restore_checked_annotations(path,record)
    assert path.read_bytes()==b'user change'


def test_nontext_candidates_cannot_be_invented_omitted_or_duplicated(tmp_path):
    image=tmp_path/'p.png';Image.new('RGB',(100,100),'white').save(image)
    value=dict(job_id='job',provider='gemini',model='test',
               blocks=[dict(id='B_IMG',type='illustration',line_ids=[],region_ids=['R1'],article_id=None,uncertain=False),
                       dict(id='B_SEP',type='separator',line_ids=[],region_ids=['S1'],article_id=None,uncertain=False)],
               reading_order=['B_IMG','B_SEP'],articles=[],rejected_regions=[])
    regions=[dict(id='R1',bbox=[10,10,60,60]),dict(id='S1',bbox=[5,80,90,82])]
    result=validate(value,[],'job',regions)
    (tmp_path/'annotations.json').write_text('[]')
    (tmp_path/'provenance.json').write_text(json.dumps(dict(taille=[100,100],lecture='gemini',geometrie='pixels')))
    (tmp_path/'olr.json').write_text(json.dumps(result))
    report=export(image,tmp_path)
    assert report['nontext_blocks_exported']==2
    root=etree.parse(str(tmp_path/'training.alto.xml'))
    assert root.xpath('//*[local-name()="Illustration"]/@ID') == ['B_IMG']
    assert root.xpath('//*[local-name()="GraphicalElement"]/@ID') == ['B_SEP']
    root=etree.parse(str(tmp_path/'training.page.xml'))
    assert root.xpath('//*[local-name()="RegionRefIndexed"]/@regionRef') == ['B_IMG','B_SEP']
    value['blocks'][0]['region_ids']=['UNKNOWN']
    with pytest.raises(ResponseError):validate(value,[],'job',regions)
    value['blocks'][0]['region_ids']=['S1']
    with pytest.raises(ResponseError):validate(value,[],'job',regions)


def test_separator_geometry_comes_from_native_ink(tmp_path):
    from PIL import ImageDraw
    from bb_layout import separators
    image=tmp_path/'lines.png';im=Image.new('L',(1000,1000),255)
    ImageDraw.Draw(im).rectangle([100,400,899,402],fill=0);im.save(image)
    found=separators(image)
    assert [r['bbox'] for r in found]==[[100,400,900,403]]


def test_line_growth_requires_baseline_continuity_and_stops_at_large_blank():
    from line_repair import grow_components
    import numpy as np
    import cv2
    gray=np.full((100,600),255,np.uint8)
    for x in range(70,490,10):cv2.rectangle(gray,(x,42),(x+5,57),0,-1)
    cv2.rectangle(gray,(10,42),(20,57),0,-1)  # région indépendante après un grand blanc
    cv2.rectangle(gray,(510,35),(550,43),0,-1)  # fragment d’une autre ligne
    grown,proof=grow_components(gray,[200,35,350,65],[0,0,580,100])
    assert 65<=grown[0]<=72 and 485<=grown[2]<=495
    assert grown[1::2]==[35,65]
    assert proof['baseline_anchors']>=8


def test_line_repair_preserves_all_detected_ids_and_checks_image_provenance(tmp_path):
    import hashlib
    from line_repair import repair
    path=tmp_path/'image.png';Image.new('L',(200,100),255).save(path)
    rows=[dict(id='hard',bbox=[10,10,100,30]),dict(id='easy',bbox=[10,40,100,60])]
    layout=dict(image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),blocks=[])
    after,audit=repair(path,rows,layout)
    assert after==rows and audit['input_lines']==audit['output_lines']==2
    layout['image_sha256']='different image'
    with pytest.raises(ValueError,match='autre image'):repair(path,rows,layout)


def test_segmentation_recovers_completed_tiles_after_local_failure(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import segmentation
    image=tmp_path/'p.png';Image.new('L',(10,10),255).save(image)
    weights=tmp_path/'blla.mlmodel';weights.write_bytes(b'dummy')
    model=SimpleNamespace(input=(1,3,1800,0))
    monkeypatch.setattr(segmentation,'_model_path',lambda:weights)
    monkeypatch.setattr(segmentation,'_load_model',lambda path:model)
    calls=[];failed=False
    line=SimpleNamespace(boundary=[[1,1],[5,1],[5,4],[1,4]],baseline=[[1,3],[5,3]])
    def inference(crop,model):
        nonlocal failed
        calls.append(crop.size)
        if len(calls)==2 and not failed:
            failed=True;raise RuntimeError('interrupted second tile')
        return SimpleNamespace(lines=[line])
    monkeypatch.setitem(sys.modules,'kraken',SimpleNamespace(blla=SimpleNamespace(segment=inference)))
    cache=tmp_path/'tiles'
    with pytest.raises(RuntimeError,match='second tile'):
        segmentation.segment(image,'tiles',tile_width=6,tile_height=10,overlap_x=2,overlap_y=2,cache_directory=cache)
    assert len(list(cache.glob('*.json')))==2  # one complete tile + state
    result=segmentation.segment(image,'tiles',tile_width=6,tile_height=10,overlap_x=2,overlap_y=2,cache_directory=cache)
    assert len(calls)==3 and len(result)==2
    assert json.loads((cache/'state.json').read_text())['status']=='completed'


def test_segmentation_scale_change_cannot_reuse_incompatible_tile_cache(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import segmentation
    image=tmp_path/'p.png';Image.new('L',(100,50),255).save(image)
    weights=tmp_path/'model';weights.write_bytes(b'weights')
    monkeypatch.setattr(segmentation,'_model_path',lambda:weights)
    monkeypatch.setattr(segmentation,'_load_model',lambda path:SimpleNamespace(input=(1,3,1800,0)))
    calls=[]
    def inference(crop,model):
        calls.append(model.input[2]);right=model.input[2]//4
        return SimpleNamespace(lines=[SimpleNamespace(boundary=[[1,1],[right,1],[right,10],[1,10]],
                                                     baseline=[[1,8],[right,8]])])
    monkeypatch.setitem(sys.modules,'kraken',SimpleNamespace(blla=SimpleNamespace(segment=inference)))
    cache=tmp_path/'cache'
    first=segmentation.segment(image,cache_directory=cache,network_height=48)
    second=segmentation.segment(image,cache_directory=cache,network_height=96)
    replay=segmentation.segment(image,cache_directory=cache,network_height=48)
    assert calls==[48,96] and replay==first and first[0]['bbox']!=second[0]['bbox']


def test_short_text_band_uses_body_ink_scale_instead_of_discarding_large_glyphs(tmp_path):
    from segmentation import ink_network_height
    image=Image.new('L',(300,160),255);draw=ImageDraw.Draw(image)
    for y in range(5,150,30):
        for x in range(10,290,20):draw.rectangle((x,y,x+7,y+19),fill=0)
    p=tmp_path/'short.png';image.save(p)
    height,proof=ink_network_height(p)
    assert proof['glyph_height']==20 and height==160


def test_completed_automatic_segmentation_can_be_reused_but_reference_fields_are_rejected(tmp_path):
    import hashlib
    from segmentation import prime_from_suite
    image=tmp_path/'p.png';Image.new('L',(100,30),255).save(image)
    source=tmp_path/'source';source.mkdir();out=tmp_path/'out'
    config=dict(image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),strategy='auto',version='blla-rectangles-v1')
    (source/'segmentation-config.json').write_text(json.dumps(config))
    rows=[dict(id='L1',bbox=[0,0,90,25],source='kraken-blla/full',polygon=[],baseline=[])]
    (source/'segmentation-ink.json').write_text(json.dumps(rows))
    assert prime_from_suite(image,source,out,'auto','ink')
    assert json.loads((out/'segmentation.json').read_text())==rows
    assert json.loads((out/'segmentation-config.json').read_text())['line_refinement']=='ink'
    rows[0]['reference']='forbidden';(source/'segmentation-ink.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError,match='interdites'):prime_from_suite(image,source,tmp_path/'bad','auto','ink')
    assert not (tmp_path/'bad/segmentation.json').exists()
