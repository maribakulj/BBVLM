#!/usr/bin/env python3
"""Sealed A26 evaluator for BnF/IMPACT CTC+raw-Otsu word boxes."""
from __future__ import annotations
from collections import defaultdict
import configparser,hashlib,json,time,unicodedata
from pathlib import Path
import cv2,numpy as np
from lxml import etree as E

import evaluate_french_holdout_a25 as core
from bbvlm.ocr_conventions import private_use_inventory
from bbvlm.pero import bind_native_alto_ids,load_cache,realign,save_cache

ROOT=Path(__file__).resolve().parents[1]; EXP=ROOT/'experiments/loop/bnf-impact-a26'
OPEN=EXP/'opened'; OUT=EXP/'output'
MODEL=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
MODEL_SHA='cb38dd0792c7145b8ba4dd64df255980e4633f4ca1d406f7f230b9c174c0c70d'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(node): return ''.join(node.xpath('./*[local-name()="TextEquiv"][1]/*[local-name()="Unicode"]/text()'))

def load_rows(split):
    rows=[]; images={}; page_meta={}
    for page in split['pages']:
        xp=OPEN/page['xml']; ip=OPEN/page['image']; tree=E.parse(str(xp),E.XMLParser(resolve_entities=False,no_network=True))
        root=tree.getroot(); page_node=tree.xpath('//*[local-name()="Page"]')[0]
        pid=page['page']; images[pid]=ip
        values=[]; mismatches=[]
        for line in tree.xpath('//*[local-name()="TextLine"]'):
            coords=line.xpath('./*[local-name()="Coords"]'); words=line.xpath('./*[local-name()="Word"]')
            line_text=text(line)
            if not coords or not words or not line_text.strip(): continue
            word_rows=[]
            for word in words:
                wc=word.xpath('./*[local-name()="Coords"]')
                if wc: word_rows.append({'text':text(word),'bbox':core.bbox(core.points(wc[0].get('points')))})
            if not word_rows: continue
            joined=' '.join(w['text'] for w in word_rows).strip()
            if line_text.strip()!=joined: mismatches.append({'line':line.get('id'),'line_text':line_text,'word_text':joined})
            poly=core.points(coords[0].get('points')); lid=f'P{pid}_{line.get("id")}'
            values.append({'id':lid,'source_id':line.get('id'),'page':pid,'text':line_text,
              'polygon':poly.tolist(),'line_bbox':core.bbox(poly),'words':word_rows})
        if mismatches: raise ValueError(f'line/word text mismatch on {pid}: {len(mismatches)}')
        rows+=values; page_meta[pid]={'xml_root':E.QName(root).localname,
          'namespace':E.QName(root).namespace,'image_width':page_node.get('imageWidth'),
          'image_height':page_node.get('imageHeight'),'lines':len(values),
          'words':sum(len(r['words']) for r in values)}
    if len({r['id'] for r in rows})!=len(rows): raise ValueError('duplicate internal line IDs')
    return rows,images,page_meta

def build_layout(pid,rows,image_path):
    from pero_ocr.core.layout import PageLayout,RegionLayout,TextLine
    image=cv2.imread(str(image_path));
    if image is None: raise FileNotFoundError(image_path)
    layout=PageLayout(id=f'A26_{pid}',page_size=image.shape[:2])
    boxes=np.asarray([r['line_bbox'] for r in rows],dtype=float); lo=boxes[:,:2].min(0);hi=boxes[:,2:].max(0)
    region=RegionLayout(f'REG_A26_{pid}',np.asarray([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]]))
    for row in rows:
        x0,y0,x1,y1=row['line_bbox'];h=max(2.,y1-y0)
        region.lines.append(TextLine(id=row['id'],baseline=np.asarray([[x0,y0+.8*h],[x1,y0+.8*h]]),
          polygon=np.asarray(row['polygon']),heights=np.asarray([.8*h,.2*h])))
    layout.regions.append(region);return image,layout

def compact(m): return {k:v for k,v in m.items() if k!='per_line'}

