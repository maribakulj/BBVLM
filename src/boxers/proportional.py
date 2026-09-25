"""Ligne de base : répartition proportionnelle au nombre de caractères.

C'est ce que fait saknussemm en production. Elle ne regarde pas l'image.
Tout le reste doit la battre, sinon il ne sert à rien.
"""
from __future__ import annotations
import numpy as np


class Proportional:
    name = 'proportional'

    def boxes(self, gray: np.ndarray, line) -> list[tuple[int, int, int, int]]:
        x0, y0, x1, y1 = line.line_box
        n = sum(len(w) for w in line.words) + max(0, len(line.words)-1)
        if n <= 0: raise ValueError('ligne vide')
        span = x1 - x0
        out, pos = [], float(x0)
        for i, w in enumerate(line.words):
            wd = span * len(w) / n
            out.append((int(round(pos)), y0, int(round(pos+wd))-1, y1))
            pos += wd
            if i < len(line.words)-1: pos += span/n     # l'espace
        return out
