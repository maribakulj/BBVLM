"""G03 — boîte de ligne prédite resserrée sur l'encre de son polygone kraken.

Le rectangle englobant du polygone kraken mord sur les lignes voisines ; les
boîtes de ligne de référence OCR-D sont serrées sur les glyphes. On garde
l'encre (Otsu local) à l'intérieur du polygone seulement, et la boîte de ligne
devient l'enveloppe de cette encre, en écartant les composantes minuscules.
Développement sur les pages déjà utilisées en G01/E01.
"""
import json, os, sys
import numpy as np, cv2
from e01 import e01


def resserre(gray, boundary, bbox, aire_min=6, baseline=None, autres=None):
    x0, y0, x1, y1 = bbox
    H, W = gray.shape
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W-1, x1), min(H-1, y1)
    crop = gray[y0:y1+1, x0:x1+1]
    if crop.size < 16: return bbox
    m = np.zeros(crop.shape, np.uint8)
    cv2.fillPoly(m, [np.array([[p[0]-x0, p[1]-y0] for p in boundary], np.int32)], 1)
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    if os.environ.get('BBVLM_G04', '0') == '1':
        keep_m = _proprietaires(gray, (x0, y0, x1, y1), bw, m, baseline, autres)
        bw = bw*m*keep_m
    else:
        bw = bw*m
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= aire_min]
    if not keep: return bbox
    xs0 = min(st[i, 0] for i in keep); ys0 = min(st[i, 1] for i in keep)
    xs1 = max(st[i, 0]+st[i, 2]-1 for i in keep); ys1 = max(st[i, 1]+st[i, 3]-1 for i in keep)
    pad = int(round(float(os.environ.get('BBVLM_G04_PAD', '0')) * (ys1 - ys0))) if os.environ.get('BBVLM_G04', '0') == '1' else 0
    return [int(x0+xs0), int(max(0, y0+ys0-pad)), int(x0+xs1), int(min(H-1, y0+ys1+pad))]


TOL = float(__import__('os').environ.get('BBVLM_G04_TOL', '0.2'))


def _proprietaires(gray, box, bw, m, baseline, autres=None):
    """G04 (L14) : une composante coupée par le polygone appartient à la ligne
    qui porte la majorité de son encre ; celle qui traverse la ligne de base
    appartient à cette ligne. On écarte donc de la ligne les bouts de hampes et
    de jambages des lignes voisines (ſ, p, g de la ligne du dessus)."""
    x0, y0, x1, y1 = box
    H, W = gray.shape; h = y1 - y0
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0 - h), min(W-1, x1), min(H-1, y1 + h)
    big = gray[Y0:Y1+1, X0:X1+1]
    _, bb = cv2.threshold(big, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bb, 8)
    oy, ox = y0 - Y0, x0 - X0
    sub = lab[oy:oy+bw.shape[0], ox:ox+bw.shape[1]]
    dedans = np.bincount((sub * (m > 0)).ravel(), minlength=n)
    total = st[:, cv2.CC_STAT_AREA]
    if autres is not None and os.environ.get('BBVLM_G04_MODE', 'autres') == 'autres':
        # G04b : retirée seulement si la majorité de son encre est dans le polygone
        # d'une AUTRE ligne (jambage de la ligne du dessus) ; un accent, un point,
        # un e suscrit flottent entre les polygones et restent à leur ligne
        ma = np.zeros(big.shape, np.uint8)
        for poly in autres:
            cv2.fillPoly(ma, [np.array([[p[0]-X0, p[1]-Y0] for p in poly], np.int32)], 1)
        mp = np.zeros(big.shape, np.uint8)
        mp[oy:oy+bw.shape[0], ox:ox+bw.shape[1]] = m
        ma[mp > 0] = 0
        ailleurs = np.bincount((lab * ma).ravel(), minlength=n)
        a_moi = np.bincount((lab * mp).ravel(), minlength=n)
        garde = ailleurs <= a_moi
    else:
        garde = dedans >= 0.5 * np.maximum(total, 1)
    if baseline and len(baseline) >= 2:
        px, py = zip(*sorted(baseline))
        for i in np.nonzero(~garde & (dedans > 0))[0]:
            cx0, cy0, cw, ch = st[i, 0] + X0, st[i, 1] + Y0, st[i, 2], st[i, 3]
            yb = float(np.interp(cx0 + cw / 2, px, py))
            tol = TOL * h                        # ligne de base kraken parfois sous le pied des lettres
            if cy0 - tol <= yb <= cy0 + ch + tol: garde[i] = True
    garde[0] = False
    return garde[sub].astype(np.uint8)


if __name__ == '__main__':
    import connexe
    b = connexe.Connexe()
    for arg in sys.argv[1:]:
        d, lec = arg.split('=')
        k = json.load(open(f'{d}/kraken.json'))
        g = cv2.imread(f'{d}/page.png', cv2.IMREAD_GRAYSCALE)
        for l in k['lignes']:
            l['bbox_brut'] = l.get('bbox_brut', l['bbox'])
            l['bbox'] = resserre(g, l['boundary'], l['bbox_brut'])
        json.dump(k, open(f'{d}/kraken_serre.json', 'w'))
        s, r = e01(d, lec, b, 'kraken_serre.json')
        nom = d.rstrip('/').split('/')[-1][:10]
        print(f"{nom:10s} S01 trouvées {s.get('trouvees_iou50')}/{s.get('ref')} IoU méd {s.get('iou_med', 0):.3f} || E01s lignes {r['lignes']} échec {r['lignes_en_echec']} ≤0,5c {r['pct_sous_0.5c']} pire {r['err_max']} IoU méd {r['iou_med']}", flush=True)
