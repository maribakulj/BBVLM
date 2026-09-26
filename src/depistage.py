"""B44 — dépistage visuel des boîtes, une ligne à la fois.

B39 a fait juger 24 vignettes sur une planche unique, réduite de moitié à
l'affichage : rappel 62 %, inutilisable. Ici une planche par ligne, à la
résolution que la contrainte de lisibilité impose (voir regle_ligne.ECART_MIN),
avec chaque boîte numérotée. Le VLM nomme les numéros dont la boîte ne colle pas
le mot. Coût : un regard par ligne, contre un pour 1,5 mot au relevé sur règle.

Le dépistage ne mesure pas, il TRIE. Ce qu'il désigne part au relevé sur règle,
qui lui mesure. C'est une cascade, pas un remplacement.
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont

LARGEUR = 1400          # largeur rendue ; au-delà l'afficheur réduit et tout se perd
HAUTEUR_MIN_MOT = 26    # px de hauteur de bande en dessous desquels on ne juge rien


def _fonte(px):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf'):
        try: return ImageFont.truetype(p, px)
        except Exception: pass
    return ImageFont.load_default()


def planche(image_path, line_box, boxes, sortie, depart=1, marge=8):
    """Une bande de ligne, les boîtes en surimpression, numérotées.

    Renvoie None si la bande est trop petite pour qu'un jugement ait un sens —
    refuser de montrer vaut mieux que recueillir un avis sur du flou."""
    im = Image.open(image_path).convert('RGB')
    x0, y0, x1, y1 = [int(v) for v in line_box]
    cx0, cy0 = max(0, x0-marge), max(0, y0-marge)
    cx1, cy1 = min(im.size[0], x1+marge), min(im.size[1], y1+marge)
    c = im.crop((cx0, cy0, cx1, cy1))
    z = LARGEUR/max(1, c.size[0])
    if c.size[1]*z < HAUTEUR_MIN_MOT:
        return None
    c = c.resize((int(c.size[0]*z), int(c.size[1]*z)), Image.LANCZOS)
    BAS = 30
    pl = Image.new('RGB', (c.size[0], c.size[1]+BAS), (255, 255, 255))
    pl.paste(c, (0, 0)); d = ImageDraw.Draw(pl)
    f = _fonte(16)
    for k, (bx0, by0, bx1, by1) in enumerate(boxes):
        a = (bx0-cx0)*z; b = (bx1-cx0)*z
        u = (by0-cy0)*z; v = (by1-cy0)*z
        d.rectangle((a, u, b, v), outline=(225, 0, 0), width=2)
        n = str(depart+k)
        w = d.textlength(n, font=f)
        d.rectangle((a, c.size[1], a+w+6, c.size[1]+BAS-2), fill=(225, 0, 0))
        d.text((a+3, c.size[1]+5), n, fill=(255, 255, 255), font=f)
    pl.save(sortie)
    return {'cx0': cx0, 'z': z, 'n': len(boxes), 'taille': pl.size}


def decouper(boxes, largeur_cible=LARGEUR, min_px_par_mot=110):
    """Groupes de mots tenables sur une planche : chaque mot doit disposer d'au
    moins `min_px_par_mot` pixels rendus, sinon on ne voit pas ses bords."""
    if not boxes: return []
    groupes, i = [], 0
    while i < len(boxes):
        j = i
        while j+1 < len(boxes):
            larg = boxes[j+1][2] - boxes[i][0]
            z = largeur_cible/max(1, larg)
            if min((boxes[k][2]-boxes[k][0])*z for k in range(i, j+2)) < min_px_par_mot:
                break
            j += 1
        groupes.append(list(range(i, j+1)))
        i = j+1
    return groupes
