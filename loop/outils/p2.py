"""Chaîne texte P2 : déclaration d'écriture par le lecteur, OCR-D, R1 si Fraktur.

R1 (tréma minuscule → e suscrit) réfutée en O05 sur une page en romain
(fiscfrie : +20 fautes) : elle n'est plus appliquée que si le lecteur déclare
`#ECRITURE: fraktur` et que la page ne porte pas ů (XVIe s.).
"""
import re, sys, unicodedata
from ocrd2 import conforme
from harmonise import TREMA, E_

ROLE = re.compile(r'^\s*\[[a-z\-]+\+?\]\s?')   # étiquettes de rôle (consigne P4), retirées du texte
# Jetons ASCII de la consigne P6 pour les glyphes sans Unicode standard
# (le lecteur n'émet pas de PUA brut) → codes PUA de la VT OCR-D/SBB.
JETONS = {'{florin}': '\uf2e8', '{groschen}': '\uf2e9'}


def post(lignes):
    ecriture = None
    corps = []
    for l in lignes:
        if l.strip().lower().startswith('#ecriture:'):
            ecriture = l.split(':', 1)[1].strip().lower(); continue
        l = ROLE.sub('', l)
        for j, c in JETONS.items(): l = l.replace(j, c)
        corps.append(conforme(l))
    t = unicodedata.normalize('NFC', '\n'.join(corps))
    if ecriture == 'fraktur' and 'ů' not in t:
        for c, v in TREMA.items(): t = t.replace(c, v+E_)
    from r2 import applique           # R2 : ů / uͤ par l'étymologie (L06), développée sur O02-O08
    return applique(t.split('\n')), ecriture


if __name__ == '__main__':
    print('\n'.join(post(open(sys.argv[1], encoding='utf-8').read().splitlines())[0]))
