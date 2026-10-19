from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from page_alignment import align_page
from page_line_split import split_crossing_lines, assign_regions


def line(lid, text, bbox):
    return dict(id=lid, bbox=list(bbox), auxiliary_text=text, source='kraken-blla/full')


def two_regions(left_lines, right_lines):
    left, right = '\n'.join(left_lines), '\n'.join(right_lines)
    markdown = left+'\n\n'+right
    spans = {'A': [0, len(left)], 'B': [len(left)+2, len(markdown)]}
    return markdown, spans


BODY = ['Une ligne ordinaire de colonne {}', 'La chambre des mises en accusation',
        'une autre ligne assez longue {} ici', 'La chambre des mises en accusation',
        'et encore une phrase de colonne {}', 'puis la suite du texte imprimé {}',
        'avant la toute dernière ligne {} ok']


def column(name, x0):
    texts = [t.format(name) for t in BODY]
    rows = [line(f'{name}{k}', t, (x0, 100+40*k, x0+len(t)*10, 130+40*k)) for k, t in enumerate(texts)]
    return texts, rows


def test_repeated_lines_are_resolved_by_region_and_order_without_changing_text():
    texts_a, rows_a = column('A', 10)
    texts_b, rows_b = column('B', 500)
    markdown, spans = two_regions(texts_a, texts_b)
    rows = rows_a+rows_b
    regions = {r['id']: r['id'][0] for r in rows}
    plain = align_page(markdown, rows, image_size=(1000, 1000))
    assert plain['status_counts'].get('ambiguous_text_match', 0) >= 4
    result = align_page(markdown, rows, image_size=(1000, 1000), line_regions=regions, region_spans=spans)
    assert result['text_coverage']['fraction'] == 1
    by = {a['line_id']: a for a in result['assignments']}
    # Chaque occurrence répétée reçoit SA ligne de texte, dans l'ordre de la région.
    assert by['A1']['start'] < by['A3']['start'] < by['B1']['start'] < by['B3']['start']
    assert all(by[k]['text'] == 'La chambre des mises en accusation' for k in ('A1', 'A3', 'B1', 'B3'))
    assert result['criteria']['regional_constraint']


def unique_column(name, x0, n=8):
    pool = ['Le ministre fut reçu sur le quai du port', 'par le directeur de la Compagnie générale',
            'Puis ce fut la visite des salons du navire', 'des magnifiques cabines dotées de confort',
            'Le déjeuner fut servi dans la grande salle', 'Toutes les personnalités qui entouraient',
            'M. Du Pasquier salua le ministre au nom', 'du port autonome et demanda son appui']
    texts = pool[:n]
    rows = [line(f'{name}{k}', t, (x0, 100+40*k, x0+len(t)*10, 130+40*k)) for k, t in enumerate(texts)]
    return texts, rows


def test_unreadable_line_between_anchors_takes_the_only_text_line_of_its_gap():
    texts, rows = unique_column('A', 10)
    rows[2]['auxiliary_text'] = 's tnse Mfannien de degprggrmse'  # lecture CTC illisible
    markdown, spans = two_regions(texts, ['autre région'])
    result = align_page(markdown, rows, image_size=(1000, 1000),
                        line_regions={r['id']: 'A' for r in rows}, region_spans=spans)
    by = {a['line_id']: a for a in result['assignments']}
    assert by['A2']['text'] == texts[2]
    assert by['A2']['regional_order_support']['previous_anchor'] == 'A1'
    assert by['A2']['regional_order_support']['next_anchor'] == 'A3'


def test_gap_filling_refuses_a_width_incompatible_with_the_text():
    texts, rows = unique_column('A', 10)
    rows[2]['auxiliary_text'] = '~'
    rows[2]['bbox'] = [10, 180, 40, 210]  # 30 px pour 34 caractères : pas cette ligne
    markdown, spans = two_regions(texts, ['autre région'])
    result = align_page(markdown, rows, image_size=(1000, 1000),
                        line_regions={r['id']: 'A' for r in rows}, region_spans=spans)
    assert 'A2' not in {a['line_id'] for a in result['assignments']}


