import sys, json, os, re, subprocess, urllib.parse
sys.path.insert(0,'/home/user/BBVLM/loop/outils')
from meta_mesure import nz, juge
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
def fam(forme): return nz(forme.split(',')[0])
SUF=('iae','ii','ae','um','us','i','o','a','e')
def rad(t):
    for _ in range(2):
        for s in SUF:
            if len(t)>4 and t.endswith(s) and len(t)-len(s)>=4: t=t[:-len(s)]; break
    return t
def lieux_gnd(nom):
    f=f'{S}/m03/{re.sub(r"[^A-Za-z0-9]","_",nom)}.json'
    if os.path.exists(f): return json.load(open(f))
    q=urllib.parse.quote(f'preferredName:"{nom}" OR variantName:"{nom}"')
    u=f'https://lobid.org/gnd/search?q={q}&filter=type:PlaceOrGeographicName+OR+type:TerritorialCorporateBodyOrAdministrativeUnit&format=json&size=5'
    try: d=json.loads(subprocess.run(['curl','-s','-m','30',u],capture_output=True,text=True).stdout)
    except Exception: d={}
    noms=[]
    for m in d.get('member',[]): noms+= [m.get('preferredName','')]+m.get('variantName',[])
    json.dump(noms,open(f,'w'),ensure_ascii=False); return noms
for jeu in ['m01v','m01bv','m01cv']:
    T={'M01':{},'M02':{},'M03':{}}
    for n in sorted(os.listdir(S+'/'+jeu)):
        f=f'{S}/{jeu}/{n}/lecture.json'
        if not os.path.exists(f): continue
        m=json.load(open(f'{S}/m01/{n}/mods.json')); l=json.load(open(f))
        r1=juge(m,l); r2=dict(r1)
        g=json.load(open(f'{S}/m02/{n}.json')) if os.path.exists(f'{S}/m02/{n}.json') else {}
        if g and r1['auteur'].split()[0] in ('juste','faux','absent'):
            c=(l.get('champs',{}).get('auteur') or {}); lus=[x for x in [c.get('norme'), c.get('lu')] if x]; lf=set()
            for x in lus:
                for part in str(x).split(';'):
                    t=nz(part)
                    if t: lf.add(' '.join(t)); lf.add(t[-1])
            formes={' '.join(fam(v)) for vs in g.values() for v in vs if fam(v)}
            r2['auteur']='absent' if not lus else ('juste' if lf & formes else 'faux')
        r3=dict(r2); ch=l.get('champs',{})
        v=(ch.get('lieu') or {}).get('norme')
        if r2['lieu']=='faux' and v:
            mods_r={rad(t) for x in m['lieu'] for t in nz(x)}
            cands={rad(t) for t in nz(v)} | {rad(t) for nm in lieux_gnd(v) for t in nz(nm)}
            if mods_r & cands: r3['lieu']='juste'
        v=(ch.get('imprimeur') or {}).get('norme')
        if r2['imprimeur']=='faux' and v:
            im={rad(t) for i in m['imprimeur'] for t in nz(i.get('famille') or i.get('forme','').split(',')[0])}
            if im & {rad(t) for t in nz(v)}: r3['imprimeur']='juste'
        for k in r2:
            if r2[k]!=r3[k]: print(jeu,n,k,r2[k],'→',r3[k])
        for nomr,r in (('M01',r1),('M02',r2),('M03',r3)):
            for k,vv in r.items(): T[nomr][vv.split()[0]]=T[nomr].get(vv.split()[0],0)+1
    print(jeu, {k:(v.get('juste',0),v.get('faux',0)) for k,v in T.items()}, '(justes, faux)')
