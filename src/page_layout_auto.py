"""Plan de lecture automatique à partir des pixels et lignes BLLA seulement."""
from pathlib import Path
import argparse
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

from page_anchors import load_automatic_lines, save_json, sha256


VERSION = 'image-lines-layout-v2'


def pixel_spanners(gray,columns,line_height,top,bottom,boxes):
    """Titres fragmentés par BLLA et cadres publicitaires traversants."""
    spans=[];h=line_height
    for i,(left,right) in enumerate(zip(columns,columns[1:])):
        edge=int((left['bbox'][2]+right['bbox'][0])/2)
        x=max(0,int(edge-3*h));a=min(gray.shape[1],int(edge+3*h))
        _,_,stats,_=cv2.connectedComponentsWithStats((gray[top:bottom,x:a]<140).astype('uint8'),8)
        for sx,sy,w,height,area in stats[1:]:
            if not (sx+x<edge-2<sx+x+w-4 and .65*h<height<5*h and w<3*h and area>h*.5):continue
            if not any(b[0]<edge-h*.7 and b[2]>edge+h*.7 and
                       max(0,min(top+sy+height,b[3])-max(top+sy,b[1]))>.5*min(height,b[3]-b[1])
                       for b in boxes):continue
            # Un grand trait de bordure ou une tache isolée n'est pas un
            # titre : exiger plusieurs glyphes de taille comparable.
            gy=max(top,int(top+sy-h*.5));gb=min(bottom,int(top+sy+height+h*.5))
            neighborhood=gray[gy:gb,left['bbox'][0]:right['bbox'][2]]
            _,_,near,_=cv2.connectedComponentsWithStats((neighborhood<140).astype('uint8'),8)
            near=near[1:]
            glyphs=near[(near[:,3]>max(h*.65,height*.55))&(near[:,3]<height*1.6)&
                        (near[:,2]<h*3)&(near[:,4]>h*.5)]
            if len(glyphs)<5:continue
            spans.append(dict(first=i,last=i+1,top=max(top,int(top+sy-h*.35)),
                              bottom=min(bottom,int(top+sy+height+h*.35))))
    # Les cadres fermés donnent l'étendue complète des annonces, y compris
    # leur petit texte que la détection des grands caractères ne voit pas.
    scale=min(1.,1600/gray.shape[1]);small=cv2.resize(gray[top:bottom],None,fx=scale,fy=scale)
    binary=cv2.morphologyEx((small<140).astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    contours,_=cv2.findContours(binary,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x,y,w,height=cv2.boundingRect(contour)
        if height<5*h*scale or w<10*h*scale:continue
        polygon=cv2.approxPolyDP(contour,cv2.arcLength(contour,True)*.02,True)
        if len(polygon)!=4 or cv2.contourArea(contour)<w*height*.85:continue
        x0=x/scale;x1=(x+w)/scale
        touched=[i for i,c in enumerate(columns) if max(0,min(x1,c['bbox'][2])-max(x0,c['bbox'][0]))>
                 (c['bbox'][2]-c['bbox'][0])*.35]
        if len(touched)>=2:
            spans.append(dict(first=min(touched),last=max(touched),top=max(top,int(top+y/scale-h*.1)),
                              bottom=min(bottom,int(top+(y+height)/scale+h*.1))))
    return spans


def separate_spanning_regions(regions, boxes, line_height, gray=None):
    """Extraire les grandes lignes traversantes avant les crops de colonnes."""
    output = []
    bands = sorted(set((r['bbox'][1], r['bbox'][3]) for r in regions))
    for top,bottom in bands:
        columns = sorted([r for r in regions if r['bbox'][1:4:2] == [top,bottom]], key=lambda r:r['bbox'][0])
        if len(columns) < 2:
            output.extend(columns);continue
        spans=pixel_spanners(gray,columns,line_height,top,bottom,boxes) if gray is not None else []
        heading_seeds=list(spans)
        for box in boxes:
            if not top <= (box[1]+box[3])/2 < bottom:
                continue
            touched=[]
            for i,c in enumerate(columns):
                a,_,b,_=c['bbox']
                if max(0,min(b,box[2])-max(a,box[0])) > (b-a)*.35:
                    touched.append(i)
            if len(touched)<2:continue
            near_heading=any(s['first']<=min(touched) and max(touched)<=s['last'] and
                             s['bottom']-line_height<=box[1]<s['bottom']+line_height*3
                             for s in heading_seeds)
            if box[3]-box[1]<line_height*(.8 if near_heading else 1.5):continue
            strong=box[3]-box[1]>=line_height*1.5
            if gray is not None:
                x0,y0,x1,y1=map(int,box)
                ink=(gray[y0:y1,x0:x1]<140).astype('uint8')
                _,_,stats,_=cv2.connectedComponentsWithStats(ink,8)
                glyphs=stats[1:]
                glyphs=glyphs[(glyphs[:,4]>8)&(glyphs[:,2]<line_height*3)&(glyphs[:,3]>line_height*.2)]
                # Une boîte fusionnée par le détecteur peut être haute sans
                # contenir de gros caractères traversant les colonnes.
                if not len(glyphs) or np.median(glyphs[:,3])<line_height*(.4 if near_heading else .6):continue
                strong=strong and np.median(glyphs[:,3])>=line_height*.6
                if near_heading and not strong:
                    # Un sous-titre prolonge un titre traversant seulement
                    # si ses caractères franchissent réellement la gouttière.
                    # Les faux raccords BLLA entre deux colonnes restent exclus.
                    _,contrast=cv2.threshold(gray[y0:y1,x0:x1],0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
                    _,_,dark,_=cv2.connectedComponentsWithStats(contrast,8)
                    dark=dark[1:];dark=dark[(dark[:,3]>line_height*.25)&(dark[:,2]>line_height*.07)]
                    across=False
                    for i in touched[:-1]:
                        edge=(columns[i]['bbox'][2]+columns[i+1]['bbox'][0])/2
                        lefts=dark[:,0]+x0;rights=lefts+dark[:,2]
                        if np.any((lefts<edge-line_height*.1)&(rights>edge+line_height*.1)):
                            across=True;break
                        before=rights[rights<=edge];after=lefts[lefts>=edge]
                        if len(before) and len(after) and after.min()-before.max()<line_height*.25:
                            across=True;break
                    if not across:continue
            if len(touched)>=2:
                span=dict(first=min(touched),last=max(touched),top=max(top,int(box[1]-line_height*.12)),
                          bottom=min(bottom,int(box[3]+line_height*.12)))
                spans.append(span)
                if strong:heading_seeds.append(span)
        merged=[]
        for span in sorted(spans,key=lambda s:s['top']):
            match=next((s for s in reversed(merged) if s['first']<=span['last'] and span['first']<=s['last']
                        and span['top']-s['bottom']<line_height*2),None)
            if match:
                match.update(first=min(match['first'],span['first']),last=max(match['last'],span['last']),
                             bottom=max(match['bottom'],span['bottom']))
            else:merged.append(span)
        changed=True
        while changed:
            changed=False
            for i,a in enumerate(merged):
                for j in range(i+1,len(merged)):
                    b=merged[j]
                    if a['first']<=b['last'] and b['first']<=a['last'] and max(a['top'],b['top'])<min(a['bottom'],b['bottom'])+line_height*2:
                        a.update(first=min(a['first'],b['first']),last=max(a['last'],b['last']),
                                 top=min(a['top'],b['top']),bottom=max(a['bottom'],b['bottom']))
                        merged.pop(j);changed=True;break
                if changed:break
        for span in merged:
            left=columns[span['first']]['bbox'][0];right=columns[span['last']]['bbox'][2]
            if span['top']-top<line_height*2 and not any(
                left<=(b[0]+b[2])/2<right and top<=(b[1]+b[3])/2<span['top'] for b in boxes):
                span['top']=top
            if bottom-span['bottom']<line_height*2 and not any(
                left<=(b[0]+b[2])/2<right and span['bottom']<=(b[1]+b[3])/2<bottom for b in boxes):
                span['bottom']=bottom
        pieces=[]
        for i,column in enumerate(columns):
            left,_,right,_=column['bbox'];ys=[(top,bottom)]
            for span in merged:
                if not span['first']<=i<=span['last']:continue
                next_ys=[]
                for a,b in ys:
                    if span['bottom']<=a or span['top']>=b:next_ys.append((a,b));continue
                    if span['top']>a:next_ys.append((a,span['top']))
                    if span['bottom']<b:next_ys.append((span['bottom'],b))
                ys=next_ys
            for j,(a,b) in enumerate(ys):
                if b-a < line_height*.3:continue
                pieces.append((i,a,{**column,'id':column['id']+f'_p{j+1}', 'bbox':[left,a,right,b]}))
        for i,span in enumerate(merged):
            pieces.append((span['first'],span['top'],dict(id=columns[span['first']]['id']+f'_span{i+1}',
                          kind='spanning_region',bbox=[columns[span['first']]['bbox'][0],span['top'],
                          columns[span['last']]['bbox'][2],span['bottom']])))
        output.extend(r for _,_,r in sorted(pieces,key=lambda t:(t[0],t[1])))
    for i,r in enumerate(output):r['order']=i+1
    return output


def column_starts(boxes, width, line_height):
    boxes = np.asarray(boxes, dtype=float)
    lengths = boxes[:, 2]-boxes[:, 0]
    normal = lengths[lengths > 6*line_height]
    if len(normal) < 6:
        return [float(np.min(boxes[:, 0]))]
    typical = float(np.median(normal))
    voters = boxes[(lengths > typical*.65) & (lengths < typical*1.4)]
    histogram = np.zeros(width+1)
    for x in voters[:, 0]:
        histogram[int(x)] += 1
    sigma = max(2, line_height*.4)
    density = gaussian_filter1d(histogram, sigma)
    peaks, _ = find_peaks(density, distance=max(1, int(typical*.45)),
                         prominence=max(.01, float(density.max())*.12))
    centers = []
    for peak in peaks:
        nearby = voters[np.abs(voters[:, 0]-peak) < max(line_height*2, typical*.12), 0]
        if len(nearby) >= max(4, len(voters)*.025):
            centers.append(float(np.median(nearby)))
    return centers or [float(np.min(boxes[:, 0]))]


def horizontal_separators(gray, content, line_height):
    height, width = gray.shape
    scale = min(1., 1600/width)
    small = cv2.resize(gray, None, fx=scale, fy=scale)
    # Les très longs filets sont mieux isolés par morphologie que par Hough
    # sur tous les contours de lettres d'une page dense.
    binary=cv2.dilate((small<140).astype('uint8'),np.ones((3,1),np.uint8))
    rules=cv2.morphologyEx(binary,cv2.MORPH_OPEN,np.ones((1,100),np.uint8))
    profile=cv2.dilate(rules,np.ones((15,1),np.uint8)).sum(axis=1)
    ys=np.where(profile>(content[2]-content[0])*scale*.65)[0]
    groups=np.split(ys,np.where(np.diff(ys)>1)[0]+1)
    morphology=[float(np.median(group)/scale) for group in groups if len(group)]
    morphology=[y for y in morphology if content[1]+line_height*.3<y<content[3]-line_height*.3]
    edges = cv2.Canny(small, 60, 150)
    minimum = (content[2]-content[0])*.12*scale
    lines = cv2.HoughLinesP(edges, 1, np.pi/1800, threshold=80,
                            minLineLength=max(50, int(minimum)), maxLineGap=20)
    candidates = []
    for x0, y0, x1, y1 in ([] if lines is None else lines.reshape(-1, 4)):
        if abs(x1-x0) < minimum or abs(y1-y0) > .025*abs(x1-x0):
            continue
        if x0 > x1:
            x0,y0,x1,y1 = x1,y1,x0,y0
        xs = np.arange(x0, x1+1)
        ys = np.rint(np.linspace(y0, y1, len(xs))).astype(int)
        # Les alignements fortuits de caractères ne constituent pas un filet.
        values = np.stack([small[np.clip(ys+d, 0, small.shape[0]-1), xs] for d in range(-2, 3)])
        if float((values.min(axis=0) < 110).mean()) < .88:
            continue
        y = (y0+y1)/(2*scale)
        if content[1]+line_height < y < content[3]-line_height:
            candidates.append((float(y), x0/scale, x1/scale))
    groups = []
    for candidate in sorted(candidates):
        if groups and candidate[0]-groups[-1][-1][0] < line_height*.7:
            groups[-1].append(candidate)
        else:
            groups.append([candidate])
    accepted = []
    for group in groups:
        intervals = sorted((x0, x1) for _,x0,x1 in group)
        total = 0.; end = -1.
        for a,b in intervals:
            total += max(0., b-max(a,end)); end=max(end,b)
        if total > (content[2]-content[0])*.65:
            accepted.append(float(np.median([y for y,_,_ in group])))
    for y in morphology:
        if not any(abs(y-old)<line_height for old in accepted):accepted.append(y)
    return sorted(accepted)


def detect(image, lines):
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    if gray is None or not lines:
        raise ValueError('Image ou lignes automatiques absentes')
    height, width = gray.shape
    boxes = np.array([r.get('detector_bbox', r['bbox']) for r in lines])
    line_height = float(np.median(boxes[:, 3]-boxes[:, 1]))
    content = [int(boxes[:, 0].min()), int(boxes[:, 1].min()),
               int(boxes[:, 2].max()), int(boxes[:, 3].max())]
    centers = column_starts(boxes, width, line_height)
    separators = horizontal_separators(gray, content, line_height)
    # Un filet peut passer au milieu d'un folio ou d'un titre courant.
    # Rattacher ces caractères à l'en-tête avant de couper la bande.
    if separators:
        first=separators[0]
        margin=line_height*.5 if first-content[1]<2*line_height else 0
        crossing=boxes[(boxes[:,1]<first)&(boxes[:,3]>first)&
                       ((boxes[:,1]+boxes[:,3])/2<=first+margin)&
                       (boxes[:,3]<=first+line_height)]
        if len(crossing):separators[0]=float(crossing[:,3].max())
    cuts = [max(0, content[1]-int(line_height*.3))]
    cuts += [int(y) for y in separators]
    cuts += [min(height, content[3]+int(line_height*.3))]
    regions = []
    for band, (top, bottom) in enumerate(zip(cuts, cuts[1:])):
        selected = boxes[((boxes[:, 1]+boxes[:, 3])/2 >= top) &
                         ((boxes[:, 1]+boxes[:, 3])/2 < bottom)]
        if not len(selected):
            if bottom-top>=line_height*.3:
                regions.append(dict(id=f'b{band+1:02d}_c01',kind='undetected_band',
                                    bbox=[max(0,content[0]-int(line_height*.3)),top,
                                          min(width,content[2]+int(line_height*.3)),bottom],order=len(regions)+1))
            continue
        # Une bande d'en-tête n'est pas artificiellement divisée en colonnes.
        starts = column_starts(selected, width, line_height) if len(selected) >= 12 else [content[0]]
        if len(starts) == 1:
            spans = [(max(0, int(content[0]-line_height*.3)),
                      min(width, int(content[2]+line_height*.3)))]
        else:
            typical = float(np.median(np.diff(starts)))
            spans = []
            for i, start in enumerate(starts):
                # Chaque frontière est fondée sur les extents robustes des
                # lignes voisines, avec marge contre le bruit du détecteur.
                near = selected[np.abs(selected[:, 0]-start) < typical*.2]
                normal = near[(near[:, 2]-near[:, 0]) < typical*1.15]
                left = np.percentile(near[:, 0], 10) if len(near) else start
                right = np.percentile(normal[:, 2], 99) if len(normal) else start+typical
                spans.append((max(0, int(left-line_height*.3)),
                              min(width, int(right+line_height*.18))))
        for index, (left, right) in enumerate(spans):
            regions.append(dict(id=f'b{band+1:02d}_c{index+1:02d}', kind='automatic_region',
                                bbox=[left, top, right, bottom], order=len(regions)+1))
    regions = separate_spanning_regions(regions, boxes.tolist(), line_height, gray)
    assignments, unassigned, ambiguous, crossing = {}, [], [], []
    for line, box in zip(lines, boxes.tolist()):
        x, y = (box[0]+box[2])/2, (box[1]+box[3])/2
        hits = [r for r in regions if r['bbox'][0] <= x < r['bbox'][2] and r['bbox'][1] <= y < r['bbox'][3]]
        if not hits:
            unassigned.append(line['id'])
        elif len(hits) > 1:
            ambiguous.append(line['id'])
        else:
            assignments[line['id']] = hits[0]['id']
            a,b,c,d = hits[0]['bbox']
            if box[0] < a-line_height*.2 or box[2] > c+line_height*.2 or box[1] < b or box[3] > d:
                crossing.append(line['id'])
    return dict(version=VERSION, image=str(Path(image).resolve()), image_sha256=sha256(image),
                regions=regions, coordinate_system='source_pixels_xyxy', reference_used=False,
                parameters=dict(line_height=line_height, column_starts=centers, separators=separators),
                audit=dict(detected_lines=len(lines), assigned_lines=len(assignments),
                           unassigned=unassigned, ambiguous=ambiguous, crossing=crossing,
                           requires_review=bool(unassigned or ambiguous or crossing)),
                line_regions=assignments)


def write_plan(image, segmentation, output):
    lines = load_automatic_lines(image, segmentation)
    plan = detect(image, lines)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_json(output/'plan.json', plan)
    with Image.open(image) as page:
        preview = page.convert('RGB')
    draw = ImageDraw.Draw(preview)
    for region in plan['regions']:
        draw.rectangle(region['bbox'], outline='red', width=max(2, preview.width//1000))
    preview.thumbnail((1500, 1800))
    preview.save(output/'plan-preview.jpg')
    return plan


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image'); p.add_argument('segmentation'); p.add_argument('output')
    a = p.parse_args()
    result = write_plan(a.image, a.segmentation, a.output)
    print(json.dumps(dict(regions=len(result['regions']), parameters=result['parameters'], audit=result['audit'])))
