import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from olr_local import batches,local_hints


def test_local_batches_preserve_all_lines_and_all_nontext_candidates():
    annotations=[dict(id=f'L{i}',bbox=[10,10+15*i,90,20+15*i],text='',uncertain=True,
                      status='diagnostic_layout_only_no_vt') for i in range(85)]
    regions=[dict(id=f'S{i}',bbox=[100,10+15*i,110,20+15*i]) for i in range(11)]
    schedule=batches(annotations,[],regions,count=2)
    assert sorted(a['id'] for b in schedule for a in b['annotations'])==sorted(a['id'] for a in annotations)
    assert sorted(r['id'] for b in schedule for r in b['regions'])==sorted(r['id'] for r in regions)
    assert all(not (b['regions'] and b['annotations']) for b in schedule)
    assert max(len(b['regions']) for b in schedule)<=2


def test_local_hints_preserve_semantic_ids_notes_uncertainty_and_native_provenance():
    result=dict(job_id='j1',model='Gemini model claim',model_display_terminal='native footer',
                visual_notes=[['B1','topic','first','last']],
                blocks=[dict(id='B1_G1',semantic_block_id='B1',type='heading',line_ids=['L1'],
                             uncertain=True,article_id=None)])
    hints=local_hints(result,'local-1')
    assert hints[0]['visual_notes']==['topic','first','last']
    assert hints[0]['line_ids']==['L1'] and hints[0]['uncertain'] is True
    assert hints[0]['reading_job_id']=='j1' and hints[0]['model_display_terminal']=='native footer'
    assert 'article_id' not in hints[0]  # local batches do not imply global membership


def test_local_notes_cannot_omit_a_block_or_establish_global_article_membership():
    import pytest
    from olr_groups import validate_local_notes
    from lecture import ResponseError
    raw=dict(blocks=[dict(id='B1',group_ids=['G1'],segments=[])],visual_notes=[])
    result=dict(articles=[],blocks=[dict(article_id=None)])
    with pytest.raises(ResponseError,match='exactement'):
        validate_local_notes(raw,result)
    raw['visual_notes']=[['B1','topic','first','last']]
    assert validate_local_notes(raw,result)==raw['visual_notes']
    with pytest.raises(ResponseError,match='globale'):
        validate_local_notes(raw,dict(articles=[dict(id='A1')],blocks=[dict(article_id='A1')]))
