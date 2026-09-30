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
    A = lignes(f'{d}/lu_a.txt')
    # mode économe : une seule lecture (pas de lu_b) → aucune tâche, texte = A (+ I01)
    B = lignes(f'{d}/lu_b.txt') if os.path.exists(f'{d}/lu_b.txt') else A
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
    # P3b (O15, cingdei) : une ligne que seule B porte (A l'a omise) devient aussi
    # une tâche — X/Y = la ligne ou rien ; retenue, elle est insérée après la
    # ligne de A appariée à la ligne de B qui la précède.
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from cer import lev
    ins = []
    if B is not A and A and B:
        C = np.array([[lev(a, b)/max(1, len(a)) for b in B] for a in A])
        ra, rb = linear_sum_assignment(C)
        mB = {int(j): int(i) for i, j in zip(ra, rb) if C[i, j] <= 1}
        locB = aligne(B, kr)
        for j, b in enumerate(B):
            if j in mB or not b.strip(): continue
            prec = [k for k in mB if k < j]
            pos = mB[max(prec)] if prec else -1
            nom = f'b{j:03d}.png'
            if j in locB:
                x0, y0, x1, y1 = kr[locB[j]]; h = y1-y0
                c = img[max(0, y0-h//2):min(H, y1+h//2), max(0, x0-20):min(W, x1+20)]
                f = max(1.0, min(3.0, 2400/max(1, c.shape[1])))
                cv2.imwrite(f'{d}/p3/{nom}', cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC))
            x, y = (b, '') if rng.random() < .5 else ('', b)
            taches.append({'id': f'b{j:03d}', 'image': nom, 'X': x, 'Y': y,
                           'divergences_X_vers_Y': [(x, y)], 'note': 'ligne portée par une seule lecture : existe-t-elle ?'})
            ins.append((pos, f'b{j:03d}'))
    json.dump(taches, open(f'{d}/p3/taches.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(A, open(f'{d}/p3/base_A.json', 'w'), ensure_ascii=False)
    json.dump(ins, open(f'{d}/p3/insertions.json', 'w'))
    print(d.rstrip('/').split('/')[-1], 'lignes A', len(A), 'désaccords arbitrés', len(taches))


def fusionne(d):
    A = json.load(open(f'{d}/p3/base_A.json'))
    v = {x['id']: x for x in json.load(open(f'{d}/p3/verdicts.json'))}
    from p2 import JETONS                 # l'arbitre écrit aussi les jetons {florin}…
    def dejeton(t):
        for j, c in JETONS.items(): t = t.replace(j, c)
        t = t.replace('q\u0301\ua76b', '\uf50d').replace('q\ua76b', '\ue8bf')   # L1 (même table que p2)
        from p2 import parenthese, fraction                         # R3 (désactivée), R5
        t = fraction(parenthese(t))
        return t.replace('\u2019', "'") if os.environ.get('BBVLM_APOS', '1') == '1' else t   # L2
    out = [dejeton(v[f'l{i:03d}']['texte_correct']) if f'l{i:03d}' in v else a for i, a in enumerate(A)]
    try: ins = json.load(open(f'{d}/p3/insertions.json'))
    except FileNotFoundError: ins = []
    for pos, tid in sorted(ins, key=lambda t: -t[0]):        # de la fin vers le début
        t = v.get(tid, {}).get('texte_correct', '').strip()
        if t: out.insert(pos + 1, dejeton(t))
    open(f'{d}/p3_final.txt', 'w').write('\n'.join(l for l in out if l.strip()))


if __name__ == '__main__':
    {'prepare': prepare, 'fusionne': fusionne}[sys.argv[1]](sys.argv[2].rstrip('/'))
