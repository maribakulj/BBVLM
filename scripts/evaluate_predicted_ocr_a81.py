"""Score actual blind responses on predicted crops; missing references stay unknown."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from evaluate_bnl_vlm_a54 import measures,VIEWS
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'experiments/loop/next-a81'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 request=json.loads((P/'blind/request.json').read_text());response=json.loads((P/'luna-response.json').read_text());private=json.loads((P/'private-map.json').read_text());ids=[x['id'] for x in request['items']];answers=response['items'];assert len(answers)==len(ids)==8 and len({x['id'] for x in answers})==8 and set(ids)=={x['id'] for x in answers};assert response['model']=='gpt-6-luna'
 images=[y for x in request['items'] for y in x['images']];assert len(response['inspected_images'])==len(images)==16 and set(response['inspected_images'])==set(images)
 for x in request['items']:
  for path,digest in zip(x['images'],x['sha256']):assert sha(ROOT/path)==digest
 assert sha(P/'PROTOCOL.md')==private['protocol_sha256'];assert sha(ROOT/'experiments/loop/next-a80/routed/candidates.json')==private['source_candidates_sha256']
 byid={x['id']:x for x in answers};rows=[]
 for m in private['mapping']:
  a=byid[m['id']];assert isinstance(a['text'],str);assert a['visual_role'] in ['running_text','heading','marginalia','nontext','uncertain'];assert isinstance(a['clipped_edges'],list) and isinstance(a['uncertain_spans'],list)
  xml=ROOT/'corpora/chronicling-germany/annotations'/f"{m['page']}.xml";assert sha(xml)==m['xml_sha256'];assert sha(ROOT/m['image_path'])==m['image_sha256'];ref=None
  if m['line_id'] is not None:
   root=ET.parse(xml).getroot();ns={'p':root.tag.split('}')[0][1:]};els=[x for x in root.findall('.//p:TextLine',ns) if x.get('id')==m['line_id']];assert len(els)==1;node=els[0].find('p:TextEquiv/p:Unicode',ns);assert node is not None;ref=node.text or ''
  rows.append(dict(m,text=a['text'],reference=ref,visual_role=a['visual_role'],clipped_edges=a['clipped_edges'],uncertain_spans=a['uncertain_spans'],note=a.get('note',''),agreement=measures(ref,a['text']) if ref is not None else None))
 summary={}
 eligible=[x for x in rows if x['agreement'] is not None]
 for view in VIEWS:
  n=sum(x['agreement'][view]['characters'] for x in eligible);e=sum(x['agreement'][view]['edits'] for x in eligible);summary[view]={'characters':n,'edits':e,'cer':e/n if n else None,'exact_crops':sum(x['agreement'][view]['exact'] for x in eligible),'scored_crops':len(eligible)}
 result={'status':'consumed_oracle_selected_predicted_crop_diagnostic','agreement_only':summary,'unmatched_reference_unknown':[x['id'] for x in rows if x['reference'] is None],'rows':rows,'cost':{'new_reader_sessions':1,'model':'gpt-6-luna','image_views':16,'target_crops':8,'new_cpu_model_forwards':0,'tokens_and_money':'not exposed'},'invariants':{'exact_ids':True,'all_images_declared_inspected':True,'source_and_crop_hashes_unchanged':True,'original_xml_unchanged':True},'independent_adjudication':False,'global_completion':False,'test_pages_opened':0}
 (P/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
