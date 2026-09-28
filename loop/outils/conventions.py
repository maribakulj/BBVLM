"""Explicit evaluation views; never rewrite diplomatic transcription in place.

Ligature identities: OCR-D coordination encoding table and dinglehopper
1efb382a54c98cf2c6d716d134c57a2d1325a6b6. The latter's full normalization is
deliberately NOT the diplomatic view. Unknown PUA remains visible.
"""
import unicodedata

LIGATURES = {
    '\ueba6': 'ſſ', '\ueba7': 'ſſi', '\uf502': 'ch', '\ueec4': 'ck',
    '\uf4f9': 'll', '\ueba2': 'ſi', '\ueada': 'ſt', 'ﬁ': 'fi', 'ﬀ': 'ff',
    'ﬂ': 'fl', 'ﬃ': 'ffi', '\ueec5': 'ct', '\ueedc': 'tz',
    '\uf532': 'as', '\uf533': 'is', '\uf534': 'us', '\uf535': 'Qu',
    'ĳ': 'ij', '\ueba5': 'ſp', 'ﬆ': 'st',
}
# Preserve e-above as e-above, not diaeresis. No NFKC or long-s folding.
DIACRITICS = {'\ue42c': 'a\u0364', '\ue644': 'o\u0364',
              '\ue72b': 'u\u0364', '\uf50e': 'q\u0301'}
PROFILES = ('strict', 'glyph_decomposition_v1')


def transform(text, profile='strict'):
    if profile not in PROFILES:
        raise ValueError(f'Unknown evaluation convention: {profile}')
    if profile == 'strict':
        return text
    text = unicodedata.normalize('NFC', text)
    return unicodedata.normalize('NFC', ''.join(
        LIGATURES.get(c, DIACRITICS.get(c, c)) for c in text))


def private_use_inventory(text):
    from collections import Counter
    return dict(sorted(Counter(f'U+{ord(c):04X}' for c in text
                               if unicodedata.category(c) == 'Co').items()))
