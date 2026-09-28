"""G03 — boîte de ligne prédite resserrée sur l'encre de son polygone kraken.

Le rectangle englobant du polygone kraken mord sur les lignes voisines ; les
boîtes de ligne de référence OCR-D sont serrées sur les glyphes. On garde
l'encre (Otsu local) à l'intérieur du polygone seulement, et la boîte de ligne
devient l'enveloppe de cette encre, en écartant les composantes minuscules.
Développement sur les pages déjà utilisées en G01/E01.
"""
import json, sys
import numpy as np, cv2
from e01 import e01


def resserre(gray, boundary, bbox, aire_min=6):
    x0, y0, x1, y1 = bbox
    H, W = gray.shape
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W-1, x1), min(H-1, y1)
    crop = gray[y0:y1+1, x0:x1+1]
    if crop.size < 16: return bbox
    m = np.zeros(crop.shape, np.uint8)
    cv2.fillPoly(m, [np.array([[p[0]-x0, p[1]-y0] for p in boundary], np.int32)], 1)
    _, bw = cv2.threshold(crop, 0, 1, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    bw = bw*m
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= aire_min]
    if not keep: return bbox
    xs0 = min(st[i, 0] for i in keep); ys0 = min(st[i, 1] for i in keep)
    xs1 = max(st[i, 0]+st[i, 2]-1 for i in keep); ys1 = max(st[i, 1]+st[i, 3]-1 for i in keep)
    return [int(x0+xs0), int(y0+ys0), int(x0+xs1), int(y0+ys1)]


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
