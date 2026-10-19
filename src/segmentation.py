"""Segmentation de pixels uniquement, avec conservation des polygones/baselines."""
from __future__ import annotations
from importlib import resources
from pathlib import Path
import math
import hashlib
import json
import numpy as np
from PIL import Image


def _model_path():
    return resources.files('kraken').joinpath('blla.mlmodel')


def _load_model(path):
    from kraken.lib import vgsl
    return vgsl.TorchVGSLModel.load_model(path)


def atomic_json(path, value):
    path=Path(path);temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def prime_from_suite(image,source,output,strategy,refinement):
    """Réutilise une segmentation achevée du même producteur, jamais du gold."""
    source=Path(source);output=Path(output)
    if (output/'segmentation.json').exists() or (output/'segmentation-config.json').exists():return False
    image_sha=hashlib.sha256(Path(image).read_bytes()).hexdigest()
    expected=dict(image_sha256=image_sha,strategy=strategy,version='blla-rectangles-v1')
    config=source/'segmentation-config.json'
    if not config.exists() or json.loads(config.read_text())!=expected:
        raise ValueError('Segmentation source/configuration/image différente')
    if refinement not in ('none','ink'):raise ValueError('Rétraction inconnue')
    path=source/('segmentation-ink.json' if refinement=='ink' else 'segmentation.json')
    rows=json.loads(path.read_text())
    allowed={'id','bbox','polygon','baseline','interior','tile','source','strategy_requested',
             'resolution_decision','detector_bbox','refinement'}
    if any(set(row)-allowed or not row.get('source','').startswith('kraken-blla/') for row in rows):
        raise ValueError('Entrées non automatiques/interdites dans la segmentation sauvegardée')
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('IDs automatiques dupliqués')
    output.mkdir(parents=True,exist_ok=True)
    if refinement!='none':expected['line_refinement']=refinement
    atomic_json(output/'segmentation.json',rows);atomic_json(output/'segmentation-config.json',expected)
    atomic_json(output/'reused-source-segmentation.json',dict(source=str(path.resolve()),
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),image_sha256=image_sha,
                lines=len(rows),scope='completed automatic producer output; no reference geometry'))
    return True


def refine_lines(image, rows, margin=2):
    """Diagnostic image-only : enveloppe des composantes d'encre de la ligne.

    Conserve les anciens rectangles pour rendre chaque déplacement auditable.
    Cette variante reste expérimentale avant mesure de couverture des glyphes.
    """
    import cv2
    from ink import alignment_mask
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    out=[]
    for row in rows:
        mask,ox,oy=alignment_mask(gray,row['bbox'])
        ys,xs=np.where(mask>0)
        if len(xs):
            old=row['bbox']
            box=[max(old[0],int(xs.min())+ox-margin),max(old[1],int(ys.min())+oy-margin),
                 min(old[2],int(xs.max())+ox+1+margin),min(old[3],int(ys.max())+oy+1+margin)]
            out.append({**row,'bbox':box,'detector_bbox':old,'refinement':'native_ink_margin_2'})
        else:
            out.append({**row,'refinement':'no_ink_preserved'})
    return out


def choose_strategy(image):
    """Éviter les glyphes réduits à moins de 8 pixels dans le réseau BLLA."""
    import cv2
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError('image de segmentation illisible')
    ratio=min(1.,2400/max(gray.shape))
    small=cv2.resize(gray,None,fx=ratio,fy=ratio)
    binary=cv2.adaptiveThreshold(small,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV,51,15)
    _,_,stats,_=cv2.connectedComponentsWithStats(binary,8)
    heights=[h/ratio for x,y,w,h,area in stats[1:]
             if area>=12 and h>=5 and w<4*h and h<.05*small.shape[0]]
    median=float(np.median(heights)) if heights else 0.
    projected=median*1800/gray.shape[0]
    return ('tiles' if projected<8 else 'full'),dict(median_component_height=median,
            projected_height=projected,minimum_projected_height=8,network_height=1800)


