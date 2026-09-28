"""Oracle geometry ablation; never infer OCR, read transcripts, or repair GT."""
import collections
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from shapely import __version__ as shapely_version
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/loop/next-a65'


def polygon(element, ns):
    coords = element.find('p:Coords', ns)
    points = [] if coords is None else [tuple(map(float, p.split(',')))
                                      for p in coords.get('points', '').split()]
    if len(points) < 3:
        return None
    shape = Polygon(points)
    return shape if shape.is_valid and shape.area > 0 else None


def missing(line, mask):
    return max(0.0, min(1.0, line.difference(mask).area / line.area))


def self_test():
    parent = box(0, 0, 10, 10)
    assert missing(box(1, 1, 2, 2), parent) == 0
    assert abs(missing(box(9, 1, 11, 2), parent) - .5) < 1e-12
    concave = Polygon([(0,0),(10,0),(10,2),(2,2),(2,10),(0,10)])
    neighbour = box(3,3,8,8)
    assert concave.intersection(neighbour).area == 0
    assert box(*concave.bounds).difference(concave).intersection(neighbour).area == 25
    assert Polygon([(0,0),(1,1),(0,1),(1,0)]).is_valid is False


def main():
    started = time.perf_counter()
    self_test()
    split = json.loads((ROOT/'experiments/loop/chronicling-a58/official_split.json').read_text())
    names = sorted(split['Validation'])
    assert len(names) == len(set(names)) == 50
    assert not set(names).intersection(split['Test'])
    expected = {r['file']:r['sha256'] for r in json.loads(
        (ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
    page_rows, region_rows, line_rows, fingerprints = [], [], [], {}
    invalid = collections.Counter()
    for name in names:
        path = ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml'
        raw = path.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        assert sha == expected[path.name], f'changed source: {name}'
        fingerprints[name] = sha
        root = ET.fromstring(raw); ns = {'p':root.tag.split('}')[0][1:]}
        page = root.find('p:Page', ns)
        regions = []
        for element in page.findall('p:TextRegion', ns):
            shape = polygon(element, ns)
            if shape is None:
                invalid['region'] += 1
                invalid['lines_with_invalid_parent'] += len(element.findall('p:TextLine',ns))
            else:
                regions.append((element, shape))
        union = unary_union([shape for _,shape in regions])
        local_lines = []
        local_regions = []
        for index,(element,shape) in enumerate(regions):
            envelope = box(*shape.bounds)
            others = unary_union([s for i,(_,s) in enumerate(regions) if i != index])
            foreign = envelope.difference(shape).intersection(others).area
            rr = {'page':name, 'region_id':element.get('id'),
                  'polygon_bbox_iou':shape.area/envelope.area,
                  'added_area':envelope.area-shape.area,
                  'foreign_area':foreign, 'foreign_fraction':foreign/envelope.area}
            local_regions.append(rr)
            for line_element in element.findall('p:TextLine', ns):
                line = polygon(line_element,ns)
                if line is None:
                    invalid['line'] += 1; continue
                row = {'page':name, 'region_id':element.get('id'),
                       'line_id':line_element.get('id'), 'area':line.area,
                       'parent_polygon':missing(line,shape),
                       'parent_rectangle':missing(line,envelope),
                       'all_text_polygons':missing(line,union)}
                assert row['parent_rectangle'] <= row['parent_polygon'] + 1e-9
                assert row['all_text_polygons'] <= row['parent_polygon'] + 1e-9
                local_lines.append(row)
        region_rows.extend(local_regions); line_rows.extend(local_lines)
        page_rows.append({'page':name, 'valid_regions':len(local_regions),
                          'valid_lines':len(local_lines),
                          'polygon_clip_gt_1pct':sum(r['parent_polygon']>.01 for r in local_lines),
                          'rectangle_foreign_gt_1pct':sum(r['foreign_fraction']>.01 for r in local_regions)})
    line_summary = {}
    for method in ('parent_polygon','parent_rectangle','all_text_polygons'):
        line_summary[method] = {'lines':len(line_rows),
            'missing_gt_1pct':sum(r[method]>.01 for r in line_rows),
            'missing_gt_5pct':sum(r[method]>.05 for r in line_rows),
            'area_weighted_missing':sum(r[method]*r['area'] for r in line_rows)/sum(r['area'] for r in line_rows)}
    report = {'schema':'bbvlm.crop-geometry-a65/1', 'status':'completed_oracle_structural_ablation',
        'pages':len(names), 'test_pages_opened':0, 'transcription_values_read':False,
        'input_sha256':fingerprints, 'invalid_geometry':dict(invalid),
        'line_summary':line_summary,
        'region_summary':{'valid_regions':len(region_rows),
            'mean_polygon_bbox_iou':sum(r['polygon_bbox_iou'] for r in region_rows)/len(region_rows),
            'bbox_iou_below_80':sum(r['polygon_bbox_iou']<.8 for r in region_rows),
            'foreign_gt_1pct':sum(r['foreign_fraction']>.01 for r in region_rows)},
        'by_page':page_rows, 'regions':region_rows, 'lines':line_rows,
        'cost':{'seconds':time.perf_counter()-started,'model_forwards':0,'shapely':shapely_version},
        'synthetic_tests_passed':4,'global_completion':False,
        'limitations':['Oracle annotations, not predicted crops or detector accuracy.',
            'Area loss is not ink loss or CER.', 'Line polygons selectively corrected; no perfect line GT.',
            'No independent OLR or article reference.', 'Invalid polygons quarantined without silent repair.']}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','pages','invalid_geometry','line_summary','region_summary','cost']},indent=2))


if __name__ == '__main__':
    main()