def main():
    started=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True)
    split=json.loads((EXP/'split.json').read_text());opened=json.loads((EXP/'opened.json').read_text())
    checks={'protocol':EXP/'PROTOCOL.md','evaluator':ROOT/'scripts/evaluate_bnf_impact_a26.py',
      'candidate_core_a25':ROOT/'scripts/evaluate_french_holdout_a25.py',
      'extractor':ROOT/'scripts/open_bnf_impact_a26.py','archive_manifest':EXP/'source/archive-manifest.json'}
    for key,path in checks.items():
        if sha(path)!=split['sealed_sha256'][key]: raise ValueError(f'sealed file changed: {key}')
    protected=[EXP/'split.json',EXP/'opened.json',*checks.values()]
    protected += [OPEN/f['name'] for f in opened['files']]
    before={str(p.relative_to(ROOT)):sha(p) for p in protected}
    rows,images,page_meta=load_rows(split);by_page=defaultdict(list)
    for row in rows: by_page[row['page']].append(row)

    import torch
    from pero_ocr.document_ocr.page_parser import PageParser
    torch.set_num_threads(4);cfg=configparser.ConfigParser();cfg.read(MODEL/'config_cpu.ini')
    cfg['PAGE_PARSER']['RUN_LAYOUT_PARSER']='no';tic=time.perf_counter()
    parser=PageParser(cfg,device=torch.device('cpu'),config_path=str(MODEL));load_sec=time.perf_counter()-tic
    native={};forced={};otsu={};proxy={};rec_sec=align_sec=0.;fallback_cells=0
    for pid,group in sorted(by_page.items()):
        cache=OUT/'recognition'/pid
        if not (cache/'cache.json').exists():
            image,layout=build_layout(pid,group,images[pid]);tic=time.perf_counter();layout=parser.process_page(image,layout)
            rec_sec+=time.perf_counter()-tic;save_cache(layout,cache,'PERO 0.7.0 eu/cz newspapers 2022-09-26; oracle A26 lines')
        layout,_=load_cache(cache);gray=cv2.imread(str(images[pid]),cv2.IMREAD_GRAYSCALE)
        xml=layout.to_altoxml_string();xml=xml.encode() if isinstance(xml,str) else xml
        xml=bind_native_alto_ids(xml,layout.regions);(OUT/f'native-{pid}.alto.xml').write_bytes(xml)
        ids={r['id'] for r in group};native.update(core.alto_rows(xml,ids));refs={r['id']:r['text'] for r in group}
        proxies={};changes={}
        for line in layout.lines_iterator(): proxies[line.id],changes[line.id]=core.make_proxy(refs[line.id],set(line.characters[:-1]))
        tic=time.perf_counter();fxml,alignment=realign(layout,proxies);align_sec+=time.perf_counter()-tic
        (OUT/f'forced-{pid}.alto.xml').write_bytes(fxml);fp=core.alto_rows(fxml,ids)
        for row in group:
            lid=row['id'];tokens=row['text'].split()
            if len(fp[lid])!=len(tokens) or len(tokens)!=len(row['words']): forced[lid]=[];otsu[lid]=[];continue
            forced[lid]=[{'text':t,'bbox':w['bbox']} for t,w in zip(tokens,fp[lid])]
            boxes=core.raw_otsu_boxes(gray,row['line_bbox'],[w['bbox'] for w in fp[lid]])
            fallback_cells+=sum(a==b for a,b in zip(boxes,[w['bbox'] for w in fp[lid]]))
            otsu[lid]=[{'text':t,'bbox':b} for t,b in zip(tokens,boxes)]
        proxy.update({lid:{'reference':refs[lid],'proxy':proxies[lid],'changes':changes[lid]} for lid in ids})
    methods={'pero_native':(native,False),'reference_forced_ctc':(forced,True),'ctc_raw_otsu_v1':(otsu,True)}
    metrics={name:core.box_metrics(rows,pred,name,indexed) for name,(pred,indexed) in methods.items()}
    per_page={pid:{name:compact(core.box_metrics(group,pred,name,indexed)) for name,(pred,indexed) in methods.items()}
              for pid,group in sorted(by_page.items())}
    conditions={}
    for pid,p in per_page.items():
        o=p['ctc_raw_otsu_v1'];f=p['reference_forced_ctc'];n=p['pero_native']
        conditions[pid]={'zero_omission':o['predicted_words']==o['reference_words'],
          'recall_iou50_eq_1':o['recall_iou50']==1.,'recall_iou80_ge_090':o['recall_iou80']>=.90,
          'mean_iou_ge_090':o['mean_iou_matched']>=.90,
          'iou80_strictly_better_both':o['recall_iou80']>f['recall_iou80'] and o['recall_iou80']>n['recall_iou80'],
          'iou50_mean_noninferior_both':o['recall_iou50']>=max(f['recall_iou50'],n['recall_iou50']) and o['mean_iou_matched']>=max(f['mean_iou_matched'],n['mean_iou_matched'])}
    gate=all(all(c.values()) for c in conditions.values())
    samples=' '.join(r['text'] for r in rows[:24]).lower()
    french_markers=sum(samples.count(x) for x in (' le ',' la ',' les ',' de ',' des ',' une ',' que ',' est ',' et '))
    report={'schema':'bbvlm.bnf-impact-a26/1','scope':'one manifest-selected page from each of four BnF/IMPACT filename groups; oracle line polygons/text/token order',
      'source_claim':'BnF: French press pages, manual transcription and zone identification, PAGE XML',
      'page_metadata':page_meta,'counts':{'pages':len(by_page),'lines':len(rows),'reference_words':sum(len(r['words']) for r in rows)},
      'observed_language_probe':{'first_24_lines_french_function_word_hits':french_markers,'classified':'French-plausible' if french_markers>=8 else 'not-established'},
      'reference_status':'official BnF corrected OCR ground truth; manual transcription and zones; not independently adjudicated perfect truth',
      'reference_pua':private_use_inventory(''.join(r['text'] for r in rows)),
      'model':{'package':'pero-ocr==0.7.0','weights':MODEL.name,'archive_sha256':MODEL_SHA,
        'torch':torch.__version__,'opencv':cv2.__version__,'device':'cpu','threads':4},
      'cost':{'model_load_seconds':load_sec,'recognition_seconds':rec_sec,'recognized_lines':len(rows),
        'recognizer_forwards':len(rows),'forced_alignment_seconds':align_sec,'new_vlm_tasks':0,
        'total_wall_seconds':time.perf_counter()-started},
      'native_ocr':core.text_metrics(rows,native),'measurements':metrics,'per_page_measurements':per_page,
      'candidate_page_conditions':conditions,'candidate_conditional_gate_passed':gate,
      'fallback_cells':fallback_cells,'proxy':proxy,
      'invariants':{'protocol_evaluator_split_frozen_before_member_open':True,'archive_sha256_verified':True,
        'selected_member_crc_and_size_verified':True,'all_line_text_equals_joined_word_text':True,
        'protected_inputs_unchanged':before=={str(p.relative_to(ROOT)):sha(p) for p in protected}},
      'limitations':['Oracle line polygons, reference text and token order: not end-to-end layout.',
        'Four filename groups are treated as document clusters; internal workbook metadata was not used for selection.',
        'External manual GT is not independently adjudicated perfect truth.',
        'Synthetic horizontal baselines may disadvantage PERO.'],
      'accepted_for_project_completion_gate':False,'protected_input_sha256':before}
    (OUT/'boxes.json').write_text(json.dumps({'native':native,'forced':forced,'otsu':otsu},ensure_ascii=False,indent=2)+'\n')
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'counts':report['counts'],'language':report['observed_language_probe'],'cost':report['cost'],
      'measurements':{k:compact(v) for k,v in metrics.items()},'per_page_candidate':{p:m['ctc_raw_otsu_v1'] for p,m in per_page.items()},
      'candidate_conditional_gate_passed':gate},indent=2))
if __name__=='__main__': main()
