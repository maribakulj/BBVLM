"""B6 — géométrie fournie par l'alignement CTC d'un recognizer kraken.

`hans` a mesuré cette route à 99,7-99,9 % de frontières justes, corroborée sur
deux moteurs et cinq corpus. Un CTC associe chaque symbole émis à une colonne de
l'image : les positions de caractères (`cuts`) sont un sous-produit de la
reconnaissance, pas un ajustement a posteriori.

La difficulté propre à notre cadre : le texte vient du VLM, pas du CTC. Les deux
lectures diffèrent. On aligne donc la prédiction du CTC sur le texte connu par
distance d'édition, et on transporte les frontières de mots à travers cet
alignement. Le CTC ne fournit que la géométrie — jamais le texte.

Réserve mesurée dans hans (H1, réfutée) : un recognizer hors domaine produit
« une géométrie confiante et fausse ». C'est ce que ce banc doit vérifier.
"""
from __future__ import annotations
import difflib
import os
import numpy as np
import ink

_MODELE = None
CHEMIN = os.path.expanduser(
    '~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/'
    'catmus-print-fondue-large.mlmodel')


def modele():
    global _MODELE
    if _MODELE is None:
        from kraken.lib import models
        _MODELE = models.load_any(CHEMIN)
    return _MODELE


def _record(gray: np.ndarray, line):
    from PIL import Image
    from kraken import rpred
    from kraken.containers import Segmentation, BaselineLine
    x0, y0, x1, y1 = line.line_box
    im = Image.fromarray(gray).convert('L')
    yb = int(y0 + (y1-y0)*0.78)                     # ligne de base approchée
    bl = BaselineLine(id='l', baseline=[(x0, yb), (x1, yb)],
                      boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    seg = Segmentation(type='baselines', imagename='x', text_direction='horizontal-lr',
                       script_detection=False, lines=[bl], regions={}, line_orders=[])
    it = rpred.rpred(modele(), im, seg)
    return next(iter(it))


class CTCBoxer:
    name = 'ctc_kraken'

    def boxes(self, gray: np.ndarray, line):
        rec = _record(gray, line)
        pred = str(rec.prediction or '')
        cuts = list(rec.cuts or [])
        if not pred or len(cuts) < len(pred):
            raise ValueError('ctc sans coupes exploitables')

        def xbords(i: int) -> tuple[float, float]:
            """Bords gauche et droit de la coupe du caractère i. Prendre le
            centre rétrécissait les boîtes de 10 à 16 px sur le bord droit."""
            pts = np.asarray(cuts[i], float).reshape(-1, 2)
            return float(pts[:, 0].min()), float(pts[:, 0].max())

        cible = ' '.join(line.words)
        sm = difflib.SequenceMatcher(None, pred, cible, autojunk=False)
        # position dans le texte cible -> index de caractère du CTC
        vers_ctc: dict[int, int] = {}
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ('equal', 'replace'):
                for k in range(min(i2-i1, j2-j1)):
                    vers_ctc[j1+k] = i1+k

        mask, ox, oy = ink.line_mask(gray, line.line_box)
        occ = (mask > 0).any(axis=0) if mask.size > 1 else None
        out, pos = [], 0
        for w in line.words:
            a, b = pos, pos+len(w)-1
            ia = next((vers_ctc[k] for k in range(a, b+1) if k in vers_ctc), None)
            ib = next((vers_ctc[k] for k in range(b, a-1, -1) if k in vers_ctc), None)
            if ia is None or ib is None:
                raise ValueError('mot non aligné sur le ctc')
            xa, xb = int(xbords(ia)[0]), int(xbords(ib)[1])
            if xb <= xa: xb = xa+1
            if occ is not None:
                ra = max(0, min(len(occ)-1, xa-ox)); rb = max(0, min(len(occ)-1, xb-ox))
                seg = np.nonzero(occ[ra:rb+1])[0]
                if len(seg):
                    xa, xb = ox+ra+int(seg.min()), ox+ra+int(seg.max())
            ya, yb = ink.vertical_extent(mask, max(0, xa-ox), max(0, xb-ox)) if mask.size > 1 else (0, 0)
            out.append((xa, oy+ya, xb, oy+yb))
            pos = b+2
        return out
