"""B3 — alignement DTW d'un gabarit rendu sur le profil d'encre observé.

Fondement : les travaux d'alignement texte-image de documents historiques
(Likforman-Sulem et al., survey IJDAR ; Kornfield et al.) alignent une image et
sa transcription par *dynamic time warping* sur des profils simples — projection,
profil de mot, transitions fond/encre — et y montrent que le DTW bat SSD et la
distance euclidienne.

Le retournement utile ici : le texte est CONNU (c'est la sortie du VLM). On le
**rend** dans une fonte à l'échelle de la ligne, on calcule le profil d'encre du
rendu, et on l'aligne sur le profil observé. Les frontières de mots sont exactes
dans le rendu ; le chemin DTW les transporte vers l'image.

Avantage décisif sur le CTC : aucun recognizer entraîné, donc aucun problème de
domaine — c'est ce qui a fait échouer H1 sur du Fraktur.
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ink
from band import core_band

_CACHE: dict = {}
import os, glob

# Familles de gabarits. AUCUNE n'est choisie a priori : la ligne 78 sélectionne
# celle qui minimise le coût DTW, page par page et ligne par ligne. Ajouter une
# fonte ici ne peut donc que réduire le coût — jamais l'augmenter — et le choix
# reste reproductible sur un document inconnu.
_RACINE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'fontes')

def _familles():
    fam = []
    for p in sorted(glob.glob(os.path.join(_RACINE, '*.tt[fc]'))
                    + glob.glob(os.path.join(_RACINE, '*.otf'))):
        fam.append((os.path.splitext(os.path.basename(p))[0], p))
    for nom, p in (('serif', '/System/Library/Fonts/Supplemental/Times New Roman.ttf'),
                   ('serif', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'),
                   ('serif', '/System/Library/Fonts/Times.ttc')):
        if os.path.exists(p):
            fam.append((nom, p)); break
    return fam or [('defaut', None)]

FAMILLES = _familles()
# BBVLM_FONTES=serif restreint la sélection — sert à mesurer l'apport du choix
# de gabarit, pas à régler la chaîne.
# Par défaut UNE seule famille. La sélection par coût DTW double le nombre
# d'appels au DP — c'est-à-dire le coût de `connexe`, qui en dépend par
# dtwsnap — et B36 a mesuré qu'elle n'améliore pas la géométrie (le coût DTW
# mesure une ressemblance de profils, pas une justesse de frontière : le
# gabarit Fraktur fait passer les chevauchements de 10 à 16). On garde le
# mécanisme, désarmé : BBVLM_FONTES=toutes le rallume pour la mesurer.
_filtre = os.environ.get('BBVLM_FONTES', 'serif')
if _filtre and _filtre != 'toutes':
    _garde = {x.strip() for x in _filtre.split(',')}
    FAMILLES = [f for f in FAMILLES if f[0] in _garde] or FAMILLES[-1:]


def _font(px: int, fam: str | None = None):
    px = max(8, min(400, int(px)))
    cle = (px, fam)
    if cle in _CACHE: return _CACHE[cle]
    chemins = [c for n, c in FAMILLES if fam is None or n == fam] or \
              [c for _, c in FAMILLES]
    f = None
    for p in chemins:
        if p is None: continue
        try:
            f = ImageFont.truetype(p, px); break
        except Exception:
            continue
    if f is None: f = ImageFont.load_default()
    _CACHE[cle] = f
    return f


def render_profile(words, px: int, space_ratio: float = 1.0, fam=None):
    """Rend le texte et renvoie (profil d'encre par colonne, frontières de mots).
    Les frontières sont les milieux des espaces rendus — exactes par construction."""
    f = _font(px, fam)
    sp = max(1.0, f.getlength(' ') * space_ratio)
    widths = [max(1.0, f.getlength(w)) for w in words]
    total = int(sum(widths) + sp*(len(words)-1)) + 4
    h = int(px*1.8)
    im = Image.new('L', (max(4, total), h), 255)
    d = ImageDraw.Draw(im)
    x = 2.0
    spans = []
    for i, (w, wd) in enumerate(zip(words, widths)):
        d.text((x, px*0.25), w, font=f, fill=0)
        spans.append((x, x+wd))
        x += wd
        if i < len(words)-1: x += sp
    a = np.asarray(im)
    prof = (a < 200).sum(axis=0).astype(float)
    return prof, spans


def dtw_path(a: np.ndarray, b: np.ndarray, band_frac: float = 0.25,
              with_cost: bool = False):
    """Chemin DTW entre deux profils 1-D, avec bande de Sakoe-Chiba."""
    n, m = len(a), len(b)
    if n < 2 or m < 2: return (None, float('inf')) if with_cost else None
    a = (a - a.mean()) / (a.std() + 1e-6)
    b = (b - b.mean()) / (b.std() + 1e-6)
    w = max(8, int(max(n, m) * band_frac))
    INF = 1e18
    D = np.full((n+1, m+1), INF)
    D[0, 0] = 0.0
    for i in range(1, n+1):
        j0 = max(1, int(i*m/n) - w); j1 = min(m, int(i*m/n) + w)
        if j1 < j0: continue
        # Ce qui ne dépend que de la ligne précédente se calcule d'un coup ;
        # seule la récurrence sur D[i, j-1] reste séquentielle. Sortie
        # identique, l'ordre des opérations ne change pas.
        cout = np.abs(a[i-1] - b[j0-1:j1])
        haut = np.minimum(D[i-1, j0-1:j1], D[i-1, j0:j1+1])
        ligne = D[i]
        for t, j in enumerate(range(j0, j1+1)):
            v = haut[t]
            g = ligne[j-1]
            if g < v: v = g
            ligne[j] = cout[t] + v
    if not np.isfinite(D[n, m]):
        return (None, float('inf')) if with_cost else None
    cout = float(D[n, m]) / (n + m)
    # remontée
    i, j = n, m
    map_ab = np.zeros(n, dtype=float)
    cnt = np.zeros(n, dtype=float)
    while i > 0 and j > 0:
        map_ab[i-1] += j-1; cnt[i-1] += 1
        step = int(np.argmin([D[i-1, j-1], D[i-1, j], D[i, j-1]]))
        if step == 0: i, j = i-1, j-1
        elif step == 1: i -= 1
        else: j -= 1
    cnt[cnt == 0] = 1
    res = map_ab/cnt
    return (res, cout) if with_cost else res


class RenderDTW:
    name = 'render_dtw'

    def boxes(self, gray: np.ndarray, line):
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        if mask.size <= 1: raise ValueError('masque vide')
        a, b = core_band(mask)
        obs = (mask[a:b+1, :] > 0).sum(axis=0).astype(float)
        if obs.sum() <= 0: raise ValueError('pas d\'encre')
        # échelle : hauteur du corps des minuscules ~ hauteur d'x de la fonte
        px = max(8, int((b-a+1) / 0.46))
        nz = np.nonzero(obs)[0]
        o0, o1 = int(nz.min()), int(nz.max())
        obs_c = obs[o0:o1+1]
        # Sélection du gabarit par coût DTW : la fonte n'est pas un réglage,
        # c'est une inconnue que l'alignement tranche lui-même.
        best = None
        for nom, _ in FAMILLES:
            prof, spans = render_profile(line.words, px, fam=nom)
            nzp = np.nonzero(prof)[0]
            if nzp.size < 2: continue
            p0, p1 = int(nzp.min()), int(nzp.max())
            path, cout = dtw_path(prof[p0:p1+1], obs_c, with_cost=True)
            if path is None: continue
            if best is None or cout < best[0]:
                best = (cout, path, spans, p0, nom)
        if best is None: raise ValueError('dtw échoue')
        _, path, spans, p0, self.fam_choisie = best
        def to_obs(xr: float) -> float:
            k = int(round(xr - p0))
            k = max(0, min(len(path)-1, k))
            return o0 + path[k]
        out = []
        for (sa, sb) in spans:
            xa, xb = to_obs(sa), to_obs(sb)
            if xb <= xa: xb = xa+1
            ya, yb = ink.vertical_extent(mask, int(xa), int(xb))
            out.append((ox+int(round(xa)), oy+ya, ox+int(round(xb)), oy+yb))
        return out
