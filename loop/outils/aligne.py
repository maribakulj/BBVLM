"""Aligner les lignes lues (ordre de lecture) sur les lignes prédites (kraken).

Sans référence : programmation dynamique sur deux suites ordonnées. Les lignes
kraken sont ordonnées par colonnes (bord gauche regroupé) puis par y. Coût
d'une paire = écart relatif entre la largeur de la ligne kraken et la largeur
attendue (nombre de caractères × largeur moyenne d'un caractère estimée sur
la page par moindres carrés robustes). Sauts autorisés des deux côtés
(ligne kraken sans texte : filet, bruit ; ligne lue sans ligne kraken : non
détectée) avec une pénalité fixe.
"""
import os
import numpy as np


def xycut(boites):
    """S03 — découpe XY récursive (Nagy & Seth 1984 ; Ha et al. 1995, L09) sur
    les boîtes de lignes : à chaque nœud, colonnes d'abord (blanc vertical
    traversant ≥ 0,5 h), sinon bandes (blanc horizontal ≥ 0,5 h), h = hauteur
    médiane de ligne ; colonnes de gauche à droite, bandes de haut en bas. Un
    titre pleine largeur devient une bande au lieu de fondre les colonnes."""
    n = len(boites)
    if not n: return []
    h = float(np.median([b[3]-b[1] for b in boites])) or 1.0
    def coupe(idx, lo, hi):
        s = sorted(idx, key=lambda i: boites[i][lo])
        gr, fin = [[s[0]]], boites[s[0]][hi]
        for i in s[1:]:
            if boites[i][lo] - fin >= .5*h: gr.append([i])
            else: gr[-1].append(i)
            fin = max(fin, boites[i][hi])
        return gr
    def rec(idx):
        if len(idx) <= 1: return idx
        for lo, hi in ((0, 2), (1, 3)):
            gr = coupe(idx, lo, hi)
            if len(gr) > 1: return [i for g in gr for i in rec(g)]
        return sorted(idx, key=lambda i: (boites[i][1]+boites[i][3])/2)
    return rec(list(range(n)))


def ordre_lecture(boites):
    if os.environ.get('BBVLM_ORDRE') == 'xy': return xycut(boites)
    return ordre_union(boites)


def ordre_union(boites):
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
    if os.environ.get('BBVLM_CHASSE', 'h') == 'h':
        # S04 : la chasse suit le corps — largeur attendue ∝ caractères × hauteur
        # de ligne (un titre en gros corps n'est plus pris pour une ligne courte)
        hb = [max(1, b[3]-b[1]) for b in B]
        w = [w[j]/hb[j] for j in range(len(B))]
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


def colonnes(boites):
    """Groupes de recouvrement horizontal (voir ordre_lecture) ; renvoie la liste
    des groupes, le plus large (colonne principale) en premier."""
    n = len(boites); par = list(range(n))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(n):
        for j in range(i+1, n):
            a, b = boites[i], boites[j]
            if min(a[2], b[2]) - max(a[0], b[0]) >= .3*min(a[2]-a[0], b[2]-b[0]): par[f(i)] = f(j)
    g = {}
    for i in range(n): g.setdefault(f(i), []).append(i)
    return sorted(g.values(), key=lambda x: -sum(boites[i][2]-boites[i][0] for i in x))


def aligne_roles(textes, roles, boites):
    """Manchettes alignées sur les lignes hors colonne principale, le reste sur
    la colonne principale et les lignes courtes qui la prolongent (folio,
    réclame, signature). Rend {indice_texte: indice_boite}."""
    gs = colonnes(boites)
    principal = set(gs[0]) if gs else set()
    larges = max((boites[i][2]-boites[i][0] for i in principal), default=1)
    marge = [i for i in range(len(boites)) if i not in principal and (boites[i][2]-boites[i][0]) < .5*larges]
    reste = [i for i in range(len(boites)) if i not in marge]
    res = {}
    for groupe, filtre in ((reste, lambda r: r != 'marginalia'), (marge, lambda r: r == 'marginalia')):
        idx_t = [k for k, r in enumerate(roles) if filtre(r)]
        if not idx_t or not groupe: continue
        a = aligne([textes[k] for k in idx_t], [boites[i] for i in groupe])
        for kt, kb in a.items(): res[idx_t[kt]] = groupe[kb]
    return res
