import sys
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from evaluation import convention, score, match_boxes, segmentation,exported_annotations,olr_detection
from banc_couple import provider, lire_churro
from lecture import HerdrGeminiReader, LineRequest, prepare_job


def test_convention_never_hides_punctuation_errors_or_historical_spelling():
    assert convention("l’été\u00a0cou¬") == "l'été cou-"
    assert convention('ſœur ;') == 'ſœur ;'
    assert convention('a¬b') == 'a¬b'
    assert convention('Marie. juge') != convention('Marie, juge')


def test_alto_physical_units_require_documented_dpi_and_convert_lines_and_words(tmp_path):
    from evaluation import load_reference
    p=tmp_path/'ref.xml';p.write_text('''<alto><Description><MeasurementUnit>mm10</MeasurementUnit></Description>
      <Layout><Page><TextLine ID="L" HPOS="254" VPOS="127" WIDTH="254" HEIGHT="25.4">
      <String CONTENT="mot" HPOS="254" VPOS="127" WIDTH="254" HEIGHT="25.4"/>
      </TextLine></Page></Layout></alto>''')
    with pytest.raises(ValueError,match='DPI'):load_reference(p)
    rows=load_reference(p,dpi=300)
    assert rows[0]['bbox']==pytest.approx([300,150,600,180])
    assert rows[0]['words'][0]['bbox']==pytest.approx([300,150,600,180])
    assert rows[0]['reference_coordinates']['pixels_per_unit']==300/254
    assert rows[0]['text']=='mot'


def test_historical_alto_diagnostic_crops_use_pixels_after_physical_unit_conversion(tmp_path):
    from corpora import load_alto
    p=tmp_path/'ref.xml';p.write_text('''<alto xmlns="urn:alto"><Description><MeasurementUnit>mm10</MeasurementUnit></Description>
      <Layout><Page><TextLine HPOS="0" VPOS="127" WIDTH="254" HEIGHT="25.4">
      <String CONTENT="un" HPOS="0" VPOS="127" WIDTH="100" HEIGHT="25.4"/>
      <String CONTENT="mot" HPOS="120" VPOS="127" WIDTH="134" HEIGHT="25.4"/>
      </TextLine></Page></Layout></alto>''')
    with pytest.raises(ValueError,match='DPI'):load_alto(str(p),'unused','BNL','test')
    page=load_alto(str(p),'unused','BNL','test',dpi=300)
    assert page.lines[0].line_box==(0,150,300,180)
    assert page.lines[0].word_boxes[1][0]==141


def test_olr_classification_is_measured_after_untyped_geometry_matching():
    refs=[dict(id='R1',bbox=[0,0,20,10],type='titre'),dict(id='R2',bbox=[0,20,20,30],type='texte')]
    pred=[dict(id='P1',bbox=[0,0,20,10],type='texte'),dict(id='P2',bbox=[0,20,20,30],type='titre')]
    result=olr_detection(refs,pred)
    assert result['blocks']['detection']['f1']==1
    assert result['blocks']['classification']['accuracy']==0
    pred[0]['type']='titre';pred[0]['uncertain']=True;pred[1]['type']='texte'
    result=olr_detection(refs,pred)
    assert result['blocks']['classification']['accuracy']==.5
    assert result['blocks']['classification']['unresolved_matched']==1


def test_many_correct_separators_cannot_hide_a_missing_text_block():
    refs=[dict(id='text',bbox=[0,0,100,10],type='texte')]
    separators=[dict(id=f'S{i}',bbox=[0,20+i*3,100,21+i*3],type='separator') for i in range(50)]
    result=olr_detection(refs+separators,separators)
    assert result['blocks']['detection']['recall']==0 and result['blocks']['detection']['f1']==0
    assert result['separators']['detection']['f1']==1


def test_missing_article_assignments_cannot_receive_a_perfect_pairwise_score():
    from evaluation import article_pairwise
    reference=dict(R1='A',R2='A',R3='A')
    missing=article_pairwise(reference,{})
    assert missing['f1']==0 and missing['gt']==3 and missing['assignment_coverage']==0
    partial=article_pairwise(reference,dict(R1='B',R2='B'))
    assert partial['tp']==1 and partial['gt']==3 and partial['f1']==.5
    extra=article_pairwise(reference,dict(R1='B',R2='B',R3='B',P1='B',P2='B'))
    assert extra['tp']==3 and extra['pred']==10 and extra['f1']<.5
    assert article_pairwise({},dict(P1='B'))['f1'] is None


