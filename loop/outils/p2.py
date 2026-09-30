"""Chaîne texte P2 : déclaration d'écriture par le lecteur, OCR-D, R1 si Fraktur.

R1 (tréma minuscule → e suscrit) réfutée en O05 sur une page en romain
(fiscfrie : +20 fautes) : elle n'est plus appliquée que si le lecteur déclare
`#ECRITURE: fraktur` et que la page ne porte pas ů (XVIe s.).
"""
import os, re, sys, unicodedata
from ocrd2 import conforme
from harmonise import TREMA, E_

ROLE = re.compile(r'^\s*\[[a-z\-]+\+?\]\s?')   # étiquettes de rôle (consigne P4), retirées du texte
# Jetons ASCII de la consigne P6 pour les glyphes sans Unicode standard
# (le lecteur n'émet pas de PUA brut) → codes PUA de la VT OCR-D/SBB.
JETONS = {'{florin}': '\uf2e8', '{groschen}': '\uf2e9'}


def parenthese(l):
    # R3 : parenthèse ouvrante séparée du mot qui précède (VT SBB : 23 « x ( » contre 0 « x( » ;
    # les lecteurs la collent parfois, ce qui fusionne deux mots : buchdas/24 « ſie(die »)
    if os.environ.get('BBVLM_R3', '1') != '1': return l
    import re
    l = re.sub(r'(\w)\(', r'\1 (', l)
    if os.environ.get('BBVLM_R4', '1') == '1':
        # R4 : blanc après un point d'abréviation collé au mot suivant (VT : 795 « x. y » contre 2 sigles
        # minuscules « v.c. ») ; sigle de lettres minuscules isolées gardé tel quel
        l = re.sub(r'(?<!\w)([a-zſ])\.([a-zſ])(?=\.)', lambda m: m.group(1) + '\x00' + m.group(2), l)
        l = re.sub(r'(\w)\.(\w)', r'\1. \2', l)
        l = re.sub(r'(\w)\.(\w)', r'\1. \2', l)
        l = l.replace('\x00', '.')
    return l


def post(lignes):
    ecriture = inflexion = None
    corps = []
    for l in lignes:
        if l.strip().lower().startswith('#ecriture:'):
            ecriture = l.split(':', 1)[1].strip().lower(); continue
        if l.strip().lower().startswith('#inflexion:'):   # P7 : signe d'inflexion de l'imprimeur
            inflexion = l.split(':', 1)[1].strip().lower(); continue
        l = ROLE.sub('', l)
        for j, c in JETONS.items(): l = l.replace(j, c)
        corps.append(parenthese(conforme(l)))
    t = unicodedata.normalize('NFC', '\n'.join(corps))
    if os.environ.get('BBVLM_QUE', '1') == '1':
        # L1 (après O15) : l'abréviation latine « -que » (q + ꝫ final) est codée
        # par la VT OCR-D/SBB en ligature MUFI PUA : U+E8BF, et U+F50D avec accent
        if os.environ.get('BBVLM_QFIN', '1') == '1':
            # T01b : « q́ » final de mot est toujours q́ꝫ dans la VT (14 + 1 q́;, aucun seul)
            t = re.sub('q\u0301(?![\\w;])', 'q\u0301\ua76b', t)
        t = t.replace('q\u0301\ua76b', '\uf50d').replace('q\ua76b', '\ue8bf')
    if os.environ.get('BBVLM_APOS', '1') == '1':
        # L2 : la VT SBB code toute apostrophe en ' droite (29 pages, aucune ’)
        t = t.replace('\u2019', "'")
    e_ok = inflexion in (None, 'e')   # R1, R2 supposent l'inflexion notée par e suscrit (herbdulc : anneau)
    if ecriture == 'fraktur' and 'ů' not in t and e_ok:
        for c, v in TREMA.items(): t = t.replace(c, v+E_)
    if os.environ.get('BBVLM_R2', '1') == '0' or not e_ok: return t.split('\n'), ecriture
    from r2 import applique           # R2 : ů / uͤ par l'étymologie (L06), développée sur O02-O08
    return applique(t.split('\n')), ecriture


if __name__ == '__main__':
    print('\n'.join(post(open(sys.argv[1], encoding='utf-8').read().splitlines())[0]))
