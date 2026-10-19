from copy import deepcopy
from pathlib import Path
import sys

from lxml import etree
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import alto
from page_collision_export import diagnostic_alto, pair_claim, schema_check, schema_shape_contract


def observed():
    return [dict(id='A', text='pas', status='collision', training_eligible=False,
                 words=[dict(text='pas', x0=10, y0=10, x1=35, y1=25)]),
            dict(id='B', text='de', status='collision', training_eligible=False,
                 words=[dict(text='de', x0=34, y0=24, x1=55, y1=40)]),
            dict(id='C', text='non placé', status='texte_absent', training_eligible=False)]


def test_unchanged_overlapping_rectangles_are_xsd_valid_and_production_invalid():
    annotations = observed()
    before = deepcopy(annotations)
    xml = diagnostic_alto(annotations, 100, 100, 'source.png')
    assert annotations == before
    assert schema_check(xml)['valid']
    with pytest.raises(ValueError, match='Mots ALTO superposés'):
        alto.validate(xml)
    tree = etree.fromstring(xml)
    words = tree.findall('.//{%s}String' % alto.NS)
    assert [w.get('CONTENT') for w in words] == ['pas', 'de']
    assert all(w.get('TAGREFS') == 'DIAGNOSTIC_UNCERTIFIED' for w in words)
    assert [tuple(float(w.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT')) for w in words] == [(10, 10, 26, 16), (34, 24, 22, 17)]


def test_single_string_polygon_is_supported_but_does_not_override_rectangle_guard():
    tree = etree.fromstring(diagnostic_alto(observed(), 100, 100, 'source.png'))
    first = tree.find('.//{%s}String' % alto.NS)
    shape = etree.SubElement(first, '{%s}Shape' % alto.NS)
    etree.SubElement(shape, '{%s}Polygon' % alto.NS, POINTS='10,10 35,10 35,25 10,25')
    xml = etree.tostring(tree)
    assert schema_check(xml)['valid']
    with pytest.raises(ValueError, match='Mots ALTO superposés'):
        alto.validate(xml)
    second = etree.SubElement(shape, '{%s}Polygon' % alto.NS, POINTS='11,11 12,11 12,12')
    assert not schema_check(etree.tostring(tree))['valid']
    shape.remove(second)
    etree.SubElement(first, '{%s}Shape' % alto.NS)
    assert not schema_check(etree.tostring(tree))['valid']
    contract = schema_shape_contract()
    assert contract['string_shape_max_occurs'] == 1 and not contract['multipolygon_declared']


def test_disjoint_masks_with_foreign_ink_are_not_labeled_certified():
    pair = dict(word_profiles=['A:0', 'B:0'], support_kind='disjoint_mask_pixels', raw_dark_pixels=4,
                foreign_ink_anywhere_in_words=[5, 0])
    profiles = {'A:0': dict(pixel_causes={'proved_own_ink': 100, 'proved_foreign_ink': 5}),
                'B:0': dict(pixel_causes={'proved_own_ink': 80})}
    claim = pair_claim(pair, profiles)
    assert claim['whole_word_masks_only_proved_own_ink'] == [False, True]
    assert claim['foreign_ink_in_either_word']
    assert not claim['raw_intersection_has_no_dark_pixel_at_160']
    assert not claim['acceptance_changed'] and not claim['glyph_completeness_certified']
