"""Chaîne texte P2 : déclaration d'écriture par le lecteur, OCR-D, R1 si Fraktur.

R1 (tréma minuscule → e suscrit) réfutée en O05 sur une page en romain
(fiscfrie : +20 fautes) : elle n'est plus appliquée que si le lecteur déclare
`#ECRITURE: fraktur` et que la page ne porte pas ů (XVIe s.).
"""
import sys, unicodedata
from ocrd2 import conforme
from harmonise import TREMA, E_


def post(lignes):
    ecriture = None
    corps = []
    for l in lignes:
        if l.strip().lower().startswith('#ecriture:'):
            ecriture = l.split(':', 1)[1].strip().lower(); continue
        corps.append(conforme(l))
    t = unicodedata.normalize('NFC', '\n'.join(corps))
    if ecriture == 'fraktur' and 'ů' not in t:
        for c, v in TREMA.items(): t = t.replace(c, v+E_)
    return t.split('\n'), ecriture


if __name__ == '__main__':
    print('\n'.join(post(open(sys.argv[1], encoding='utf-8').read().splitlines())[0]))
