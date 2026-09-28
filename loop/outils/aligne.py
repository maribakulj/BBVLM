"""Aligner les lignes lues (ordre de lecture) sur les lignes prédites (kraken).

Sans référence : programmation dynamique sur deux suites ordonnées. Les lignes
kraken sont ordonnées par colonnes (bord gauche regroupé) puis par y. Coût
d'une paire = écart relatif entre la largeur de la ligne kraken et la largeur
attendue (nombre de caractères × largeur moyenne d'un caractère estimée sur
la page par moindres carrés robustes). Sauts autorisés des deux côtés
(ligne kraken sans texte : filet, bruit ; ligne lue sans ligne kraken : non
détectée) avec une pénalité fixe.
"""
import numpy as np


def ordre_lecture(boites):
    """Colonnes = groupes de lignes dont les étendues horizontales ne se
    recouvrent pas (une ligne en retrait recouvre la ligne pleine : même
    colonne). Union-find sur le recouvrement horizontal ≥ 30 % de la plus
    étroite ; chaque colonne est lue de haut en bas, colonnes de gauche à droite.
    Les colonnes d'une ou deux lignes (manchettes) sont fondues dans la
    colonne voisine par y, pour garder l'ordre de lecture du lecteur."""
    n = len(boites)
    if not n: return []
    par = list(range(n))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(n):
        for j in range(i+1, n):
            a, b = boites[i], boites[j]
            rec = min(a[2], b[2]) - max(a[0], b[0])
            if rec >= .3*min(a[2]-a[0], b[2]-b[0]): par[f(i)] = f(j)
    groupes = {}
    for i in range(n): groupes.setdefault(f(i), []).append(i)
    grands = [g for g in groupes.values() if len(g) >= 3]
    if len(grands) < 2:
        return sorted(range(n), key=lambda i: (boites[i][1]+boites[i][3])/2)
    grands.sort(key=lambda g: min(boites[i][0] for i in g))
    rang = {}
    for c, g in enumerate(grands):
        for i in g: rang[i] = c
    for g in groupes.values():
        if len(g) < 3:
            for i in g:
                yc = (boites[i][1]+boites[i][3])/2
                rang[i] = min(range(len(grands)), key=lambda c: min(abs((boites[k][1]+boites[k][3])/2-yc) for k in grands[c]))
    return sorted(range(n), key=lambda i: (rang[i], (boites[i][1]+boites[i][3])/2))


def aligne(textes, boites, penalite=0.8):
    """Rend {indice_texte: indice_boite}."""
    if not textes or not boites: return {}
    ordre = ordre_lecture(boites)
    B = [boites[i] for i in ordre]
    n = [max(1, len(t)) for t in textes]; w = [b[2]-b[0] for b in B]
    # largeur de caractère : médiane des rapports sur l'appariement diagonal
    k = min(len(n), len(w))
    cw = float(np.median([w[i]/n[i] for i in range(k)])) or 1.0
    INF = 1e18
    T, K = len(textes), len(B)
    D = np.full((T+1, K+1), INF); D[0, :] = np.arange(K+1)*penalite; D[:, 0] = np.arange(T+1)*penalite
    P = {}
    for i in range(1, T+1):
        for j in range(1, K+1):
            c = abs(w[j-1] - n[i-1]*cw) / max(w[j-1], n[i-1]*cw)
            opts = [(D[i-1, j-1]+c, 'm'), (D[i-1, j]+penalite, 't'), (D[i, j-1]+penalite, 'k')]
            D[i, j], P[i, j] = min(opts)
    i, j, res = T, K, {}
    while i > 0 and j > 0:
        op = P[i, j]
        if op == 'm': res[i-1] = ordre[j-1]; i -= 1; j -= 1
        elif op == 't': i -= 1
        else: j -= 1
    return res
