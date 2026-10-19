import json
from pathlib import Path
import sqlite3
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lecture import LineRequest, ResponseError
from page_markdown import validate_page_response
from native_page_history import identified_response, input_view_audit, resolve_conversation

CID='12345678-1234-1234-1234-123456789abc'
JOB='a'*32
REQUESTS=[LineRequest('PAGE',(0,0,20,30))]
PROMPT=f'Image entière /source.png, requête {JOB}'


def native_db(tmp_path,rows):
    path=tmp_path/(CID+'.db')
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',rows)


def response(text):
    return json.dumps(dict(kind='page_markdown',job_id=JOB,provider='gemini',model='test',
        lines=[dict(id='PAGE',text_parts=text,uncertain=False)]),ensure_ascii=False).encode()


def test_native_long_response_recovers_original_without_terminal_limit_or_format_changes(tmp_path):
    parts=['texte\n']*1500
    blob=b'\x01opaque\x00'+response(parts)+b'\x01'+response(parts)
    native_db(tmp_path,[(0,14,3,PROMPT.encode()),(1,15,3,blob),
                        (2,14,3,('reformat '+JOB).encode()),(3,15,3,response(['texte modifié']))])
    value,readings,proof=identified_response(CID,PROMPT,REQUESTS,JOB,validate_page_response,tmp_path)
    assert readings[0].text==''.join(parts) and proof['response_step_index']==1
    assert proof['equivalent_objects']==2 and proof['source']=='agy_native_sqlite_read_only'
    assert value['job_id']==JOB


@pytest.mark.parametrize('rows',[
    [(0,14,3,b'other prompt'),(1,15,3,response(['wrong association']))],
    [(0,14,3,PROMPT.encode()),(1,14,3,b'new unrelated task'),(2,15,3,response(['stale']))],
    [(0,14,3,PROMPT.encode()),(1,15,1,response(['still running']))],
    [(0,14,3,PROMPT.encode()),(1,15,3,response(['one'])+response(['two']))],
])
def test_wrong_conversation_task_running_or_ambiguous_history_is_never_accepted(tmp_path,rows):
    native_db(tmp_path,rows)
    with pytest.raises(ResponseError):
        identified_response(CID,PROMPT,REQUESTS,JOB,validate_page_response,tmp_path)


def test_view_audit_does_not_credit_similar_path_or_other_job(tmp_path):
    native_db(tmp_path,[(0,14,3,PROMPT.encode()),
        (1,132,3,b'/authorized/view-001.png'),(2,132,3,b'/other/view-002.png'),
        (3,14,3,b'other job'),(4,132,3,b'/authorized/view-002.png')])
    result=input_view_audit(CID,PROMPT,JOB,['/authorized/view-001.png','/authorized/view-002.png'],tmp_path)
    assert result['coverage']==.5 and result['observed']==1
    assert result['missing_paths']==['/authorized/view-002.png']


def test_async_clear_hint_is_repaired_only_by_unique_exact_prompt(tmp_path):
    import shutil
    native_db(tmp_path,[(0,14,3,PROMPT.encode())])
    old='87654321-4321-4321-4321-cba987654321'
    cid,proof=resolve_conversation([old,CID],PROMPT,JOB,tmp_path)
    assert cid==CID and proof['basis']=='exact_original_prompt_and_UUID'
    shutil.copy2(tmp_path/(CID+'.db'),tmp_path/(old+'.db'))
    with pytest.raises(ResponseError,match='ambigu'):
        resolve_conversation([old,CID],PROMPT,JOB,tmp_path)
