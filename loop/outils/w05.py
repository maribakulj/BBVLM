"""W05 — alignement forcé CTC du texte lu (VLM) sur les émissions d'un reconnaisseur kraken.

On ne décode pas le CTC : on impose la transcription et on cherche son chemin
le plus probable (Viterbi CTC standard, états blank intercalés, un caractère
peut durer plusieurs trames). Correctif par rapport à kraken.align.forced_align
(7.1.1) : `model.outputs` est déjà une probabilité (softmax), on en prend le log
(kraken y réapplique log_softmax, ce qui aplatit les émissions).
Frontière entre mots k et k+1 : milieu entre la dernière trame émise du mot k et
la première du mot k+1, recalée au blanc d'encre qui la contient s'il existe.
"""
import os
import numpy as np

_M = None
CHEMIN = os.path.expanduser('~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/'
                            'catmus-print-fondue-large.mlmodel')


def modele():
    global _M
    if _M is None:
        import torch
        torch.set_num_threads(int(os.environ.get('BBVLM_W05_FILS', '1')))
        from kraken.lib import models
        _M = models.load_any(CHEMIN)
    return _M


def emissions(gray, box, binarise=False):
    """(T, C) log-probabilités et fonction trame → x page ; cache .npz si BBVLM_W05_CACHE"""
    cache = os.environ.get('BBVLM_W05_CACHE')
    if cache:
        import hashlib
        cle = hashlib.sha1(f'{gray.shape}{int(gray[::97, ::89].sum())}{tuple(int(v) for v in box)}{binarise}'.encode()).hexdigest()
        f = os.path.join(cache, cle + '.npz')
        if os.path.exists(f):
            z = np.load(f)
            xs = z['xs']
            return z['lp'], (lambda t: float(np.interp(t, np.arange(len(xs)), xs))), _Rec(str(z['pred']))
        lp, sc, rec = _emissions(gray, box, binarise)
        os.makedirs(cache, exist_ok=True)
        np.savez_compressed(f, lp=lp.astype(np.float32), xs=np.array([sc(t) for t in range(lp.shape[0] + 1)]), pred=str(rec.prediction or ''))
        # même chemin que les appels suivants (reproductibilité : float32 et interpolation identiques)
        z = np.load(f); xs = z['xs']
        return z['lp'], (lambda t: float(np.interp(t, np.arange(len(xs)), xs))), rec
    return _emissions(gray, box, binarise)


class _Rec:
    def __init__(self, p): self.prediction = p