def ink_network_height(image,target_glyph_height=20):
    """Échelle expérimentale pondérée par l'encre, indépendante des annotations.

    Une bande de cinq lignes ne doit pas exclure les corps de caractères au
    motif qu'ils dépassent 5 % de sa hauteur : ce filtre ne gardait que les points.
    La hauteur relative au document ne détermine pas la taille d'un glyphe.
    """
    import cv2
    gray=cv2.imread(str(image),cv2.IMREAD_GRAYSCALE)
    if gray is None:raise ValueError('image illisible')
    ratio=min(1.,2400/max(gray.shape));small=cv2.resize(gray,None,fx=ratio,fy=ratio)
    binary=cv2.adaptiveThreshold(small,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV,51,15)
    _,_,stats,_=cv2.connectedComponentsWithStats(binary,8)
    components=sorted((float(h)/ratio,int(area)) for x,y,w,h,area in stats[1:]
                       if area>=12 and 3<=h<=max(100,small.shape[0]*.15) and w<=4*h)
    if not components:raise ValueError('Aucun corps d’encre mesurable pour l’échelle')
    cumulative=np.cumsum([area for h,area in components])
    scale=components[int(np.searchsorted(cumulative,cumulative[-1]/2))][0]
    height=max(32,round(gray.shape[0]*target_glyph_height/scale))
    return height,dict(method='ink-area-weighted-native-component-height-v1',
                       glyph_height=scale,target_glyph_height=target_glyph_height,network_height=height,
                       image_size=[gray.shape[1],gray.shape[0]],promoted=False)


