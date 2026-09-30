"""M01 — mesure champ par champ : lecture VLM (lecture.json) contre MODS (mods.json).
usage : python meta_mesure.py DOSSIER_MODS DOSSIER_LECTURES  (sous-dossiers par œuvre)"""
import json, os, sys, re, unicodedata


def nz(s):
    s = unicodedata.normalize('NFKD', s or '').replace('ſ', 's').lower()
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('ß', 'ss').replace('ck', 'k')
    s = s.replace('v', 'u').replace('j', 'i')
    return re.sub(r'[^a-z0-9 ]', ' ', s).split()


def juge(m, l):
    ch = l.get('champs', {}); out = {}
    tr = nz(l.get('transcription', ''))
    def val(k): return (ch.get(k) or {}).get('norme')
    # auteur
    fam = [nz(a.get('famille') or a.get('forme', '').split(',')[0]) for a in m['auteurs']]
    fam = [f for f in fam if f]
    v = val('auteur')
    if not fam: out['auteur'] = 'sans VT' if not v else 'VT vide (lu : %s)' % v
    elif not v: out['auteur'] = 'absent'
    else: out['auteur'] = 'juste' if any(f[-1] in nz(v) for f in fam) else 'faux'
    # année
    v = val('annee'); md = re.findall(r'\d{4}', m.get('date') or '')
    if not md: out['annee'] = 'sans VT'
    elif not v: out['annee'] = 'absent'
    else:
        y = re.findall(r'\d{4}', str(v))
        ok = bool(y) and (y[0] == md[0] or ('ca' in (m['date'] or '') and abs(int(y[0]) - int(md[0])) <= 5))
        out['annee'] = 'juste' if ok else 'faux'
    # lieu
    v = val('lieu'); lm = [nz(x) for x in m['lieu'] if nz(x)]
    if not lm: out['lieu'] = 'sans VT'
    elif not v: out['lieu'] = 'absent'
    else: out['lieu'] = 'juste' if any(nz(v)[:1] == x[:1] for x in lm) else 'faux'
    # imprimeur
    v = val('imprimeur')
    im = [nz(i.get('famille') or i.get('forme', '').split(',')[0]) for i in m['imprimeur']]
    im = [x for x in im if x]
    if not im: out['imprimeur'] = 'sans VT' if not v else 'VT vide (lu : %s)' % v
    elif not v: out['imprimeur'] = 'absent'
    else:
        toks = set(nz(v))
        out['imprimeur'] = 'juste' if any(set(x) & toks for x in im) else 'faux'
    # titre : 5 premiers mots du titre MODS dans l'ordre dans la transcription
    t = [w for w in nz((m.get('titre') or '').replace('...', ''))][:5]
    if not t: out['titre'] = 'sans VT'
    else:
        i = 0
        for w in tr:
            if i < len(t) and w == t[i]: i += 1
        out['titre'] = 'juste' if i == len(t) else f'faux ({i}/{len(t)})'
    return out


if __name__ == '__main__':
    dm, dl = sys.argv[1], sys.argv[2]
    tot = {}
    for n in sorted(os.listdir(dl)):
        f = os.path.join(dl, n, 'lecture.json')
        if not os.path.exists(f): continue
        m = json.load(open(os.path.join(dm, n, 'mods.json'))); l = json.load(open(f))
        r = juge(m, l)
        print(f'{n:10s}', ' | '.join(f'{k} {v}' for k, v in r.items()))
        for k, v in r.items(): tot.setdefault(v.split(' ')[0], 0); tot[v.split(' ')[0]] += 1
    print('total', tot)