def test_unmatched_and_refused_lines_count_as_errors():
    refs=[dict(id='R1',bbox=[0,0,20,10],text='un',words=[]),
          dict(id='R2',bbox=[0,20,20,30],text='deux',words=[])]
    pred=[dict(id='P1',bbox=[0,0,20,10],text='un',training_eligible=False,status='uncertain'),
          dict(id='P2',bbox=[0,40,20,50],text='extra')]
    s=score(refs,pred)['text']['strict_NFC']
    assert s['errors'] == 11 and s['characters'] == 6 and s['coverage'] == 0


def test_final_metrics_include_olr_refusals_and_actual_export_order(tmp_path):
    refs=[dict(id='R1',bbox=[0,0,20,10],text='un',words=[]),
          dict(id='R2',bbox=[0,20,20,30],text='deux',words=[]),
          dict(id='R3',bbox=[0,40,20,50],text='trois',words=[])]
    ann=[dict(id=f'L{i+1}',bbox=r['bbox'],text=r['text'],training_eligible=True,status='retenue')
         for i,r in enumerate(refs)]
    (tmp_path/'training.jsonl').write_text(json.dumps({'line_id':'L3'})+'\n'+json.dumps({'line_id':'L1'})+'\n')
    (tmp_path/'olr.json').write_text(json.dumps(dict(blocks=[dict(id='B',line_ids=['L3','L1','L2'])],reading_order=['B'])))
    pred=exported_annotations(ann,tmp_path);s=score(refs,pred)
    assert s['text']['strict_NFC']['errors']==4
    assert s['refusals']=={'exclue_par_olr':1}
    assert s['order']['inversions']==1 and s['order']['matched_lines']==2
    assert s['ordered_page_text']['strict_NFC']['errors']>4


def test_native_detail_crops_cover_wide_lines_without_downscaling(tmp_path):
    image=Image.new('RGB',(3000,50),'white')
    manifest,_=prepare_job(image,[LineRequest('A',(0,0,3000,50))],tmp_path/'job',input_style='lines')
    details=manifest['lines'][0]['detail_crops']
    assert details[0]['x_start']==0 and details[-1]['x_end']==3000
    assert all(Image.open(d['path']).height==50 for d in details)
    assert all(b['x_start']<a['x_end'] for a,b in zip(details,details[1:]))


def test_glyph_review_uses_production_peaks_and_never_other_annotation_fields(tmp_path):
    from review import targets,Reviewer
    ann=[dict(id='L1',text='é,x',bbox=[10,10,90,40],
              chars=[[15,20,.01],[30,35,.9],[50,55,.8]],reference='FORBIDDEN',
              word_boxes_reference=[[1,2,3,4]])]
    selected=targets(ann,100,50)
    assert len(selected)==1 and selected[0]['index']==0
    assert selected[0]['bbox']==[0,10,38,40]
    reader=Reviewer('pane',tmp_path,selected)
    requests=[LineRequest(t['id'],tuple(t['bbox'])) for t in selected]
    _,prompt=reader._prepare(Image.new('RGB',(100,50)),requests,tmp_path/'job',1)
    payload=(tmp_path/'job/production-targets.json').read_text()
    assert 'FORBIDDEN' not in payload and 'word_boxes_reference' not in payload
    assert 'masked_production_context' in payload and 'pas une référence' in prompt
    assert 'current_symbol' not in payload and 'é' not in payload


def test_spacing_keeps_text_when_positions_or_anchors_are_unusable():
    from spacing import propose
    gray=np.full((30,100),255,np.uint8)
    ann=dict(id='L',bbox=[0,0,100,30],text='un,mot',chars=[])
    value=propose(gray,ann)
    assert value['text']=='un,mot' and not value['edits']


