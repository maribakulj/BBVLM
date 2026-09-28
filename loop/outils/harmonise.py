"""Cohérence typographique de la page : une fonte = une forme d'inflexion.

Dans une page, tréma (ä ö ü) et e suscrit (aͤ oͤ uͤ) d'une même fonte ne
coexistent pas ; le lecteur hésite pourtant d'une occurrence à l'autre. Si une
forme est majoritaire à ≥ SEUIL parmi les inflexions de la page, les autres
occurrences y sont ramenées. Le rond suscrit ů (uo, XVIe s.) est une lettre
distincte : jamais touché. Majuscules non touchées (Ä peut être une autre fonte).
Développé sur O02-O04 (consommées) ; à valider sur des pages neuves.
"""
import sys, unicodedata
SEUIL = 0.7
E_ = 'ͤ'
TREMA = {'ä': 'a', 'ö': 'o', 'ü': 'u'}


def formes(texte):
    t = unicodedata.normalize('NFC', texte)
    tr = sum(t.count(c) for c in TREMA)
    es = sum(t.count(v+E_) for v in 'aou')
    return tr, es


def harmonise(lignes, seuil=SEUIL):
    tr, es = formes('\n'.join(lignes))
    n = tr+es
    if n < 3: return lignes
    out = []
    for l in lignes:
        l = unicodedata.normalize('NFC', l)
        if es/n >= seuil:
            for c, v in TREMA.items(): l = l.replace(c, v+E_)
        elif tr/n >= seuil:
            for c, v in TREMA.items(): l = l.replace(v+E_, c)
        out.append(l)
    return out


if __name__ == '__main__':
    print('\n'.join(harmonise(open(sys.argv[1], encoding='utf-8').read().splitlines())))


def regle_fraktur(lignes):
    """Règle R1 (développée sur O02-O04, à valider) : dans ce corpus (VD17-VD18,
    Fraktur), l'inflexion minuscule est un e suscrit — 0 tréma dans les 13
    références SBB consommées. Exception : une page qui porte ů (système
    graphique du XVIe s.) garde ses trémas, qui y sont réels (ejngerez)."""
    t = '\n'.join(lignes)
    if 'ů' in unicodedata.normalize('NFC', t):
        return lignes
    out = []
    for l in lignes:
        l = unicodedata.normalize('NFC', l)
        for c, v in TREMA.items(): l = l.replace(c, v+E_)
        out.append(l)
    return out
