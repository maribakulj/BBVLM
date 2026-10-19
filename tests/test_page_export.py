from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from lxml import etree
from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_export import export
from page_alignment import markdown_document


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


@pytest.fixture
def source(tmp_path):
    image = tmp_path / 'source.png'
    Image.new('L', (150, 100), 'white').save(image)
    out = tmp_path / 'out'
    out.mkdir()
    markdown = '# Édition\n\nUn mot\n\nTexte non placé.\n'
    artifact = out / 'transcription.md'
    artifact.write_text(markdown, encoding='utf-8')
    plain, _, _ = markdown_document(markdown)
    assignments, annotations, blocks = [], [], []
    for lid, text, box, words, kind in [
        ('L1', 'Édition', [5, 5, 100, 20], [dict(text='Édition', x0=10, y0=8, x1=80, y1=17)], 'heading'),
        ('L2', 'Un mot', [5, 30, 100, 50], [dict(text='Un', x0=10, y0=33, x1=30, y1=46),
                                          dict(text='mot', x0=40, y0=33, x1=80, y1=46)], 'text')]:
        start = plain.index(text)
        assignments.append(dict(id=lid, line_id=lid, start=start, end=start+len(text), text=text))
        annotations.append(dict(id=lid, text=text, bbox=box, words=words,
            chars=[[10., 11., .5] for _ in text], training_eligible=True, status='retenue',
            assignment_status='matched', alignment={'character_scope': 'word'},
            model='observed-model', reading_job_id='page-job', baseline=[]))
        blocks.append(dict(id='B_'+lid, type=kind, line_ids=[lid], bbox=box,
                           article_id=None, uncertain=True, type_source='markdown'))
    annotations.append(dict(id='L3', text='', bbox=[5, 60, 100, 80], status='texte_absent',
                            training_eligible=False, assignment_status='ambiguous_text_match'))
    alignment = dict(markdown=markdown, markdown_sha256=hashlib.sha256(markdown.encode()).hexdigest(),
                     markdown_artifact=str(artifact), plain_text=plain, image_size=[150, 100], assignments=assignments)
    olr = dict(model='markdown-structure', blocks=blocks, articles=[], article_candidates=[{'uncertain': True}])
    write_json(out / 'annotations.json', annotations)
    write_json(out / 'page-alignment.json', alignment)
    write_json(out / 'olr.json', olr)
    write_json(out / 'provenance.json', dict(taille=[150, 100], lecture='gemini', geometrie='forcectc',
                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest()))
    return image, out, annotations, alignment, olr


def test_uncertain_olr_does_not_filter_reliably_placed_text(source):
    image, out, annotations, alignment, olr = source
    original = {name: (out / name).read_bytes() for name in ('transcription.md', 'page-alignment.json', 'annotations.json', 'olr.json')}
    report = export(image, out)
    assert report['lines_exported'] == 2 and report['excluded'] == 1
    assert report['alto_validation']['valid'] and report['page_validation']
    assert report['lines_with_baselines'] == 0 and not report['baseline_reader_compatible']
    assert not report['criteria_met'] and report['articles_certified'] == 0
    root = etree.parse(str(out / 'page.alto.xml'))
    assert root.xpath('//*[local-name()="String"]/@CONTENT') == ['Édition', 'Un', 'mot']
    assert root.xpath('//*[local-name()="OtherTag"]') == []
    rows = [json.loads(line) for line in (out / 'training.jsonl').read_text().splitlines()]
    assert all(row['article_id'] is None and row['olr']['uncertain'] for row in rows)
    assert all(row['quality_status'].startswith('pseudo_annotation') for row in rows)
    assert rows[1]['words'][1] == dict(text='mot', start=3, end=6, bbox=[40, 33, 81, 47])
    ir = json.loads((out / 'axel-ir.json').read_text())
    assert ir['articles'] == [] and [b['type'] for b in ir['blocks']] == ['heading', 'text']
    assert all(isinstance(value, str) for value in ir['provenance'].values())
    page = etree.parse(str(out / 'page.page.xml'))
    assert 'provisoires' in page.xpath('string(//*[local-name()="Comments"])')
    assert all('provisional_markdown_structure' in value
               for value in page.xpath('//*[local-name()="TextRegion"]/@custom'))
    assert page.xpath('//*[local-name()="MetadataItem"][@name="reading_certified"]/@value') == ['false']
    assert all((out / name).read_bytes() == data for name, data in original.items())


def test_coverage_uses_entire_markdown_not_only_matched_lines(source):
    image, out, _, alignment, _ = source
    report = export(image, out)
    total = sum(not c.isspace() for c in alignment['plain_text'])
    assert report['text_coverage'] == dict(nonspace_characters=total, exported_nonspace_characters=12, fraction=12/total)
    excluded_text = json.loads((out / 'text-unplaced.json').read_text())
    assert any(item['text'].strip() == 'Texte non placé.' and item['status'] == 'unplaced_text' for item in excluded_text)


