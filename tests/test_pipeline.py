import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'src'/'boxers'))
from lecture import LineRequest, Reading, ResponseError, ReaderUnavailable, HerdrGeminiReader, validate_response, prepare_job, response_in_text
from forcectc import frame_x, encode_text, graphe_ctc, viterbi, alignment_mask
from produire import produire
import correct


def envelope(rows):
    return {'provider': 'gemini', 'model': 'test', 'job_id': 'new', 'lines': rows}


def row(lid, text='mot', uncertain=False):
    return {'id': lid, 'text': text, 'uncertain': uncertain}


def test_responses_follow_ids_even_when_returned_in_reverse_order():
    requests = [LineRequest('A', (0,0,10,10)), LineRequest('B', (20,0,30,10))]
    readings = validate_response(envelope([row('B','deux'), row('A','un')]), requests)
    assert [(r.id,r.text) for r in readings] == [('A','un'), ('B','deux')]


@pytest.mark.parametrize('rows', [[row('A')], [row('A'),row('A')],
                                  [row('A'),row('C')], [row('A','mot\nautre'),row('B')],
                                  [row('A',uncertain='false'),row('B')]])
def test_malformed_responses_cannot_shift_the_association(rows):
    with pytest.raises(ResponseError):
        validate_response(envelope(rows), [LineRequest('A',(0,0,10,10)), LineRequest('B',(10,0,20,10))])


def test_terminal_recovery_ignores_an_old_complete_answer():
    request = [LineRequest('A',(0,0,10,10))]
    old = {**envelope([row('A','ancien')]), 'job_id':'old'}
    new = envelope([row('A','nouveau')])
    _, result = response_in_text(json.dumps(old)+'\n'+json.dumps(new), request, 'new')
    assert result[0].text == 'nouveau'


def test_cancelled_native_shell_reuses_only_the_identified_source_request(tmp_path,monkeypatch):
    requests=[LineRequest('A',(0,0,20,10))]
    job=tmp_path/'job';manifest,prompt=prepare_job(Image.new('RGB',(20,10),'white'),requests,job,input_style='sheets')
    (job/'prompt.txt').write_text(prompt)
    reader=HerdrGeminiReader('pane',tmp_path)
    reader.last_terminal=f"{manifest['job_id']}\nBash(tail internal log)\nRequesting permission for:\nRun this command?"
    calls=[];gets=0
    def call(*args):
        nonlocal gets
        calls.append(args)
        if args[0]=='get':
            gets+=1
            return 0,dict(result=dict(agent=dict(agent='agy',agent_status='blocked' if gets==1 else 'done'))),''
        return 0,dict(result=dict(agent=dict(agent='agy',agent_status='done'))),''
    monkeypatch.setattr(reader,'_call',call)
    answer=({**envelope([row('A')]),'job_id':manifest['job_id']},[Reading('A','mot',False,'gemini','test')])
    monkeypatch.setattr(reader,'_read',lambda *args:answer)
    assert reader._resume_after_cancelled_shell(job,requests,manifest['job_id'])==answer
    assert [c[:3] for c in calls if c[0]=='send-keys']==[('send-keys','pane','esc')]
    controlled=next(c[2] for c in calls if c[0]=='prompt')
    assert manifest['job_id'] in controlled and manifest['detail_sheets'][0]['path'] in controlled
    assert 'annulée' in controlled and 'sans outil Bash' in controlled
    assert json.loads((job/'cancelled-native-tool.json').read_text())['blind_timeout_retry'] is False
    with pytest.raises(ResponseError,match='Deux commandes'):
        reader._resume_after_cancelled_shell(job,requests,manifest['job_id'])
    assert (job/'rejected-response.json').exists()  # découpe possible, parent jamais renvoyé


def test_unknown_blocked_ui_or_timeout_never_triggers_native_shell_replay(tmp_path,monkeypatch):
    reader=HerdrGeminiReader('pane',tmp_path)
    monkeypatch.setattr(reader,'_call',lambda *args:pytest.fail('Unknown state must not control Gemini'))
    for terminal in ('job\nRequesting permission for:\nRun this command?',
                     'other\nBash(tail)\nRequesting permission for:\nRun this command?',
                     'job\nBash(tail)\nRequesting permission for:\nRun this command?\n'+'x'*3000):
        reader.last_terminal=terminal
        assert reader._resume_after_cancelled_shell(tmp_path,[],'job') is None


