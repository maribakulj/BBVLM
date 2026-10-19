from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from gemini_provenance import normalize_provider
from lecture import HerdrGeminiReader,LineRequest,ReaderUnavailable,validate_response

JOB='14d1470374654bc49024719fc332946e'


def value(provider='Google',model='Gemini 3.1 Pro'):
    return dict(job_id=JOB,provider=provider,model=model,
                lines=[dict(id='L0044',text='ſix,',uncertain=False)])


def terminal():return JOB+'\n réponse identifiée\n? for shortcuts     Gemini 3.1 Pro · high'


def test_native_vendor_label_preserves_original_claim_and_exact_transcription():
    raw=value();normalized=normalize_provider(raw,terminal())
    assert raw['provider']=='Google' and normalized['provider']=='gemini'
    assert normalized['provider_claim_original']=='Google'
    assert normalized['lines']==raw['lines'] and normalized['model']==raw['model']
    assert normalized['provider_normalization']['text_changed'] is False


@pytest.mark.parametrize('screen,model',[(JOB,'Gemini 3.1 Pro'),(terminal(),'Churro'),
    (terminal()+'\n'+'a'*32,'Gemini 3.1 Pro'),('Gemini 3.1 Pro · high','Gemini 3.1 Pro')])
def test_vendor_normalization_requires_current_identified_native_gemini_evidence(screen,model):
    with pytest.raises(ValueError):normalize_provider(value(model=model),screen)


def test_reader_saves_attested_vendor_claim_and_cache_without_native_prompt(tmp_path):
    reader=HerdrGeminiReader('test-pane',tmp_path);reader.last_terminal=terminal()
    request=[LineRequest('L0044',(0,0,100,40))];raw=value();readings=validate_response(raw,request,JOB)
    result=reader._store_response(tmp_path,request,1,raw,readings)
    saved=json.loads((tmp_path/'response.json').read_text())
    assert saved['provider']=='gemini' and saved['provider_claim_original']=='Google'
    assert saved['lines'][0]['text']=='ſix,' and result[0].text=='ſix,'
    assert result[0].provider=='gemini' and validate_response(saved,request,JOB)==result
    assert reader.journal[-1]['provider_normalization']['native_model_display']=='Gemini 3.1 Pro · high'
    assert json.loads((tmp_path/'state.json').read_text())['phase']=='completed'


def test_foreign_provider_or_unattested_vendor_stops_instead_of_becoming_empty_ocr(tmp_path):
    reader=HerdrGeminiReader('test-pane',tmp_path);request=[LineRequest('L0044',(0,0,100,40))]
    for raw in (value(provider='churro',model='Churro'),value()):
        readings=validate_response(raw,request,JOB)
        with pytest.raises(ReaderUnavailable):reader._store_response(tmp_path,request,1,raw,readings)
    assert not (tmp_path/'response.json').exists()
