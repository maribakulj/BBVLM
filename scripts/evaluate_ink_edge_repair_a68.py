"""A68 image-only edge repair; persist candidates before opening XML truth."""
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
from PIL import Image, ImageDraw
from shapely.geometry import box
from shapely.ops import unary_union

from bbvlm.refine import extend_crop_edges_to_connected_ink
from evaluate_crop_geometry_a65 import polygon
from fetch_crop_pilot_a66 import NAMES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/loop/next-a68'
A66 = ROOT / 'experiments/loop/next-a66'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixed_pad(native, pad, width, height):
    x0, y0, x1, y1 = native
    return [max(0, x0-pad), max(0, y0-pad),
            min(width, x1+pad), min(height, y1+pad)]


def load_annotations(expected):
    annotations, hashes = {}, {}
    for page in NAMES:
        path = ROOT/'corpora/chronicling-germany/annotations'/f'{page}.xml'
        hashes[page] = sha(path)
        assert hashes[page] == expected[path.name]
        root = ET.fromstring(path.read_bytes())
        ns = {'p': root.tag.split('}')[0][1:]}
        page_el = root.find('p:Page', ns)
        regions, lines = [], []
        for region_el in page_el.findall('p:TextRegion', ns):
            region = polygon(region_el, ns)
            if region is not None:
                regions.append(region)
            for line_el in region_el.findall('p:TextLine', ns):
                line = polygon(line_el, ns)
                if line is not None:
                    lines.append((line_el.get('id'), line))
        annotations[page] = (regions, lines)
    return annotations, hashes


def score(candidates, annotations):
    detail = []
    for page in NAMES:
        _, lines = annotations[page]
        for line_id, line in lines:
            row = {'page': page, 'line_id': line_id}
            for policy in ('native', 'fixed', 'ink_crossing'):
                shapes = [box(*r['bbox']) for r in candidates[page][policy]]
                row[policy] = max(
                    (line.intersection(crop).area/line.area for crop in shapes),
                    default=0.0)
            detail.append(row)

    summary = {}
    for policy in ('native', 'fixed', 'ink_crossing'):
        values = [r[policy] for r in detail]
        record = {
            'lines': len(values),
            'mean_best_coverage': sum(values)/len(values),
            'lt50': sum(v < .5 for v in values),
            'lt95': sum(v < .95 for v in values),
            'improved_lines': sum(r[policy] > r['native']+1e-12 for r in detail),
            'regressed_lines': sum(r[policy]+1e-12 < r['native'] for r in detail),
            'added_area': 0.0, 'foreign_added_area': 0.0,
            'foreign_fraction_of_added': 0.0,
            'foreign_added_boxes_gt1pct': 0,
        }
        if policy != 'native':
            for page in NAMES:
                regions, _ = annotations[page]
                for native_row, candidate_row in zip(
                        candidates[page]['native'], candidates[page][policy]):
                    native_shape = box(*native_row['bbox'])
                    candidate_shape = box(*candidate_row['bbox'])
                    added = candidate_shape.difference(native_shape)
                    record['added_area'] += added.area
                    intersections = [native_shape.intersection(r).area for r in regions]
                    if not intersections:
                        continue
                    dominant = max(range(len(regions)), key=lambda i: intersections[i])
                    others = unary_union([r for i, r in enumerate(regions) if i != dominant])
                    foreign = added.intersection(others).area
                    record['foreign_added_area'] += foreign
                    if added.area and foreign/added.area > .01:
                        record['foreign_added_boxes_gt1pct'] += 1
            if record['added_area']:
                record['foreign_fraction_of_added'] = (
                    record['foreign_added_area']/record['added_area'])
        summary[policy] = record
    return summary, detail


def nearest_index(rows, target):
    return min(range(len(rows)), key=lambda i: sum(
        abs(a-b) for a,b in zip(rows[i]['bbox'], target)))


