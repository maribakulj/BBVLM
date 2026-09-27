#!/usr/bin/env python
"""Production traçable : image → graphe documentaire → ALTO/METS brouillons.

Les lignes rejetées ou non traitées restent représentées et à relire. Les
lecteurs positionnels historiques sont limités à une ligne par appel. Un lecteur
par lots doit fournir des réponses associées aux identifiants demandés.
La conformité XML ne constitue jamais une validation humaine du contenu.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'boxers'))


def produire(image, sortie, lire, boxer, max_lignes=None, par_bloc=20, verbose=True):
    """Production traçable ; les lignes refusées restent dans document.json/ALTO.

    Lecteur historique positionnel : une ligne par appel. Pour des lots, fournir
    lire.returns_ids=True et retourner ({line_id: texte}, qualite).
    """
    from bbvlm.production import produce
    return produce(image, sortie, lire, boxer, max_lines=max_lignes,
                   batch_size=par_bloc, verbose=verbose)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('sortie')
    ap.add_argument('--max-lignes', type=int, default=None)
    ap.add_argument('--par-bloc', type=int, default=20)
    a = ap.parse_args()
    sys.path.insert(0, os.path.expanduser('~/vlm-alto-fresh/src'))
    import vlm as V
    from connexe import Connexe
    be = V.OllamaVLM("hf.co/mradermacher/churro-3B-GGUF:Q4_K_M")
    def lire(crop, n):
        return V.block_robuste(be, lambda d, m, j=0: crop, 0, n, essais=3)
    lire.nom = 'churro-3B'
    produire(a.image, a.sortie, lire, Connexe(),
             max_lignes=a.max_lignes, par_bloc=a.par_bloc)
