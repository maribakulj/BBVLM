"""Après adjudication : fautes du lecteur et fautes de la référence, en caractères.

Pour chaque item adjugé, on compare lecture et référence au texte retenu par
l'arbitre (vue diplo). « indecidable » est compté à part, jamais en faveur du
lecteur. Les lignes non appariées (découpage folio/signature) sont rapportées
séparément par cer.py, pas ici.
usage : python bilan_adj.py DOSSIER_ADJ (contient cle.json et verdicts.json)
"""
import json, sys
from collections import defaultdict
from cer import vue, lev


def bilan(dossier):
    cle = {c['id']: c for c in json.load(open(f'{dossier}/cle.json'))}
    ver = {v['id']: v for v in json.load(open(f'{dossier}/verdicts.json'))}
    par_lecture = defaultdict(lambda: {'fautes_lecteur': 0, 'fautes_reference': 0, 'indecidables': 0, 'items': 0, 'detail': []})
    for i, c in cle.items():
        v = ver.get(i)
        ref = c['X'] if c['_ref'] == 'X' else c['Y']
        lu = c['Y'] if c['_ref'] == 'X' else c['X']
        b = par_lecture[c['_lecture'].split('/')[-1]]; b['items'] += 1
        if v is None: b['indecidables'] += 1; continue
        juste = vue(v['texte_correct'], 'diplo')
        el, er = lev(lu, juste), lev(ref, juste)
        b['fautes_lecteur'] += el; b['fautes_reference'] += er
        if v['verdict'] == 'indecidable': b['indecidables'] += 1
        if el: b['detail'].append({'lu': lu, 'juste': juste, 'ed': el})
    return dict(par_lecture)


if __name__ == '__main__':
    for k, b in bilan(sys.argv[1]).items():
        print(k, {x: b[x] for x in ('items', 'fautes_lecteur', 'fautes_reference', 'indecidables')})
