"""B38 — double lecture indépendante pour produire de la VT au mot.

Protocole standard en production de vérité-terrain (*double keying*) : deux
lecteurs indépendants transcrivent, l'accord vaut présomption de justesse,
le désaccord seul remonte à l'humain. Rien d'inventé ici — ce qui est mesuré,
c'est le taux de désaccord, donc le coût humain réel.

Lecteur A : l'OCR déjà présent dans le dépôt de pages (Gallica, ONB, ...).
Lecteur B : un recognizer CTC assorti à l'écriture (kraken), indépendant de A.
Arbitre   : un VLM de frontière, appelé UNIQUEMENT sur les désaccords.

Sortie : pour chaque ligne, un statut (accord / désaccord / refus) et, pour les
accords, les boîtes de mots placées par le moteur géométrique du dépôt.
"""
from __future__ import annotations
import json, os, sys, time, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))

MODELES = {
    'latin': '~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/catmus-print-fondue-large.mlmodel',
    'german': '~/Library/Application Support/htrmopo/71d9d381-c404-53dc-97a2-a33024db3f57/german_print.mlmodel',
}


import re

# Marqueurs de césure en fin de ligne. Chaque outil a le sien : Gallica aplatit
# le SUBS_TYPE d'ALTO en doublant le tiret, kraken sort le ¬ des éditions
# philologiques, d'autres ne mettent rien. Ce n'est pas une lecture, c'est une
# convention — la confondre avec un désaccord gonfle artificiellement le coût
# humain (mesuré B38 : 5 des 11 « désaccords » d'un échantillon de 16).
_CESURE = re.compile(r'[\-\u00ac\u2010-\u2015=]+\s*$')
# Espacement de la ponctuation haute : l'espace fine française est encodée de
# dix façons. L'identité du signe reste comparée, seul son espacement est canonisé.
_PONCT = re.compile(r'\s*([;:!?%»])')
_PONCT_G = re.compile(r'([«])\s*')


def norm(s: str, cesure: bool = True) -> str:
    """Normalisation minimale : ce qui sépare deux lecteurs doit être une
    divergence de LECTURE, pas d'encodage. On ne touche ni à la casse, ni aux
    accents, ni à l'identité des signes — ce sont des lectures."""
    s = unicodedata.normalize('NFC', s)
    for a, b in (('\u2019', "'"), ('\xa0', ' '), ('\u202f', ' '), ('\u2009', ' '),
                 ('\u2018', "'"), ('\u02bc', "'"), ('\u201c', '"'), ('\u201d', '"')):
        s = s.replace(a, b)
    s = ' '.join(s.split())
    if cesure and _CESURE.search(s):
        s = _CESURE.sub('-', s)
    s = _PONCT.sub(r'\1', s)
    s = _PONCT_G.sub(r'\1', s)
    return s


def lev(a: str, b: str) -> int:
    if a == b: return 0
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0]*len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j]+1, cur[j-1]+1, prev[j-1] + (ca != cb))
        prev = cur
    return prev[-1]


def lire_kraken(image, boites, modele='latin', ids=None):
    """Lecteur B. `boites` : liste de (x0, y0, x1, y1) en pixels de l'image."""
    from kraken import rpred
    from kraken.lib import models
    from kraken.containers import Segmentation, BaselineLine
    m = models.load_any(os.path.expanduser(MODELES[modele]))
    bl = []
    for i, (x0, y0, x1, y1) in enumerate(boites):
        yb = int(y0 + (y1-y0)*0.78)
        bl.append(BaselineLine(id=(ids[i] if ids else f'l{i}'),
                               baseline=[(x0, yb), (x1, yb)],
                               boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    seg = Segmentation(type='baselines', imagename='x', text_direction='horizontal-lr',
                       script_detection=False, lines=bl, regions={}, line_orders=[])
    t = time.time()
    hyp = [str(r.prediction or '') for r in rpred.rpred(m, image.convert('L'), seg)]
    return hyp, time.time()-t


def confronter(a: list[str], b: list[str], seuil_refus: int = 3):
    """Confronte deux lectures. Un statut par ligne.

    - `accord`    : identiques après normalisation — validé sans humain
    - `refus`     : au moins un lecteur ne rend rien de substantiel ; ce n'est
                    pas du texte, la ligne sort de la VT au lieu d'être comblée
    - `desaccord` : à arbitrer
    """
    out = []
    for i, (x, y) in enumerate(zip(a, b)):
        na, nb = norm(x), norm(y)
        if len(na) < seuil_refus or len(nb) < seuil_refus:
            out.append({'i': i, 'statut': 'refus', 'a': na, 'b': nb, 'd': None})
        elif na == nb:
            out.append({'i': i, 'statut': 'accord', 'texte': na, 'd': 0})
        else:
            out.append({'i': i, 'statut': 'desaccord', 'a': na, 'b': nb,
                        'd': lev(na, nb)})
    return out


def resume(statuts):
    n = len(statuts)
    c = {k: sum(1 for s in statuts if s['statut'] == k)
         for k in ('accord', 'desaccord', 'refus')}
    return {'lignes': n,
            **{k: v for k, v in c.items()},
            'taux_accord': round(100*c['accord']/max(1, n), 1),
            'taux_relecture': round(100*(c['desaccord']+c['refus'])/max(1, n), 1)}
