import hashlib
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lecture import ResponseError
from native_page_history import attest_native_resume, identified_markdown

CID='12345678-1234-1234-1234-123456789abc'
JOB='a'*32
PROMPT='source page, request '+JOB


def vi(value):
    result=bytearray()
    while value>127:result.append((value&127)|128);value>>=7
    result.append(value)
    return bytes(result)


def field(number,value):
    return vi(number*8+2)+vi(len(value))+value


def human(text):
    data=text.encode()
    return b'\x08\x0e\x20\x03'+field(19,field(2,data)+field(3,field(1,data)))


def error(index=2):
    identifier=(CID+'-'+str(index)).encode()
    details=field(2,b'agent executor error: request failed: write: broken pipe')+field(6,identifier)
    return b'\x08\x11\x20\x03'+field(24,field(3,details))


def final(text):
    data=text.encode()
    return b'\x08\x0f\x20\x03'+field(20,field(1,data)+field(8,data))


def make_db(path,followup='reprends',unrelated=False):
    rows=[(0,14,3,PROMPT.encode()),(1,132,3,b'/source.png'),(2,17,3,error()),
          (3,14,3,human(followup)),(4,15,3,final('# Toute la page\n'))]
    if unrelated:rows.insert(2,(1.5,14,3,b'other task'))
    with sqlite3.connect(path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',rows)


def test_explicit_same_task_resume_is_attested_and_final_recovered_without_submission(tmp_path):
    make_db(tmp_path)
    with pytest.raises(ResponseError):identified_markdown(CID,PROMPT,JOB,tmp_path)
    evidence=attest_native_resume(CID,PROMPT,JOB,3,tmp_path)
    text,proof=identified_markdown(CID,PROMPT,JOB,tmp_path,authorized_continuations=[evidence])
    assert text=='# Toute la page\n'
    assert proof['request_step_index']==0 and proof['response_step_index']==4
    assert proof['authorized_continuations']==[evidence]
    assert evidence['blind_timeout_retry'] is False
    assert evidence['resume_text']=='reprends'


@pytest.mark.parametrize('followup,unrelated',[('transcris une autre page',False),('reprends',True)])
def test_unrelated_instruction_or_task_is_never_bridged(tmp_path,followup,unrelated):
    make_db(tmp_path,followup,unrelated)
    with pytest.raises(ResponseError):attest_native_resume(CID,PROMPT,JOB,3,tmp_path)


def test_resume_payload_or_error_changes_invalidate_attestation(tmp_path):
    make_db(tmp_path)
    evidence=attest_native_resume(CID,PROMPT,JOB,3,tmp_path)
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('UPDATE steps SET step_payload=? WHERE idx=2',(error()+field(99,b'changed'),))
    with pytest.raises(ResponseError,match='modifiée'):
        identified_markdown(CID,PROMPT,JOB,tmp_path,authorized_continuations=[evidence])


def test_attestation_does_not_authorize_a_later_unrelated_turn(tmp_path):
    make_db(tmp_path)
    evidence=attest_native_resume(CID,PROMPT,JOB,3,tmp_path)
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('DELETE FROM steps WHERE idx=4')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',[(5,14,3,b'unrelated'),(6,15,3,final('wrong'))])
    with pytest.raises(ResponseError,match='Aucun Markdown'):
        identified_markdown(CID,PROMPT,JOB,tmp_path,authorized_continuations=[evidence])


def test_resume_requires_an_explicit_native_error_not_a_timeout(tmp_path):
    make_db(tmp_path)
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('UPDATE steps SET step_type=15 WHERE idx=2')
    with pytest.raises(ResponseError,match='erreur native précédente'):
        attest_native_resume(CID,PROMPT,JOB,3,tmp_path)


def test_native_error_after_saved_text_marks_partial_generation(tmp_path):
    make_db(tmp_path)
    evidence=attest_native_resume(CID,PROMPT,JOB,3,tmp_path)
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('INSERT INTO steps VALUES(5,17,3,?)',(error(5),))
        db.execute('INSERT INTO steps VALUES(6,15,3,?)',(final('Résumé, pas OCR'),))
    text,proof=identified_markdown(CID,PROMPT,JOB,tmp_path,authorized_continuations=[evidence])
    assert text=='# Toute la page\n'
    assert proof['response_completeness']=='interrupted_native_generation'
    assert proof['trailing_native_errors'][0]['step_index']==5


def test_continuation_can_reuse_only_an_identified_source_read_in_same_conversation(tmp_path):
    prior_job='b'*32
    prior_prompt='original source '+prior_job
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',[
            (0,14,3,prior_prompt.encode()),(1,132,3,b'/source.png'),(2,15,3,final('Part one')),
            (3,14,3,PROMPT.encode()),(4,15,3,final('Part two'))])
    prior=dict(job_id=prior_job,prompt=prior_prompt,image='/source.png')
    text,proof=identified_markdown(CID,PROMPT,JOB,tmp_path,prior_image_request=prior)
    assert text=='Part two' and proof['prior_source_image_read']['read_step_index']==1
    with pytest.raises(ResponseError,match='Image source absente'):
        identified_markdown(CID,PROMPT,JOB,tmp_path,prior_image_request={**prior,'image':'/other.png'})
