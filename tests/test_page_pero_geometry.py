from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_pero_geometry import geometry_rows, geometric_neighbors, reciprocal_matches


def test_reference_text_never_enters_geometric_comparison():
    rows = geometry_rows([dict(id='A', text='unchanged', auxiliary_text='ignored',
        bbox=[10, 10, 100, 30], baseline=[[10, 25], [100, 25]], polygon=[], source='detector')])
    assert 'text' not in rows[0] and 'auxiliary_text' not in rows[0]
    candidates = [dict(id='P1', baseline=[[10, 27], [100, 27]]),
                  dict(id='P2', baseline=[[500, 25], [590, 25]])]
    result = geometric_neighbors(rows, candidates)[0]
    assert result['nearest']['id'] == 'P1'
    assert result['nearest']['baseline_distance_px'] == 2
    assert result['candidates_within_half_reference_height'] == 1
    assert not result['correspondence_certified']


def test_missing_or_multiple_neighbors_are_not_silently_certified():
    ref = [dict(id='A', bbox=[10, 10, 100, 30], baseline=[[10, 25], [100, 25]])]
    assert geometric_neighbors(ref, [dict(id='Q', baseline=[[95, 25], [180, 25]])])[0]['nearest'] is None
    matches = geometric_neighbors(ref, [dict(id='P1', baseline=[[10, 26], [100, 26]]),
                                       dict(id='P2', baseline=[[10, 27], [100, 27]])])[0]
    assert matches['candidates_within_half_reference_height'] == 2
    assert not matches['correspondence_certified']


def test_two_references_cannot_claim_one_unique_pero_line():
    reference = [dict(id=lid, bbox=[10, y-10, 100, y+10], baseline=[[10, y], [100, y]])
                 for lid, y in [('A', 25), ('B', 27)]]
    candidate = [dict(id='P', bbox=[10, 15, 100, 40], baseline=[[10, 26], [100, 26]])]
    rows = reciprocal_matches(reference, candidate)
    assert all(r['reciprocal_status'] == 'nonreciprocal_or_ambiguous_geometry_neighbor' for r in rows)
    assert all(r['unique_reciprocal_neighbor'] is None for r in rows)
    assert reciprocal_matches(reference[:1], candidate)[0]['unique_reciprocal_neighbor'] == 'P'
