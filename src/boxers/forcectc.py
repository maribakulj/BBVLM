"""B25 — alignement forcé CTC : on impose le texte, on ne le demande pas.

Défaut de `ctc.py`, signalé et vérifié : il demandait d'abord au recognizer
*quelle* transcription il préfère (`rec.prediction`), puis raccrochait cette
lecture au texte du VLM par `difflib.SequenceMatcher`. Ce n'est pas de
l'alignement forcé, c'est de l'appariement de deux lectures — et quand elles
divergent, il n'y a plus rien à quoi s'accrocher. D'où les 32 lignes en échec,
toutes sur des lignes dégradées (`bles. L r s personnes dont ces chemins des`).

L'alignement forcé ne pose jamais cette question. Il prend la matrice de
probabilités du réseau, construit le graphe CTC de la transcription **imposée** —
blank, c1, blank, c2, blank… avec les transitions propres aux caractères
répétés — et cherche par Viterbi le chemin qui explique le mieux CE texte. Le
réseau peut n'avoir que 0,42 sur « e » à une frame : le chemin global s'en
accommode, là où un décodage glouton aurait produit autre chose.

C'est la méthode que PERO applique dans `core/force_alignment.py`, et elle est
documentée — ce n'est pas une trouvaille de ce dépôt.

Ce qui reste propre à BBVLM et qu'on garde : les positions CTC servent de
**séparateurs**, pas de bords de glyphes (B19 : IoU 0,635 → 0,829 sans déplacer
une frontière), et l'étendue vient de l'encre observée.
"""
from __future__ import annotations
import os
import numpy as np
import torch
import ink

CHEMIN = os.path.expanduser(
    '~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/'
    'catmus-print-fondue-large.mlmodel')
_M = None


def modele():
    global _M
    if _M is None:
        from kraken.lib import models
        _M = models.load_any(CHEMIN)
    return _M


