"""M01 — notice MODS (VT de métadonnées) et image de la page de titre d'une œuvre SBB.

usage : python meta_sbb.py PPN DOSSIER → DOSSIER/mods.json, DOSSIER/titre.jpg (page de titre,
fichiers DEFAULT) ; si le METS ne marque aucune page de titre : titre.jpg = première page
après la couverture (rapportée dans mods.json['page_titre'])."""
import json, os, sys, urllib.request
from lxml import etree

M = '{http://www.loc.gov/METS/}'; X = '{http://www.w3.org/1999/xlink}'; D = '{http://www.loc.gov/mods/v3}'


def get(u):
    # curl : le mandataire sortant de l'environnement refuse urllib (503), pas curl
    import subprocess, time
    for k in range(6):          # le serveur SBB répond 503 par intermittence
        r = subprocess.run(['curl', '-sfL', '--max-time', '90', u], capture_output=True)
        if r.returncode == 0 and r.stdout: return r.stdout
        time.sleep(2 ** (k + 1))
    raise IOError(f'{u} : échec après 6 essais')


def mods(r):
    m = r.find(f'.//{D}mods')
    out = {'auteurs': [], 'titre': None, 'lieu': [], 'imprimeur': [], 'date': None, 'langue': None, 'vd': None}
    for n in m.findall(f'{D}name'):
        roles = [t.text for t in n.iter(f'{D}roleTerm')]
        fam = n.find(f"{D}namePart[@type='family']"); giv = n.find(f"{D}namePart[@type='given']")
        disp = n.find(f'{D}displayForm')
        v = {'famille': fam.text if fam is not None else None, 'prenom': giv.text if giv is not None else None,
             'forme': disp.text if disp is not None else ' '.join(p.text for p in n.findall(f'{D}namePart') if p.text)}
        if 'aut' in roles: out['auteurs'].append(v)
        elif any(x in roles for x in ('prt', 'pbl')): out['imprimeur'].append(v)
    oi = [o for o in m.findall(f'{D}originInfo') if o.find(f'{D}dateCaptured') is None]
    for o in oi:
        out['lieu'] += [p.text for p in o.iter(f'{D}placeTerm') if p.get('type') == 'text' and p.text]
        out['imprimeur'] += [{'forme': p.text} for p in o.findall(f'{D}publisher') if p.text]
        d = o.find(f'{D}dateIssued')
        if d is not None and d.text: out['date'] = d.text
    ti = m.find(f'{D}titleInfo')
    if ti is not None:
        out['titre'] = ' '.join(x.text for x in ti if x.text)
    la = m.find(f'.//{D}languageTerm')
    out['langue'] = la.text if la is not None else None
    for i in m.findall(f'{D}identifier'):
        if i.get('type') in ('vd16', 'vd17', 'vd18'): out['vd'] = f"{i.get('type').upper()} {i.text}"
    return out


def page_titre(r):
    log = [d.get('ID') for d in r.iter(f'{M}div') if d.get('TYPE') in ('title_page', 'TitlePage')]
    phys = None
    for l in r.iter(f'{M}smLink'):
        if log and l.get(f'{X}from') == log[0]: phys = l.get(f'{X}to'); break
    pdiv = {d.get('ID'): d for d in r.iter(f'{M}div') if d.get('TYPE') == 'page'}
    marque = phys is not None
    if not marque:
        pages = [d for d in pdiv.values()]
        pages.sort(key=lambda d: int(d.get('ORDER', 0)))
        phys = pages[min(2, len(pages) - 1)].get('ID') if pages else None
    fid = {f.get('ID'): f for f in r.iter(f'{M}file')}
    grp = {f.get('ID'): g.get('USE') for g in r.iter(f'{M}fileGrp') for f in g.iter(f'{M}file')}
    for fp in pdiv[phys].iter(f'{M}fptr'):
        if grp.get(fp.get('FILEID')) == 'DEFAULT':
            loc = fid[fp.get('FILEID')].find(f'{M}FLocat')
            return loc.get(f'{X}href'), marque, pdiv[phys].get('ORDER')
    return None, marque, None


if __name__ == '__main__':
    ppn, d = sys.argv[1], sys.argv[2]
    os.makedirs(d, exist_ok=True)
    # point OAI d'abord (content.staatsbibliothek-berlin.de répond 503 par périodes)
    x = get(f'https://oai.sbb.berlin/?verb=GetRecord&metadataPrefix=mets&identifier=oai:digital.staatsbibliothek-berlin.de:{ppn}')
    r = etree.fromstring(x).find(f'.//{M}mets')
    v = mods(r)
    u, marque, ordre = page_titre(r)
    v['page_titre'] = {'url': u, 'marquee_dans_mets': marque, 'ordre': ordre}
    json.dump(v, open(f'{d}/mods.json', 'w'), ensure_ascii=False, indent=1)
    if u and os.environ.get('BBVLM_SANS_IMAGE') != '1':
        open(f'{d}/titre.jpg', 'wb').write(get(u))
    print(ppn, marque, ordre, v['auteurs'][:1], v['date'], v['lieu'][:1])
