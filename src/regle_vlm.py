"""B40 — lire les frontières de mot sur une règle graduée.

Le VLM ne sait pas estimer une coordonnée dans une image ; il sait LIRE. On
surimprime donc une règle graduée sur la bande de ligne (Set-of-Mark prompting,
Yang et al. 2023 — documenté, pas une trouvaille) et on lui demande de relever
les graduations où le mot commence et finit. La mesure : distance entre ce qu'il
relève et la VT, en fractions de caractère, comparable au critère gelé.
"""
import sys, os, json, random
sys.path.insert(0,'src'); sys.path.insert(0,'src/boxers')
import corpora
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from connexe import Connexe

N = int(sys.argv[1]) if len(sys.argv)>1 else 10
pages=[p for p in corpora.all_pages(limit_per_corpus=2, only_geometric=True)
       if p.corpus in ('BnF','PetitParisien')]
b=Connexe(); cands=[]
for p in pages:
    g=np.array(Image.open(p.image_path).convert('L'))
    for ln in p.lines:
        if len(ln.words)<4 or len(ln.word_boxes)!=len(ln.words): continue
        try: bs=b.boxes(g,ln)
        except Exception: continue
        if len(bs)!=len(ln.words): continue
        for i,(w,pred,vt) in enumerate(zip(ln.words,bs,ln.word_boxes)):
            if not w.isalpha() or len(w)<3: continue
            lc=max(1.0,(vt[2]-vt[0])/len(w))
            e=max(abs(pred[0]-vt[0]),abs(pred[2]-vt[2]))/lc
            cands.append({'mot':w,'img':p.image_path,'lb':list(ln.line_box),
                          'pred':[int(x) for x in pred],'vt':[int(x) for x in vt],
                          'err':round(float(e),2),'larg_car':round(lc,1),'i':i})
print(f"{len(cands)} candidats")
random.seed(5)
qs=[[c for c in cands if c['err']<0.10],
    [c for c in cands if 0.10<=c['err']<0.50],
    [c for c in cands if c['err']>=0.50]]
print('strates :',[len(q) for q in qs])
sel=[]
for q in qs: sel+=random.sample(q,min(max(1,N//3),len(q)))
random.shuffle(sel); sel=sel[:N]

PAS=10           # graduation, en pixels de la bande d'origine
ZOOM=None
planches=[]
for k,s in enumerate(sel,1):
    im=Image.open(s['img']).convert('RGB')
    x0,y0,x1,y1=s['lb']; h=y1-y0
    vx0,vx1=s['vt'][0],s['vt'][2]
    # La marge se prend dans l'IMAGE, pas dans la boîte de ligne : borner par
    # line_box tronque les mots situés au bord de la ligne — c'est ce qui a
    # coupé 3 mots sur 9 au premier tir, et un mot coupé n'est pas mesurable.
    marge=int(max(60,(vx1-vx0)*0.9))
    cx0=max(0,vx0-marge); cx1=min(im.size[0],vx1+marge)
    cy0=max(0,y0-4); cy1=min(im.size[1],y1+4)
    c=im.crop((cx0,cy0,cx1,cy1))
    z=min(6.0, 1200/max(1,c.size[0]))
    c=c.resize((int(c.size[0]*z),int(c.size[1]*z)),Image.LANCZOS)
    R=44
    pl=Image.new('RGB',(c.size[0], c.size[1]+R),(255,255,255))
    pl.paste(c,(0,R)); d=ImageDraw.Draw(pl)
    try: f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    except Exception: f=ImageFont.load_default()
    n=0
    for px in range(0, cx1-cx0, PAS):
        X=int(px*z)
        gros = (n % 5 == 0)
        d.line((X, R-(16 if gros else 8), X, R + (c.size[1] if gros else 6)),
               fill=(255,60,60) if gros else (255,170,170), width=1)
        if gros: d.text((X+2, 2), str(n), fill=(200,0,0), font=f)
        n+=1
    pl.save(f'/tmp/regle_{k:02d}.png')
    s['crop']={'cx0':cx0,'z':z,'pas':PAS}
    planches.append(f'/tmp/regle_{k:02d}.png')
json.dump(sel,open('/tmp/regle_cache.json','w'),ensure_ascii=False)
print(f"{len(sel)} planches écrites ; mots : {[s['mot'] for s in sel]}")
print("erreur connexe cachée :", [s['err'] for s in sel])