def test_reading_provenance_keeps_claim_and_native_model_distinct(tmp_path):
    reader=HerdrGeminiReader('pane',tmp_path)
    reader.last_terminal='Gemini 3.1 Pro · high\n'
    request=[LineRequest('A',(0,0,10,10))]
    value=envelope([row('A')]);value['model']='older self claim'
    readings=validate_response(value,request,'new');job=tmp_path/'job';job.mkdir()
    readings=reader._store_response(job,request,1,value,readings)
    assert readings[0].model=='older self claim'
    assert readings[0].model_display_terminal=='Gemini 3.1 Pro · high'
    assert readings[0].job_id=='new'
    cached=validate_response(json.loads((job/'response.json').read_text()),request,'new')
    assert cached==readings


def test_herdr_read_accepts_plain_terminal_output(monkeypatch,tmp_path):
    import subprocess
    value = envelope([row('A','exact')])
    def run(args,**kwargs):
        assert args[:3] == ['herdr','agent','read']
        return SimpleNamespace(returncode=0,stdout='Interface Gemini\n'+json.dumps(value),stderr='')
    monkeypatch.setattr(subprocess,'run',run)
    reader = HerdrGeminiReader('pane',tmp_path)
    _, readings = reader._read([LineRequest('A',(0,0,10,10))],'new')
    assert readings[0].text == 'exact'


def test_segmented_terminal_recovery_preserves_exact_text_and_job_id(tmp_path,monkeypatch):
    requests = [LineRequest('A',(0,0,10,10))]
    manifest,_ = prepare_job(Image.new('RGB',(10,10)),requests,tmp_path/'job')
    reader = HerdrGeminiReader('pane',tmp_path)
    state = {'result': {'agent': {'agent_status':'done'}}}
    terminal = 'JSON tronqué'
    def call(*args):
        nonlocal terminal
        if args[0] == 'get': return 0,state,''
        if args[0] == 'read': return 0,{'result':{'text':terminal}},''
        assert args[0] == 'prompt' and 'Ne relis pas' in args[2]
        value = {**envelope([{'id':'A','text_parts':['Siège',' :'],'uncertain':False}]), 'job_id':manifest['job_id']}
        terminal = json.dumps(value,indent=2)
        return 0,state,''
    monkeypatch.setattr(reader,'_call',call)
    readings = reader.recover_job(tmp_path/'job')
    assert readings[0].text == 'Siège :'


def test_timeout_does_not_resubmit_an_unfinished_reading(tmp_path,monkeypatch):
    requests = [LineRequest('A',(0,0,10,10))]
    prepare_job(Image.new('RGB',(10,10)),requests,tmp_path/'job')
    reader = HerdrGeminiReader('pane',tmp_path)
    calls = []
    def call(*args):
        calls.append(args[0])
        return 0,{'result':{'text':'incomplet'}},''
    monkeypatch.setattr(reader,'_call',call)
    with pytest.raises(ReaderUnavailable):
        reader.recover_job(tmp_path/'job',submission=(1,None,'timeout'))
    assert calls == ['read']


def test_rejected_parent_response_survives_terminal_history_and_reuses_split_cache(tmp_path,monkeypatch):
    requests=[LineRequest('A',(0,0,10,10)),LineRequest('B',(10,0,20,10))]
    manifest,_=prepare_job(Image.new('RGB',(20,10)),requests,tmp_path/'job')
    value={**envelope([row('A','un')]),'job_id':manifest['job_id']}
    reader=HerdrGeminiReader('pane',tmp_path);calls=[]
    def call(*args):
        calls.append(args[0])
        if args[0]=='read':return 0,{'result':{'text':json.dumps(value)}},''
        return 0,{'result':{'agent':{'agent_status':'done'}}},''
    monkeypatch.setattr(reader,'_call',call)
    with pytest.raises(ResponseError,match='manquantes'):reader.recover_job(tmp_path/'job')
    assert calls.count('prompt')==1
    assert json.loads((tmp_path/'job/state.json').read_text())['phase']=='rejected_response'
    calls.clear()
    with pytest.raises(ResponseError,match='rejetée sauvegardée'):reader.recover_job(tmp_path/'job')
    assert calls==[]