def tile_starts(length, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError('recouvrement de tuiles invalide')
    if length <= size:
        return [0]
    starts=list(range(0,length-size+1,size-overlap))
    if starts[-1] != length-size:
        starts.append(length-size)
    return starts


def deduplicate(candidates):
    """Préférer le recadrage complet, sans fusionner des colonnes disjointes."""
    kept=[]
    for candidate in sorted(candidates,key=lambda c:(-c['interior'],-(c['bbox'][2]-c['bbox'][0]))):
        x0,y0,x1,y1=candidate['bbox']
        duplicate=False
        for other in kept:
            a,b,c,d=other['bbox']
            xov=max(0,min(c,x1)-max(a,x0))/max(1,min(c-a,x1-x0))
            yov=max(0,min(d,y1)-max(b,y0))/max(1,min(d-b,y1-y0))
            if xov >= .8 and yov >= .65:
                duplicate=True
                break
        if not duplicate:
            kept.append(candidate)
    kept.sort(key=lambda c:(c['bbox'][1],c['bbox'][0]))
    for i,c in enumerate(kept,1):
        c['id']=f'L{i:04d}'
    return kept


def segment(image, strategy='full', tile_width=2400, tile_height=2000,
            overlap_x=1200, overlap_y=400, layout_candidates=None,cache_directory=None,network_height=None):
    from kraken import blla
    im=Image.open(image).convert('L')
    requested=strategy
    decision=None
    if strategy in ('auto','auto-v2'):
        strategy,decision=choose_strategy(image)
        if requested=='auto-v2' and im.height<1800:
            if network_height is not None:raise ValueError('Échelle automatique et explicite incompatibles')
            network_height,proof=ink_network_height(image)
            strategy='full';decision['short_canvas_scale']=proof
        print(f'  segmentation auto : {strategy}, projection {decision["projected_height"]:.2f} px',flush=True)
    model=None;model_path=_model_path()
    fingerprint=dict(image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
                     model_sha256=hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),
                     strategy=strategy,version='blla-rectangles-v1')
    if network_height is not None:
        if strategy=='regions' or not isinstance(network_height,int) or network_height<32:
            raise ValueError('Hauteur réseau expérimentale invalide')
        fingerprint['network_height']=network_height
    cache=Path(cache_directory) if cache_directory else None
    if cache:cache.mkdir(parents=True,exist_ok=True)
    if strategy == 'full':
        tiles=[(0,0,im.width,im.height)]
    elif strategy == 'tiles':
        tiles=[(x,y,min(im.width,x+tile_width),min(im.height,y+tile_height))
               for y in tile_starts(im.height,tile_height,overlap_y)
               for x in tile_starts(im.width,tile_width,overlap_x)]
    elif strategy == 'regions':
        from bb_layout import text_regions
        if layout_candidates is None:
            raise ValueError('regions exige les candidats image-only de mise en page')
        tiles=[]
        for region in text_regions(layout_candidates):
            x0,y0,x1,y1=region['bbox']
            x0=max(0,math.floor(x0)-16);y0=max(0,math.floor(y0)-16)
            x1=min(im.width,math.ceil(x1)+16);y1=min(im.height,math.ceil(y1)+16)
            tiles.extend((x0,y0+dy,x1,min(y1,y0+dy+2400))
                         for dy in tile_starts(y1-y0,2400,400))
    else:
        raise ValueError(f'segmenteur inconnu : {strategy}')
    candidates=[]
    completed=[]
    for ti,(ox,oy,ex,ey) in enumerate(tiles,1):
        key=hashlib.sha256(json.dumps({**fingerprint,'tile':[ox,oy,ex,ey]},sort_keys=True).encode()).hexdigest()
        tile_file=cache/(key+'.json') if cache else None
        if tile_file and tile_file.exists():
            try:
                saved=json.loads(tile_file.read_text())
                if saved['key']!=key:raise ValueError('cache de tuile incohérent')
                tile_candidates=saved['candidates']
                for row in tile_candidates:
                    row.update(tile=ti,strategy_requested=requested,resolution_decision=decision)
                candidates.extend(tile_candidates);completed.append(key)
                print(f'  segmentation {strategy} : tuile {ti}/{len(tiles)}, cache {len(tile_candidates)} lignes',flush=True)
                continue
            except (ValueError,KeyError,TypeError):
                tile_file.rename(tile_file.with_suffix('.corrupt'))
        if model is None:
            model=_load_model(model_path)
            if network_height is not None:model.input=(1,3,network_height,0)
        crop=im.crop((ox,oy,ex,ey))
        if strategy == 'regions':
            # Le réseau conserve ici l'échelle physique du recadrage. Une
            # courte région n'est pas agrandie artificiellement à 1800 px.
            if crop.height < 600:
                canvas=Image.new('L',(crop.width,600),255)
                canvas.paste(crop,(0,0));crop=canvas
            model.input=(1,3,min(crop.height,2400),0)
        try:
            seg=blla.segment(crop,model=model)
        except Exception as exc:
            if cache:atomic_json(cache/'state.json',dict(**fingerprint,completed=completed,
                                  failed_tile=[ox,oy,ex,ey],error=str(exc),status='interrupted'))
            raise
        tile_candidates=[]
        for line in seg.lines:
            pts=np.asarray(line.boundary,float)+[ox,oy]
            if not len(pts):
                continue
            bbox=[max(0,math.floor(pts[:,0].min())),max(0,math.floor(pts[:,1].min())),
                  min(im.width,int(pts[:,0].max())),min(im.height,int(pts[:,1].max()))]
            x0,y0,x1,y1=bbox
            if x1 <= x0 or y1 <= y0:
                continue
            interior=(ox == 0 or x0>ox+10) and (oy == 0 or y0>oy+10) and \
                     (ex == im.width or x1<ex-10) and (ey == im.height or y1<ey-10)
            baseline=(np.asarray(line.baseline,float)+[ox,oy]).tolist()
            if min(p[1] for p in baseline) >= ey:
                continue
            tile_candidates.append(dict(bbox=bbox,polygon=pts.tolist(),baseline=baseline,
                                   interior=bool(interior),tile=ti,source='kraken-blla/'+strategy,
                                   strategy_requested=requested,resolution_decision=decision))
        candidates.extend(tile_candidates);completed.append(key)
        if cache:
            atomic_json(tile_file,dict(key=key,candidates=tile_candidates))
            atomic_json(cache/'state.json',dict(**fingerprint,completed=completed,total=len(tiles),status='running'))
        print(f'  segmentation {strategy} : tuile {ti}/{len(tiles)}, {len(seg.lines)} lignes',flush=True)
    if cache:atomic_json(cache/'state.json',dict(**fingerprint,completed=completed,total=len(tiles),status='completed'))
    return deduplicate(candidates)


if __name__ == '__main__':
    import argparse,json,time
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('output')
    ap.add_argument('--strategy',choices=('full','tiles','auto','auto-v2','regions'),default='auto')
    ap.add_argument('--layout-candidates');args=ap.parse_args()
    import hashlib
    layout=None
    if args.layout_candidates:
        layout=json.loads(Path(args.layout_candidates).read_text())
        if layout['image_sha256'] != hashlib.sha256(Path(args.image).read_bytes()).hexdigest():
            raise ValueError('candidats issus d’une autre image')
    t=time.time();rows=segment(args.image,args.strategy,layout_candidates=layout)
    Path(args.output).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(rows)} lignes, {time.time()-t:.1f} s',flush=True)
