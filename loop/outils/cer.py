"""CER de page, indépendant de l'ordre de lecture.

Les lignes lues sont appariées aux lignes de référence (Hongrois sur la distance
d'édition normalisée) ; une ligne non appariée compte entièrement, des deux
côtés. L'ordre de lecture se note à part : il n'a rien à faire dans un CER.

Vues : `strict` (octets NFC), `diplo` (ligatures MUFI décomposées, ſ conservé), `glyphe` (diplo +
tout PUA OCR-D décomposable + variantes typographiques d'un même signe, glyphe.py),
`norm` (diplo + ſ→s, espaces multiples réduites, apostrophes/tirets unifiés,
dont ⸗, e suscrit → tréma). Vue étendue le 2026-09-28 avant O02, sans résultat vu.
Chaque vue est déclarée ; aucune n'est ajustée après lecture d'un résultat.
"""
from __future__ import annotations
import json, sys, unicodedata
import numpy as np
from scipy.optimize import linear_sum_assignment
from conventions import transform

TIRETS = dict.fromkeys(map(ord, '\u2010\u2011\u2012\u2013\u00ad\u2e17'), '-')
UMLAUT = {'a\u0364': '\u00e4', 'o\u0364': '\u00f6', 'u\u0364': '\u00fc'}
APOS = dict.fromkeys(map(ord, '’ʼ‘'), "'")


def vue(t: str, nom: str) -> str:
    t = unicodedata.normalize('NFC', t)
    if nom == 'strict':
        return t
    if nom == 'glyphe':            # mêmes signes, quel que soit le codage (glyphe.py)
        from glyphe import glyphe
        return glyphe(t)
    t = transform(t, 'glyph_decomposition_v1')
    if nom == 'diplo':
        return t
    if nom == 'norm':
        from glyphe import glyphe          # norm englobe glyphe (N01) : codage d'abord, puis replis
        t = glyphe(t)
        t = t.replace('ſ', 's').translate(TIRETS).translate(APOS)
        for k, v in UMLAUT.items(): t = t.replace(k, v)
        return ' '.join(t.split())
    raise ValueError(nom)


def lev(a: str, b: str) -> int:
    if len(a) < len(b): a, b = b, a
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j]+1, cur[j-1]+1, prev[j-1]+(ca != cb)))
        prev = cur
    return prev[-1]


def score(ref: list[str], hyp: list[str], nom: str) -> dict:
    R = [vue(x, nom) for x in ref if x.strip()]
    Hh = [vue(x, nom) for x in hyp if x.strip()]
    n = sum(len(x) for x in R)
    if not R: raise ValueError('référence vide')
    C = np.array([[lev(r, h)/max(1, len(r)) for h in Hh] for r in R]) if Hh else np.zeros((len(R), 0))
    ri, hi = linear_sum_assignment(C) if Hh else ([], [])
    ed, paires, vus = 0, [], set()
    for a, b in zip(ri, hi):
        e = lev(R[a], Hh[b])
        if e > len(R[a]):              # pire que rien : on ne l'apparie pas
            continue
        ed += e; vus.add(b); paires.append((a, b, e))
    apparies = {a for a, _, _ in paires}
    ed += sum(len(R[a]) for a in range(len(R)) if a not in apparies)
    ed += sum(len(Hh[b]) for b in range(len(Hh)) if b not in vus)
    fautes = [{'ref': R[a], 'lu': Hh[b], 'ed': e} for a, b, e in paires if e]
    fautes += [{'ref': R[a], 'lu': None, 'ed': len(R[a])} for a in range(len(R)) if a not in apparies]
    fautes += [{'ref': None, 'lu': Hh[b], 'ed': len(Hh[b])} for b in range(len(Hh)) if b not in vus]
    return {'vue': nom, 'car_ref': n, 'editions': ed, 'cer': ed/n,
            'lignes_ref': len(R), 'lignes_lues': len(Hh),
            'lignes_exactes': sum(1 for _, _, e in paires if e == 0), 'fautes': fautes}


if __name__ == '__main__':
    ref = json.load(open(sys.argv[1])); hyp = open(sys.argv[2], encoding='utf-8').read().splitlines()
    out = {v: score(ref, hyp, v) for v in ('strict', 'diplo', 'norm')}
    for v, s in out.items():
        print(f"{v:7s} CER {100*s['cer']:.3f} %  ({s['editions']}/{s['car_ref']})  exactes {s['lignes_exactes']}/{s['lignes_ref']}  lues {s['lignes_lues']}")
    if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