def make_contact_sheet(candidates):
    prior = json.loads((ROOT/'experiments/loop/next-a67/private-map.json').read_text())
    selected = []
    for wanted in ('K482', 'K951'):
        item = next(r for r in prior if r['id'] == wanted)
        idx = nearest_index(candidates[item['page']]['native'], item['box']['bbox'])
        selected.append((item['page'], idx, wanted))
    largest = max(
        ((box(*r['bbox']).area-box(*n['bbox']).area, page, i)
         for page in NAMES
         for i,(n,r) in enumerate(zip(candidates[page]['native'],
                                      candidates[page]['ink_crossing']))),
        default=(0,NAMES[0],0))
    selected.append((largest[1], largest[2], 'largest-expansion'))
    tiles = []
    for page, index, label in selected:
        image = Image.open(ROOT/'corpora/chronicling-germany/images'/f'{page}.jpg').convert('RGB')
        boxes = {p:candidates[page][p][index]['bbox']
                 for p in ('native','fixed','ink_crossing')}
        x0=max(0,min(b[0] for b in boxes.values())-20)
        y0=max(0,min(b[1] for b in boxes.values())-20)
        x1=min(image.width,max(b[2] for b in boxes.values())+20)
        y1=min(image.height,max(b[3] for b in boxes.values())+20)
        tile=image.crop((x0,y0,x1,y1)); draw=ImageDraw.Draw(tile)
        for name,color in [('native','red'),('fixed','blue'),('ink_crossing','lime')]:
            b=boxes[name]
            draw.rectangle((b[0]-x0,b[1]-y0,b[2]-x0,b[3]-y0),outline=color,width=3)
        draw.text((4,4),label,fill='yellow',stroke_width=1,stroke_fill='black')
        tiles.append(tile)
    width=max(t.width for t in tiles)
    canvas=Image.new('RGB',(width,sum(t.height for t in tiles)),'white')
    y=0
    for tile in tiles:
        canvas.paste(tile,(0,y)); y+=tile.height
    canvas.save(OUT/'audit-contact-sheet.png')


def main():
    started=time.perf_counter()
    predictions=json.loads((A66/'predictions.json').read_text())
    assets=json.loads((A66/'assets-v2.json').read_text())
    source_hashes={r['page']:r['sha256'] for r in assets['images']}
    candidates={}
    for page in NAMES:
        image_path=ROOT/'corpora/chronicling-germany/images'/f'{page}.jpg'
        assert sha(image_path)==source_hashes[page]
        gray=cv2.imread(str(image_path),cv2.IMREAD_GRAYSCALE)
        assert gray is not None
        height,width=gray.shape
        pad=max(4,round(.003*min(height,width)))
        prediction=next(r for r in predictions if r['page']==page and r['imgsz']==1024)
        rows=[r for r in prediction['boxes'] if r['class_id'] not in (3,5)]
        native,fixed,ink=[],[],[]
        for row in rows:
            b=row['bbox']
            nb=[max(0,math.floor(b[0])),max(0,math.floor(b[1])),
                min(width,math.ceil(b[2])),min(height,math.ceil(b[3]))]
            cb,audit=extend_crop_edges_to_connected_ink(
                gray,nb,max_pad=pad,min_area=3,min_side_pixels=2)
            common={'class_id':row['class_id'],'class_name':row['class_name'],
                    'confidence':row['confidence']}
            native.append({'bbox':nb,**common})
            fixed.append({'bbox':fixed_pad(nb,pad,width,height),**common})
            ink.append({'bbox':cb,'edge_audit':audit,**common})
        candidates[page]={'shape':[height,width],'max_pad':pad,
                          'native':native,'fixed':fixed,'ink_crossing':ink}
    payload={'schema':'bbvlm.a68.candidates/1',
             'status':'image_only_candidates_written_before_xml_scoring',
             'parameters':{'pad_formula':'max(4, round(0.003 * min(H,W)))',
                           'connectivity':8,'min_area':3,'inner_strip_pixels':2,
                           'min_side_pixels':2,'binarization':'crop_context_otsu'},
             'source_sha256':source_hashes,'pages':candidates}
    candidate_path=OUT/'candidates.json'
    candidate_path.write_text(json.dumps(payload,indent=2)+'\n')
    candidate_hash=sha(candidate_path)

    expected={r['file']:r['sha256'] for r in json.loads(
        (ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
    annotations,xml_hashes=load_annotations(expected)
    summary,detail=score(candidates,annotations)
    make_contact_sheet(candidates)
    changed=sum(bool(r['edge_audit']['changed_sides'])
                for page in candidates.values() for r in page['ink_crossing'])
    report={'status':'consumed_development_not_independent_validation',
            'candidate_sha256_before_scoring':candidate_hash,
            'parameters':payload['parameters'],'summary':summary,
            'image_guided_boxes_changed':changed,
            'boxes':sum(len(p['native']) for p in candidates.values()),
            'line_detail':detail,'xml_sha256':xml_hashes,
            'pages':len(NAMES),'vlm_calls':0,'ocr_calls':0,'test_pages_opened':0,
            'seconds':time.perf_counter()-started,'all_scientific_gates_passed':False,
            'limitations':['Five Validation pages are consumed development data.',
                           'Line/region polygon area is not perfect ALTO box truth.',
                           'Connected foreground does not prove semantic ownership.',
                           'No OCR, OLR, metadata or retrieval gate was tested.']}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'summary':summary,'changed':changed},indent=2))


if __name__=='__main__':
    main()