def test_overlap_audit_cannot_authorize_changed_annotation_pixels(source):
    image,out,annotations,_,_=source
    write_json(out/'ownership-overlap-permissions.json',dict(
        image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
        annotations_sha256=hashlib.sha256((out/'annotations.json').read_bytes()).hexdigest(),
        basis='zero_shared_owned_ink_pixels',pairs=[]))
    assert export(image,out)['alto_validation']['valid']
    annotations[0]['words'][0]['x0']+=1
    write_json(out/'annotations.json',annotations)
    with pytest.raises(ValueError):export(image,out)


def test_reflow_export_keeps_exact_markdown_source_and_line_view(source):
    image, out, annotations, alignment, _ = source
    markdown = alignment['markdown'].replace('Un mot', 'Un\nmot')
    alignment.update(markdown=markdown, plain_text=markdown_document(markdown)[0],
                     markdown_sha256=hashlib.sha256(markdown.encode()).hexdigest())
    alignment['assignments'][1]['text'] = 'Un\nmot'
    annotations[1]['source_text'] = 'Un\nmot'
    Path(alignment['markdown_artifact']).write_text(markdown, encoding='utf-8')
    write_json(out / 'page-alignment.json', alignment)
    write_json(out / 'annotations.json', annotations)
    report = export(image, out)
    assert report['lines_exported'] == 2 and report['layout_whitespace_normalized_lines'] == 1
    rows = [json.loads(line) for line in (out / 'training.jsonl').read_text().splitlines()]
    assert rows[1]['text'] == 'Un mot' and rows[1]['raw_text'] == 'Un\nmot'
    assert rows[1]['source_text']['original'] == 'Un\nmot'
    spans = rows[1]['source_text']['view_source_spans']
    assert spans[2] == [2, 3]
    page = etree.parse(str(out / 'training.page.xml'))
    assert page.xpath('string(//*[local-name()="TextLine"][@id="L2"]/*[local-name()="TextEquiv"]/*[local-name()="Unicode"])') == 'Un mot'
    assert Path(alignment['markdown_artifact']).read_text() == markdown
    annotations[1]['source_spans'] = [[0, 0]] * len('Un mot')
    write_json(out / 'annotations.json', annotations)
    assert export(image, out)['lines_exported'] == 1
    assert report['source_markdown_sha256'] == alignment['markdown_sha256']


def test_missing_and_ambiguous_olr_groups_keep_words_in_provisional_regions(source):
    image, out, _, _, olr = source
    duplicate = deepcopy(olr['blocks'][0])
    duplicate['id'] = 'B_duplicate'
    olr['blocks'] = [olr['blocks'][0], duplicate]
    write_json(out / 'olr.json', olr)
    report = export(image, out)
    assert report['lines_exported'] == 2
    ir = json.loads((out / 'axel-ir.json').read_text())
    assert all(block['id'].startswith('B_UNGROUPED_') for block in ir['blocks'])
    assert all(meta['uncertain'] for meta in json.loads(ir['provenance']['block_olr']).values())


@pytest.mark.parametrize('mutation,reason', [
    (lambda a: a.update(text='Inventé'), 'tranche Markdown'),
    (lambda a: a['words'][0].update(text='Inventé'), 'mots différents'),
    (lambda a: a['words'][0].update(x1=140), 'mot hors'),
    (lambda a: a['words'][0].update(synthetic=True), 'synthétique'),
])
def test_invalid_line_is_excluded_locally_with_text_retained(source, mutation, reason):
    image, out, annotations, _, _ = source
    mutation(annotations[0])
    write_json(out / 'annotations.json', annotations)
    report = export(image, out)
    assert report['lines_exported'] == 1
    excluded = json.loads((out / 'training-excluded.json').read_text())
    failure = next(item for item in excluded if item['id'] == 'L1')
    assert failure['reason'] == 'export_validation_failed' and reason in failure['detail']
    assert json.loads((out / 'annotations.json').read_text())[0]['text'] == annotations[0]['text']


def test_word_collisions_do_not_yield_overlapping_alto(source):
    image, out, annotations, _, _ = source
    annotations[1]['bbox'] = [5, 5, 100, 50]
    annotations[1]['words'][0].update(y0=10, y1=20)
    write_json(out / 'annotations.json', annotations)
    report = export(image, out)
    assert report['lines_exported'] == 0 and report['alto_validation']['valid']
    assert report['excluded_reasons']['overlapping_source_text_or_word_geometry'] == 2


def test_source_artifact_modification_is_detected(source):
    image, out, _, _, _ = source
    (out / 'transcription.md').write_text('autre texte')
    with pytest.raises(ValueError, match='absent ou modifié'):
        export(image, out)


def test_plain_text_cannot_diverge_from_hashed_markdown(source):
    image, out, _, alignment, _ = source
    alignment['plain_text'] = alignment['plain_text'].replace('Édition', 'Edition')
    write_json(out / 'page-alignment.json', alignment)
    with pytest.raises(ValueError, match='contenu Markdown'):
        export(image, out)


