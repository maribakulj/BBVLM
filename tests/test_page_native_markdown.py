import json
from pathlib import Path
import sqlite3
import sys

import numpy as np
from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lecture import ResponseError, LineRequest
from native_page_history import identified_markdown
from page_native_markdown import NativeMarkdownReader, tile_boxes

CID='12345678-1234-1234-1234-123456789abc';JOB='a'*32


def varint(value):
    result=bytearray()
    while value>127:result.append((value&127)|128);value>>=7
    result.append(value);return bytes(result)


def field(number,value):
    return varint(number*8+2)+varint(len(value))+value


def model(text,other=None,tool=False):
    text=text.encode();raw=(other.encode() if other is not None else text)
    planner=field(1,text)+field(8,raw)+(field(7,b'tool') if tool else b'')
    return b'\x08\x0f\x20\x03'+field(20,planner)


def test_natural_markdown_uses_only_identified_final_fields_after_read(tmp_path):
    prompt='same original '+JOB
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',[
            (0,14,3,prompt.encode()),(1,15,3,model('prior thoughts')),
            (2,132,3,b'image read'),(3,15,3,model('tool narration',tool=True)),
            (4,15,3,model('# Titre\n\nÉté.\n'))])
    text,proof=identified_markdown(CID,prompt,JOB,tmp_path)
    assert text=='# Titre\n\nÉté.\n' and proof['response_step_index']==4
    assert proof['format_reprompt'] is False


def test_natural_markdown_refuses_disagreement_in_final_fields(tmp_path):
    prompt='same '+JOB
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',[(0,14,3,prompt.encode()),
            (1,132,3,b'image'),(2,15,3,model('one','two'))])
    with pytest.raises(ResponseError,match='ambigu'):identified_markdown(CID,prompt,JOB,tmp_path)


def test_empty_region_requires_explicit_permission_and_native_final_evidence(tmp_path):
    prompt='same '+JOB
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:
        db.execute('CREATE TABLE steps(idx integer,step_type integer,status integer,step_payload blob)')
        db.executemany('INSERT INTO steps VALUES(?,?,?,?)',[(0,14,3,prompt.encode()),
            (1,132,3,b'image'),(2,15,3,model('\n'))])
    with pytest.raises(ResponseError,match='vide'):identified_markdown(CID,prompt,JOB,tmp_path)
    text,proof=identified_markdown(CID,prompt,JOB,tmp_path,allow_empty=True)
    assert text=='\n' and proof['response_completeness']=='native_empty_response_pending_review'
    with sqlite3.connect(tmp_path/(CID+'.db')) as db:db.execute('DELETE FROM steps WHERE idx=2')
    with pytest.raises(ResponseError,match='Aucun Markdown'):
        identified_markdown(CID,prompt,JOB,tmp_path,allow_empty=True)


def test_all_view_pixels_and_page_edges_are_native(tmp_path,monkeypatch):
    image=Image.fromarray(np.random.default_rng(1).integers(0,255,(620,900,3),dtype=np.uint8))
    source=tmp_path/'page.png';image.save(source)
    reader=NativeMarkdownReader('pane',tmp_path/'jobs',tile_size=384)
    reader.source_path=source;reader.native_cwd='/native-cwd'
    monkeypatch.setattr('page_native_markdown.conversation_hint',lambda cwd:CID)
    manifest,prompt=reader._prepare(image,[LineRequest('PAGE',(0,0,*image.size))],tmp_path/'job',1)
    coverage=np.zeros((image.height,image.width),dtype=bool)
    for view in manifest['native_views']:
        x0,y0,x1,y1=view['source_bbox'];coverage[y0:y1,x0:x1]=True
        with Image.open(view['path']) as crop:
            assert np.array_equal(np.asarray(crop),np.asarray(image)[y0:y1,x0:x1])
    assert coverage.all() and 'sans JSON' in prompt
    assert reader.allow_format_recovery is False