def test_raw_typography_is_preserved_and_scored_without_relaxing_convention():
    from lecture import validate_response,ResponseError
    request=[LineRequest('L',(0,0,50,20))]
    payload=dict(provider='gemini',model='test',lines=[dict(id='L',text='cou-',uncertain=False,
                  linebreak=dict(raw='=',role='hyphenation'))])
    reading=validate_response(payload,request)[0]
    assert reading.text=='cou-' and reading.linebreak['raw']=='='
    refs=[dict(id='R',bbox=[0,0,50,20],text='cou¬',words=[])]
    scores=score(refs,[dict(id='L',bbox=[0,0,50,20],text='cou-',raw_text='cou=')])['text']
    assert scores['strict_NFC']['errors']==1
    assert scores['raw_source_strict_NFC']['errors']==1
    assert scores['convention_v1']['errors']==0
    payload['lines'][0]['text']='cou='
    with pytest.raises(ResponseError):validate_response(payload,request)


def test_detail_sheets_preserve_pixels_and_cover_every_native_line(tmp_path):
    image=Image.new('RGB',(3000,200),'red');image.paste('blue',(1500,0,3000,200))
    manifest,_=prepare_job(image,[LineRequest('A',(0,0,3000,80)),LineRequest('B',(100,100,2700,180))],
                           tmp_path/'job',input_style='sheets')
    sheets=manifest['detail_sheets']
    assert all(max(s['size'])<=1024 for s in sheets)
    for lid,width,y in [('A',3000,0),('B',2600,104)]:
        spans=[r for s in sheets for r in s['rows'] if r['id']==lid]
        assert spans[0]['x_start']==0 and spans[-1]['x_end']==width
        assert all(b['x_start']<a['x_end'] for a,b in zip(spans,spans[1:]))
    first=Image.open(sheets[0]['path'])
    assert first.getpixel((sheets[0]['gutter']+100,20))==image.getpixel((100,20))


def test_overlapping_words_no_longer_win_by_midpoint():
    words=[dict(text='un',bbox=[0,0,20,10]),dict(text='deux',bbox=[30,0,60,10])]
    refs=[dict(id='R',bbox=[0,0,60,10],text='un deux',words=words)]
    pred=[dict(id='P',bbox=[0,0,60,10],text='un deux',words=[
        dict(text='un',bbox=[0,0,45,10]),dict(text='deux',bbox=[5,0,60,10])])]
    s=score(refs,pred)['geometry']
    assert s['overlapping_prediction_lines'] == ['P']
    assert s['boundaries']['maximum'] > .5


def test_line_matching_is_one_to_one_even_for_duplicate_detections():
    refs=[[0,0,20,10],[0,20,20,30]]
    pred=[[0,0,20,10],[0,0,20,10],[0,20,20,30]]
    assert len(match_boxes(refs,pred)) == 2


def test_opus_label_cannot_execute_churro():
    with pytest.raises(ValueError,match='non implémenté'):
        provider('opus')


def test_churro_diagnostic_reads_each_real_crop(tmp_path,monkeypatch):
    image=Image.new('RGB',(40,20),'red');image.paste('blue',(20,0,40,20))
    path=tmp_path/'page.png';image.save(path)
    seen=[]
    def robust(be,callback,d,n,essais):
        seen.append(callback(d,n).getpixel((1,1)))
        assert n == 1
        return ['mot'],0
    monkeypatch.setitem(sys.modules,'vlm',SimpleNamespace(OllamaVLM=lambda name:object(),block_robuste=robust))
    page=SimpleNamespace(name='page',image_path=str(path),lines=[
        SimpleNamespace(line_box=(0,0,20,20),text='secret1'),
        SimpleNamespace(line_box=(20,0,40,20),text='secret2')])
    assert lire_churro([page],2)['page']['hyp'] == ['mot','mot']
    assert seen == [(255,0,0),(0,0,255)]


def test_reader_resume_uses_disk_cache_without_a_second_prompt(tmp_path,monkeypatch):
    reader=HerdrGeminiReader('pane',tmp_path)
    calls=[]
    value={}
    def call(*args):
        calls.append(args[0])
        state={'result':{'agent':{'agent':'agy','agent_status':'done'}}}
        if args[0] == 'prompt':
            manifest=json.loads(next(tmp_path.glob('*/request.json')).read_text())
            value.update(job_id=manifest['job_id'],provider='gemini',model='test',
                         lines=[dict(id='A',text='é',uncertain=False)])
        if args[0] == 'read':
            return 0,{'result':{'text':json.dumps(value)}},''
        return 0,state,''
    monkeypatch.setattr(reader,'_call',call)
    im=Image.new('RGB',(10,10));requests=[LineRequest('A',(0,0,10,10))]
    assert reader.read_lines(im,requests)[0].text == 'é'
    assert reader.read_lines(im,requests)[0].text == 'é'
    assert calls.count('prompt') == 1


