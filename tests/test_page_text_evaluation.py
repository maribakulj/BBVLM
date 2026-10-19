"""L'évaluation de page mesure le texte complet, sans notation spatiale implicite."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from page_text_evaluation import evaluate, markdown_text, score_page_text


@pytest.mark.parametrize(('markdown', 'plain'), [
    ('# Titre\n\nDu **gras**, *italique* et [texte](https://example.test).',
     'Titre\nDu gras, italique et texte.'),
    ('1. Premier\n2. Second\n\n> Citation', 'Premier\nSecond\nCitation'),
    ('Ligne  \nSuite\nFin', 'Ligne\nSuite\nFin'),
    ('| Nom | Prix |\n| --- | --- |\n| Pain | 2,50 |', 'Nom\nPrix\nPain\n2,50'),
    ('![Une **légende** &amp; fin](image.png)', 'Une légende & fin'),
    ('Mot <em>important</em><br>suite &amp; fin.', 'Mot important\nsuite & fin.'),
    ('<div>Texte <strong>fort</strong><br>suite &amp; fin.</div>',
     'Texte fort\nsuite & fin.'),
    ('Du `# code`\n\n```text\n**littéral**\n```', 'Du # code\n**littéral**'),
    (r'\# Titre \*visible\*', '# Titre *visible*'),
])
def test_markdown_removes_presentation_but_preserves_visible_text(markdown, plain):
    actual, info = markdown_text(markdown)
    assert actual == plain
    assert info['unhandled_token_types'] == []
    assert info['unhandled_html_tags'] == []
    assert info['converter_revision'] == 2


def test_unknown_html_is_retained_and_reported_instead_of_silently_lost():
    text, info = markdown_text('Texte <inconnu>visible</inconnu>.')
    assert text == 'Texte <inconnu>visible</inconnu>.'
    assert info['unhandled_html_tags'] == ['inconnu']


def test_whitespace_measure_does_not_also_normalize_typography():
    ref = [{'text': 'L’été'}, {'text': 'est là.'}]
    scores, plain = score_page_text(ref, "L’été\t est  là.")
    assert plain == 'L’été\t est  là.'
    assert scores['text']['strict_NFC']['errors'] > 0
    assert scores['text']['strict_NFC_whitespace']['exact'] is True
    scores, _ = score_page_text(ref, "L'ete est la.")
    assert scores['text']['strict_NFC_whitespace']['exact'] is False
    assert scores['text']['convention_v1']['exact'] is False
    assert scores['text']['convention_v2']['exact'] is True
    assert scores['spatial_coverage'] == 'not_measured_by_whole_page_VT'
    assert scores['complete_pipeline_certified'] is False


def test_hyphenation_convention_is_applied_per_printed_line_only():
    ref = [{'text': 'Inter¬'}, {'text': 'national et a¬b'}]
    scores, _ = score_page_text(ref, 'Inter-\nnational et a¬b')
    assert scores['text']['convention_v1']['exact'] is True
    scores, _ = score_page_text(ref, 'Inter-\nnational et a-b')
    assert scores['text']['convention_v1']['errors'] == 1


@pytest.mark.parametrize('prediction', ['Deux. Un.', 'Un.', 'Un. Deux. Trois.', 'Un, Deux.'])
def test_reordering_omissions_additions_and_punctuation_remain_errors(prediction):
    scores, _ = score_page_text([{'text': 'Un. Deux.'}], prediction)
    for name, value in scores['text'].items():
        if name in ('hipe_ocrepair_2026', 'cer_vt') and prediction == 'Un, Deux.':
            assert value['errors'] == 0
            continue
        assert value['errors'] > 0
        assert value['exact'] is False
        assert value['errors'] == value['substitutions'] + value['deletions'] + value['insertions']


def test_hipe_ignores_case_punctuation_and_ligature_variants_but_keeps_accents():
    scores, _ = score_page_text([{'text': 'L’ŒUVRE : « ÉTÉ » !'}], "l'oeuvre — été.")
    assert scores['text']['hipe_ocrepair_2026']['errors'] == 0
    scores, _ = score_page_text([{'text': 'été'}], 'ete')
    assert scores['text']['hipe_ocrepair_2026']['errors'] == 2
    assert scores['text']['convention_v2']['errors'] == 0


def test_hipe_applies_official_line_break_markers_before_whitespace_collapse():
    scores, _ = score_page_text([{'text': 'inter¬'}, {'text': 'national'}], 'international')
    assert scores['text']['hipe_ocrepair_2026']['errors'] == 0
    scores, _ = score_page_text([{'text': 'inter-'}, {'text': 'national'}], 'international')
    assert scores['text']['hipe_ocrepair_2026']['errors'] == 1


def _fixture_page(tmp_path, page_id, text):
    image = tmp_path / (page_id + '.png')
    image.write_bytes(b'image source hash only')
    reference = tmp_path / (page_id + '.xml')
    reference.write_text('<PcGts><Page><TextRegion id="r"><TextLine id="l">'
                         '<Coords points="0,0 20,0 20,10 0,10"/>'
                         '<TextEquiv><Unicode>' + text + '</Unicode></TextEquiv>'
                         '</TextLine></TextRegion></Page></PcGts>')
    return dict(id=page_id, split='dev', family='synthetic', human_text=True,
                image=str(image), reference=str(reference),
                image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest())


def test_suite_keeps_missing_pages_and_never_certifies_pipeline_from_text(tmp_path):
    rows = [_fixture_page(tmp_path, 'available', 'Titre'),
            _fixture_page(tmp_path, 'missing', 'Suite')]
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(dict(pages=rows, protocol_sha256='original')))
    output = tmp_path / 'out' / 'available'
    output.mkdir(parents=True)
    artifact = output / 'vt.gemini.md'
    artifact.write_text('# Titre')
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    provenance = dict(artifact_sha256=digest, image_sha256=rows[0]['image_sha256'], uncertain=True)
    (output / 'vt-provenance.json').write_text(json.dumps(provenance))

    report = evaluate(manifest, tmp_path / 'out', 'dev')
    assert report['pages'] == 2
    assert report['measured'] == report['missing'] == 1
    assert report['criteria_met'] is False
    measured, missing = report['rows']
    assert measured['metrics']['text']['convention_v2']['exact'] is True
    assert measured['uncertain'] is True
    assert measured['criteria_met'] is False
    assert missing['coverage'] == 0
    assert missing['criteria_met'] is False
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest
    assert (output / 'independent-plain-vt.txt').read_text() == 'Titre'

    artifact.write_text('# Texte modifié')
    with pytest.raises(ValueError, match='VT/provenance modifiée'):
        evaluate(manifest, tmp_path / 'out', 'dev')


def test_cer_vt_ignores_long_s_ligatures_apostrophes_but_keeps_accents():
    scores, _ = score_page_text([{'text': "L’aſſemblée a ﬁni"}], "L'assemblée a fini")
    assert scores['text']['cer_vt']['errors'] == 0
    scores, _ = score_page_text([{'text': 'été'}], 'ete')
    assert scores['text']['cer_vt']['errors'] == 2


def test_cer_vt_joins_line_end_hyphen_like_hipe_join_not_sign():
    scores, _ = score_page_text([{'text': 'commence¬'}, {'text': 'ment'}], 'commence-\nment')
    assert scores['text']['cer_vt']['errors'] == 0
