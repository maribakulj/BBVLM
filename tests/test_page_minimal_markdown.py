from pathlib import Path
import sqlite3
import sys

from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lecture import LineRequest,ResponseError
from native_page_history import identified_markdown,resolve_conversation
from page_minimal_markdown import MinimalMarkdownReader,TASK
from test_native_resume_history import field,vi,final

CID='12345678-1234-1234-1234-123456789abc'
JOB='a'*32
PROMPT=TASK+'\n/source.png'


def human(prompt=PROMPT,created=200):
    data=prompt.encode()
    stamp=field(1,vi(8)+vi(created))
    return b'\x08\x0e\x20\x03'+field(5,stamp)+field(19,field(2,data)+field(3,field(1,data)))


def database(path,human_index=0,repeat=False):
    rows=[(human_index,14,3,human()),(human_index+1,132,3,b'/source.png'),(human_index+2,15,3,final('# OCR\n'))]
    if repeat:rows.append((human_index+3,14,3,human()))
    with sqlite3.connect(path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',rows)


def test_exact_fresh_minimal_request_is_bound_without_transmitting_UUID(tmp_path):
    database(tmp_path)
    text,proof=identified_markdown(CID,PROMPT,JOB,tmp_path,out_of_band=True,native_not_before=190)
    assert text=='# OCR\n' and JOB not in PROMPT
    assert proof['job_id']==JOB and proof['request_binding']=='exact_fresh_human_prompt_out_of_band_UUID'
    cid,resolution=resolve_conversation([CID],PROMPT,JOB,tmp_path,out_of_band=True,native_not_before=190)
    assert cid==CID and 'out_of_band' in resolution['basis']


@pytest.mark.parametrize('index,repeat,epoch',[(4,False,190),(0,True,190),(0,False,210)])
def test_stale_repeated_or_nonfresh_minimal_request_is_not_recovered(tmp_path,index,repeat,epoch):
    database(tmp_path,index,repeat)
    with pytest.raises(ResponseError):identified_markdown(CID,PROMPT,JOB,tmp_path,out_of_band=True,native_not_before=epoch)


def test_prepare_has_only_user_sentence_and_image_path_no_protocol_in_prompt(tmp_path,monkeypatch):
    source=tmp_path/'source.png';image=Image.new('RGB',(20,30));image.save(source)
    reader=MinimalMarkdownReader('pane',tmp_path/'jobs');reader.source_path=source;reader.native_cwd='/cwd'
    monkeypatch.setattr('page_minimal_markdown.conversation_hint',lambda cwd:CID)
    calls=[]
    reader._call=lambda *args:(calls.append(args) or (0,{},''))
    manifest,prompt=reader._prepare(image,[LineRequest('PAGE',(0,0,20,30))],tmp_path/'job',1)
    assert prompt==TASK+'\n'+str(source)
    assert manifest['job_id'] not in prompt and not manifest['native_views']
    assert calls==[('prompt','pane','/clear')]
    assert manifest['native_request_not_before']>0