def test_subrequests_use_their_own_pixels_and_preserve_resolution(tmp_path):
    image = Image.new('RGB',(2000,20),'red')
    image.paste(Image.new('RGB',(1000,20),'blue'),(1000,0))
    prepare_job(image,[LineRequest('A',(0,0,1000,20))],tmp_path/'first')
    prepare_job(image,[LineRequest('B',(1000,0,2000,20))],tmp_path/'second')
    a = Image.open(tmp_path/'first'/'crop-0001.png')
    b = Image.open(tmp_path/'second'/'crop-0001.png')
    assert a.size == b.size == (1000,20)
    assert a.getpixel((500,10)) == (255,0,0)
    assert b.getpixel((500,10)) == (0,0,255)


def test_ctc_coordinates_exclude_network_padding():
    # 16 frames of margin per side and 100 image pixels, 1 frame/input pixel.
    assert frame_x(16,132,132,200,100) == 200.5
    assert frame_x(115,132,132,200,100) == 299.5


def test_word_boundaries_keep_a_wide_glyph_whole_with_offcenter_ctc_peaks():
    from forcectc import word_geometry
    gray=np.full((50,240),255,np.uint8)
    gray[10:40,10:60]=0
    gray[5:45,80:140]=0  # large esperluette, pic à son bord gauche
    gray[10:40,160:225]=0
    boxes,meta=word_geometry(gray,(0,0,240,50),'a & b',{0:55,1:68,2:85,3:140,4:175})
    assert boxes==[(10,10,59,39),(80,5,139,44),(160,10,224,39)]
    assert all(b['ink_free'] for b in meta['boundaries'])
    old,_=word_geometry(gray,(0,0,240,50),'a & b',{0:55,1:68,2:85,3:140,4:175},'midpoint')
    assert old[1][2]<139  # le milieu brut coupe le glyphe


def test_word_boundary_without_observed_separation_is_an_explicit_failure():
    from forcectc import word_geometry
    gray=np.full((30,60),255,np.uint8);gray[5:25,5:55]=0
    with pytest.raises(ValueError,match='sans séparation'):
        word_geometry(gray,(0,0,60,30),'a b',{0:15,1:30,2:45})


def test_clean_ink_keeps_faint_letters_and_ignores_unaligned_leading_fragments():
    from forcectc import word_geometry
    gray=np.full((50,180),255,np.uint8)
    gray[5:40,0:12]=0  # fragment étranger avant le premier pic imposé
    gray[10:40,40:60]=205
    gray[10:40,80:100]=0
    boxes,_=word_geometry(gray,(0,0,180,50),'ab',{0:50,1:90},'ink_clean_baseline')
    assert boxes==[(40,10,99,39)]


def test_faint_glyphs_and_punctuation_survive_without_neighbor_fragments():
    gray = np.full((40,120),255,np.uint8)
    gray[8:31,10:16] = 0
    gray[12:29,30:36] = 205  # caractère pâle, perdu par un seuil global
    gray[20:24,60:83] = 0   # tiret isolé
    gray[0:3,90:97] = 0    # fragment de la ligne voisine
    mask,_,_ = alignment_mask(gray,(0,0,120,40))
    assert mask[8:31,10:16].any()
    assert mask[12:29,30:36].any()
    assert mask[20:24,60:83].any()
    assert not mask[0:3,90:97].any()


def test_encoding_retains_accents_and_refuses_unsupported_characters():
    codec = SimpleNamespace(c2l={'e':[1], '\u0301':[2], ' ':[3], 'a':[4]})
    codes, positions = encode_text(codec, 'é a')
    assert codes == [1,2,3,4]
    assert positions == [(0,),(0,),(1,),(2,)]
    with pytest.raises(ValueError,match='hors alphabet'):
        encode_text(codec,'€')


