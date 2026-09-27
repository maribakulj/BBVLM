"""A15: reuse A13 Sol paragraphs, bind to A14 predicted lines, cache CTC once.

No source reference XML is read. This is a 20-line partial-page integration
probe, not an independent OCR/geometry benchmark. Strict line counts gate binding.
"""
from pathlib import Path
import configparser,hashlib,json,time
import numpy as np
from bbvlm.pero import save_cache,load_cache,realign
from bbvlm.formats import import_xml
from bbvlm.__main__ import export_package

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop/spiritualist-v1'
OUT=BASE/'predicted-alignment-a15-0044'

def main():
    from pero_ocr.core.layout import PageLayout,RegionLayout,TextLine
    from pero_ocr.document_ocr.page_parser import PageParser
    import cv2,torch
    raw=json.loads((BASE/'column-lines-a14-0044/raw-detection.json').read_text())
    req=json.loads((BASE/'yolo-ocr-a13-0044/input/request.json').read_text())
    response=json.loads((BASE/'yolo-ocr-a13-0044/sol.response.json').read_text())
    texts={r['id']:r['text'] for r in response['regions']}
    assert len(texts)==len(response['regions']) and set(texts)=={r['id'] for r in req['regions']}
    page=PageLayout(id='A15_0044',page_size=(3508,2479));binding=[];transcriptions={}
    for region in req['regions']:
        x0,y0,x1,y1=region['detector_bbox']
        selected=[l for l in raw['lines'] if x0<=(l['bbox'][0]+l['bbox'][2])/2<=x1
                  and y0<=(l['bbox'][1]+l['bbox'][3])/2<=y1]
        selected.sort(key=lambda l:(float(np.median(np.asarray(l['baseline'])[:,1])),l['id']))
        paragraphs=texts[region['id']].splitlines()
        if not selected or len(selected)!=len(paragraphs) or any(not t.strip() for t in paragraphs):
            raise ValueError('ambiguous region/line binding; requires a visual reread: '+region['id'])
        bounds=np.asarray([l['bbox'] for l in selected])
        left,top=bounds[:,:2].min(0);right,bottom=bounds[:,2:].max(0)
        reg=RegionLayout(region['id'],np.asarray([[left,top],[right,top],[right,bottom],[left,bottom]]))
        for line,text in zip(selected,paragraphs):
            if line['id'] in transcriptions:raise ValueError('line assigned twice')
            transcriptions[line['id']]=text
            reg.lines.append(TextLine(id=line['id'],baseline=np.asarray(line['baseline']),
                polygon=np.asarray(line['polygon']),heights=np.asarray(line['heights'])))
        page.regions.append(reg)
        binding.append({'region_id':region['id'],'predicted_line_ids':[l['id'] for l in selected],
                        'returned_text_lines':len(paragraphs),'rule':'equal-count physical top-to-bottom; not human verified'})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    (OUT/'transcriptions.json').write_text(json.dumps(transcriptions,ensure_ascii=False,indent=2)+'\n')
    cache=OUT/'recognition'
    if not (cache/'cache.json').exists():
        model=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
        config=configparser.ConfigParser();config.read(model/'config_cpu.ini')
        config['PAGE_PARSER']['RUN_LAYOUT_PARSER']='no'
        torch.set_num_threads(4);t=time.perf_counter()
        parser=PageParser(config,device=torch.device('cpu'),config_path=str(model))
        load_seconds=time.perf_counter()-t
        im=cv2.imread(str(ROOT/'corpora/spiritualist/companion/Spiritualist_Images/0044.png'))
        t=time.perf_counter();page=parser.process_page(im,page);elapsed=time.perf_counter()-t
        save_cache(page,cache,'PERO 0.7.0 eu/cz newspapers 2022-09-26; A14 raw predicted lines')
        (OUT/'cost.json').write_text(json.dumps({'ocr_load_seconds':load_seconds,'recognition_seconds':elapsed,
             'recognized_lines':len(transcriptions),'new_vlm_passes':0,'new_layout_passes':0},indent=2)+'\n')
        (OUT/'native.alto.xml').write_text(page.to_altoxml_string())
    # Reload enforces the same portable path as future runs.
    page,meta=load_cache(cache)
    try:
        t=time.perf_counter();xml,alignment=realign(page,transcriptions);align_seconds=time.perf_counter()-t
    except ValueError as error:
        report={'status':'alignment_rejected','reason':str(error),'binding':binding,
                'scope':'partial-page integration, no independent benchmark',
                'accepted_for_project_completion_gate':False}
        (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return
    path=OUT/'realigned.alto.xml';path.write_bytes(xml)
    graph=import_xml(path)
    original_lines={l['id']:l for l in raw['lines']}
    for n in graph['nodes']:
        if n['kind']=='page':n['image']='https://huggingface.co/datasets/NationalLibraryOfScotland/Spiritualist_Newspaper/resolve/57244e5d175380ebc110b0d8b130b2dff30aeadd/Spiritualist_Images/0044.png'
        if n['kind']=='line':
            # Native ALTO only exports an average scalar baseline; restore the
            # actually predicted polyline/polygon using the checked ID binding.
            original=original_lines[n['source_id']]
            n['baseline']=original['baseline'];n['polygon']=original['polygon'];n['bbox']=original['bbox']
    graph['events'].append({'type':'partial_page_predicted_line_vlm_ctc_integration',
        'scope':'only 20 lines from 3 short YOLO crops; other page content not processed by this package',
        'text_source':'saved blind A13 gpt-6-sol response; oracle-assisted escalation selected in A13',
        'geometry_source':'A14 PERO raw predictions, no source annotations',
        'binding':'equal line counts plus physical baseline order, requires visual validation',
        'source_image_sha256':raw['image_sha256']})
    package=export_package(graph,OUT/'package',ROOT/'schemas')
    lines=[n for n in graph['nodes'] if n['kind']=='line'];words=[n for n in graph['nodes'] if n['kind']=='word']
    text_preserved=all(n['text']==transcriptions[n['source_id']] for n in lines)
    if not text_preserved:raise ValueError('export changed diplomatic text')
    report={'schema':'bbvlm.predicted-vlm-alignment/1','status':'integration_complete_not_verified_gt',
        'scope':'20 predicted lines / 3 short crops of consumed0044; not full page or independent comparison',
        'reference_inputs':False,'binding':binding,'aligned_lines':len(lines),'word_boxes':len(words),
        'text_preserved':text_preserved,'alignment_seconds':align_seconds,
        'native_alignment_review_flags':sum(l['requires_review'] for l in alignment['lines']),
        'cost':json.loads((OUT/'cost.json').read_text()),'package':package,
        'limitations':['equal-count order binding may still pair text incorrectly; needs image adjudication',
            'XSD and zero fallback flags do not validate word box boundaries',
            'METS institutional MODS/PREMIS profile and image fileSec references remain pending',
            'all imported nodes remain automatic; all line reviews remain open'],
        'accepted_for_project_completion_gate':False}
    (OUT/'alignment.json').write_text(json.dumps(alignment,indent=2)+'\n')
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