def test_interrupted_submission_intent_cannot_resubmit(tmp_path,monkeypatch):
    reader=HerdrGeminiReader('pane',tmp_path)
    manifest,_=prepare_job(Image.new('RGB',(10,10)),[LineRequest('A',(0,0,10,10))],tmp_path/'job')
    reader._save_state(tmp_path/'job','submission_intent')
    def call(*args):
        assert args[0] != 'prompt'
        return 0,{'result':{'agent':{'agent_status':'done'}}},''
    monkeypatch.setattr(reader,'_call',call)
    from lecture import ReaderUnavailable
    with pytest.raises(ReaderUnavailable,match='sans resoumission'):
        reader.recover_job(tmp_path/'job')


def test_historical_judge_refuses_reference_text_as_alignment_input():
    from judge import score
    with pytest.raises(ValueError,match='texte de référence'):
        score(SimpleNamespace(name='test'),[])


@pytest.mark.parametrize('refresh_after_error',[True,False])
def test_auth_repair_requires_observed_native_refresh_after_failure(tmp_path,monkeypatch,refresh_after_error):
    from lecture import ReaderUnavailable
    requests=[LineRequest('A',(0,0,10,10))]
    directory=tmp_path/'job';manifest,_=prepare_job(Image.new('RGB',(10,10)),requests,directory)
    reader=HerdrGeminiReader('pane',tmp_path)
    reader._save_state(directory,'format_requested')
    logs=tmp_path/'.gemini/antigravity-cli/log';logs.mkdir(parents=True)
    failure='agent executor error: UNAUTHENTICATED (code 401)\n'
    refresh='browser: token refreshed, new expiry=mock timestamp\n'
    (logs/'cli-test.log').write_text(failure+refresh if refresh_after_error else refresh+failure)
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:tmp_path))
    called=[];completed=False
    def read(req,job_id):
        reader.last_terminal=f'> job {job_id}\nUNAUTHENTICATED (code 401)'
        if not completed:
            from lecture import ResponseError
            raise ResponseError('no response')
        value=dict(job_id=job_id,provider='gemini',model='test',lines=[dict(id='A',text='exact',uncertain=False)])
        from lecture import validate_response
        return value,validate_response(value,req,job_id)
    def call(*args):
        nonlocal completed
        called.append(args[0])
        if args[0]=='prompt':
            assert manifest['job_id'] in args[2] and 'Continue la même' in args[2]
            completed=True
        return 0,{'result':{'agent':{'agent_status':'done'}}},''
    monkeypatch.setattr(reader,'_read',read);monkeypatch.setattr(reader,'_call',call)
    if refresh_after_error:
        assert reader.recover_job(directory)[0].text == 'exact'
        assert called.count('prompt') == 1
        assert reader.recover_job(directory)[0].text == 'exact'
        assert called.count('prompt') == 1
    else:
        with pytest.raises(ReaderUnavailable):reader.recover_job(directory)
        assert 'prompt' not in called


def test_already_resumed_quota_hands_owned_401_to_auth_guard_without_reprompt(tmp_path,monkeypatch):
    from lecture import ReaderUnavailable
    from native_quota import save
    reader=HerdrGeminiReader('pane',tmp_path)
    job_id='a'*32
    evidence=dict(job_id=job_id,error_id='quota-error',retry_at=0)
    save(tmp_path/'quota-interruption.json',evidence)
    save(tmp_path/'quota-resume-attempts.json',[dict(error_id='quota-error')])
    monkeypatch.setattr(reader,'_quota_guard',lambda:None)
    called=[]
    def call(*args):
        called.append(args[0])
        return 0,dict(result=dict(agent=dict(agent='agy',agent_status='done'))),''
    monkeypatch.setattr(reader,'_call',call)
    reader.last_terminal=job_id+'\nUNAUTHENTICATED (code 401)'
    assert reader._resume_after_native_quota(tmp_path,[],job_id) is None
    assert called==['get']
    reader.last_terminal=job_id+'\n'+'b'*32+'\nUNAUTHENTICATED (code 401)'
    assert reader._native_auth_failure(job_id) is False
    with pytest.raises(ReaderUnavailable,match='déjà soumise'):
        reader._resume_after_native_quota(tmp_path,[],job_id)
    assert 'prompt' not in called