def test_repeated_ctc_characters_require_a_blank_between_them():
    logp = np.log(np.array([[.1,.9],[.9,.1],[.1,.9]]))
    graph = graphe_ctc([1,1])
    assert viterbi(logp[:2],graph) is None
    positions = viterbi(logp,graph)
    assert positions[1] == 0 and positions[3] == 2


def test_invalid_batch_is_split_without_reusing_original_pixels(tmp_path, monkeypatch):
    image = Image.new('RGB',(40,10),'white')
    path = tmp_path/'page.png'; image.save(path)
    requests = [LineRequest('A',(0,0,10,10)),LineRequest('B',(20,0,30,10))]
    class Reader:
        nom = 'test'
        def __init__(self): self.calls = []
        def read_lines(self, image, requests, scale=1):
            self.calls.append([(r.id,r.bbox) for r in requests])
            if len(requests)>1: raise ResponseError('ligne manquante')
            return [Reading(requests[0].id,requests[0].id,False,'test','test')]
    class Boxer:
        name = 'test'
        def boxes(self,gray,line):
            x0,y0,x1,y1=line.line_box
            return [(x0,y0,x1-1,y1-1)]
    monkeypatch.setattr(correct,'cout_ligne',lambda *args:(0,None,None))
    reader = Reader()
    result = produire(str(path),tmp_path/'out',reader,Boxer(),requests=requests,verbose=False)
    assert reader.calls == [[('A',(0,0,10,10)),('B',(20,0,30,10))],
                            [('A',(0,0,10,10))],[('B',(20,0,30,10))]]
    assert result['lignes_retenues'] == 2
    text = etree.parse(str(tmp_path/'out'/'page.alto.xml'))
    assert text.xpath('//*[local-name()="String"]/@CONTENT') == ['A','B']


def test_uncertain_lines_remain_recorded_and_empty_alto_is_valid(tmp_path):
    image = Image.new('RGB',(30,10),'white')
    path = tmp_path/'page.png'; image.save(path)
    class Reader:
        nom = 'test'
        def read_lines(self,image,requests,scale=1):
            return [Reading(r.id,'ambigu',True,'test','test') for r in requests]
    class Boxer:
        name = 'test'
        def boxes(self,*args): raise AssertionError('Une lecture incertaine ne doit pas être placée')
    result = produire(str(path),tmp_path/'out',Reader(),Boxer(),
                      requests=[LineRequest('A',(0,0,20,10))],verbose=False)
    assert result['lignes_retenues'] == 0 and not result['complet']
    annotations = json.loads((tmp_path/'out'/'annotations.json').read_text())
    assert annotations[0]['text'] == 'ambigu' and not annotations[0]['training_eligible']
    etree.parse(str(tmp_path/'out'/'page.alto.xml'))


def test_overlapping_words_are_excluded_even_with_a_good_ink_cost(tmp_path,monkeypatch):
    image = Image.new('RGB',(30,10),'white')
    path = tmp_path/'page.png'; image.save(path)
    class Reader:
        nom = 'test'
        def read_lines(self,image,requests,scale=1):
            return [Reading(r.id,'un deux',False,'test','test') for r in requests]
    class Boxer:
        name = 'test'
        def boxes(self,*args): return [(0,0,15,9),(10,0,29,9)]
    monkeypatch.setattr(correct,'cout_ligne',lambda *args:(0,None,None))
    result = produire(str(path),tmp_path/'out',Reader(),Boxer(),
                      requests=[LineRequest('A',(0,0,30,10))],verbose=False)
    assert result['lignes_retenues'] == 0
    assert result['ecartees'][0]['motif'] == 'boîtes hors page ou mots superposés'


def test_duplicate_detected_lines_cannot_export_the_same_ink_twice(tmp_path,monkeypatch):
    image=Image.new('RGB',(30,20),'white');path=tmp_path/'page.png';image.save(path)
    class Reader:
        nom='test'
        def read_lines(self,image,requests,scale=1):
            return [Reading(r.id,'mot',False,'test','test') for r in requests]
    class Boxer:
        name='test'
        def boxes(self,*args):return [(2,2,20,9)]
    monkeypatch.setattr(correct,'cout_ligne',lambda *args:(0,None,None))
    result=produire(str(path),tmp_path/'out',Reader(),Boxer(),verbose=False,
                    requests=[LineRequest('A',(0,0,30,12)),LineRequest('B',(0,1,30,13))])
    assert result['lignes_retenues'] == 0
    ann=json.loads((tmp_path/'out'/'annotations.json').read_text())
    assert {a['status'] for a in ann} == {'superposition_inter_lignes'}


