"""Vue CTC d'un passage Markdown remis à la ligne, sans correction du texte.

L'artefact ``source_text`` reste intact. La vue remplace chaque caractère
reconnu par ``str.isspace`` par un espace ASCII, un pour un : ``\r\n`` donne
deux espaces. Elle ne fusionne pas les blancs, ne supprime aucun caractère,
ne touche ni à la ponctuation ni à la composition Unicode et ne raccorde
jamais les mots coupés. Les offsets sont des indices de points de code
Python, pas des offsets UTF-8 ni des positions de graphèmes.

La variante compacte regroupe les blancs internes pour le transport ALTO et
explicite les blancs de bord retirés ; ses intervalles gardent chaque adresse
dans la même source intacte.
"""
from __future__ import annotations


VERSION = 'page-line-text-view-v1'
COMPACT_VERSION = 'page-compact-line-text-view-v1'


def line_text_view(source_text):
    """Retourner la vue d'alignement, sa source exacte et les offsets réversibles.

    ``source_offsets[i]`` désigne le caractère de ``source_text`` représenté
    par le caractère ``text[i]``. Remplacer les seuls blancs un pour un garde
    tous les indices et la même suite de mots pour le placement CTC. Le
    consommateur conserve cette provenance et les caractères source lors de
    l'export ; ``text`` est une vue de calcul, pas une transcription corrigée.
    """
    if not isinstance(source_text, str):
        raise TypeError('Le texte source doit être une chaîne')
    text = ''.join(' ' if character.isspace() else character for character in source_text)
    changed = [index for index, (before, after) in enumerate(zip(source_text, text)) if before != after]
    if len(text) != len(source_text) or text.split() != source_text.split():
        raise ValueError('La vue de ligne ne conserve pas les caractères et les mots source')
    return dict(text=text, source_text=source_text, source_offsets=list(range(len(source_text))),
        transform=dict(name='whitespace_to_ascii_space', version=VERSION,
            whitespace_policy='python_str_isspace', changed_indices=changed,
            offset_unit='unicode_codepoints', mapping='one_to_one',
            crlf='two_ascii_spaces', token_sequence_preserved=True))


def compact_line_text_view(source_text):
    """Vue compatible avec des mots ALTO réunis par un seul espace ASCII.

    Chaque run interne de caractères ``str.isspace`` devient un seul espace.
    Les blancs de bord sont retirés de la vue et leurs intervalles sont
    déclarés dans ``transform.trimmed_source_spans``. Ils restent évidemment
    dans ``source_text``, conservé à l'identique. Aucun caractère non blanc
    n'est supprimé, normalisé ou remplacé.

    ``source_spans[i] == [a, b]`` est l'intervalle source demi-ouvert associé
    au caractère ``text[i]``. Une lettre représente exactement ``[a, a+1]``
    dans la source ; un espace peut représenter tout un run CRLF/tabulation/
    espace Unicode. Les offsets comptent les points de code Unicode, pas les
    octets ni les graphèmes. La vue vérifie ``' '.join(source_text.split())``.
    """
    if not isinstance(source_text, str):
        raise TypeError('Le texte source doit être une chaîne')
    characters, spans, trimmed, whitespace_runs = [], [], [], []
    index = 0
    while index < len(source_text):
        start = index
        if source_text[index].isspace():
            while index < len(source_text) and source_text[index].isspace():
                index += 1
            span = [start, index]
            whitespace_runs.append(span)
            if not characters or index == len(source_text):
                trimmed.append(span)
                continue
            characters.append(' ')
            spans.append(span)
        else:
            characters.append(source_text[index])
            spans.append([index, index+1])
            index += 1
    text = ''.join(characters)
    if text != ' '.join(source_text.split()) or len(spans) != len(text):
        raise ValueError('La vue compacte ne conserve pas les mots et intervalles source')
    return dict(text=text, source_text=source_text, source_spans=spans,
        source_offsets=[span[0] for span in spans],
        transform=dict(name='whitespace_runs_to_ascii_space', version=COMPACT_VERSION,
            whitespace_policy='python_str_isspace', whitespace_runs=whitespace_runs,
            boundary_whitespace='trimmed_in_view_only', trimmed_source_spans=trimmed,
            offset_unit='unicode_codepoints', mapping='one_character_to_source_span',
            crlf='one_ascii_space_inside_text', token_sequence_preserved=True,
            nonwhitespace_characters_preserved=True))
