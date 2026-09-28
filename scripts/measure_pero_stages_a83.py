"""Measure genuine PERO layout/crop only; no recognizer or reference enters inference."""
import configparser,hashlib,json,time,importlib.metadata as md
from pathlib import Path
import cv2,numpy as np,torch
from pero_ocr.document_ocr.page_parser import PageParser
from pero_ocr.core.layout import PageLayout
from evaluate_textline_instances_a75 import box_iou,parse_reference,summarize
from scipy.optimize import linear_sum_assignment
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a83';MODEL=ROOT/'models/pero/pero_eu_cz_print_newspapers_2022-09-26'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bbox(poly):
 q=np.asarray(poly);return [float(q[:,0].min()),float(q[:,1].min()),float(q[:,0].max()),float(q[:,1].max())]
def main():
 start=time.perf_counter();torch.set_num_threads(4);torch.set_num_interop_threads(1);cv2.setNumThreads(4);config=configparser.ConfigParser();config.read(MODEL/'config_cpu.ini');config['PAGE_PARSER']['RUN_OCR']='no';config['PAGE_PARSER']['RUN_DECODER']='no'
 with (P/'config-layout-crop.ini').open('w') as f:config.write(f)
 tick=time.perf_counter();parser=PageParser(config,device=torch.device('cpu'),config_path=str(MODEL));load_seconds=time.perf_counter()-tick;assert parser.ocr is None and parser.decoder is None and not parser.run_ocr and not parser.run_decoder
 pn=parser.layout_parsers[0].engine.parsenet;original=pn.get_maps;calls=[]
 def counted(img,downsample):
  t=time.perf_counter();result=original(img,downsample);calls.append({'downsample':float(downsample),'image_shape':list(img.shape),'seconds':time.perf_counter()-t});return result
 pn.get_maps=counted
 assets=json.loads((ROOT/'experiments/loop/next-a80/dense/assets.json').read_text())['images'];selected=json.loads((ROOT/'experiments/loop/next-a81/private-map.json').read_text())['mapping'];selected=[x for x in selected if x['line_id'] is not None];pages={};crops=[]
 for a in assets:
  image_path=ROOT/a['path'];assert sha(image_path)==a['sha256'];image=cv2.imread(str(image_path));page=PageLayout(id=a['page'],page_size=image.shape[:2]);before=len(calls);tick=time.perf_counter()
  for stage in parser.layout_parsers:page=stage.process_page(image,page)
  layout_seconds=time.perf_counter()-tick;tick=time.perf_counter();page=parser.line_cropper.process_page(image,page);crop_seconds=time.perf_counter()-tick;lines=list(page.lines_iterator());assert all(l.logits is None and l.transcription in [None,''] for l in lines)
  items=[{'id':l.id,'bbox_native':bbox(l.polygon),'polygon':np.asarray(l.polygon).tolist(),'baseline':np.asarray(l.baseline).tolist(),'heights':np.asarray(l.heights).tolist(),'crop_shape':list(l.crop.shape)} for l in lines]
  pages[a['page']]={'image_sha256':a['sha256'],'image_path':a['path'],'regions':len(page.regions),'lines':items,'layout_seconds':layout_seconds,'crop_seconds':crop_seconds,'forwards':calls[before:]}
  for m in [x for x in selected if x['page']==a['page']]:
   iou=box_iou(np.array([m['bbox_native']]),np.array([x['bbox_native'] for x in items]))[0];j=int(iou.argmax());line=lines[j];tick=time.perf_counter();crop,xy=parser.line_cropper.crop_engine.crop(image,line.baseline,line.heights,return_forward_mapping=True);seconds=time.perf_counter()-tick;file=P/f"{m['id']}-pero.png";cv2.imwrite(str(file),crop);mp=P/f"{m['id']}-map.npz";np.savez_compressed(mp,xy=xy);crops.append({'a81_id':m['id'],'page':m['page'],'pero_line_id':line.id,'predicted_box_iou':float(iou[j]),'file':str(file.relative_to(ROOT)),'sha256':sha(file),'map_file':str(mp.relative_to(ROOT)),'map_sha256':sha(mp),'extra_mapping_crop_seconds':seconds})
  print(a['page'],len(items),layout_seconds,crop_seconds,flush=True)
 output={'config_sha256':sha(P/'config-layout-crop.ini'),'protocol_sha256':sha(P/'PROTOCOL.md'),'weight_sha256':sha(MODEL/'ParseNet_296000.pt.cpu'),'source_config_sha256':sha(MODEL/'config_cpu.ini'),'versions':{n:md.version(n) for n in ['pero-ocr','numpy','torch','numba','scipy','shapely','opencv-python-headless']},'load_seconds':load_seconds,'pages':pages,'selected_crops':crops,'ocr_models_loaded':0,'ocr_calls':0,'decoder_calls':0,'total_layout_forwards':len(calls),'prediction_seconds':time.perf_counter()-start}
 path=P/'predictions.json';path.write_text(json.dumps(output,indent=2)+'\n');seal=sha(path);expected={r['file']:r['sha256'] for r in json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text())['files_detail']};scores={}
 for name,page in pages.items():
  refs,_=parse_reference(name,expected);b=np.array([x['bbox_native'] for x in page['lines']]);rb=np.array([x['bbox'] for x in refs]);iou=box_iou(b,rb);rr,cc=linear_sum_assignment(-iou);scores[name]=summarize(iou,rr,cc,len(b),len(rb))
 assert sha(path)==seal;report={'status':'consumed_pero_layout_crop_only','pages':scores,'load_seconds':load_seconds,'layout_seconds':sum(x['layout_seconds'] for x in pages.values()),'crop_seconds':sum(x['crop_seconds'] for x in pages.values()),'extra_mapping_crop_seconds':sum(x['extra_mapping_crop_seconds'] for x in crops),'layout_forwards':len(calls),'ocr_models_loaded':0,'ocr_calls':0,'decoder_calls':0,'prediction_sha256_before_xml':seal,'seconds':time.perf_counter()-start,'test_pages_opened':0,'global_completion':False};(P/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='pages'},indent=2))
 for stage in parser.layout_parsers:
  if hasattr(stage,'pool'):stage.pool.close();stage.pool.join()
if __name__=='__main__':main()