def test_proposed_article_never_becomes_certified_membership(source):
    image, out, _, _, olr = source
    olr['blocks'][0]['article_id'] = 'A_guess'
    olr['articles'] = [dict(id='A_guess', uncertain=True)]
    write_json(out / 'olr.json', olr)
    export(image, out)
    row = json.loads((out / 'training.jsonl').read_text().splitlines()[0])
    assert row['article_id'] is None and row['olr']['proposed_article_id'] == 'A_guess'
    assert not row['olr']['article_certified']


def test_reading_uncertainty_survives_export_even_from_older_geometry_annotations(source):
    image, out, _, _, _ = source
    provenance = json.loads((out / 'provenance.json').read_text())
    provenance['lecture_provenance'] = {'uncertain': True, 'page_reading_uncertain': True}
    write_json(out / 'provenance.json', provenance)
    report = export(image, out)
    assert report['lines_exported'] == 2 and report['page_reading_uncertain']
    assert not report['reading_certified']
    rows = [json.loads(line) for line in (out / 'training.jsonl').read_text().splitlines()]
    assert all(row['page_reading_uncertain'] and not row['reading_certified'] for row in rows)
    ir = json.loads((out / 'axel-ir.json').read_text())
    assert ir['provenance']['page_reading_uncertain'] == 'true'
    assert all(line['page_reading_uncertain'] and not line['reading_certified']
               for line in json.loads(ir['provenance']['line_reading_provenance']).values())


def test_axel_contract_roundtrip_keeps_provenance_without_dropping_extra_fields(source):
    image, out, _, _, _ = source
    export(image, out)
    raw = json.loads((out / 'axel-ir.json').read_text())
    # Contrat externe axel.pipeline.ir : ses dataclasses Block et Line ne
    # préservent pas des champs supplémentaires ; Page.provenance est str→str.
    projected = {key: deepcopy(raw[key]) for key in ('id', 'width', 'height', 'image', 'articles')}
    projected['provenance'] = {str(key): str(value) for key, value in raw['provenance'].items()}
    projected['blocks'] = []
    for block in raw['blocks']:
        target = {key: deepcopy(block[key]) for key in ('id', 'type', 'polygon')}
        target['lines'] = [{key: deepcopy(line[key])
                            for key in ('id', 'polygon', 'baseline', 'text', 'chars', 'article')}
                           for line in block['lines']]
        projected['blocks'].append(target)
    assert projected == raw
    metadata = json.loads(projected['provenance']['block_olr'])
    assert metadata and all(value['uncertain'] for value in metadata.values())
    reading = json.loads(projected['provenance']['line_reading_provenance'])
    assert set(reading) == {'L1', 'L2'} and not any(v['reading_certified'] for v in reading.values())


def test_bad_character_intervals_are_exposed_without_dropping_valid_word_boxes(source):
    image, out, annotations, _, _ = source
    annotations[0]['chars'][0] = [10., 10., .5]
    write_json(out / 'annotations.json', annotations)
    report = export(image, out)
    assert report['lines_exported'] == 2 and report['alto_validation']['valid']
    assert report['character_geometry']['issue_counts']['nonpositive_character_width'] == 1
    assert not report['character_geometry']['certified']
    audit = json.loads((out / 'character-geometry-audit.json').read_text())
    assert not audit['L1']['consistent'] and not audit['L1']['certified']
    ir = json.loads((out / 'axel-ir.json').read_text())
    assert json.loads(ir['provenance']['line_reading_provenance'])['L1']['character_geometry'] == audit['L1']
    rows = [json.loads(line) for line in (out / 'training.jsonl').read_text().splitlines()]
    assert rows[0]['character_geometry'] == audit['L1']
    assert not rows[0]['character_training_eligible']
    assert rows[0]['chars'][0] == annotations[0]['chars'][0]


@pytest.mark.parametrize('mutation,reason', [
    (lambda a: a.update(chars=[]), 'missing_or_inconsistent_character_count'),
    (lambda a: a['chars'][0].__setitem__(1, 999), 'character_interval_outside_page_or_reversed'),
    (lambda a: a['chars'][0].__setitem__(2, 1.1), 'invalid_character_confidence'),
])
def test_unexportable_characters_keep_words_and_original_evidence(source, mutation, reason):
    image, out, annotations, _, _ = source
    mutation(annotations[0])
    write_json(out / 'annotations.json', annotations)
    before = (out / 'annotations.json').read_bytes()
    report = export(image, out)
    assert report['lines_exported'] == 2 and report['alto_validation']['valid']
    assert report['character_geometry']['lines_without_exportable_character_positions'] == 1
    rows = [json.loads(line) for line in (out / 'training.jsonl').read_text().splitlines()]
    assert rows[0]['chars'] == [] and rows[0]['character_position_sources'] == []
    assert not rows[0]['character_training_eligible']
    assert rows[0]['character_geometry']['issue_counts'][reason] == 1
    assert rows[0]['original_character_positions_artifact'] == 'annotations.json'
    ir = json.loads((out / 'axel-ir.json').read_text())
    assert ir['blocks'][0]['lines'][0]['chars'] == []
    assert ir['blocks'][0]['lines'][0]['text'] == annotations[0]['text']
    assert (out / 'annotations.json').read_bytes() == before
