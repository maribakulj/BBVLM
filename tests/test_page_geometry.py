import json
from pathlib import Path
import sys

from lxml import etree
from PIL import Image, ImageDraw
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_geometry import place_assignments
import page_geometry
from export_training import export


class Boxer:
    name = 'test_forced_placement'

    def __init__(self, results):
        self.results = results
        self.calls = []
        self.last_alignment = None
        self.last_char_positions = None

    def boxes(self, gray, line):
        self.calls.append((line.text, line.line_box))
        result = self.results[line.text]
        if isinstance(result, Exception):
            raise result
        self.last_alignment = {'character_scope': 'line'}
        self.last_char_positions = [[float(line.line_box[0]), float(line.line_box[0] + 1), .5]
                                    for _ in line.text]
        return result


@pytest.fixture
def page(tmp_path, monkeypatch):
    path = tmp_path / 'page.png'
    im = Image.new('L', (100, 80), 'white')
    ImageDraw.Draw(im).rectangle((10, 10, 50, 20), fill='black')
    im.save(path)
    monkeypatch.setattr(page_geometry.correct, 'cout_ligne', lambda *args: (.1, None, None))
    return path


def assignment(lid, text, bbox=(5, 5, 60, 25), **kwargs):
    return dict(line_id=lid, bbox=list(bbox), text=text, status='matched', **kwargs)


def test_failed_placement_keeps_every_text_and_does_not_re_read(page, tmp_path):
    rows = [assignment('L1', 'Texte exact'), assignment('L2', 'L’apostrophe', (5, 30, 70, 50))]
    boxer = Boxer({'Texte exact': [(10, 10, 25, 20), (30, 10, 50, 20)],
                   'L’apostrophe': ValueError('caractère hors alphabet CTC : ’')})
    out = tmp_path / 'out'
    result = place_assignments(page, rows, boxer, out, {'provider': 'gemini', 'model': 'observed', 'job_id': 'page-job'})
    annotations = json.loads((out / 'annotations.json').read_text())
    assert [a['text'] for a in annotations] == [r['text'] for r in rows]
    assert [a['assignment_status'] for a in annotations] == ['matched', 'matched']
    assert [a['status'] for a in annotations] == ['retenue', 'alphabet_aligneur_incompatible']
    assert annotations[0]['reading_job_id'] == 'page-job'
    assert len(boxer.calls) == 2 and result['report']['reading_calls'] == 0
    assert (out / 'transcription.txt').read_text() == 'Texte exact\nL’apostrophe'
    assert json.loads((out / 'assignments.json').read_text()) == rows
    assert rows[0].get('training_eligible') is None  # input not mutated
    root = etree.parse(str(out / 'page.alto.xml'))
    assert root.xpath('//*[local-name()="String"]/@CONTENT') == ['Texte', 'exact']
    assert result['report']['alto_validation']['valid']


def test_words_expand_line_to_observed_ink_and_keep_coordinate_conventions(page, tmp_path):
    row = assignment('L1', 'Été', (12, 12, 40, 18), detector_bbox=[5, 5, 60, 25])
    boxer = Boxer({'Été': [(10, 10, 50, 20)]})
    result = place_assignments(page, [row], boxer, tmp_path / 'out')
    annotation = result['annotations'][0]
    assert boxer.calls == [('Été', (5, 5, 60, 25))]
    assert annotation['geometry_bbox_before_words'] == [12, 12, 40, 18]
    assert annotation['bbox'] == [10, 10, 51, 21]
    assert annotation['words'][0]['x1'] == 50
    root = etree.parse(str(tmp_path / 'out' / 'page.alto.xml'))
    assert root.xpath('//*[local-name()="String"]/@WIDTH') == ['41']


def test_unresolved_assignment_does_not_become_trusted_through_ctc(page):
    row = assignment('L1', 'Mot')
    row['status'] = 'ambiguous_text_match'
    result = place_assignments(page, [row], Boxer({'Mot': [(10, 10, 20, 20)]}))
    annotation = result['annotations'][0]
    assert annotation['assignment_status'] == 'ambiguous_text_match'
    assert annotation['geometry_valid'] and not annotation['alto_eligible']
    assert annotation['status'] == 'appariement_non_resolu'


def test_page_reading_uncertainty_is_preserved_without_blocking_pseudo_geometry(page):
    result = place_assignments(page, [assignment('L1', 'Mot')], Boxer({'Mot': [(10, 10, 20, 20)]}),
                               metadata={'page_reading_uncertain': True})
    annotation = result['annotations'][0]
    assert annotation['page_reading_uncertain'] and annotation['uncertain']
    assert not annotation['reading_certified'] and not annotation['assignment_uncertain']
    assert annotation['training_eligible'] and annotation['status'] == 'retenue'
    assert result['report']['page_reading_uncertain'] and not result['report']['reading_certified']


