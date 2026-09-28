"""Bounded Eynollah textline-only recall diagnostic on consumed A69 pages."""
import hashlib, json, math, os, time
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
os.environ["ORT_DISABLE_TELEMETRY_EVENTS"] = "1"
import onnxruntime as ort
ort.disable_telemetry_events()

from evaluate_crop_geometry_a65 import ROOT, polygon

OUT = ROOT / "experiments/loop/next-a72"
MODEL = ROOT / "models/eynollah/modelens_textline_0_1__2_4_16092024.onnx"
MODEL_SHA = "bc6575898c41bba852b3c5367c92add6663ba121e45c325fe770e1cc05241e5c"
PAGES = ["Reichs_Post_Reuter_1700-11-16_0001", "Koelnische_Zeitung_1924_0001"]
TARGET_WIDTH = 2000
PATCH = 672
MARGIN = 67


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_xml(name, expected):
    path=ROOT/'corpora/chronicling-germany/annotations'/f'{name}.xml'
    assert sha(path)==expected[path.name]
    root=ET.fromstring(path.read_bytes()); ns={'p':root.tag.split('}')[0][1:]}
    page=root.find('p:Page',ns); lines=[]
    for region in page.findall('p:TextRegion',ns):
        for element in region.findall('p:TextLine',ns):
            shape=polygon(element,ns)
            if shape is not None: lines.append((element.get('id'),shape))
    return lines,sha(path)


def predict_tiled(session, image):
    """Mirror Eynollah 0.9.2 overlapping-patch probability accumulation."""
    height, width = image.shape[:2]
    mid = PATCH - 2 * MARGIN
    nxf = math.ceil((width - 2.0 * MARGIN) / mid)
    nyf = math.ceil((height - 2.0 * MARGIN) / mid)
    window = 1 / (1 + np.exp(5.0 - 5 * np.arange(2 * MARGIN) / MARGIN))
    prediction = np.zeros((height, width, 3), dtype=np.float32)
    input_name = session.get_inputs()[0].name
    tiles = 0
    for i in range(nxf):
        for j in range(nyf):
            xd, yd = i * mid, j * mid
            xu, yu = xd + PATCH, yd + PATCH
            xs = max(0, xu - width); ys = max(0, yu - height)
            if xs: xu, xd = width, width - PATCH
            if ys: yu, yd = height, height - PATCH
            tile = image[yd:yu, xd:xu].astype(np.float32) / 255.0
            probs = session.run(None, {input_name: tile[np.newaxis]})[0][0]
            ay = np.ones(PATCH - ys, dtype=np.float32)
            ax = np.ones(PATCH - xs, dtype=np.float32)
            if MARGIN and j > 0: ay[:2 * MARGIN] = window
            if MARGIN and j < nyf - 1: ay[-2 * MARGIN:] = 1 - window
            if MARGIN and i > 0: ax[:2 * MARGIN] = window
            if MARGIN and i < nxf - 1: ax[-2 * MARGIN:] = 1 - window
            part = probs[ys:, xs:] * ay[:, None, None] * ax[None, :, None]
            prediction[yd+ys:yu, xd+xs:xu] += part
            tiles += 1
    return np.argmax(prediction, axis=2).astype(np.uint8) == 1, tiles


def polygon_coverage(mask, geom, sx, sy):
    pts = np.rint(np.asarray(geom.exterior.coords) * np.array([sx, sy])).astype(np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    x0=max(0,x); y0=max(0,y); x1=min(mask.shape[1],x+w); y1=min(mask.shape[0],y+h)
    if x1 <= x0 or y1 <= y0: return 0.0
    local = np.zeros((y1-y0, x1-x0), dtype=np.uint8)
    shifted = pts - np.array([x0, y0])
    cv2.fillPoly(local, [shifted], 1)
    denom = int(local.sum())
    return float(np.logical_and(local, mask[y0:y1, x0:x1]).sum()/denom) if denom else 0.0


def main():
    started=time.perf_counter(); assert sha(MODEL)==MODEL_SHA
    assets=json.loads((ROOT/'experiments/loop/next-a69/assets.json').read_text())['images']
    asset={r['page']:r for r in assets}; a70=json.loads((ROOT/'experiments/loop/next-a70/report-v2.json').read_text())
    zero={(r['page'],r['line_id']) for r in a70['rows'] if not r['contributors']}
    opts=ort.SessionOptions(); opts.intra_op_num_threads=4; opts.inter_op_num_threads=1
    session=ort.InferenceSession(str(MODEL),sess_options=opts,providers=['CPUExecutionProvider'])
    masks={}; image_audit={}
    for page in PAGES:
        path=ROOT/asset[page]['path']; assert sha(path)==asset[page]['sha256']
        image=cv2.imread(str(path),cv2.IMREAD_COLOR); assert image is not None
        h,w=image.shape[:2]; nh=round(h*TARGET_WIDTH/w)
        resized=cv2.resize(image,(TARGET_WIDTH,nh),interpolation=cv2.INTER_AREA)
        t=time.perf_counter(); mask,tiles=predict_tiled(session,resized); elapsed=time.perf_counter()-t
        out=OUT/f'{page}-textline-mask.png'; cv2.imwrite(str(out),mask.astype(np.uint8)*255)
        masks[page]=(mask,TARGET_WIDTH/w,nh/h)
        image_audit[page]={'image_sha256':sha(path),'shape':[h,w],'resized_shape':[nh,TARGET_WIDTH],
                           'mask_sha256':sha(out),'tiles':tiles,'seconds':elapsed,
                           'positive_pixels':int(mask.sum())}
    # Only after all image-only masks are sealed may reference geometry be opened.
    expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']}
    rows=[]
    for page in PAGES:
        lines,xh=parse_xml(page,expected); mask,sx,sy=masks[page]
        for line_id,geom in lines:
            cov=polygon_coverage(mask,geom,sx,sy)
            rows.append({'page':page,'line_id':line_id,'coverage':cov,'hit_ge1pct':cov>=.01,
                         'a70_zero_contributor':(page,line_id) in zero,'xml_sha256':xh})
    target=[r for r in rows if r['a70_zero_contributor']]; all_hits=sum(r['hit_ge1pct'] for r in rows)
    target_hits=sum(r['hit_ge1pct'] for r in target); ratio=target_hits/len(target) if target else 0.0
    report={'status':'consumed_textline_stage_diagnostic','implementation':'Eynollah 0.9.2 textline ONNX only',
            'model_sha256':MODEL_SHA,'pages':PAGES,'image_audit':image_audit,'all_lines':len(rows),
            'all_lines_hit_ge1pct':all_hits,'zero_contributor_lines':len(target),
            'zero_contributor_hit_ge1pct':target_hits,'zero_contributor_hit_ratio':ratio,
            'local_gate_ge50pct':ratio>=.5,'rows':rows,'detector_forwards':0,'vlm_calls':0,'ocr_calls':0,
            'test_pages_opened':0,'seconds':time.perf_counter()-started,'all_scientific_gates_passed':False,
            'limitations':['Consumed pages and oracle-selected residuals.','A 1% mask hit is line recall, not an ALTO box.',
                           'PAGE line polygons and a single threshold are not perfect truth.']}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('all_lines','all_lines_hit_ge1pct','zero_contributor_lines','zero_contributor_hit_ge1pct','zero_contributor_hit_ratio','local_gate_ge50pct','seconds')},indent=2))


if __name__=='__main__': main()
