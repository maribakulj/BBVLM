from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lecture import Reading, ReaderUnavailable, ResponseError
from page_paged_markdown import PagedMarkdownReader,PagedPartReader,pagination_text,REVISION

JOB='a'*32
CID='12345678-1234-1234-1234-123456789abc'


@pytest.mark.parametrize('raw',[
    'texte sans fin',
    f'texte\n<!--BBVLM:{JOB}:END-->\nencore texte',
    f'<!--BBVLM:{JOB}:MORE-->\n<!--BBVLM:{JOB}:END-->',
    'texte\n<!--BBVLM:'+('b'*32)+':END-->',
])
def test_marker_absent_ambiguous_foreign_or_followed_by_content_is_rejected(raw):
    with pytest.raises(ResponseError):pagination_text(raw,JOB)


def test_marker_removal_preserves_all_source_content_and_does_not_certify_quality():
    text='## Été\n\n mot  ancien-\n'
    content,status=pagination_text(text+f'<!--BBVLM:{JOB}:MORE-->\n',JOB)
    assert content==text and status=='MORE'


def fake_transport(monkeypatch,parts,interrupt=False):
    submitted=[]
    interrupted=[False]
    def read_page(self,source,output):
        output=Path(output);job=output/'page-lecture-jobs'/'own-job';job.mkdir(parents=True,exist_ok=True)
        response=job/'response.json'
        if not response.exists():
            if interrupt and self.index==2 and not interrupted[0]:
                interrupted[0]=True
                raise ReaderUnavailable('native still working')
            submitted.append(self.index)
            text,marker=parts[self.index-1]
            jid=f'{self.index:032x}'
            value=dict(job_id=jid,model='Gemini test',lines=[dict(id='PAGE',text=text,uncertain=False)],
                       pagination=dict(index=self.index,marker=marker),
                       native_history_provenance=dict(conversation_id=CID))
            response.write_text(json.dumps(value))
            (job/'request.json').write_text(json.dumps(dict(job_id=jid)))
            (job/'prompt.txt').write_text('source prompt '+jid)
        value=json.loads(response.read_text());text=value['lines'][0]['text']
        self.journal=[dict(directory=str(job))]
        output.mkdir(exist_ok=True)
        (output/'vt.gemini.md').write_text(text)
        return Reading('PAGE',text,False,'gemini','Gemini test',job_id=value['job_id'],model_display_terminal='Gemini test')
    monkeypatch.setattr(PagedPartReader,'read_page',read_page)
    return submitted


def test_partial_vt_saved_before_next_portion_and_restart_does_not_resubmit_finished_parts(tmp_path,monkeypatch):
    source=tmp_path/'source.png';Image.new('RGB',(20,30),'white').save(source)
    submitted=fake_transport(monkeypatch,[('# Été\n','MORE'),('la suite.\n','END')],interrupt=True)
    out=tmp_path/'out';reader=PagedMarkdownReader('pane',out/'jobs')
    with pytest.raises(ReaderUnavailable):reader.read_page(source,out)
    assert (out/'vt.gemini.md').read_text()=='# Été\n'
    provenance=json.loads((out/'vt-provenance.json').read_text())
    assert provenance['reading_status']=='partial_awaiting_next_portion' and provenance['uncertain']
    reading=reader.read_page(source,out)
    assert submitted==[1,2] and reading.text=='# Été\nla suite.\n'
    provenance=json.loads((out/'vt-provenance.json').read_text())
    assert provenance['model_reported_complete'] and not provenance['coverage_certified']
    assert not provenance['complete_pipeline_certified']
    reader.read_page(source,out)
    assert submitted==[1,2]


def test_refusal_preserves_received_text_and_is_never_a_complete_page(tmp_path,monkeypatch):
    source=tmp_path/'source.png';Image.new('RGB',(10,10)).save(source)
    fake_transport(monkeypatch,[('lisible.\n','REFUSED')])
    out=tmp_path/'out'
    with pytest.raises(ReaderUnavailable,match='Refus'):PagedMarkdownReader('pane',out/'jobs').read_page(source,out)
    assert (out/'vt.gemini.md').read_text()=='lisible.\n'
    assert json.loads((out/'vt-provenance.json').read_text())['reading_status']=='refused_partial'


def test_changed_saved_part_cannot_be_overwritten_silently(tmp_path,monkeypatch):
    source=tmp_path/'source.png';Image.new('RGB',(10,10)).save(source)
    fake_transport(monkeypatch,[('source.\n','END')])
    out=tmp_path/'out';reader=PagedMarkdownReader('pane',out/'jobs');reader.read_page(source,out)
    (out/'vt-parts/001/vt.gemini.md').write_text('modification utilisateur')
    with pytest.raises(ReaderUnavailable,match='modifiée'):reader.read_page(source,out)
