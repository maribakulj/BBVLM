"""B39 — calibrer l'œil du VLM comme instrument de mesure des boîtes.

On tire des mots dans les corpus QUI ONT une VT au mot, on place les boîtes avec
le moteur du dépôt, on en fait une planche SANS la VT. Le VLM juge. On confronte
ensuite son jugement à l'erreur réellement mesurée. Si les deux se suivent, le
VLM devient une règle utilisable là où aucune VT n'existe (Fraktur).
"""
import sys, os, json, random
sys.path.insert(0,'src'); sys.path.insert(0,'src/boxers')
import corpora, ink
import numpy as np
from PIL import Image, ImageDraw
from connexe import Connexe

N = int(sys.argv[1]) if len(sys.argv)>1 else 24
pages = [p for p in corpora.all_pages(limit_per_corpus=3, only_geometric=True)
         if p.corpus in ('BnF','PetitParisien')]
print(f"{len(pages)} pages : {[p.corpus for p in pages]}")
b = Connexe()
cands = []
for p in pages:
    g = np.array(Image.open(p.image_path).convert('L'))
    for ln in p.lines:
        if not ln.words or len(ln.words) < 3 or not ln.word_boxes: continue
        if len(ln.word_boxes) != len(ln.words): continue
        try: bs = b.boxes(g, ln)
        except Exception: continue
        if len(bs) != len(ln.words): continue
        h = ln.line_box[3]-ln.line_box[1]
        for i,(w, pred, vt) in enumerate(zip(ln.words, bs, ln.word_boxes)):
            # erreur de frontière en caractères, comme dans judge.py
            larg_car = max(1.0, (vt[2]-vt[0])/max(1,len(w)))
            e = max(abs(pred[0]-vt[0]), abs(pred[2]-vt[2]))/larg_car
            cands.append({'corpus':p.corpus,'img':p.image_path,'mot':w,
                          'pred':[int(x) for x in pred],'vt':[int(x) for x in vt],
                          'err':round(float(e),2),'h':int(h)})
print(f"{len(cands)} mots candidats")
random.seed(3)
# échantillon STRATIFIÉ sur l'erreur réelle, pour que la planche contienne
# vraiment des cas mauvais — sinon le VLM dit « bon » partout et a raison.
# seuils ABSOLUS : le critère gelé parle en fractions de caractère, la planche
# doit donc contenir des cas de part et d'autre de 0,5 car — sinon le juge dit
# « bon » partout et a raison sans rien prouver.
qs = [[c for c in cands if c['err'] < 0.10],
      [c for c in cands if 0.10 <= c['err'] < 0.50],
      [c for c in cands if c['err'] >= 0.50]]
print('effectifs par strate :', [len(q) for q in qs])
sel=[]
for q in qs: sel += random.sample(q, min(N//3, len(q)))
random.shuffle(sel)
imgs={}
crops=[]
for s in sel:
    if s['img'] not in imgs: imgs[s['img']] = Image.open(s['img']).convert('RGB')
    im = imgs[s['img']]
    x0,y0,x1,y1 = s['pred']; m = max(14, s['h']//2)
    c = im.crop((max(0,x0-m), max(0,y0-m), x1+m, y1+m)).copy()
    d = ImageDraw.Draw(c)
    d.rectangle((x0-max(0,x0-m), y0-max(0,y0-m), x1-max(0,x0-m), y1-max(0,y0-m)),
                outline=(230,0,0), width=2)
    k = min(4.0, 520/max(1,c.size[0]))
    crops.append(c.resize((max(1,int(c.size[0]*k)), max(1,int(c.size[1]*k))), Image.LANCZOS))
# grille 3 colonnes
import math
COL=3; R=math.ceil(len(crops)/COL)
cw=max(c.size[0] for c in crops)+48; ch=max(c.size[1] for c in crops)+26
pl=Image.new('RGB',(cw*COL, ch*R),(255,255,255)); dr=ImageDraw.Draw(pl)
for i,c in enumerate(crops):
    cx,cy = (i%COL)*cw, (i//COL)*ch
    dr.text((cx+8, cy+ch//2-6), f"{i+1:>2}", fill=(0,120,0))
    pl.paste(c,(cx+40, cy+13))
    dr.line((cx+cw-2, cy, cx+cw-2, cy+ch), fill=(220,220,220))
    dr.line((cx, cy+ch-2, cx+cw, cy+ch-2), fill=(220,220,220))
pl.save('/tmp/planche_boites.png')
json.dump(sel, open('/tmp/planche_boites_cache.json','w'), ensure_ascii=False)
print(f"planche {pl.size} — {len(sel)} mots, erreur réelle cachée")
print("distribution de l'erreur réelle dans l'échantillon :",
      [round(float(x),2) for x in np.percentile([s['err'] for s in sel],[10,50,90])])