def _page_with_gutter(rule):
    gray = np.full((200, 1000), 255, np.uint8)
    for x in range(20, 460, 30):       # « mots » de la colonne gauche
        gray[60:85, x:x+18] = 0
    for x in range(520, 980, 30):      # colonne droite
        gray[60:85, x:x+18] = 0
    if rule:
        gray[50:95, 488:491] = 0       # filet vertical dans la gouttière
    return gray


def _plan():
    return dict(parameters=dict(line_height=30., column_starts=[20., 520.]),
                regions=[dict(id='A', bbox=[10, 0, 480, 200]), dict(id='B', bbox=[505, 0, 990, 200])])


def test_line_crossing_a_gutter_is_cut_on_observed_white_and_keeps_its_pixels():
    row = dict(id='L1', bbox=[20, 55, 978, 90], detector_bbox=[20, 55, 978, 90],
               baseline=[[20, 85], [978, 85]], polygon=[[20, 55], [978, 55], [978, 90], [20, 90]],
               source='kraken-blla/full')
    for rule in (False, True):
        lines, log = split_crossing_lines(_page_with_gutter(rule), [row], _plan())
        assert [l['id'] for l in lines] == ['L1_S1', 'L1_S2'], log
        a, b = lines
        assert a['bbox'][2] <= 488 and b['bbox'][0] >= 491
        assert a['bbox'][0] == 20 and b['bbox'][2] == 978
        assert a['split_from'] == b['split_from'] == 'L1'
        assert assign_regions(lines, _plan()) == {'L1_S1': 'A', 'L1_S2': 'B'}


def test_line_inside_one_column_is_never_cut():
    row = dict(id='L1', bbox=[20, 55, 460, 90], detector_bbox=[20, 55, 460, 90], source='kraken-blla/full')
    lines, log = split_crossing_lines(_page_with_gutter(True), [row], _plan())
    assert lines == [row] and log == []


def test_table_row_cells_receive_the_rest_of_the_gemini_row_and_repeated_headers_follow_position():
    texts, rows = unique_column('A', 10)
    table = ['Jeudi  Vendr.', 'Pacific Central.......... 113 1/2  114 ..',
             'Jeudi  Vendr.', 'Lake Shore et Michigan.... 102 5/8  103 1/8']
    lines_text = texts[:4]+table+texts[4:]
    markdown = '\n'.join(lines_text)
    spans = {'A': [0, len(markdown)]}
    y = lambda k: (100+40*k, 130+40*k)
    cells = [line('H1', 'Jeudi Vendr.', (300, *y(4)[:1], 420, y(4)[1])),
             line('N1', 'Pacific Central...........', (10, *y(5)[:1], 270, y(5)[1])),
             line('C1', '113 12', (300, *y(5)[:1], 370, y(5)[1])),
             line('D1', '114..', (390, *y(5)[:1], 440, y(5)[1])),
             line('H2', 'Jeudi Vendr.', (300, *y(6)[:1], 420, y(6)[1])),
             line('N2', 'Lalse Shore et Michigan....', (10, *y(7)[:1], 270, y(7)[1])),
             line('C2', '102 58', (300, *y(7)[:1], 370, y(7)[1])),
             line('D2', '103 18', (390, *y(7)[:1], 450, y(7)[1]))]
    body = [dict(r, id=f'P{k}', bbox=[r['bbox'][0], y(k if k < 4 else k+4)[0], r['bbox'][2], y(k if k < 4 else k+4)[1]])
            for k, r in enumerate(rows)]
    allrows = body+cells
    regions = {r['id']: 'A' for r in allrows}
    result = align_page(markdown, allrows, image_size=(1000, 1000), line_regions=regions, region_spans=spans)
    by = {a['line_id']: a['text'] for a in result['assignments']}
    assert by['N1'] == 'Pacific Central..........' and by['C1'] == '113 1/2' and by['D1'] == '114 ..'
    assert by['C2'] == '102 5/8' and by['D2'] == '103 1/8'
    starts = {a['line_id']: a['start'] for a in result['assignments']}
    assert starts['H1'] < starts['N1'] < starts['H2'] < starts['N2']
    assert ''.join(s['text'] for s in result['segments']) == result['plain_text']
