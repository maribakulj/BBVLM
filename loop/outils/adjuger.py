"""Prépare une adjudication aveugle lecteur/référence sur l'image.

Pour chaque ligne appariée où lecture et référence diffèrent (vue diplo), on
recadre la ligne de référence (marge verticale d'une demi-hauteur), on
l'agrandit, et on propose les deux textes sous des étiquettes X/Y tirées au
hasard (graine fixe). L'adjudicateur ne sait pas lequel est la référence.
usage : python adjuger.py DOSSIER_PAGE LECTURE1 [LECTURE2...]  -> DOSSIER_PAGE/adj/
"""
import difflib, json, os, random, sys
import cv2
from cer import vue, lev
from accord import apparie


def diff_court(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']


def main(dossier, *lectures):
    ref = json.load(open(f'{dossier}/ref.json')); boites = json.load(open(f'{dossier}/ref_boites.json'))
    img = cv2.imread(f'{dossier}/page.png'); H, W = img.shape[:2]
    idx = [i for i, x in enumerate(ref) if x.strip()]
    R = [vue(ref[i], 'diplo') for i in idx]
    os.makedirs(f'{dossier}/adj', exist_ok=True)
    rng = random.Random(20260928)
    items, vus = [], set()
    for lec in lectures:
        L = [vue(x, 'diplo') for x in open(lec, encoding='utf-8').read().splitlines() if x.strip()]
        for k, h in apparie(R, L).items():
            if h == R[k] or (k, h) in vus: continue
            vus.add((k, h))
            x0, y0, x1, y1 = boites[idx[k]]; m = (y1-y0)//2
            c = img[max(0, y0-m):min(H, y1+m), max(0, x0-20):min(W, x1+20)]
            f = max(1.0, min(3.0, 2400/max(1, c.shape[1])))
            nom = f'l{len(items):03d}.png'
            cv2.imwrite(f'{dossier}/adj/{nom}', cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC))
            ref_est_x = rng.random() < .5
            X, Y = (R[k], h) if ref_est_x else (h, R[k])
            items.append({'id': nom[:-4], 'image': nom, 'X': X, 'Y': Y,
                          'divergences_X_vers_Y': diff_court(X, Y),
                          '_ref': 'X' if ref_est_x else 'Y', '_lecture': lec})
    json.dump(items, open(f'{dossier}/adj/cle.json', 'w'), ensure_ascii=False, indent=1)
    public = [{k: v for k, v in it.items() if not k.startswith('_')} for it in items]
    json.dump(public, open(f'{dossier}/adj/taches.json', 'w'), ensure_ascii=False, indent=1)
    print(len(items), 'items')


if __name__ == '__main__':
    main(*sys.argv[1:])
