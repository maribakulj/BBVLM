import json
from pathlib import Path
import sys
from types import SimpleNamespace
from PIL import Image
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import native_quota
from lecture import HerdrGeminiReader,LineRequest,Reading,ReaderQuotaExceeded,ReaderUnavailable,prepare_job
from produire_suite import run_page
from reparer_quota_cache import repair


def terminal(job,error='native-error',duration='1h6m30s'):
    return f'requête {job}\nIndividual quota reached. Resets in {duration}.\nError ID: {error}\n'


@pytest.fixture(autouse=True)
def isolate_service(tmp_path,monkeypatch):
    monkeypatch.setattr(native_quota,'SERVICE_DIRECTORY',tmp_path/'service')


def test_observation_requires_correlated_quota_and_keeps_original_deadline(tmp_path):
    job='a'*32
    assert native_quota.quota_observation('timeout '+job,job,100) is None
    assert native_quota.quota_observation('requête '+job+'\n'+terminal('b'*32),job,100) is None
    first=native_quota.observe('pane',tmp_path/'job',terminal(job),job,100)
    assert first['retry_at']==100+3990+30
    replay=native_quota.observe('pane',tmp_path/'job',terminal(job),job,500)
    assert replay['retry_at']==first['retry_at']
    assert native_quota.pending('pane',100)==first
    assert native_quota.pending('pane',first['retry_at']) is None


def test_quota_stops_new_visual_job_without_submission_or_preparation(tmp_path,monkeypatch):
    native_quota.observe('pane',tmp_path/'previous',terminal('a'*32),'a'*32)
    reader=HerdrGeminiReader('pane',tmp_path/'new')
    monkeypatch.setattr(reader,'_call',lambda *args:pytest.fail('No native call while quota is pending'))
    with pytest.raises(ReaderQuotaExceeded):
        reader.read_lines(Image.new('RGB',(20,10)),[LineRequest('L1',(0,0,20,10))])
    assert not reader.directory.exists()


def test_cached_response_remains_available_during_quota(tmp_path,monkeypatch):
    native_quota.observe('pane',tmp_path/'previous',terminal('a'*32),'a'*32)
    job=tmp_path/'cached';manifest,_=prepare_job(Image.new('RGB',(20,10)),[LineRequest('L1',(0,0,20,10))],job)
    (job/'response.json').write_text(json.dumps(dict(job_id=manifest['job_id'],provider='gemini',model='test',lines=[dict(id='L1',text='mot',uncertain=False)])))
    reader=HerdrGeminiReader('pane',tmp_path)
    monkeypatch.setattr(reader,'_call',lambda *args:pytest.fail('Cache must not need native service'))
    assert reader.recover_job(job)[0].text=='mot'


def test_quota_resume_requires_deadline_and_native_done_and_preserves_uuid(tmp_path,monkeypatch):
    requests=[LineRequest('L1',(0,0,20,10))]
    job=tmp_path/'job';manifest,_=prepare_job(Image.new('RGB',(20,10)),requests,job)
    reader=HerdrGeminiReader('pane',tmp_path)
    native_quota.observe('pane',job,terminal(manifest['job_id'],duration='1s'),manifest['job_id'],0)
    reader.last_terminal='historique absent'
    calls=[];status='working'
    def call(*args):
        calls.append(args)
        return 0,dict(result=dict(agent=dict(agent='agy',agent_status=status))),''
    monkeypatch.setattr(reader,'_call',call)
    with pytest.raises(ReaderUnavailable,match='fin native'):
        reader._resume_after_native_quota(job,requests,manifest['job_id'])
    assert not any(c[0]=='prompt' for c in calls)
    status='done';calls.clear()
    answer=(dict(job_id=manifest['job_id']),[Reading('L1','mot',False,'gemini','test')])
    monkeypatch.setattr(reader,'_read',lambda *args:answer)
    assert reader._resume_after_native_quota(job,requests,manifest['job_id'])==answer
    prompt=next(c[2] for c in calls if c[0]=='prompt')
    assert manifest['job_id'] in prompt and str(job/'lecture.png') in prompt
    calls.clear()
    with pytest.raises(ReaderUnavailable,match='déjà soumise'):
        reader._resume_after_native_quota(job,requests,manifest['job_id'])
    assert not any(c[0]=='prompt' for c in calls)


def test_suite_waits_only_for_explicit_quota_and_replays_after_deadline(tmp_path,monkeypatch):
    import produire_suite
    now=[100.];calls=[];sleeps=[]
    monkeypatch.setattr(produire_suite.time,'time',lambda:now[0])
    def sleep(seconds):sleeps.append(seconds);now[0]+=seconds
    monkeypatch.setattr(produire_suite.time,'sleep',sleep)
    def run(command,**kwargs):
        calls.append(command)
        state={'stage':'waiting_for_native_quota','retry_at':165,'evidence':{'error_id':'native'}} if len(calls)==1 else {'stage':'done'}
        (tmp_path/'pipeline-state.json').write_text(json.dumps(state))
        return SimpleNamespace(returncode=1 if len(calls)==1 else 0)
    monkeypatch.setattr(produire_suite.subprocess,'run',run)
    assert run_page(['production'],tmp_path,True)==0
    assert calls==[['production'],['production']] and sleeps==[30,30,5]
    assert json.loads((tmp_path/'native-quota-wait.json').read_text())['blind_timeout_retry'] is False


def test_old_quota_quarantines_only_affected_geometry_and_keeps_all_evidence(tmp_path):
    requests=[LineRequest('L1',(0,0,20,10))]
    job=tmp_path/'lecture-jobs/job';manifest,_=prepare_job(Image.new('RGB',(20,10)),requests,job)
    (job/'terminal.txt').write_text(terminal(manifest['job_id']))
    rejection=b'{"reason":"old_format_failure"}'
    (job/'rejected-response.json').write_bytes(rejection)
    cache=tmp_path/'geometry-cache';cache.mkdir()
    for lid in ('L1','L2'):
        (cache/(lid+'.json')).write_text(json.dumps(dict(annotation=dict(id=lid,status='lecture_non_resolue'))))
    untouched=(cache/'L2.json').read_bytes()
    initial=b'initial validated readings';(tmp_path/'readings.json').write_bytes(initial)
    report=repair(tmp_path,'pane')
    assert report['affected_line_ids']==['L1'] and len(report['quarantined_placements'])==1
    assert not (cache/'L1.json').exists() and (tmp_path/'quota-quarantine/geometry-cache/L1.json').exists()
    assert (cache/'L2.json').read_bytes()==untouched and (tmp_path/'readings.json').read_bytes()==initial
    assert (job/'rejected-response.json').read_bytes()==rejection
    assert repair(tmp_path,'pane')==report
