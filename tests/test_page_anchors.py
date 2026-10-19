import json
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_anchors import cached_reading_anchors, ctc_anchors, load_automatic_lines, sha256


def cache(tmp_path):
    image = tmp_path / 'image.png'
    Image.new('L', (100, 80), 255).save(image)
    directory = tmp_path / 'auto'
    directory.mkdir()
    rows = [dict(id='L1', bbox=[2, 2, 90, 20], source='kraken-blla/tiles'),
            dict(id='L2', bbox=[2, 25, 90, 40], source='kraken-blla/tiles')]
    (directory / 'segmentation.json').write_text(json.dumps(rows))
    (directory / 'segmentation-config.json').write_text(json.dumps(dict(
        image_sha256=sha256(image), version='blla-rectangles-v1')))
    (directory / 'readings.json').write_text(json.dumps([
        dict(id='L1', text='Mauvaise lecture auxiliaire', provider='gemini', job_id='test')]))
    return image, directory, rows


def test_import_requires_same_image_and_automatic_boxes(tmp_path):
    image, directory, rows = cache(tmp_path)
    result = cached_reading_anchors(image, directory)
    assert result['transcription_source'] is False
    assert result['lines'][1]['auxiliary_status'] == 'missing'
    other = tmp_path / 'other.png'
    Image.new('L', (100, 80), 0).save(other)
    with pytest.raises(ValueError, match='autre image'):
        load_automatic_lines(other, directory)
    rows[0]['reference_text'] = 'secret'
    (directory / 'segmentation.json').write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='référence'):
        load_automatic_lines(image, directory)


def test_ctc_resume_preserves_completed_lines_after_interruption(tmp_path):
    image, _, rows = cache(tmp_path)
    calls = []
    def interrupted(line):
        calls.append(line['id'])
        if line['id'] == 'L2':
            raise KeyboardInterrupt()
        return 'première'
    output = tmp_path / 'anchors'
    with pytest.raises(KeyboardInterrupt):
        ctc_anchors(image, rows, output, decoder=interrupted, model_signature='test')
    def resumed(line):
        calls.append(line['id'])
        return 'deuxième'
    result = ctc_anchors(image, rows, output, decoder=resumed, model_signature='test')
    assert calls == ['L1', 'L2', 'L2']
    assert [r['auxiliary_text'] for r in result['lines']] == ['première', 'deuxième']
    with pytest.raises(ValueError, match='Configuration'):
        ctc_anchors(image, rows, output, decoder=resumed, model_signature='changed')


def test_decode_failure_is_retained_and_never_filled(tmp_path):
    image, _, rows = cache(tmp_path)
    def failing(_):
        raise ValueError('pixels illisibles')
    result = ctc_anchors(image, rows, tmp_path / 'anchors', decoder=failing, model_signature='test')
    assert len(result['lines']) == len(rows)
    assert all(r['auxiliary_status'] == 'decode_failed' and r['auxiliary_text'] == '' for r in result['lines'])


def test_corrupt_cache_is_preserved_and_redecoded_instead_of_silent_omission(tmp_path):
    image, _, rows = cache(tmp_path)
    output = tmp_path / 'anchors'
    ctc_anchors(image, rows[:1], output, decoder=lambda _: 'valide', model_signature='test')
    stored = next((output / 'line-cache').glob('*.json'))
    stored.write_text('{}')
    result = ctc_anchors(image, rows[:1], output, decoder=lambda _: 'recalculé', model_signature='test')
    assert result['lines'][0]['auxiliary_text'] == 'recalculé'
    assert len(list((output / 'line-cache').glob('*.invalid-*.json'))) == 1
