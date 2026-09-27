"""A13 evaluate frozen blind paragraph OCR; annotations never feed readers."""
from pathlib import Path
import json,hashlib
from lxml import etree as E
from bbvlm.metrics import text_scores
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/loop/spiritualist-v1/yolo-ocr-a13-0044'
NS={'a':'http://www.loc.gov/standards/alto/ns-v4#'}

def read_response(path,expected):
    response=json.loads(path.read_text());rows=response['regions']
    if len(rows)!=len(expected) or {r['id'] for r in rows}!=set(expected):
        raise ValueError('response IDs missing, extra or duplicated')
    for row in rows:
        if not isinstance(row['text'],str) or type(row['uncertain']) is not bool:
            raise ValueError('invalid response types')
    return rows

def flat(text): return ' '.join(text.split())

def main():
    request=json.loads((BASE/'input/request.json').read_text())
    ids=[r['id'] for r in request['regions']]
    luna=read_response(BASE/'luna.response.json',ids)
    source=next((ROOT/'corpora/spiritualist/alto_xml/ocr_gt_labelled').glob('0044_*.xml'))
    tree=E.parse(str(source));refs=[];associations=[]
    for region in request['regions']:
        x0,y0,x1,y1=region['detector_bbox'];lines=[]
        for line in tree.findall('.//a:TextLine',NS):
            x,y,w,h=map(float,(line.get(k) for k in ('HPOS','VPOS','WIDTH','HEIGHT')))
            if x0<=(x+w/2)<=x1 and y0<=(y+h/2)<=y1:
                text=' '.join(s.get('CONTENT','') for s in line.findall('./a:String',NS))
                lines.append({'id':line.get('ID'),'bbox':[x,y,x+w,y+h],'text':text})
        lines.sort(key=lambda r:(r['bbox'][1],r['bbox'][0],r['id']))
        if not lines: raise ValueError('no matched lines')
        refs.append({'id':region['id'],'text':flat('\n'.join(r['text'] for r in lines))})
        associations.append({'id':region['id'],'lines':lines})
    scores={'luna':text_scores(refs,[{'id':r['id'],'text':flat(r['text'])} for r in luna])}
    sol=BASE/'sol.response.json'
    if sol.exists():
        route=json.loads((BASE/'escalation.json').read_text())
        retry=read_response(sol,route['ids']);merged={r['id']:r for r in luna}
        merged.update({r['id']:r for r in retry})
        scores['luna_sol']=text_scores(refs,[{'id':i,'text':flat(merged[i]['text'])} for i in ids])
    report={'schema':'bbvlm.predicted-paragraph-ocr/1','page':'0044',
        'scoring_unit':'region, not TextLine; generic text_scores lines fields count 3 regions',
        'scope':'consumed page, 3 short detector crops; not a representative or independent benchmark',
        'reference_status':'distributed text provisional; differences require independent image adjudication',
        'source_xml_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'new_passes':{'luna':1,'sol':int(sol.exists()),'detector':0},
        'cost_unavailable':['token counts','monetary cost','internal model inference latency'],
        'scores':scores,'reference_associations':associations,
        'normalisation_before_scoring':'collapse whitespace only; no punctuation/case/hyphen folding',
        'accepted_for_project_completion_gate':False}
    (BASE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a!='per_line'} for k,v in scores.items()},indent=2))

if __name__=='__main__':main()
