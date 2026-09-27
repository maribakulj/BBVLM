#!/usr/bin/env python3
"""Post-score audit of A28 failures; never changes the sealed candidate/reference."""
from __future__ import annotations
import json,statistics
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
import evaluate_french_holdout_a25 as core

ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/loop/french-word-gt-a28'

def main():
    split=json.loads((EXP/'split.json').read_text());core.EXP=EXP;core.SOURCE=EXP/'source';rows,images=core.load_rows(split)
    boxes=json.loads((EXP/'output/boxes.json').read_text())['otsu'];work_by_page={p['page']:p['work'] for p in split['pages']}
    values=[]
    for row in rows:
        pred=boxes[row['id']]
        if len(pred)!=len(row['words']):continue
        for i,(gt,pr) in enumerate(zip(row['words'],pred)):
            gb,pb=gt['bbox'],pr['bbox'];score=core.iou(gb,pb);ga=max(1,(gb[2]-gb[0])*(gb[3]-gb[1]));pa=max(1,(pb[2]-pb[0])*(pb[3]-pb[1]))
            values.append({'page':row['page'],'work':work_by_page[row['page']],'line':row['id'],'index':i,'text':gt['text'],'gt':gb,'pred':pb,
              'iou':score,'pred_gt_area_ratio':pa/ga,'pred_inside_gt':pb[0]>=gb[0] and pb[1]>=gb[1] and pb[2]<=gb[2] and pb[3]<=gb[3]})
    by_work={}
    for work in sorted(set(x['work'] for x in values)):
        v=[x for x in values if x['work']==work]
        by_work[work]={'words':len(v),'mean_iou':sum(x['iou'] for x in v)/len(v),'recall_iou50':sum(x['iou']>=.5 for x in v)/len(v),
          'recall_iou80':sum(x['iou']>=.8 for x in v)/len(v),'median_pred_gt_area_ratio':statistics.median(x['pred_gt_area_ratio'] for x in v),
          'pred_inside_gt_rate':sum(x['pred_inside_gt'] for x in v)/len(v)}
    worst=sorted(values,key=lambda x:x['iou'])[:40];tiles=[]
    for item in worst:
        image=cv2.imread(str(images[item['page']]));g,p=item['gt'],item['pred'];x0=max(0,min(g[0],p[0])-16);y0=max(0,min(g[1],p[1])-16);x1=min(image.shape[1],max(g[2],p[2])+16);y1=min(image.shape[0],max(g[3],p[3])+16)
        crop=image[y0:y1,x0:x1].copy();cv2.rectangle(crop,(g[0]-x0,g[1]-y0),(g[2]-x0,g[3]-y0),(0,180,0),2);cv2.rectangle(crop,(p[0]-x0,p[1]-y0),(p[2]-x0,p[3]-y0),(0,0,220),2)
        pil=Image.fromarray(cv2.cvtColor(crop,cv2.COLOR_BGR2RGB));pil.thumbnail((360,130));tile=Image.new('RGB',(380,170),'white');tile.paste(pil,(10,30));d=ImageDraw.Draw(tile);d.text((8,5),f"{item['page']} {item['text'][:28]} IoU={item['iou']:.3f}",fill='black');tiles.append(tile)
    sheet=Image.new('RGB',(760,((len(tiles)+1)//2)*170),(235,235,235))
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*380,(i//2)*170))
    out=EXP/'post-score';out.mkdir(parents=True,exist_ok=True);sheet.save(out/'worst-40-overlay.jpg',quality=94)
    report={'schema':'bbvlm.french-word-gt-a28-post-score-audit/1','status':'diagnostic_after_validation; no retuning or reference edits',
      'aggregate':{'words':len(values),'mean_iou':sum(x['iou'] for x in values)/len(values),'recall_iou50':sum(x['iou']>=.5 for x in values)/len(values),
        'recall_iou80':sum(x['iou']>=.8 for x in values)/len(values),'median_pred_gt_area_ratio':statistics.median(x['pred_gt_area_ratio'] for x in values),
        'pred_inside_gt_rate':sum(x['pred_inside_gt'] for x in values)/len(values)},'by_work':by_work,'worst_40':worst,
      'overlay':'experiments/loop/french-word-gt-a28/post-score/worst-40-overlay.jpg',
      'interpretation':'A tight ink rectangle and the project Word polygon encode different conventions when padding, faint glyph parts, bleed-through, italics or neighboring marks are present. IoU disagreement alone does not prove either box visually perfect.'}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='worst_40'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

