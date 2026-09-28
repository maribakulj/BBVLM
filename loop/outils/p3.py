"""Chaîne P3 : deux passes P2, arbitrage VLM des seules lignes en désaccord.

Sans référence. Les lignes de A et B (après P2) sont appariées ; les lignes où
elles diffèrent, et celles qu'une seule passe porte, sont localisées sur la
page par l'alignement lecture → lignes kraken resserrées (`aligne.py`), puis
recadrées avec une demi-hauteur de contexte et agrandies. L'arbitre reçoit
image + deux candidats X/Y (ordre aléatoire) et rend le texte de la ligne.
usage : python p3.py prepare DOSSIER  → DOSSIER/p3/taches.json + images
        python p3.py fusionne DOSSIER → DOSSIER/p3_final.txt
"""
import json, os, random, sys, difflib
import cv2
from p2 import post
from accord import apparie
from aligne import aligne


def lignes(p):
    return [l for l in post(open(p, encoding='utf-8').read().splitlines())[0] if l.strip()]


def prepare(d):
    A, B = lignes(f'{d}/lu_a.txt'), lignes(f'{d}/lu_b.txt')
    m = apparie(A, B)                      # indice A -> texte B
    kr = [l['bbox'] for l in json.load(open(f'{d}/kraken_serre.json'))['lignes']]
    loc = aligne(A, kr)
    img = cv2.imread(f'{d}/page.png'); H, W = img.shape[:2]
    os.makedirs(f'{d}/p3', exist_ok=True)
    rng = random.Random(7); taches = []
    for i, a in enumerate(A):
        b = m.get(i)
        if b == a: continue
        if i not in loc: continue          # non localisée : on garde A, signalé
        x0, y0, x1, y1 = kr[loc[i]]; h = y1-y0
        c = img[max(0, y0-h//2):min(H, y1+h//2), max(0, x0-20):min(W, x1+20)]
        f = max(1.0, min(3.0, 2400/max(1, c.shape[1])))
        nom = f'l{i:03d}.png'
        cv2.imwrite(f'{d}/p3/{nom}', cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC))
        b = b if b is not None else ''
        x, y = (a, b) if rng.random() < .5 else (b, a)
        sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
        taches.append({'id': f'l{i:03d}', 'image': nom, 'X': x, 'Y': y,
                       'divergences_X_vers_Y': [(x[p:q], y[r:s]) for o, p, q, r, s in sm.get_opcodes() if o != 'equal']})
    json.dump(taches, open(f'{d}/p3/taches.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(A, open(f'{d}/p3/base_A.json', 'w'), ensure_ascii=False)
    print(d.rstrip('/').split('/')[-1], 'lignes A', len(A), 'désaccords arbitrés', len(taches))


def fusionne(d):
    A = json.load(open(f'{d}/p3/base_A.json'))
    v = {x['id']: x for x in json.load(open(f'{d}/p3/verdicts.json'))}
    from p2 import JETONS                 # l'arbitre écrit aussi les jetons {florin}…
    def dejeton(t):
        for j, c in JETONS.items(): t = t.replace(j, c)
        return t
    out = [dejeton(v[f'l{i:03d}']['texte_correct']) if f'l{i:03d}' in v else a for i, a in enumerate(A)]
    open(f'{d}/p3_final.txt', 'w').write('\n'.join(l for l in out if l.strip()))


if __name__ == '__main__':
    {'prepare': prepare, 'fusionne': fusionne}[sys.argv[1]](sys.argv[2].rstrip('/'))