def _ligne_tenseur(gray, line):
    """Extrait et normalise la ligne comme le fait kraken avant reconnaissance."""
    from PIL import Image
    from kraken import rpred
    from kraken.containers import Segmentation, BaselineLine
    from kraken.lib import segmentation as kseg
    x0, y0, x1, y1 = line.line_box
    im = Image.fromarray(gray).convert('L')
    yb = int(y0 + (y1-y0)*0.78)
    bl = BaselineLine(id='l', baseline=[(x0, yb), (x1, yb)],
                      boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    seg = Segmentation(type='baselines', imagename='x', text_direction='horizontal-lr',
                       script_detection=False, lines=[bl], regions={}, line_orders=[])
    crop, _ = next(iter(kseg.extract_polygons(im, seg)))
    m = modele()
    tr = rpred.ImageInputTransforms(
        batch=1, height=m.nn.input[2], width=m.nn.input[3],
        channels=m.nn.input[1], pad=(16, 0), valid_norm=m.one_channel_mode == '1')
    return tr(crop).unsqueeze(0)


def graphe_ctc(codes: list[int], blank: int = 0) -> list[int]:
    """blank c1 blank c2 blank … — la forme canonique du graphe CTC."""
    g = [blank]
    for c in codes:
        g.append(c); g.append(blank)
    return g


def viterbi(logp: np.ndarray, etats: list[int]) -> np.ndarray:
    """Chemin de coût maximal contraint au graphe. logp : (frames, alphabet).
    Rend, pour chaque état, la frame de plus forte probabilité qui lui est
    attribuée. Transitions CTC : rester, avancer d'un, et sauter un blank quand
    les deux caractères encadrants diffèrent."""
    T, _ = logp.shape
    S = len(etats)
    if T < S//2 + 1: return None
    NEG = -1e30
    dp = np.full((T, S), NEG, dtype=np.float64)
    bk = np.zeros((T, S), dtype=np.int32)
    dp[0, 0] = logp[0, etats[0]]
    if S > 1: dp[0, 1] = logp[0, etats[1]]
    for t in range(1, T):
        for s in range(S):
            best, arg = dp[t-1, s], s
            if s >= 1 and dp[t-1, s-1] > best: best, arg = dp[t-1, s-1], s-1
            if s >= 2 and etats[s] != 0 and etats[s] != etats[s-2] and dp[t-1, s-2] > best:
                best, arg = dp[t-1, s-2], s-2
            if best <= NEG/2: continue
            dp[t, s] = best + logp[t, etats[s]]
            bk[t, s] = arg
    fin = S-1 if dp[T-1, S-1] >= dp[T-1, S-2] else S-2
    if dp[T-1, fin] <= NEG/2: return None
    chemin = np.zeros(T, dtype=np.int32)
    s = fin
    for t in range(T-1, -1, -1):
        chemin[t] = s; s = bk[t, s]
    # meilleure frame par état non-blank
    pos = np.full(S, -1, dtype=np.int32)
    for t in range(T):
        s = chemin[t]
        if etats[s] == 0: continue
        if pos[s] < 0 or logp[t, etats[s]] > logp[pos[s], etats[s]]: pos[s] = t
    return pos


class ForceCTC:
    name = 'force_ctc'

    def boxes(self, gray: np.ndarray, line):
        m = modele()
        t = _ligne_tenseur(gray, line)
        with torch.no_grad():
            out = m.forward(t)
        o = out[0] if isinstance(out, tuple) else out
        o = np.asarray(o)
        if o.ndim == 3: o = o[0]
        if o.shape[0] < o.shape[1]: o = o.T          # (frames, alphabet)
        p = np.clip(o, 1e-8, None)
        if p.max() > 1.01: p = np.exp(p - p.max(axis=1, keepdims=True))
        logp = np.log(p / p.sum(axis=1, keepdims=True))

        texte = ' '.join(line.words)
        # Le codec ÉCARTE les caractères hors alphabet (le « é » de CATMuS-Print
        # par exemple) : 21 caractères peuvent donner 20 codes. On encode donc
        # caractère par caractère en gardant la correspondance position→code.
        codes, pos_car = [], []
        for i, ch in enumerate(texte):
            try:
                e = m.codec.encode(ch)
            except Exception:
                continue
            e = e.tolist() if hasattr(e, 'tolist') else list(e)
            if not e: continue
            for c in e:
                codes.append(int(c)); pos_car.append(i)
        if len(codes) < 2: raise ValueError('encodage trop pauvre')
        etats = graphe_ctc(codes)
        pos = viterbi(logp, etats)
        if pos is None: raise ValueError('alignement forcé impossible')

        T = logp.shape[0]
        x0, _, x1, _ = line.line_box
        def frame_vers_x(f): return x0 + (x1-x0) * (f + 0.5) / T

        # x de chaque POSITION DE CARACTÈRE du texte d'origine
        par_car: dict[int, float] = {}
        for j in range(len(codes)):
            f = pos[2*j + 1]
            if f < 0: continue
            par_car.setdefault(pos_car[j], frame_vers_x(f))
        mask, ox, oy = ink.line_mask(gray, line.line_box, pad=0.10)
        occ = (mask > 0).any(axis=0) if mask.size > 1 else None
        bornes, k = [], 0
        for w in line.words:
            a, b = k, k+len(w)-1              # positions dans `texte`
            xa = next((par_car[i] for i in range(a, b+1) if i in par_car), None)
            xb = next((par_car[i] for i in range(b, a-1, -1) if i in par_car), None)
            if xa is None or xb is None: raise ValueError('mot sans frame alignée')
            bornes.append((xa, xb)); k = b+2
        seps = [x0]
        for i in range(len(bornes)-1):
            seps.append((bornes[i][1] + bornes[i+1][0]) / 2)
        seps.append(x1)
        out_b = []
        for i in range(len(bornes)):
            a = int(max(0, min(mask.shape[1]-1, seps[i]-ox))) if occ is not None else 0
            b = int(max(0, min(mask.shape[1]-1, seps[i+1]-ox))) if occ is not None else 0
            if occ is None or b <= a:
                out_b.append((int(bornes[i][0]), line.line_box[1],
                              int(bornes[i][1]), line.line_box[3])); continue
            nz = np.nonzero(occ[a:b+1])[0]
            if len(nz) == 0:
                out_b.append((int(bornes[i][0]), line.line_box[1],
                              int(bornes[i][1]), line.line_box[3])); continue
            xa2, xb2 = a+int(nz.min()), a+int(nz.max())
            ya, yb = ink.vertical_extent(mask, xa2, xb2)
            out_b.append((ox+xa2, oy+ya, ox+xb2, oy+yb))
        return out_b
