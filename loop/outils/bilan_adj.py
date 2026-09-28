"""Après adjudication : référence adjugée, puis CER de chaque lecture contre elle.

Chaque ligne de référence contestée reçoit le texte retenu par l'arbitre
(vue diplo) ; si deux verdicts sur la même ligne divergent, la ligne est
marquée « conflit » et garde la référence d'origine. On rapporte, par
lecture : CER contre la référence distribuée et contre la référence adjugée,
et le nombre de caractères où la référence distribuée se trompait.
usage : python bilan_adj.py DOSSIER_PAGE LECTURE...
"""
import json, sys
from cer import vue, lev, score
import os
A1 = os.environ.get('BBVLM_A1') == '1'


def reference_adjugee(dossier):
    ref = json.load(open(f'{dossier}/ref.json'))
    cle = json.load(open(f'{dossier}/adj/cle.json'))
    ver = {v['id']: v for v in json.load(open(f'{dossier}/adj/verdicts.json'))}
    try:
        ver2 = {v['id']: v for v in json.load(open(f'{dossier}/adj/verdicts2.json'))}
    except FileNotFoundError:
        ver2 = {}
    choix, conflits, indec, contestes = {}, set(), 0, 0
    for c in cle:
        v = ver.get(c['id'])
        if v is None: continue
        r = c['X'] if c['_ref'] == 'X' else c['Y']
        j = vue(v['texte_correct'], 'diplo')
        indec += v['verdict'] == 'indecidable'
        # Règle A2 (après O10) : tout texte autre que la référence distribuée
        # — texte neuf OU choix de la lecture contre la référence — n'est
        # retenu que si un second arbitre indépendant écrit le même. Un arbitre
        # seul a renversé à tort ﬂ → ſl sur herrkurt. BBVLM_A1=1 : règle A1.
        neuf = v['verdict'] in ('aucun', 'partage', 'indecidable') or j not in (vue(c['X'], 'diplo'), vue(c['Y'], 'diplo'))
        if neuf or (not A1 and j != vue(r, 'diplo')):
            v2 = ver2.get(c['id'])
            if v2 is None or vue(v2['texte_correct'], 'diplo') != j:
                contestes += 1
                continue
        if r in choix and choix[r] != j: conflits.add(r)
        choix.setdefault(r, j)
    adj, err_ref = [], 0
    for x in ref:
        d = vue(x, 'diplo')
        if d in choix and d not in conflits:
            err_ref += lev(d, choix[d]); adj.append(choix[d])
        else:
            adj.append(x)
    return adj, {'lignes_corrigees': sum(1 for d in choix if d not in conflits and choix[d] != d),
                 'car_faux_reference': err_ref, 'conflits': len(conflits), 'indecidables': indec,
            'contestes_non_retenus': contestes}


if __name__ == '__main__':
    dossier = sys.argv[1]
    ref = json.load(open(f'{dossier}/ref.json'))
    adj, info = reference_adjugee(dossier)
    json.dump(adj, open(f'{dossier}/ref_adjugee.json', 'w'), ensure_ascii=False, indent=0)
    print(info)
    for lec in sys.argv[2:]:
        h = open(lec, encoding='utf-8').read().splitlines()
        a, b = score(ref, h, 'diplo'), score(adj, h, 'diplo')
        n = score(adj, h, 'norm')
        print(f"{lec.split('/')[-1]:14s} diplo distribuée {100*a['cer']:.3f} % ({a['editions']}) | adjugée {100*b['cer']:.3f} % ({b['editions']}) | norm adjugée {100*n['cer']:.3f} % ({n['editions']}) exactes {b['lignes_exactes']}/{b['lignes_ref']}")
