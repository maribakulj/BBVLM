import sys, json, os, re, subprocess, urllib.parse
sys.path.insert(0,'/home/user/BBVLM/loop/outils')
exec(open('/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/m03mes.py').read().split("for jeu in")[0])
def personnes_gnd(forme):
    f=f'{S}/m03/P_{re.sub(r"[^A-Za-z0-9]","_",forme)}.json'
    if os.path.exists(f): return json.load(open(f))
    q=urllib.parse.quote(f'preferredName:"{forme}" OR variantName:"{forme}"')
    u=f'https://lobid.org/gnd/search?q={q}&filter=type:Person&format=json&size=3'
    try: d=json.loads(subprocess.run(['curl','-s','-m','30',u],capture_output=True,text=True).stdout)
    except Exception: d={}
    noms=[]
    for m in d.get('member',[]): noms+=[m.get('preferredName','')]+m.get('variantName',[])
    json.dump(noms,open(f,'w'),ensure_ascii=False); return noms
def rads_nom(forme): return {rad(t) for t in nz(forme.split(',')[0])}
T={}; lignes=[]
for n,_ in json.load(open(S+'/m05/oeuvres.json')):
    f=f'{S}/m05v/{n}/lecture.json'
    if not os.path.exists(f): lignes.append(f'{n} : pas de lecture'); continue
    m=json.load(open(f'{S}/m05/{n}/mods.json')); l=json.load(open(f)); ch=l.get('champs',{})
    r=juge(m,l)
    for k,liste in (('auteur',m['auteurs']),('imprimeur',m['imprimeur'])):
        v=(ch.get(k) or {}).get('norme')
        if r[k]=='faux' and v:
            lus={rad(t) for t in nz(v)}
            for p in liste:
                forme=p.get('forme') or p.get('famille') or ''
                cands=rads_nom(forme)|{x for nm in personnes_gnd(forme) for x in rads_nom(nm)}
                if lus & cands: r[k]='juste'; break
    v=(ch.get('lieu') or {}).get('norme')
    if r['lieu']=='faux' and v:
        mods_r={rad(t) for x in m['lieu'] for t in nz(x)}
        if mods_r & ({rad(t) for t in nz(v)}|{rad(t) for nm in lieux_gnd(v) for t in nz(nm)}): r['lieu']='juste'
    src={k:(ch.get(k) or {}).get('source') for k in ('lieu','imprimeur','annee')}
    lignes.append(f"{n:10s} "+' | '.join(f'{k} {v}' for k,v in r.items())+f"   sources {src}")
    for k,vv in r.items(): T[vv.split()[0]]=T.get(vv.split()[0],0)+1
print('\n'.join(lignes)); print('total',T)
pres=T.get('juste',0)+T.get('faux',0); print('justes / présents', T.get('juste',0),'/',pres, f"= {100*T.get('juste',0)/max(1,pres):.1f} %")
