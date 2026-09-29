"""Vue « glyphe » : deux transcriptions sont égales si elles montrent les mêmes
signes, quel que soit leur codage. Une passe juste n'est jamais comptée fausse
pour une question d'octets.

Équivalences, toutes appliquées des deux côtés (référence et lecture), jamais
à la sortie publiée :
1. Unicode canonique (NFD puis NFC) ;
2. PUA de la table de codage OCR-D (ocrd_codage_pua.json) → séquence Unicode
   standard, dérivée AUTOMATIQUEMENT de la description de chaque caractère
   (« q ligated with final et » → q + ꝫ ; « n with medium high macron above »
   → n + U+0304 ; « ligature long s descending t » → ſt). Une description non
   analysable laisse le PUA tel quel (visible, compté) ;
3. variantes typographiques d'un même signe, déclarées ici et seulement ici :
   apostrophes, point médian, fraction précomposée (½ = 1/2), trait nasal
   (tilde = macron suscrit), variantes grecques de glyphe (ϑ θ, ϖ π, ϐ β).
Ce qui reste distinct est graphémique au niveau 2 OCR-D : ſ/s, ⸗/-, uͤ/ü/ů,
ꝛ/r, abréviations, blancs.
"""
import json, os, re, unicodedata

_MARQUES = [  # (motif de description, signe combinant) — du plus long au plus court
    (r'latin small letter e above|e above', 'ͤ'), (r'latin small letter a above|a above', 'ͣ'),
    (r'medium-high macron.*|medium high macron above|high macron above|macron above|macron', '̄'),
    (r'tilde', '̃'), (r'diaeresis', '̈'), (r'acute accent above|acute accent|acute', '́'),
    (r'ring above', '̊'), (r'dot above', '̇'), (r'breve', '̆'), (r'hook above', '̉'),
]
_LETTRES = {'long s': 'ſ', 'final et': 'ꝫ', 'neckless a e': None}


def _lettre(mot):
    mot = mot.strip()
    if mot in _LETTRES: return _LETTRES[mot]
    m = re.fullmatch(r'(?:latin )?(small|capital) (?:letter )?([a-z])', mot)
    if m: return m.group(2) if m.group(1) == 'small' else m.group(2).upper()
    return None


def _derive(desc):
    d = desc.lower().replace('latin ', '').strip()
    # ligatures : « small ligature long s descending t », « ligature capital q small u »
    m = re.fullmatch(r'(small |capital )?ligature (.+)', d)
    if m:
        s = m.group(2).replace('descending ', '')
        out, reste = '', s
        while reste:
            for k in ('long s', 'capital ', 'small '):
                if reste.startswith(k):
                    if k == 'long s': out += 'ſ'; reste = reste[len(k):].lstrip()
                    else:
                        c = reste[len(k)]; out += c.upper() if k == 'capital ' else c; reste = reste[len(k)+1:].lstrip()
                    break
            else:
                m2 = re.match(r'([a-z]{1,3})(\s|$)', reste)   # « ck », « as », « a e »
                if m2 and m2.group(1) not in ('pp',) or (m2 and reste.strip() == 'pp'):
                    out += m2.group(1); reste = reste[len(m2.group(1)):].lstrip()
                else: return None
        return out if len(out) >= 2 else None
    # lettre + marque ou lettre liée : « small letter q ligated with final et and acute accent »
    m = re.fullmatch(r'(small|capital) letter ([a-z])(?: (?:with|ligated with) (.+))?', d)
    if not m or not m.group(3): return None
    base = m.group(2) if m.group(1) == 'small' else m.group(2).upper()
    marques, suite = '', m.group(3)
    lie = ''
    for partie in re.split(r' and | with ', suite):
        partie = partie.strip()
        if partie.startswith('final et'): lie = 'ꝫ'; partie = partie[len('final et'):].strip()
        m3 = re.fullmatch(r'small letter ([a-z]) above', partie)     # lettre suscrite (a e i o u c d h m r t v x)
        if m3:
            try: marques += unicodedata.lookup(f'COMBINING LATIN SMALL LETTER {m3.group(1).upper()}')
            except KeyError: return None
            continue
        if partie in ('', 'overline'): marques += '̅' if partie == 'overline' else ''; continue
        for motif, c in _MARQUES:
            if re.fullmatch(motif, partie): marques += c; break
        else:
            if partie.startswith('small letter') and 'ligated' not in partie:   # « ligated with latin small letter h »
                l = _lettre(partie)
                if l: lie += l; continue
            return None
    return base + marques + lie


def _table():
    f = os.path.join(os.path.dirname(__file__), 'ocrd_codage_pua.json')
    t = {}
    for code, v in json.load(open(f)).items():
        seq = _derive(v[2])
        if seq: t[chr(int(code, 16))] = unicodedata.normalize('NFC', seq)
    return t


PUA = _table()
TYPO = {'’': "'", 'ʼ': "'", '‘': "'", '‧': '·', '⋅': '·', '⁄': '/',
        'ϑ': 'θ', 'ϖ': 'π', 'ϐ': 'β', '̃': '̄'}


def glyphe(t):
    from conventions import transform
    t = transform(unicodedata.normalize('NFC', t), 'glyph_decomposition_v1')
    t = ''.join(PUA.get(c, c) for c in t)
    # fraction précomposée → chiffres/barre (NFKD limité aux fractions vulgaires)
    t = ''.join(unicodedata.normalize('NFKD', c) if unicodedata.name(c, '').startswith('VULGAR FRACTION') else c for c in t)
    t = unicodedata.normalize('NFD', t)
    t = ''.join(TYPO.get(c, c) for c in t)
    return unicodedata.normalize('NFC', t)


if __name__ == '__main__':
    import sys
    tab = json.load(open(os.path.join(os.path.dirname(__file__), 'ocrd_codage_pua.json')))
    n = 0
    for code, v in tab.items():
        s = PUA.get(chr(int(code, 16)))
        n += s is not None
        print(f"{code} {'→ ' + ' '.join(f'U+{ord(c):04X}' for c in s) if s else '(gardé)':40s} {v[2]}")
    print(f'{n}/{len(tab)} dérivés')
