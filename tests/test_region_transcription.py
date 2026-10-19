import importlib.util
import json
from pathlib import Path

from PIL import Image
import pytest


spec = importlib.util.spec_from_file_location('transcrire_regions', Path(__file__).parents[1] / 'scripts/transcrire_regions.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_tiles_preserve_pixels_cover_region_and_resume(tmp_path):
    image = Image.new('RGB', (80, 6500))
    # Les pixels permettent de détecter une translation incorrecte des vues.
    for y in range(image.height):
        for x in range(image.width):
            image.putpixel((x, y), (x, y % 256, y // 256))
    source = tmp_path / 'source.png'
    image.save(source)
    plan = {'regions': [{'id': 'col_1', 'order': 1, 'bbox': [10, 100, 70, 6400]}]}
    result = module.prepare(source, plan, tmp_path / 'run')
    row = result['regions'][0]
    assert len(row['views']) == 3
    previous_end = 100
    for view in row['views']:
        x0, y0, x1, y1 = view['source_bbox']
        assert y0 <= previous_end
        assert y1 - y0 <= 2800
        assert Image.open(view['path']).tobytes() == image.crop((x0, y0, x1, y1)).tobytes()
        previous_end = y1
    assert previous_end == 6400
    assert module.prepare(source, plan, tmp_path / 'run') == result
    Image.new('RGB', (60, 2800), 'red').save(row['views'][0]['path'])
    with pytest.raises(ValueError, match='Vue existante modifiée'):
        module.prepare(source, plan, tmp_path / 'run')


def test_assembly_preserves_each_transcription_and_source_spans(tmp_path, monkeypatch):
    from types import SimpleNamespace
    texts = ['mot cou-\npé', 'Suite\n\nfin.']
    class Reader:
        def __init__(self, *args, **kwargs):
            pass
        def read_page(self, source, directory):
            i = int(Path(directory).name)
            directory.mkdir(exist_ok=True)
            (directory / 'vt.gemini.md').write_text(texts[i])
            (directory / 'vt-provenance.json').write_text('{}')
            return SimpleNamespace(text=texts[i], job_id=f'job{i}', uncertain=False, model='test')
    monkeypatch.setattr(module, 'RegionMarkdownReader', Reader)
    manifest = {'image': 'source.png', 'image_sha256': 'abc', 'regions': [
        {'id': str(i), 'bbox': [i*10, 0, i*10+10, 20], 'order': i, 'image': f'{i}.png', 'views': []}
        for i in range(2)]}
    module.transcribe(manifest, tmp_path, 'test')
    combined = (tmp_path / 'vt.gemini.md').read_text()
    assert combined == '\n\n'.join(texts)
    provenance = json.loads((tmp_path / 'vt-provenance.json').read_text())
    for part, text in zip(provenance['parts'], texts):
        assert combined[slice(*part['span'])] == text
    assert not provenance['reference_used']


def test_regional_evaluation_keeps_hipe_hyphen_rules_and_all_lines(tmp_path):
    evaluation_spec = importlib.util.spec_from_file_location(
        'evaluer_regions', Path(__file__).parents[1] / 'scripts/evaluer_regions.py')
    evaluator = importlib.util.module_from_spec(evaluation_spec)
    evaluation_spec.loader.exec_module(evaluator)
    reference = tmp_path / 'reference.xml'
    reference.write_text('''<PcGts><Page><TextRegion id="r1">
      <TextLine id="l1"><Coords points="0,0 8,0 8,9 0,9"/><TextEquiv><Unicode>un¬</Unicode></TextEquiv></TextLine>
      <TextLine id="l2"><Coords points="0,10 8,10 8,19 0,19"/><TextEquiv><Unicode>mot</Unicode></TextEquiv></TextLine>
      </TextRegion><TextRegion id="r2">
      <TextLine id="l3"><Coords points="12,0 19,0 19,9 12,9"/><TextEquiv><Unicode>Fin</Unicode></TextEquiv></TextLine>
      </TextRegion></Page></PcGts>''')
    manifest = tmp_path / 'evaluation.json'
    manifest.write_text(json.dumps({'pages': [{'image_sha256': 'page', 'reference': str(reference),
                                              'reference_sha256': module.sha256(reference)}]}))
    regions = []
    for i, text in enumerate(['un-\nmot', 'Fin']):
        directory = tmp_path / f'r{i}'
        directory.mkdir()
        markdown = directory / 'vt.gemini.md'
        markdown.write_text(text)
        (directory / 'vt-provenance.json').write_text(json.dumps(
            {'artifact_sha256': module.sha256(markdown), 'image_sha256': f'crop{i}'}))
        regions.append({'id': f'r{i}', 'bbox': [i*10, 0, i*10+10, 30], 'image_sha256': f'crop{i}'})
    (tmp_path / 'regions.json').write_text(json.dumps({'image_sha256': 'page', 'regions': regions}))
    report = evaluator.evaluate(manifest, tmp_path)
    assert report['unassigned_reference_lines'] == []
    assert sum(r['reference_lines'] for r in report['regions']) == 3
    assert report['errors'] == 1
    assert report['reference_characters'] == 8
    assert report['regions'][0]['space_insertions'] == 1
    # Deux cellules d'une même rangée sont lues de gauche à droite,
    # même si le bord supérieur de la cellule droite est deux pixels plus haut.
    ordered = evaluator.geometric_order([
        {'id': 'right', 'bbox': [20, 8, 40, 18]},
        {'id': 'below', 'bbox': [0, 30, 40, 40]},
        {'id': 'left', 'bbox': [0, 10, 18, 20]},
    ])
    assert [r['id'] for r in ordered] == ['left', 'right', 'below']


def test_region_prompt_waits_for_new_empty_native_conversation(tmp_path,monkeypatch):
    import sqlite3
    import page_region_markdown as native
    from lecture import LineRequest
    history=tmp_path/'.gemini/antigravity-cli/conversations';history.mkdir(parents=True)
    old='11111111-1111-1111-1111-111111111111'
    new='22222222-2222-2222-2222-222222222222'
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:tmp_path))
    monkeypatch.setattr(native,'conversation_hint',lambda cwd:old)
    reader=native.RegionMarkdownReader('test',tmp_path/'jobs','OCR')
    reader.source_path=tmp_path/'image.png';Image.new('L',(20,20),255).save(reader.source_path)
    def call(*args):
        assert args==('prompt','test','/clear')
        with sqlite3.connect(history/(new+'.db')) as db:db.execute('CREATE TABLE steps(idx INTEGER)')
        return 0,{},''
    monkeypatch.setattr(reader,'_call',call)
    manifest,prompt=reader._prepare(Image.open(reader.source_path),[LineRequest('PAGE',(0,0,20,20))],tmp_path/'job',1)
    assert manifest['native_conversation_id']==new
    assert manifest['native_conversation_id']!=old