def _emissions(gray, box, binarise=False):
    from PIL import Image
    from kraken import rpred
    from kraken.containers import Segmentation, BaselineLine
    import cv2
    x0, y0, x1, y1 = (int(v) for v in box)
    g = gray
    if binarise:
        g = gray.copy()
        c = g[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
        g[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    im = Image.fromarray(g).convert('L')
    yb = int(y0 + (y1 - y0) * 0.78)
    bl = BaselineLine(id='l', baseline=[(x0, yb), (x1, yb)], boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    seg = Segmentation(type='baselines', imagename='x', text_direction='horizontal-lr', script_detection=False,
                       lines=[bl], regions={}, line_orders=[])
    it = rpred.rpred(modele(), im, seg)
    rec = next(iter(it))
    P = np.asarray(modele().outputs).squeeze()          # (C, T)
    if P.ndim == 3: P = P[0]
    T = P.shape[1]
    W = it.box.size[0] if hasattr(it, 'box') else (x1 - x0)
    sc = (lambda t: it._scale_val(t, 0, W)) if hasattr(it, '_scale_val') else (lambda t: t * W / T)
    return np.log(P.T + 1e-12), sc, rec


def viterbi(lp, lab):
    """lp (T, C) log-probas, lab liste d'indices (blank = 0) → trame de chaque étiquette : [(début, fin)]"""
    T = lp.shape[0]; L = len(lab); S = 2 * L + 1
    ext = np.zeros(S, dtype=np.int64)
    ext[1::2] = lab
    saut = np.zeros(S, dtype=bool)          # transition s-2 → s permise (caractère différent du précédent)
    saut[3::2] = ext[3::2] != ext[1:-2:2]
    NEG = -1e18
    D = np.full(S, NEG); B = np.zeros((T, S), dtype=np.int8)
    D[0] = lp[0, 0]
    if S > 1: D[1] = lp[0, ext[1]]
    D[2:] = NEG
    for t in range(1, T):
        c0 = D
        c1 = np.concatenate(([NEG], D[:-1]))
        c2 = np.where(saut, np.concatenate(([NEG, NEG], D[:-2])), NEG)
        m = np.stack([c0, c1, c2]); a = m.argmax(0)
        D = m[a, np.arange(S)] + lp[t, ext]; B[t] = a
    s = S - 1 if S == 1 or D[S - 1] >= D[S - 2] else S - 2
    path = [0] * T
    for t in range(T - 1, -1, -1):
        path[t] = s; s -= int(B[t, s])
    spans = [[None, None] for _ in lab]
    for t, s in enumerate(path):
        if s % 2 == 1:
            k = s // 2
            if spans[k][0] is None: spans[k][0] = t
            spans[k][1] = t
    return spans, float(D[path[-1]])


def frontieres(gray, box, mots, binarise=False):
    """x page de chaque frontière entre mots consécutifs (None si non alignable), + texte greedy"""
    m = modele()
    lp, sc, rec = emissions(gray, box, binarise)
    lab, qui = [], []
    for k, w in enumerate(mots):
        if k:
            e = m.codec.encode(' ').tolist() if _code(m, ' ') else []
            lab += e; qui += [-1] * len(e)
        for ch in w:
            e = encode(m, ch)
            lab += e; qui += [k] * len(e)
    if not lab or lp.shape[0] < len(lab): return None, rec.prediction
    spans, _ = viterbi(lp, lab)
    x0 = int(box[0])
    fins = {}; debs = {}
    for (a, b), k in zip(spans, qui):
        if k < 0 or a is None: continue
        debs.setdefault(k, a); fins[k] = b
    out = []
    for k in range(len(mots) - 1):
        if k not in fins or k + 1 not in debs: out.append(None); continue
        t = (fins[k] + 1 + debs[k + 1]) / 2
        out.append(x0 + sc(t))
    if os.environ.get('BBVLM_W05_RECALE', '1') == '1': out = recale(gray, box, out)
    return out, rec.prediction


REPLI = {'ſ': 's', 'ĳ': 'ij', 'ꝛ': 'r', 'ꝫ': ';', 'ꝰ': 'us', '⸗': '-', '\u0364': 'e', 'ß': 'ss', 'æ': 'ae', 'œ': 'oe'}


def encode(m, ch):
    """étiquettes CTC d'un caractère lu ; repli si le modèle ne le code pas"""
    import unicodedata
    for c in (ch, REPLI.get(ch), unicodedata.normalize('NFKD', ch)[:1] or None):
        if not c: continue
        try:
            e = m.codec.encode(c).tolist()
            if e: return e
        except Exception: pass
    return []


def occupation(bw):
    """colonnes encrées ; W06 (L50) : seulement l'encre des composantes qui touchent la bande
    centrale de la ligne (hampes et jambages des lignes voisines exclus)"""
    import os
    if os.environ.get('BBVLM_W06', '0') != '1' or bw.shape[0] < 8: return bw.any(axis=0)
    import cv2, numpy as np
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw.astype(np.uint8), connectivity=8)
    h = bw.shape[0]; a, b = int(.25 * h), int(.8 * h)
    ok = np.zeros(n, bool)
    for i in range(1, n):
        y, hh = st[i, cv2.CC_STAT_TOP], st[i, cv2.CC_STAT_HEIGHT]
        ok[i] = y <= b and y + hh - 1 >= a
    return ok[lab].any(axis=0)


def recale(gray, box, xs):
    """frontière → milieu du blanc d'encre qui la contient (ou le plus proche à ≤ 3 px)"""
    import cv2
    x0, y0, x1, y1 = (int(v) for v in box)
    c = gray[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
    if not c.size: return xs
    _, bw = cv2.threshold(c, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occ = occupation(bw); ox = max(0, x0)
    B, d = [], None
    for i, v in enumerate(occ):
        if not v and d is None: d = i
        if v and d is not None: B.append((d + ox, i - 1 + ox)); d = None
    out = []
    for x in xs:
        if x is None: out.append(None); continue
        c = [(a, b) for a, b in B if a - 3 <= x <= b + 3]
        out.append((min(c, key=lambda q: abs((q[0] + q[1]) / 2 - x))[0] + min(c, key=lambda q: abs((q[0] + q[1]) / 2 - x))[1]) / 2 if c else x)
    return out


def _code(m, ch):
    try: return len(m.codec.encode(ch)) > 0
    except Exception: return False


def ajuste(gray, box, mots, bs, binarise=False):
    """Boîtes de mots bs (x0, y0, x1, y1) : chaque frontière alignée remplace la
    coupure entre les mots k et k+1 ; bords recalés sur l'encre de part et d'autre."""
    if len(bs) < 2 or len(bs) != len(mots): return bs
    fr, _ = frontieres(gray, box, mots, binarise)
    if not fr: return bs
    import cv2
    x0, y0, x1, y1 = (int(v) for v in box)
    c = gray[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
    if not c.size: return bs
    _, bw = cv2.threshold(c, 0, 1, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    occ = occupation(bw); ox = max(0, x0)
    out = [list(b) for b in bs]
    for k, x in enumerate(fr):
        if x is None: continue
        lo, hi = out[k][0], out[k + 1][2]
        if not (lo < x < hi): continue
        xi = int(round(x))
        g = xi - 1
        while g > lo and not occ[min(len(occ) - 1, max(0, g - ox))]: g -= 1
        d = xi + 1
        while d < hi and not occ[min(len(occ) - 1, max(0, d - ox))]: d += 1
        out[k][2], out[k + 1][0] = g, d
    return [tuple(v) for v in out]
