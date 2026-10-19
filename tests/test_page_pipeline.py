import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_pipeline import run, verify_transcription
import page_pipeline
from page_anchors import save_json, sha256
from page_olr import infer_structure


def inputs(tmp_path):
    image = tmp_path / 'image.png'
    Image.new('L', (400, 200), 255).save(image)
    markdown = tmp_path / 'vt.gemini.md'
    markdown.write_text('# Titre\n\nUne phrase entière.\n\nTexte sans ligne détectée.', encoding='utf-8')
    provenance = tmp_path / 'vt-provenance.json'
    save_json(provenance, dict(provider='gemini', job_id='test', image_sha256=sha256(image),
                               artifact_sha256=sha256(markdown), uncertain=False))
    auto = tmp_path / 'auto'
    rows = [dict(id='L1', bbox=[10, 10, 180, 40], source='kraken-blla/tiles'),
            dict(id='L2', bbox=[10, 60, 380, 90], source='kraken-blla/tiles'),
            dict(id='L3', bbox=[10, 150, 100, 170], source='kraken-blla/tiles')]
    save_json(auto / 'segmentation.json', rows)
    save_json(auto / 'segmentation-config.json', dict(version='blla-rectangles-v1', image_sha256=sha256(image)))
    save_json(auto / 'readings.json', [dict(id='L1', text='Titre', provider='gemini', job_id='old'),
                                     dict(id='L2', text='Une phrase entière.', provider='gemini', job_id='old'),
                                     dict(id='L3', text='aucune correspondance', provider='gemini', job_id='old')])
    return image, markdown, provenance, auto


def test_pipeline_keeps_complete_markdown_and_resumes_without_gemini(tmp_path):
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    original = markdown.read_bytes()
    first = run(image, markdown, provenance, auto, out, geometry=False)
    assert len(first['assignments']) == 2
    assert len(first['unmatched_lines']) == 1
    assert 'Texte sans ligne détectée.' in first['plain_text']
    assert (out / 'vt.gemini.md').read_bytes() == original == markdown.read_bytes()
    assert first['text_coverage']['fraction'] < 1
    second = run(image, markdown, provenance, auto, out, geometry=False)
    assert second == first
    olr = json.loads((out / 'olr.json').read_text())
    assert olr['line_reading_order'] == ['L1', 'L2']
    assert olr['articles'] == [] and olr['semantic_certified'] is False
    assert all(block['article_id'] is None for block in olr['blocks'])
    assert olr['article_candidates'][0]['line_ids'] == ['L1', 'L2']
    assert olr['unlocated_markdown_blocks'][0]['text'] == 'Texte sans ligne détectée.'


def test_pipeline_refuses_changed_transcription_or_anchor_inputs(tmp_path):
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    run(image, markdown, provenance, auto, out, geometry=False)
    source = auto / 'readings.json'
    readings = json.loads(source.read_text())
    readings[0]['text'] = 'Autre titre'
    save_json(source, readings)
    with pytest.raises(ValueError, match='Configuration'):
        run(image, markdown, provenance, auto, out, geometry=False)
    markdown.write_text('Texte altéré')
    with pytest.raises(ValueError, match='ne correspondent pas'):
        verify_transcription(image, markdown, provenance)


def test_olr_uses_expanded_ink_geometry_and_does_not_invent_articles(tmp_path):
    image, markdown, provenance, auto = inputs(tmp_path)
    alignment = run(image, markdown, provenance, auto, tmp_path / 'result', geometry=False)
    olr = infer_structure(alignment, [dict(id='L1', bbox=[8, 8, 190, 43])])
    assert olr['blocks'][0]['bbox'] == [8, 8, 190, 43]
    assert olr['blocks'][0]['type'] == 'heading'
    assert olr['blocks'][0]['uncertain'] is True
    assert olr['articles'] == []


def test_unlocated_heading_still_separates_article_candidates():
    from page_alignment import align_page
    rows = [dict(id='L1', bbox=[1, 1, 80, 10], auxiliary_text='Premier titre'),
            dict(id='L2', bbox=[1, 30, 80, 40], auxiliary_text='Le texte suivant.')]
    alignment = align_page('# Premier titre\n\n# Second titre\n\nLe texte suivant.', rows, image_size=(100, 100))
    olr = infer_structure(alignment)
    assert len(olr['article_candidates']) == 2
    assert olr['article_candidates'][0]['line_ids'] == ['L1']
    assert olr['article_candidates'][1]['line_ids'] == ['L2']
    assert olr['article_candidates'][1]['heading_located'] is False


def test_alignment_only_cannot_overwrite_structure_of_existing_geometry(tmp_path):
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    run(image, markdown, provenance, auto, out, geometry=False)
    olr = out / 'olr.json'
    saved = json.loads(olr.read_text())
    saved['blocks'][0]['bbox'] = [8, 8, 190, 43]
    save_json(olr, saved)
    (out / 'annotations.json').write_text('[]')
    before = olr.read_bytes()
    with pytest.raises(ValueError, match='placements existent'):
        run(image, markdown, provenance, auto, out, geometry=False)
    assert olr.read_bytes() == before


@pytest.mark.parametrize('changed', ['implementation', 'provenance'])
def test_resume_never_overwrites_a_page_from_different_code_or_provenance(tmp_path, monkeypatch, changed):
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    run(image, markdown, provenance, auto, out, geometry=False)
    previous = {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    if changed == 'implementation':
        fingerprints = page_pipeline.implementation_fingerprints()
        fingerprints['page_alignment.py'] = 'different-algorithm'
        monkeypatch.setattr(page_pipeline, 'implementation_fingerprints', lambda: fingerprints)
    else:
        metadata = json.loads(provenance.read_text())
        metadata['job_id'] = 'another-reading-job'
        save_json(provenance, metadata)
    with pytest.raises(ValueError, match='Configuration'):
        run(image, markdown, provenance, auto, out, geometry=False)
    assert all((out / name).read_bytes() == data for name, data in previous.items())


def test_provenance_already_in_output_is_preserved_and_resumable(tmp_path):
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    out.mkdir()
    inside = out / 'vt-provenance.json'
    inside.write_bytes(provenance.read_bytes())
    before = inside.read_bytes()
    first = run(image, markdown, inside, auto, out, geometry=False)
    second = run(image, markdown, inside, auto, out, geometry=False)
    assert first == second and inside.read_bytes() == before


def test_code_change_during_alignment_is_detected_before_success(tmp_path, monkeypatch):
    import page_alignment
    image, markdown, provenance, auto = inputs(tmp_path)
    out = tmp_path / 'result'
    original = page_alignment.write_alignment
    def changing(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(page_pipeline, 'implementation_fingerprints', lambda: {'changed': 'during-run'})
        return result
    monkeypatch.setattr(page_alignment, 'write_alignment', changing)
    with pytest.raises(ValueError, match='Implémentation modifiée'):
        run(image, markdown, provenance, auto, out, geometry=False)
    state = json.loads((out / 'page-pipeline-state.json').read_text())
    assert state['stage'] == 'interrupted' and state['original_markdown_preserved']
    assert (out / 'vt.gemini.md').read_bytes() == markdown.read_bytes()
