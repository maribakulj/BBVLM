"""B20 — le CTC quand il aboutit, le DTW sinon.

État du banc après onze pistes :

| | ≤0,5c | pire cas PP | IoU PP | échecs |
|---|---|---|---|---|
| `routage` (DTW) | 98,18 % | 1,32c | 0,837 | **0** |
| `ctc_span` | 99,65 % | **0,66c** | 0,829 | 32 |

Le CTC place mieux, le DTW n'abandonne jamais. Les deux échouent sur des
lignes différentes : le CTC renonce quand sa prédiction ne s'aligne pas sur le
texte du VLM — ligne trop dégradée, hors domaine du recognizer — et c'est
précisément là que le DTW, qui n'a pas de domaine, tient encore.

On ne choisit donc pas entre eux : le CTC passe en premier, le DTW reprend ce
qu'il laisse. Aucun seuil n'est assoupli ; c'est la couverture qui est complétée.

C'est la même leçon qu'une couche plus haut, où deux lecteurs indépendants
valaient mieux qu'un seul : ici deux placeurs indépendants.
"""
from __future__ import annotations
import numpy as np
from ctcspan import CTCSpan
from routage import Routage


class Compose:
    name = 'compose'

    def __init__(self):
        self.ctc = CTCSpan()
        self.dtw = Routage()
        self.n_ctc = 0
        self.n_dtw = 0

    def boxes(self, gray: np.ndarray, line):
        try:
            r = self.ctc.boxes(gray, line)
            if len(r) == len(line.words):
                self.n_ctc += 1
                return r
        except Exception:
            pass
        self.n_dtw += 1
        return self.dtw.boxes(gray, line)
