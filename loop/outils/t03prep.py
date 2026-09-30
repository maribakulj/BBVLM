import glob, os, json, re
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
meta=[]; np_=0
for d in sorted(glob.glob(S+'/o*/*/')):
    lec=[x for x in ('p3i_final.txt','p3_final.txt') if os.path.exists(d+x)]
    if not lec or not os.path.exists(d+'adj/verdicts.json') or not os.path.exists(d+'page.alto.xml'): continue
    lu=[l for l in open(d+lec[0]).read().splitlines() if l.strip() and not l.startswith('#')]
    r=etree.parse(d+'page.alto.xml').getroot(); ns={'a':r.tag.split('}')[0][1:]}
    im=Image.open(d+'page.png').convert('RGB'); crops=[]
    for tl in r.iter('{%s}TextLine'%ns['a']):
        ss=tl.findall('a:String',ns)
        if not ss: continue
        txt=' '.join(s.get('CONTENT') for s in ss)
        if not re.search(r'[-⸗=]$', txt): continue
        if txt not in lu: continue
        s=ss[-1]
        if s.get('HPOS') is None or tl.get('VPOS') is None: continue
        x=int(float(s.get('HPOS'))); w=int(float(s.get('WIDTH'))); y=int(float(tl.get('VPOS'))); h=int(float(tl.get('HEIGHT')))
        x1=x+w; x0=max(x, x1-int(1.6*h))
        c=im.crop((x0-4, y-4, x1+int(.4*h), y+h+4))
        crops.append((c, lu.index(txt), txt[-1]))
    if not crops: continue
    page=d.rstrip('/').split('/')[-1]; np_+=1
    # planche : vignettes redimensionnées à 90 px de haut, numérotées
    th=[c.resize((max(1,int(c.size[0]*90/c.size[1])),90)) for c,_,_ in crops]
    cols=6; wmax=max(t.size[0] for t in th)+10
    rows=(len(th)+cols-1)//cols
    sheet=Image.new('RGB',(cols*wmax, rows*120),'white'); dr=ImageDraw.Draw(sheet)
    for k,t in enumerate(th):
        cx,cy=(k%cols)*wmax,(k//cols)*120
        sheet.paste(t,(cx,cy+25)); dr.text((cx+2,cy+2),str(k),fill='red')
    f=f'{S}/t03/{page}.png'; sheet.save(f)
    meta.append({'page':page,'dossier':d,'lecture':lec[0],'planche':f,'items':[{'n':k,'ligne':i,'signe':sg} for k,(_,i,sg) in enumerate(crops)]})
json.dump(meta,open(S+'/t03/meta.json','w'),ensure_ascii=False,indent=1)
print(np_, 'pages', sum(len(m['items']) for m in meta), 'tirets')
