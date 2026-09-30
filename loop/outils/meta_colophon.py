import sys, os
sys.path.insert(0,'/home/user/BBVLM/loop/outils')
from meta_sbb import get, M, X
from lxml import etree
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
EXCL={'binding','cover_front','cover_back','endsheet','paste_down','colour_checker','bookplate'}
for n,ppn in [('AmmoLIBR','895882426'),('buchdas','799145335'),('ferrepit','667769218'),('herrleyc','749899069')]:
    d=f'{S}/m04b/{n}'; os.makedirs(d, exist_ok=True)
    x=get(f'https://oai.sbb.berlin/?verb=GetRecord&metadataPrefix=mets&identifier=oai:digital.staatsbibliothek-berlin.de:PPN{ppn}')
    r=etree.fromstring(x).find(f'.//{M}mets')
    logt={dv.get('ID'):dv.get('TYPE') for dv in r.iter(f'{M}div') if dv.get('TYPE')!='page'}
    liens={}
    for l in r.iter(f'{M}smLink'):
        liens.setdefault(l.get(f'{X}to'),set()).add(logt.get(l.get(f'{X}from')))
    pages=sorted([dv for dv in r.iter(f'{M}div') if dv.get('TYPE')=='page'], key=lambda dv:int(dv.get('ORDER',0)))
    col=[p for p in pages if 'colophon' in liens.get(p.get('ID'),set())]
    sel=col if col else [p for p in pages if not (liens.get(p.get('ID'),set()) & EXCL)][-3:]
    fid={f.get('ID'):f for f in r.iter(f'{M}file')}; grp={f.get('ID'):g.get('USE') for g in r.iter(f'{M}fileGrp') for f in g.iter(f'{M}file')}
    for p in sel:
        for fp in p.iter(f'{M}fptr'):
            if grp.get(fp.get('FILEID'))=='DEFAULT':
                u=fid[fp.get('FILEID')].find(f'{M}FLocat').get(f'{X}href'); fo=f'{d}/p_o{p.get("ORDER")}.jpg'
                if not os.path.exists(fo) or os.path.getsize(fo)<1000: open(fo,'wb').write(get(u))
    print(n, 'colophon METS' if col else 'dernières pages de texte', [p.get('ORDER') for p in sel], flush=True)
