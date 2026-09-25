"""Notation d'un boxer contre les boîtes de mots de la VT.

Principe repris de hans/measure.py : une frontière prédite est JUSTE si elle
tombe n'importe où dans le blanc entre deux mots de la VT — tout x du blanc est
également correct, ce n'est pas de l'indulgence. L'erreur est la distance à cet
intervalle, normalisée par la largeur moyenne d'un caractère de la ligne.

Le rapport porte une DISTRIBUTION, pas une moyenne. Leçon de hans (AUTOPILOT
règle 8) : une moyenne excellente peut cacher exactement le cas que le système
existe pour traiter. p90 et pire cas sont ce qui bouge alors.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from statistics import median
from typing import Protocol
import numpy as np
from corpora import Line, Page


class Boxer(Protocol):
    name: str
    def boxes(self, gray: np.ndarray, line: Line) -> list[tuple[int, int, int, int]]:
        """Reçoit l'image et la ligne (texte + boîte de LIGNE). Rend une boîte
        par mot. N'a JAMAIS accès à line.word_boxes."""
        ...


def _interval_distance(x: float, lo: float, hi: float) -> float:
    if lo <= x <= hi: return 0.0
    return lo - x if x < lo else x - hi


def _iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a; bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0: return 0.0
    inter = (ix1-ix0)*(iy1-iy0)
    ua = (ax1-ax0)*(ay1-ay0) + (bx1-bx0)*(by1-by0) - inter
    return inter/ua if ua > 0 else 0.0


@dataclass
class Report:
    boxer: str
    n_lines: int = 0
    n_words: int = 0
    n_bounds: int = 0
    failed_lines: int = 0
    err: list[float] = field(default_factory=list)      # en largeurs de caractère
    iou: list[float] = field(default_factory=list)
    per_corpus: dict = field(default_factory=dict)

    def summary(self) -> dict:
        e = sorted(self.err); i = sorted(self.iou)
        def q(v, p): return float(np.percentile(v, p)) if v else float('nan')
        return {
            'boxer': self.boxer, 'lignes': self.n_lines, 'mots': self.n_words,
            'frontieres': self.n_bounds, 'lignes_en_echec': self.failed_lines,
            'err_med': round(q(e, 50), 3), 'err_p90': round(q(e, 90), 3),
            'err_p99': round(q(e, 99), 3), 'err_max': round(max(e), 2) if e else None,
            'pct_sous_0.5c': round(100*sum(1 for x in e if x <= .5)/len(e), 2) if e else None,
            'iou_med': round(q(i, 50), 3), 'iou_p10': round(q(i, 10), 3),
        }


def score(boxer: Boxer, pages: list[Page], verbose: bool = False) -> Report:
    rep = Report(boxer.name)
    for p in pages:
        g = p.gray
        if g is None: continue
        sub = Report(boxer.name)
        for ln in p.lines:
            try:
                pred = boxer.boxes(g, ln)
            except Exception:
                rep.failed_lines += 1; sub.failed_lines += 1; continue
            if len(pred) != len(ln.words):
                rep.failed_lines += 1; sub.failed_lines += 1; continue
            rep.n_lines += 1; sub.n_lines += 1
            rep.n_words += len(pred); sub.n_words += len(pred)
            gt = ln.word_boxes
            span = max(b[2] for b in gt) - min(b[0] for b in gt)
            nchar = max(1, sum(len(w) for w in ln.words))
            cw = max(1.0, span/nchar)              # largeur moyenne d'un caractère
            for k in range(len(gt)-1):             # frontières internes
                lo, hi = gt[k][2], gt[k+1][0]
                if hi < lo: lo, hi = hi, lo
                x = (pred[k][2] + pred[k+1][0])/2.0
                d = _interval_distance(x, lo, hi)/cw
                rep.err.append(d); sub.err.append(d)
                rep.n_bounds += 1; sub.n_bounds += 1
            for a, b in zip(pred, gt):
                v = _iou(a, b); rep.iou.append(v); sub.iou.append(v)
        if sub.n_lines or sub.failed_lines:
            rep.per_corpus.setdefault(p.corpus, []).append(sub)
    agg = {}
    for c, subs in rep.per_corpus.items():
        m = Report(rep.boxer)
        for s in subs:
            m.n_lines += s.n_lines; m.n_words += s.n_words; m.n_bounds += s.n_bounds
            m.failed_lines += s.failed_lines; m.err += s.err; m.iou += s.iou
        agg[c] = m.summary()
    rep.per_corpus = agg
    return rep
