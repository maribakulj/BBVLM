"""A14: one real PERO layout detection, four assignment ablations.

All assignment policies share the exact same CNN outputs. No reference enters
inference/routing. Cached JSON supports CPU replay without loading model weights.
"""
from pathlib import Path
import configparser,hashlib,json,time,collections
import numpy as np
from bbvlm.columns import route_lines_to_columns

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop/spiritualist-v1'
OUT=BASE/'column-lines-a14-0044'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def box(points):
    a=np.asarray(points);return [*a.min(0).tolist(),*a.max(0).tolist()]

def detect():
    import cv2,torch,importlib.metadata
    from pero_ocr.layout_engines.cnn_layout_engine import LayoutEngine
    torch.set_num_threads(4)
    model=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
    image_path=ROOT/'corpora/spiritualist/companion/Spiritualist_Images/0044.png'
    image=cv2.imread(str(image_path));assert image is not None
    config=configparser.ConfigParser();config.read(model/'config_cpu.ini')
    c=config['LAYOUT_PARSER_1']
    params=dict(downsample=c.getint('DOWNSAMPLE'),max_mp=c.getfloat('MAX_MEGAPIXELS'),
        detection_threshold=c.getfloat('DETECTION_THRESHOLD'),adaptive_downsample=True,
        line_end_weight=c.getfloat('LINE_END_WEIGHT'),
        vertical_line_connection_range=c.getint('VERTICAL_LINE_CONNECTION_RANGE'),
        smooth_line_predictions=c.getboolean('SMOOTH_LINE_PREDICTIONS'),paragraph_line_threshold=.3)
    t=time.perf_counter();engine=LayoutEngine(str(model/'ParseNet_296000.pt'),torch.device('cpu'),**params)
    load_seconds=time.perf_counter()-t
    forwards=[];original=engine.parsenet.get_maps
    def counted(img,downsample):
        t=time.perf_counter();result=original(img,downsample)
        forwards.append({'downsample':float(downsample),'seconds':time.perf_counter()-t})
        return result
    engine.parsenet.get_maps=counted
    t=time.perf_counter();p,b,h,polygons=engine.detect(image,rot=0);elapsed=time.perf_counter()-t
    rows=[]
    for i,(baseline,heights,polygon) in enumerate(zip(b,h,polygons)):
        rid='L'+hashlib.sha256(f'a14-0044-{i}'.encode()).hexdigest()[:12]
        rows.append({'id':rid,'bbox':box(polygon),'baseline':np.asarray(baseline).tolist(),
                     'heights':np.asarray(heights).tolist(),'polygon':np.asarray(polygon).tolist()})
    return {'schema':'bbvlm.raw-pero-layout/1','page_bbox':[0,0,image.shape[1],image.shape[0]],
        'reference_inputs':False,'image_sha256':sha(image_path),
        'model_sha256':sha(model/'ParseNet_296000.pt.cpu'),
        'config':params,'versions':{'pero-ocr':importlib.metadata.version('pero-ocr'),'torch':torch.__version__},
        'model_load_seconds':load_seconds,'detection_seconds':elapsed,'cnn_forwards':forwards,
        'regions':[np.asarray(x).tolist() for x in p],'lines':rows}

def assigned(raw,polygons):
    from pero_ocr.core.layout import RegionLayout
    from pero_ocr.layout_engines.layout_helpers import assign_lines_to_regions
    regs=[RegionLayout(f'R{i}',np.asarray(p)) for i,p in enumerate(polygons)]
    b=[np.asarray(l['baseline']) for l in raw['lines']]
    h=[np.asarray(l['heights']) for l in raw['lines']]
    t=[np.asarray(l['polygon']) for l in raw['lines']]
    result=assign_lines_to_regions(b,h,t,regs);rows=[]
    for r in result:
        for l in r.lines:
            ix=int(l.id.rsplit('-l',1)[1])-1
            rows.append({'id':l.id,'raw_id':raw['lines'][ix]['id'],'bbox':box(l.polygon),
                         'polygon':l.polygon.tolist(),'baseline':l.baseline.tolist()})
    return rows

def rectangle(b): return [[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]]

