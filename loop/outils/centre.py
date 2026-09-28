"""B01 — boîtes de mots sur une ligne redressée autour de son centre local.

Le filtre de composantes de connexe juge chaque composante contre le centre
de la boîte de ligne ; sur une ligne inclinée ou courbe (heptaldai : ≈ 40 px
de dérive), ce centre constant garde l'encre des voisines. On estime le
centre local comme OCRopus (lineest.CenterNormalizer, L07) : argmax colonne
par colonne de l'encre lissée (σ 0,5 h × 1 h), lissé à 0,3 h. On décale
chaque colonne pour rendre ce centre horizontal, on calcule les boîtes avec
Route sur la bande droite, puis on reprojette : x inchangé, y élargi du
décalage min/max sur les colonnes du mot (enveloppe du mot incliné).
"""
import copy
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from g02 import Route

SEUIL = float(__import__('os').environ.get('BBVLM_CENTRE_SEUIL', '0.25'))   # dérive / hauteur de ligne


def centre_local(gray, box):
    """Rend (décalage par colonne en px, ligne médiane, bord haut du rognage)."""
    x0, y0, x1, y1 = box
    H, W = gray.shape
    h = max(4, y1 - y0)
    ay0, ay1 = max(0, y0 - h // 4), min(H, y1 + h // 4)
    crop = gray[ay0:ay1, max(0, x0):min(W, x1 + 1)].astype(np.float32)
    ink = 255 - cv2.divide(crop, cv2.GaussianBlur(crop, (0, 0), max(2.0, h * .45)), scale=255)
    ink = np.clip(ink - np.median(ink), 0, None)
    sm = gaussian_filter(ink, (h * .5, h * 1.0), mode='constant')
    c = gaussian_filter1d(np.argmax(sm, axis=0).astype(float), h * .3)
    return c - np.median(c), float(np.median(c)) + ay0, ay0


class Centre(Route):
    name = 'centre+route'

    def boxes(self, g, ln):
        x0, y0, x1, y1 = ln.line_box
        H, W = g.shape
        s, _, _ = centre_local(g, ln.line_box)
        s = np.round(s).astype(int)
        amp = int(s.max() - s.min())
        if amp < SEUIL * (y1 - y0):                  # ligne assez droite : Route tel quel
            # (B01 : redresser une ligne droite coûte 1-4 pts sur AmmoLIBR, DasWeL)
            return super().boxes(g, ln)
        return redresse(self, g, ln, s)


def redresse(boxer, g, ln, s):
    """Boîtes Route sur la bande redressée (décalage s par colonne), reprojetées."""
    x0, y0, x1, y1 = ln.line_box
    H, W = g.shape
    amp = int(s.max() - s.min())
    xa = max(0, x0)
    pad = amp + 2
    top, bot = max(0, y0 - pad), min(H, y1 + pad + 1)
    band = np.full((bot - top + 2 * pad, W), 255, g.dtype)
    band[pad:pad + bot - top] = g[top:bot]
    droit = np.full((bot - top, W), 255, g.dtype)
    for i, d in enumerate(s):                     # colonne xa+i remontée de d
        x = xa + i
        droit[:, x] = band[pad + d:pad + d + bot - top, x]
    l2 = copy.copy(ln)
    # boîte de la ligne droite : hauteur réelle du corps, sans la dérive
    l2.line_box = (x0, y0 - top + max(0, s.max()), x1, y1 - top + min(0, s.min()))
    out = []
    for (a, b, c, d) in Route.boxes(boxer, droit, l2):
        i0, i1 = max(0, a - xa), min(len(s) - 1, c - xa)
        seg = s[i0:i1 + 1] if i1 >= i0 else s[:1]
        out.append((a, b + top + int(seg.min()), c, d + top + int(seg.max())))
    return out


class LigneBase(Route):
    """B02 — même redressement, mais la dérive vient de la ligne de base kraken
    (polyligne), pas d'une estimation sur l'encre. `bases` : {bbox: baseline}."""
    name = 'base+route'
    SEUIL = float(__import__('os').environ.get('BBVLM_BASE_SEUIL', '0.15'))

    def __init__(self, bases=None):
        super().__init__(); self.bases = bases or {}
        # B04 : la dérive est une propriété de la PAGE (gondolage, inclinaison) :
        # on ne redresse que si la dérive médiane des lignes de base ≥ SEUIL·h
        # (pages droites : les rares lignes « penchées » sont du bruit de ligne de base)
        r = []
        for bb, bl in self.bases.items():
            if bl and len(bl) >= 2:
                ys = [p[1] for p in bl]; r.append((max(ys) - min(ys)) / max(1, bb[3] - bb[1]))
        self.page_penchee = bool(r) and float(np.median(r)) >= self.SEUIL

    def boxes(self, g, ln):
        x0, y0, x1, y1 = ln.line_box
        if not self.page_penchee and __import__('os').environ.get('BBVLM_BASE_PAGE', '1') == '1':
            return super().boxes(g, ln)
        bl = self.bases.get(tuple(int(v) for v in ln.line_box))
        if not bl or len(bl) < 2: return super().boxes(g, ln)
        xs = np.arange(max(0, x0), x1 + 1)
        px, py = zip(*sorted(bl))
        yb = np.interp(xs, px, py)
        s = np.round(yb - np.median(yb)).astype(int)
        if s.max() - s.min() < self.SEUIL * (y1 - y0): return super().boxes(g, ln)
        if __import__('os').environ.get('BBVLM_BASE_ACCORD') == '1':
            # B03 : n'en croire la ligne de base que si l'encre penche pareil
            si, _, _ = centre_local(g, ln.line_box)
            pb = np.polyfit(xs, yb, 1)[0]; pi = np.polyfit(np.arange(len(si)), si, 1)[0]
            if pb == 0 or pi / pb < .5 or pi / pb > 2: return super().boxes(g, ln)
        return redresse(self, g, ln, s)