def test_geometry_checkpoint_recovers_only_finished_lines_and_rechecks_global_collisions(tmp_path,monkeypatch):
    image=tmp_path/'image.png';Image.new('RGB',(50,30),'white').save(image)
    requests=[LineRequest('A',(0,0,25,20)),LineRequest('B',(25,0,50,20))]
    class Reader:
        nom='test'
        def read_lines(self,image,requests,scale=1):return [Reading(r.id,'mot',False,'test','test') for r in requests]
    class Boxer:
        name='test';cache_signature=dict(test_model='stable')
        def __init__(self):self.calls=[];self.interrupt=True
        def boxes(self,gray,line):
            self.calls.append(line.line_box)
            if len(self.calls)==2 and self.interrupt:raise KeyboardInterrupt('incident injected')
            return [(line.line_box[0],1,line.line_box[2]-1,10)]
    boxer=Boxer();monkeypatch.setattr(correct,'cout_ligne',lambda *args:(0,None,None))
    output=tmp_path/'out'
    with pytest.raises(KeyboardInterrupt):produire(str(image),output,Reader(),boxer,requests=requests,verbose=False)
    completed=[p for p in (output/'geometry-cache').glob('*.json') if p.name!='state.json']
    assert len(completed)==1 and json.loads(completed[0].read_text())['annotation']['id']=='A'
    boxer.interrupt=False
    result=produire(str(image),output,Reader(),boxer,requests=requests,verbose=False)
    assert boxer.calls==[requests[0].bbox,requests[1].bbox,requests[1].bbox]
    assert result['geometry_cache']['hits']==1 and result['lignes_retenues']==2
    # La couverture/validité globale n’est pas dans le cache local : les deux
    # placements peuvent devenir un doublon dans un autre ensemble détecté.
    colliding=produire(str(image),output,Reader(),boxer,
                       requests=[requests[0],LineRequest('B',(10,0,50,20))],verbose=False)
    assert colliding['geometry_cache']['hits']==1 and colliding['lignes_retenues']==0
    annotations=json.loads((output/'annotations.json').read_text())
    assert {a['status'] for a in annotations}=={'superposition_inter_lignes'}
    assert not any(a['training_eligible'] for a in annotations)


def test_ctc_alphabet_routing_preserves_long_s_without_a_transcription_alias(tmp_path,monkeypatch):
    from forcectc import ForceCTC
    primary=SimpleNamespace(codec=SimpleNamespace(c2l={'s':[1]}))
    secondary=SimpleNamespace(codec=SimpleNamespace(c2l={'ſ':[2],'s':[1]}))
    boxer=ForceCTC('primary',fallback_model_path='secondary')
    monkeypatch.setattr(boxer,'_get_model',lambda:primary)
    boxer._fallback_model=secondary
    model,codes,positions,path=boxer._encode_with_model('ſs')
    assert model is secondary and codes == [2,1] and positions == [(0,),(1,)]
    assert path == 'secondary'


def test_zoom_details_cover_the_entire_real_crop_without_reducing_source(tmp_path):
    image=Image.new('RGB',(1700,20),'red');image.paste('blue',(1500,0,1700,20))
    manifest,_=prepare_job(image,[LineRequest('A',(0,0,1700,20))],tmp_path/'job',scale=2)
    pieces=manifest['lines'][0]['detail_crops']
    assert pieces[0]['x_start'] == 0 and pieces[-1]['x_end'] == 3400
    assert all(b['x_start'] <= a['x_end'] for a,b in zip(pieces,pieces[1:]))
    for p in pieces:
        assert Image.open(p['path']).width <= 1024
    assert Image.open(pieces[-1]['path']).getpixel((900,10)) == (0,0,255)
