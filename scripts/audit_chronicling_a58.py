#!/usr/bin/env python3
"""Structural audit only: never expose transcription values or alter references."""
import argparse, collections, hashlib, json, time, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def audit(archive):
    started=time.monotonic(); rows=[]; total=collections.Counter(); issues=collections.Counter(); creators=collections.Counter(); statuses=collections.Counter()
    with zipfile.ZipFile(archive) as z:
        for name in sorted(n for n in z.namelist() if n.endswith('.xml')):
            data=z.read(name); root=ET.fromstring(data); ns={'p':root.tag.split('}')[0][1:]}; page=root.find('p:Page',ns)
            w,h=int(page.get('imageWidth')),int(page.get('imageHeight'))
            counts=collections.Counter(e.tag.rsplit('}',1)[-1] for e in page.iter()); bad=collections.Counter()
            ids=[e.get('id') for e in page.iter() if e.get('id')]; bad['duplicate_ids']=len(ids)-len(set(ids))
            for e in page.iter():
                tag=e.tag.rsplit('}',1)[-1]
                if tag in ('Coords','Baseline'):
                    pts=[tuple(map(float,p.split(','))) for p in e.get('points','').split()]
                    if not pts: bad['empty_'+tag]+=1; continue
                    if any(x<0 or y<0 or x>w or y>h for x,y in pts):bad['outside_'+tag]+=1
                    if tag=='Coords':
                        area=abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))/2
                        if len(set(pts))<3 or area==0:bad['degenerate_polygon']+=1
                if tag=='RegionRefIndexed' and e.get('regionRef') not in set(ids):bad['dangling_region_ref']+=1
            creator=root.findtext('p:Metadata/p:Creator','',ns).strip();creators[creator]+=1
            meta=root.find('p:Metadata/p:TranskribusMetadata',ns)
            statuses[meta.get('status','missing') if meta is not None else 'absent']+=1
            total.update(counts);issues.update(bad)
            rows.append({'file':Path(name).name,'sha256':hashlib.sha256(data).hexdigest(),'image':page.get('imageFilename'),'width':w,'height':h,'counts':dict(counts),'issues':dict(bad)})
    return {'files':len(rows),'archive_sha256':hashlib.sha256(Path(archive).read_bytes()).hexdigest(),'archive_bytes':Path(archive).stat().st_size,'element_totals':dict(total),'issues':dict(issues),'creators':dict(creators),'statuses':dict(statuses),'elapsed_seconds':time.monotonic()-started,'files_detail':rows,'eligibility':{'region_geometry':'manual cross-check reported; inspect coordinate issues before scoring','line_geometry':'only major errors manually corrected; no perfect-box certification','word_geometry':False if total['Word']==0 else 'provenance not established','reading_order':'automatic uncorrected: not independent GT','ocr':'single-expert correction reported; conventions and coverage require audit'},'cost':{'vlm_passes':0,'ocr_passes':0,'images_downloaded':0},'accepted_for_project_completion_gate':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('archive');ap.add_argument('--out',default='experiments/loop/chronicling-a58/audit.json');a=ap.parse_args()
    result=audit(a.archive);Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files_detail'},indent=2))