def test_markdown_reflow_is_only_a_layout_view_with_exact_source_offsets(page, tmp_path):
    original = 'Texte\r\n\t exact'
    boxer = Boxer({'Texte exact': [(10, 10, 25, 20), (30, 10, 50, 20)]})
    out = tmp_path / 'out'
    result = place_assignments(page, [assignment('L1', original)], boxer, out)
    row = result['annotations'][0]
    assert row['text'] == 'Texte exact' and row['source_text'] == original
    assert row['status'] == 'retenue' and len(row['chars']) == len(row['text'])
    assert row['source_spans'][5] == [5, 9]
    assert original[row['source_spans'][6][0]:row['source_spans'][-1][1]] == 'exact'
    assert (out / 'transcription.txt').read_bytes() == original.encode()
    assert result['report']['layout_whitespace_normalized_lines'] == 1
    assert result['report']['source_text_preserved'] and not result['report']['lexical_text_changed']


def test_cross_line_collision_is_reported_for_both_without_losing_text(page):
    rows = [assignment('L1', 'Un'), assignment('L2', 'Deux')]
    result = place_assignments(page, rows, Boxer({'Un': [(10, 10, 25, 20)], 'Deux': [(20, 15, 35, 22)]}))
    assert [a['text'] for a in result['annotations']] == ['Un', 'Deux']
    assert all(a['status'] == 'superposition_inter_lignes' for a in result['annotations'])
    assert result['report']['lines_preserved'] == 2 and result['report']['lines_exported'] == 0


@pytest.mark.parametrize('boxes,expected', [
    ([(10, 10, 30, 20)], 'compte_mots_incoherent'),
    ([(10, 10, 30, 20), (20, 10, 50, 20)], 'geometrie_invalide'),
    ([(10, 10, 25, 20), (30, 10, 101, 20)], 'geometrie_invalide'),
    ([(10.2, 10, 25, 20), (30, 10, 50, 20)], 'geometrie_invalide'),
    (None, 'erreur_geometrie'),
])
def test_invalid_geometry_is_local_failure_not_text_loss(page, boxes, expected):
    result = place_assignments(page, [assignment('L1', 'Deux mots')], Boxer({'Deux mots': boxes}))
    annotation = result['annotations'][0]
    assert annotation['text'] == 'Deux mots' and annotation['status'] == expected
    assert not annotation['training_eligible']


def test_ink_suspicion_does_not_remove_transcription(page, monkeypatch):
    monkeypatch.setattr(page_geometry.correct, 'cout_ligne', lambda *args: (100, None, None))
    result = place_assignments(page, [assignment('L1', 'Mot')], Boxer({'Mot': [(10, 10, 20, 20)]}))
    annotation = result['annotations'][0]
    assert annotation['status'] == 'ajustement_encre_suspect'
    assert annotation['text'] == 'Mot' and len(annotation['words']) == 1


def test_non_nfc_is_preserved_and_flagged_without_silent_normalization(page):
    text = 'E\u0301te\u0301'
    boxer = Boxer({})
    result = place_assignments(page, [assignment('L1', text)], boxer)
    assert result['annotations'][0]['text'] == text
    assert result['annotations'][0]['status'] == 'normalisation_non_nfc'
    assert not boxer.calls


def test_missing_character_positions_cannot_crash_remaining_lines(page):
    class BadChars(Boxer):
        def boxes(self, gray, line):
            result = super().boxes(gray, line)
            self.last_char_positions = [[1, 2, .5]]
            return result
    result = place_assignments(page, [assignment('L1', 'Mot')], BadChars({'Mot': [(10, 10, 20, 20)]}))
    assert result['annotations'][0]['status'] == 'caracteres_invalides'


def test_existing_training_export_can_consume_page_annotations(page, tmp_path):
    out = tmp_path / 'out'
    place_assignments(page, [assignment('L1', 'Été')], Boxer({'Été': [(10, 10, 20, 20)]}), out)
    (out / 'olr.json').write_text(json.dumps(dict(model='test-layout', articles=[], blocks=[
        dict(id='B1', type='text', line_ids=['L1'], article_id=None, uncertain=False, bbox=[5, 5, 60, 25])
    ])))
    result = export(page, out)
    assert result['coverage'] == 1 and result['alto_validation']['valid'] and result['page_validation']
    assert json.loads((out / 'training.jsonl').read_text())['text'] == 'Été'


def test_cached_local_placements_still_recheck_global_collisions(page, tmp_path):
    boxer = Boxer({'Un': [(10, 10, 25, 20)], 'Deux': [(20, 15, 35, 22)]})
    boxer.cache_signature = {'model': 'test-v1'}
    rows = [assignment('L1', 'Un'), assignment('L2', 'Deux')]
    out = tmp_path / 'out'
    place_assignments(page, rows, boxer, out)
    boxer.calls.clear()
    result = place_assignments(page, rows, boxer, out)
    assert not boxer.calls and result['report']['geometry_cache']['hits'] == 2
    assert all(a['status'] == 'superposition_inter_lignes' for a in result['annotations'])


def test_duplicate_line_ids_are_rejected_without_guessing(page):
    with pytest.raises(ValueError, match='dupliqués'):
        place_assignments(page, [assignment('L1', 'Un'), assignment('L1', 'Deux')], Boxer({}))
