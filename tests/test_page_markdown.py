import json
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from lecture import LineRequest, ResponseError, validate_response, response_in_text
from page_markdown import PageMarkdownReader, validate_page_response
from evaluation import convention_v2
from page_text_evaluation import markdown_text, score_page_text, evaluate


def answer(job_id, text, uncertain=False):
    return dict(job_id=job_id,kind='page_markdown',provider='gemini',model='test',
                lines=[dict(id='PAGE',text_parts=[text[:4],text[4:]],uncertain=uncertain)])


def test_page_paragraphs_survive_json_and_nfc_without_weakening_line_protocol():
    requests=[LineRequest('PAGE',(0,0,20,30))]
    value=answer('new','# Titre\n\nL’e\u0301té.\nSuite, fin.')
    terminal=json.dumps(answer('old','ancien'))+'\n'+json.dumps(value,ensure_ascii=False)
    _,readings=response_in_text(terminal,requests,'new',validate_page_response)
    assert readings[0].text=='# Titre\n\nL’été.\nSuite, fin.'
    with pytest.raises(ResponseError):validate_response(value,requests,'new')
    with pytest.raises(ResponseError):validate_page_response(value,requests,'other')


def test_uncertain_whole_page_is_saved_before_geometry_and_cache_never_resubmits(tmp_path,monkeypatch):
    image=tmp_path/'source.png';Image.new('RGB',(20,30),'white').save(image)
    out=tmp_path/'out';reader=PageMarkdownReader('pane',out/'jobs')
    text='# Titre\n\nTout le texte, même sans placement.\n'
    calls=[]
    def call(*args):
        calls.append(args)
        if args[0]=='read':
            request=json.loads(next((out/'jobs').glob('*/request.json')).read_text())
            return 0,dict(result=dict(text=json.dumps(answer(request['job_id'],text,True),ensure_ascii=False))),''
        return 0,dict(result=dict(agent=dict(agent='agy',agent_status='done'))),''
    monkeypatch.setattr(reader,'_call',call)
    result=reader.read_page(image,out)
    assert result.uncertain and (out/'vt.gemini.md').read_text()==text
    request=json.loads(next((out/'jobs').glob('*/request.json')).read_text())
    assert request['lines']==[dict(id='PAGE',bbox=[0,0,20,30])]
    prompt=next((out/'jobs').glob('*/prompt.txt')).read_text()
    assert str(image) in prompt and 'gold' not in prompt and 'segmentation' not in prompt
    assert next(c for c in calls if c[0]=='read')[-1]=='1000'
    n=len(calls)
    assert reader.read_page(image,out).text==text
    assert len(calls)==n
    provenance=json.loads((out/'vt-provenance.json').read_text())
    assert provenance['geometry_required'] is False and provenance['complete_pipeline_certified'] is False


def test_v2_ignores_declared_accents_and_composition_but_keeps_word_and_punctuation_errors():
    assert convention_v2('L’été ſœur ﬁancé Æneas')==convention_v2("L'ete soeur fiance AEneas")
    assert convention_v2('Marie, juge')!=convention_v2('Marie. juge')
    assert convention_v2('chose')!=convention_v2('choſes')
    assert convention_v2('A')!=convention_v2('a')


def test_markdown_scoring_keeps_all_cells_and_punctuation_without_reordering():
    text,meta=markdown_text('# Titre\n\n**Un**, *deux*.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n')
    assert text=='Titre\nUn, deux.\nA\nB\n1\n2'
    assert meta['unhandled_token_types']==[]
    ref=[dict(text='Titre'),dict(text='Un, deux.'),dict(text='A B 1 2')]
    score,_=score_page_text(ref,'# Titre\n\nUn, deux.\n\nA B 1 2')
    assert score['text']['convention_v2']['errors']==0
    changed,_=score_page_text(ref,'# Titre\n\nUn. deux.\n\n2 1 B A')
    assert changed['text']['convention_v2']['errors']>0
    assert changed['spatial_coverage']=='not_measured_by_whole_page_VT'


def test_missing_pages_remain_in_independent_whole_suite_verdict(tmp_path):
    manifest=tmp_path/'evaluation.json'
    manifest.write_text(json.dumps(dict(protocol_sha256='original',pages=[
        dict(id='hard',family='newspaper',split='reserved',human_text=True),
        dict(id='easy',family='book',split='reserved',human_text=True)])))
    report=evaluate(manifest,tmp_path/'missing','reserved')
    assert report['pages']==report['missing']==2
    assert report['measured']==0 and report['criteria_met'] is False
    assert all(r['coverage']==0 for r in report['rows'])


def test_unordered_reading_diagnostic_keeps_order_failure_and_extra_missing_text():
    refs=[dict(id='one',text='Premier.'),dict(id='two',text='Second.')]
    score,_=score_page_text(refs,'Second.\nPremier.')
    diagnostic=score['unordered_line_diagnostic']['modes']['convention_v2']
    assert diagnostic['errors']==0 and diagnostic['inversions']==1 and diagnostic['kendall']==-1
    assert score['text']['convention_v2']['errors']>0
    missing,_=score_page_text(refs,'Premier.')
    assert missing['unordered_line_diagnostic']['modes']['convention_v2']['errors']==len('Second.')
    extra,_=score_page_text(refs,'Premier.\nSecond.\nSupplément.')
    assert extra['unordered_line_diagnostic']['modes']['convention_v2']['errors']>0
