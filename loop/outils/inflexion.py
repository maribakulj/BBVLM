"""I01 — signe d'inflexion de l'imprimeur, décidé par page en pleine résolution.

P7 (déclaration par le lecteur) a échoué : à la résolution des bandes, le
lecteur ne distingue pas l'anneau (ů) du e réduit (uͤ) ; l'arbitre, sur la
ligne recadrée en pleine résolution, le fait (herbdulc : anneau, deux
arbitres ; herrleyc : e). On recadre donc jusqu'à 4 lignes portant des mots à
signe sur u (ů ou uͤ dans le texte P3), agrandies ; un arbitre dit pour chaque
mot « anneau » ou « e » ; la majorité donne le signe de la page (zoom ciblé,
L03). Application : anneau → tout uͤ devient ů ; e → R2 (ů des mots à
inflexion → uͤ, ů des diphtongues uo gardés).
usage : python inflexion.py prepare DOSSIER → DOSSIER/inflexion/taches.json
        python inflexion.py applique DOSSIER → DOSSIER/p3i_final.txt
"""
import json, os, re, sys, unicodedata
import cv2

E_ = 'ͤ'
SIGNE = re.compile('ů|u' + E_)


def _texte(d):
    return [unicodedata.normalize('NFC', l) for l in open(f'{d}/p3_final.txt', encoding='utf-8').read().splitlines() if l.strip()]


def prepare(d, n_max=4):
    T = _texte(d)
    cand = [i for i, l in enumerate(T) if SIGNE.search(l)]
    os.makedirs(f'{d}/inflexion', exist_ok=True)
    if not cand:
        json.dump([], open(f'{d}/inflexion/taches.json', 'w')); print(d, 'aucun signe sur u'); return
    kr = [l['bbox'] for l in json.load(open(f'{d}/kraken_serre.json'))['lignes']]
    from ancre import lit_lignes, aligne_ancre
    loc = aligne_ancre(T, kr, lit_lignes(d, kr, 'fraktur'))
    img = cv2.imread(f'{d}/page.png'); H, W = img.shape[:2]
    taches, vus = [], set()
    for i in cand:                              # lignes aux mots les plus variés d'abord
        if i not in loc: continue
        mots = [m for m in T[i].split() if SIGNE.search(m)]
        if all(m in vus for m in mots) and len(taches) >= 2: continue
        vus.update(mots)
        x0, y0, x1, y1 = kr[loc[i]]; h = y1 - y0
        c = img[max(0, y0-h//3):min(H, y1+h//3), max(0, x0-10):min(W, x1+10)]
        f = max(1.0, min(3.0, 2400/max(1, c.shape[1])))
        nom = f'i{i:03d}.png'
        cv2.imwrite(f'{d}/inflexion/{nom}', cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC))
        taches.append({'id': f'i{i:03d}', 'image': nom, 'ligne': T[i],
                       'mots': [SIGNE.sub('u*', m) for m in mots]})
        if len(taches) >= n_max: break
    json.dump(taches, open(f'{d}/inflexion/taches.json', 'w'), ensure_ascii=False, indent=1)
    print(d.rstrip('/').split('/')[-1], 'lignes à signe', len(cand), 'tâches', len(taches))


def signe_page(d):
    try: v = json.load(open(f'{d}/inflexion/verdicts.json'))
    except FileNotFoundError: return None
    from r2 import decide
    taches = {t['id']: t for t in json.load(open(f'{d}/inflexion/taches.json'))}
    n = {'anneau': 0, 'e': 0}
    for t in v:
        mots = taches.get(t['id'], {}).get('mots', [])
        for m, s in zip(mots, t.get('signes', [])):
            # seuls les mots à inflexion comptent (DasWeL : ů = uo et uͤ = ü sur la même page)
            if s in n and decide(m.replace('u*', 'ů')) == 'uͤ': n[s] += 1
    if n['anneau'] == n['e']: return None
    return 'anneau' if n['anneau'] > n['e'] else 'e'


def applique(d):
    s = signe_page(d); T = _texte(d)
    from r2 import decide
    if s == 'anneau':     # l'imprimeur note l'inflexion par l'anneau : uͤ des mots à inflexion → ů
        T = [' '.join(m.replace('u' + E_, 'ů') if 'u' + E_ in m and decide(m) == 'uͤ' else m for m in l.split(' ')) for l in T]
    elif s == 'e':        # par le e suscrit : ů des mots à inflexion → uͤ (R2)
        T = [' '.join(m.replace('ů', 'u' + E_) if 'ů' in m and decide(m) == 'uͤ' else m for m in l.split(' ')) for l in T]
    open(f'{d}/p3i_final.txt', 'w').write('\n'.join(T))
    print(d.rstrip('/').split('/')[-1], 'signe de page :', s)


if __name__ == '__main__':
    {'prepare': prepare, 'applique': applique}[sys.argv[1]](sys.argv[2].rstrip('/'))
