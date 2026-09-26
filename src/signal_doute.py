"""B41 — le moteur géométrique sait-il quand il se trompe ?

Sans VT, quels indices d'une boîte fausse ? On en calcule plusieurs, tous
mesurables à l'exécution, et on regarde lequel prédit l'erreur réelle (AUC sur
le seuil gelé de 0,5 caractère). Le but n'est pas de corriger : c'est de ROUTER.
Une boîte douteuse part vers le relevé sur règle, une boîte sûre est gardée.
"""
from __future__ import annotations
import numpy as np
import ink


def indices(gray, line, boxes):
    """Un vecteur d'indices par mot. Aucun n'utilise la VT."""
    mask, ox, oy = ink.line_mask(gray, line.line_box)
    H, W = mask.shape
    col = (mask > 0).sum(axis=0).astype(float)
    out = []
    n = len(boxes)
    # largeur de caractère attendue : largeur totale d'encre / nombre de caractères
    nz = np.nonzero(col)[0]
    etendue = (nz.max()-nz.min()+1) if nz.size else 1
    ncar = max(1, sum(len(w) for w in line.words))
    lc_att = etendue / ncar
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        w = line.words[i] if i < len(line.words) else ''
        a, b = max(0, x0-ox), min(W, x1-ox+1)
        sub = col[a:b]
        larg = max(1, b-a)
        # 1. largeur observée / largeur attendue d'après le nombre de caractères
        r_larg = larg / max(1.0, lc_att*max(1, len(w)))
        # 2. encre touchant le bord de la boîte : une coupure en plein caractère
        bord = 0.0
        if sub.size > 2:
            bord = float(max(sub[0], sub[-1])) / max(1.0, sub.max())
        # 3. blanc disponible de part et d'autre (marge de manœuvre)
        gg = 0
        j = a-1
        while j >= 0 and col[j] == 0: gg += 1; j -= 1
        gd = 0
        j = b
        while j < W and col[j] == 0: gd += 1; j += 1
        # 4. creux interne le plus profond rapporté au pic : un mot qui contient
        #    un blanc large est peut-être deux mots collés
        creux = 0.0
        if sub.size > 4 and sub.max() > 0:
            z = (sub == 0).astype(int)
            run = mx = 0
            for v in z:
                run = run+1 if v else 0
                mx = max(mx, run)
            creux = mx / larg
        # 5. densité d'encre
        dens = float((mask[:, a:b] > 0).mean()) if b > a else 0.0
        out.append({'r_larg': round(r_larg, 3), 'bord': round(bord, 3),
                    'gauche': int(gg), 'droite': int(gd),
                    'creux': round(creux, 3), 'dens': round(dens, 3),
                    'marge': round(min(gg, gd)/max(1.0, lc_att), 3)})
    return out
