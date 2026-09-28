"""R2 déterministe : ů (o suscrit = uo) contre uͤ (e suscrit = inflexion), par le lexique.

Fondement : L06 (diphtongue moyen haut-allemande uo notée ů ; inflexion
notée par e suscrit). Pour un mot lu avec ů, on compare la fréquence
lexicale allemande moderne (wordfreq, zipf) de la forme en u et de la forme
en ü (ſ→s, minuscules, sans ponctuation). Si la forme en ü l'emporte d'au
moins MARGE et est attestée (zipf ≥ MIN), ů devient uͤ. Sens inverse (uͤ → ů)
seulement si la page emploie déjà ů ailleurs. Sinon : on garde la lecture.
"""
import re, unicodedata
from wordfreq import zipf_frequency

MARGE, MIN = 1.0, 2.5
E_ = 'ͤ'


def _cle(mot, v):
    m = unicodedata.normalize('NFC', mot).replace('ſ', 's').lower()
    m = m.replace('ů', v).replace('u'+E_, v)
    return re.sub(r'[^\w]', '', m)


def decide(mot):
    zu, zü = zipf_frequency(_cle(mot, 'u'), 'de'), zipf_frequency(_cle(mot, 'ü'), 'de')
    if zü >= MIN and zü - zu >= MARGE: return 'uͤ'
    if zu >= MIN and zu - zü >= MARGE: return 'ů'
    return None


def applique(lignes):
    t = unicodedata.normalize('NFC', '\n'.join(lignes))
    page_a_rond = 'ů' in t
    out = []
    for l in t.split('\n'):
        mots = []
        for m in l.split(' '):
            if 'ů' in m and decide(m) == 'uͤ':
                m = m.replace('ů', 'u'+E_)
            elif ('u'+E_) in m and page_a_rond and decide(m) == 'ů':
                m = m.replace('u'+E_, 'ů')
            mots.append(m)
        out.append(' '.join(mots))
    return out