def main():
    OUT.mkdir(parents=True,exist_ok=True);cache=OUT/'raw-detection.json'
    if not cache.exists():cache.write_text(json.dumps(detect(),indent=2)+'\n')
    raw=json.loads(cache.read_text())
    windows=json.loads((BASE/'yolo-columns-a12-0044/proposal.json').read_text())['windows']
    t=time.perf_counter()
    route=route_lines_to_columns(raw['lines'],windows,raw['page_bbox'])
    route_seconds=time.perf_counter()-t
    variants={'native_regions':assigned(raw,raw['regions']),
        'column_core_clipped':assigned(raw,[rectangle(w['core_bbox']) for w in windows]),
        'column_context_clipped':assigned(raw,[rectangle(w['context_bbox']) for w in windows]),
        'whole_line_routing':[dict(l,raw_id=l['id']) for l in raw['lines']]}
    (OUT/'routing.json').write_text(json.dumps(route,indent=2)+'\n')
    (OUT/'variants.json').write_text(json.dumps(variants,indent=2)+'\n')
    # Evaluation-only imports/references start AFTER prediction artifacts exist.
    from lxml import etree as E
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from evaluate_end_to_end import match
    xml=next((ROOT/'corpora/spiritualist/alto_xml/ocr_gt_labelled').glob('0044_*.xml'))
    ns={'a':'http://www.loc.gov/standards/alto/ns-v4#'};refs=[]
    for l in E.parse(str(xml)).findall('.//a:TextLine',ns):
        x,y,w,h=map(float,(l.get(k) for k in ('HPOS','VPOS','WIDTH','HEIGHT')))
        if w>0 and h>0:refs.append({'id':l.get('ID'),'box':[x,y,x+w,y+h]})
    metrics={}
    raw_by_id={l['id']:l for l in raw['lines']}
    for name,rows in variants.items():
        pairs,*_=match(refs,[dict(l,box=l['bbox']) for l in rows])
        groups=collections.defaultdict(list)
        for l in rows:groups[l['raw_id']].append(l)
        losses=[]
        for lid,l in raw_by_id.items():
            original=Polygon(l['polygon']).buffer(0)
            pieces=[Polygon(p['polygon']).buffer(0) for p in groups[lid]]
            covered=unary_union(pieces) if pieces else Polygon()
            losses.append(1-original.intersection(covered).area/original.area if original.area else 0)
        metrics[name]={'output_fragments':len(rows),'missing_raw_lines':sum(not groups[k] for k in raw_by_id),
            'raw_lines_with_multiple_fragments':sum(len(groups[k])>1 for k in raw_by_id),
            'raw_lines_losing_polygon_area_gt_1pct':sum(x>.01 for x in losses),
            'mean_fraction_raw_polygon_lost':float(np.mean(losses)),
            'reference_lines':len(refs),'matched_iou05':len(pairs),
            'reference_line_recall_iou05':len(pairs)/len(refs),
            'prediction_precision_iou05':len(pairs)/len(rows) if rows else 0}
    report={'schema':'bbvlm.column-line-ablation/1','page':'0044',
        'scope':'consumed-page diagnostic; provisional source line rectangles, not certified word geometry',
        'raw_detected_lines':len(raw['lines']),'native_detected_regions':len(raw['regions']),
        'metrics':metrics,'routing':{'seconds':route_seconds,
            'context_not_containing_line':sum(not l['context_contains_line'] for l in route['lines']),
            'ambiguous_owner':sum(l['column_id'] is None for l in route['lines']),
            'review_reasons':dict(collections.Counter(r for l in route['lines'] for r in l['review_reasons']))},
        'cost':{'model_load_seconds':raw['model_load_seconds'],'shared_detection_seconds':raw['detection_seconds'],
                'cnn_forward_count':len(raw['cnn_forwards']),'new_vlm_calls':0,'new_yolo_calls':0},
        'raw_detection_sha256':sha(cache),'reference_xml_sha256':sha(xml),
        'limitations':['same raw detections isolate assignment, not separate independently trained systems',
            'raw polygon loss is an introduced geometric loss, not measured loss of text ink',
            'no new OCR or word alignment in A14; source line boxes provisional',
            'whole-line preservation is an invariant, not proof detection was correct'],
        'accepted_for_project_completion_gate':False}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
