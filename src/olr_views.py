"""Vues OLR à pixels natifs, IDs dans une marge extérieure à l'image.

Les vues sont des entrées visuelles, pas des blocs ni des coordonnées prédits
par Gemini. Les groupes et candidats restent ceux de la géométrie automatique.
"""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def starts(a,b,limit,overlap):
    if b-a<=limit:return [a]
    out=list(range(a,b-limit+1,limit-overlap))
    if out[-1]!=b-limit:out.append(b-limit)
    return out


def write_native_views(image,annotations,geometry,regions,directory,limit=1024,overlap=64):
    if limit<=overlap or overlap<0:raise ValueError('dimensions des vues invalides')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    source=Image.open(image).convert('RGB');W,H=source.size
    by_id={a['id']:a for a in annotations}
    if len(by_id)!=len(annotations):raise ValueError('IDs de ligne dupliqués')
    covered=[lid for g in geometry for lid in g['line_ids']]
    if len(covered)!=len(set(covered)) or set(covered)!=set(by_id):
        raise ValueError('Les groupes doivent couvrir toutes les lignes exactement une fois')
    records=[dict(id=g['id'],kind='group',bbox=g['bbox'],line_ids=g['line_ids']) for g in geometry]
    records.extend(dict(id=r['id'],kind='region',bbox=r['bbox'],line_ids=[]) for r in regions)
    if len({r['id'] for r in records})!=len(records):raise ValueError('IDs visuels dupliqués')
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
    except OSError:font=ImageFont.load_default()
    views=[];gutter=144;header=30
    for record in records:
        x0,y0,x1,y1=record['bbox']
        if not all(isinstance(c,(int,float)) and math.isfinite(c) for c in record['bbox']) or not (0<=x0<x1<=W and 0<=y0<y1<=H):
            raise ValueError('Boîte automatique invalide : '+record['id'])
        # Un contexte natif de16px autour du candidat, sans changer sa géométrie.
        left,top,right,bottom=max(0,math.floor(x0)-16),max(0,math.floor(y0)-16),min(W,math.ceil(x1)+16),min(H,math.ceil(y1)+16)
        for yi,y in enumerate(starts(top,bottom,limit,overlap),1):
            for xi,x in enumerate(starts(left,right,limit,overlap),1):
                box=[x,y,min(right,x+limit),min(bottom,y+limit)]
                crop=source.crop(box)
                view=Image.new('RGB',(gutter+crop.width,header+crop.height),'white')
                view.paste(crop,(gutter,header));draw=ImageDraw.Draw(view)
                draw.text((4,4),f'{record["id"]}  part {yi}:{xi}  source {x},{y}  1px=1px',fill='black',font=font)
                lines=[]
                for lid in record['line_ids']:
                    a,b,c,d=by_id[lid]['bbox']
                    if min(c,box[2])<=max(a,x) or min(d,box[3])<=max(b,y):continue
                    lines.append(lid)
                    # Aucune marque ne touche les pixels OCR de la vue.
                    label_y=header+round(max(0,b-y))
                    draw.text((4,label_y),lid,fill='#900000',font=font)
                    draw.line((120,label_y,142,label_y),fill='#900000',width=1)
                path=directory/f'view-{len(views)+1:04d}.png';view.save(path)
                views.append(dict(id=record['id'],kind=record['kind'],path=str(path.resolve()),
                    source_box=box,source_pixels=True,pixel_scale=1,paste_origin=[gutter,header],
                    size=list(view.size),line_ids=lines,part=[yi,xi],
                    native_crop_sha256=hashlib.sha256(crop.tobytes()).hexdigest(),
                    view_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    result=dict(protocol='olr-native-views-v1',image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
                source_image=str(Path(image).resolve()),source_size=[W,H],records=records,views=views,
                geometry_unchanged=True,source='automatic geometry; no references',criteria_met=False)
    (directory/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result
