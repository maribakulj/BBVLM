"""Mise en conformité déterministe d'une lecture avec OCR-D niveau 2.

Règle documentée (gt-guidelines, level_2_2) : « Spaces are only reproduced as
separators of words. Punctuation marks are always added to the preceding
word. » On retire donc toute espace AVANT un signe de ponctuation. Introduite
après O02 sur la foi de la règle publiée ; validée seulement sur des pages
non encore lues.
"""
import re
PONCT = r'[/,.;:?!)\]]'


def conforme(ligne: str) -> str:
    ligne = re.sub(r'\s+(' + PONCT + ')', r'\1', ligne)
    # La virgule oblique appartient au mot précédent : le mot suivant en est
    # séparé par une espace (ajouté après O03, où les lecteurs la collaient
    # au mot suivant ; règle tirée du même principe OCR-D, pas d'un score).
    ligne = re.sub(r'/(?=[^\W\d_])', '/ ', ligne)
    return ' '.join(ligne.split())
