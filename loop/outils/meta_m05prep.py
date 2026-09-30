import sys, os, json, subprocess
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
O='/home/user/BBVLM/loop/outils'
src=open(S+'/m04bprep.py').read().split("for n,ppn in")[0]
exec(src)
for n,ppn in json.load(open(S+'/m05/oeuvres.json')):
    d=f'{S}/m05/{n}'; os.makedirs(d, exist_ok=True)
    if not os.path.exists(d+'/mods.json'):
        r=subprocess.run([sys.executable, O+'/meta_sbb.py', 'PPN'+ppn, d], capture_output=True, text=True); print(r.stdout.strip()[-200:], r.stderr.strip()[-200:], flush=True)
    x=get(f'https://oai.sbb.berlin/?verb=GetRecord&metadataPrefix=mets&identifier=oai:digital.staatsbibliothek-berlin.de:PPN{ppn}')
    r=etree.fromstring(x).find(f'.//{M}mets')
    logt={dv.get('ID'):dv.get('TYPE') for dv in r.iter(f'{M}div') if dv.get('TYPE')!='page'}
    liens={}
    for l in r.iter(f'{M}smLink'): liens.setdefault(l.get(f'{X}to'),set()).add(logt.get(l.get(f'{X}from')))
    pages=sorted([dv for dv in r.iter(f'{M}div') if dv.get('TYPE')=='page'], key=lambda dv:int(dv.get('ORDER',0)))
    col=[p for p in pages if 'colophon' in liens.get(p.get('ID'),set())]
    sel=col if col else [p for p in pages if not (liens.get(p.get('ID'),set()) & EXCL)][-3:]
    fid={f.get('ID'):f for f in r.iter(f'{M}file')}; grp={f.get('ID'):g.get('USE') for g in r.iter(f'{M}fileGrp') for f in g.iter(f'{M}file')}
    for p in sel:
        for fp in p.iter(f'{M}fptr'):
            if grp.get(fp.get('FILEID'))=='DEFAULT':
                u=fid[fp.get('FILEID')].find(f'{M}FLocat').get(f'{X}href'); fo=f'{d}/fin_o{p.get("ORDER")}.jpg'
                if not os.path.exists(fo) or os.path.getsize(fo)<1000: open(fo,'wb').write(get(u))
    print(n, 'colophon' if col else 'fin de texte', [p.get('ORDER') for p in sel], flush=True)
