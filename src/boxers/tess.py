"""Comparaison — Tesseract comme fournisseur de géométrie.

`hans` a mesuré Tesseract à 99,7 % de frontières justes sur *Le Temps*, avec le
meilleur pire cas des quatre résolveurs testés. C'est un second moteur d'une
lignée entièrement différente du CTC de kraken : s'il confirme, le résultat ne
tient pas à un modèle particulier.

Tesseract fournit directement des boîtes de mots (`image_to_data`). On les
apparie au texte connu par distance d'édition, comme pour le CTC — Tesseract ne
fournit jamais le texte, seulement la géométrie.
"""
from __future__ import annotations
import difflib
import subprocess
import tempfile
import os
import numpy as np
from PIL import Image
import ink


class TessBoxer:
    name = 'tesseract'

    def boxes(self, gray: np.ndarray, line):
        x0, y0, x1, y1 = line.line_box
        H, W = gray.shape
        pad = max(4, (y1-y0)//6)
        ax0, ay0 = max(0, x0-pad), max(0, y0-pad)
        ax1, ay1 = min(W, x1+pad), min(H, y1+pad)
        crop = Image.fromarray(gray[ay0:ay1, ax0:ax1])
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            crop.save(f.name); p = f.name
        try:
            r = subprocess.run(['tesseract', p, 'stdout', '-l', 'fra',
                                '--psm', '7', 'tsv'],
                               capture_output=True, text=True, timeout=60)
        finally:
            os.unlink(p)
        mots = []
        for ln in r.stdout.splitlines()[1:]:
            c = ln.split('\t')
            if len(c) < 12 or not c[11].strip(): continue
            try:
                l, t, w, h = int(c[6]), int(c[7]), int(c[8]), int(c[9])
            except ValueError:
                continue
            mots.append((c[11].strip(), ax0+l, ay0+t, ax0+l+w, ay0+t+h))
        if not mots: raise ValueError('tesseract muet')

        pred = [m[0] for m in mots]
        sm = difflib.SequenceMatcher(None, pred, line.words, autojunk=False)
        vers: dict[int, int] = {}
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ('equal', 'replace'):
                for k in range(min(i2-i1, j2-j1)): vers[j1+k] = i1+k
        mask, ox, oy = ink.line_mask(gray, line.line_box)
        out = []
        for j in range(len(line.words)):
            i = vers.get(j)
            if i is None: raise ValueError('mot non apparié')
            _, a, b, c, d = mots[i]
            out.append((a, b, c, d))
        return out
