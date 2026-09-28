"""Chaîne texte P1 après la passe VLM : conformité OCR-D puis règle R1."""
import sys
from ocrd2 import conforme
from harmonise import regle_fraktur


def post(lignes):
    return regle_fraktur([conforme(l) for l in lignes])


if __name__ == '__main__':
    print('\n'.join(post(open(sys.argv[1], encoding='utf-8').read().splitlines())))
