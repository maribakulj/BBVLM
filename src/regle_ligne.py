"""B42 — relever toutes les frontières d'une LIGNE sur une seule règle.

B40 a montré que le VLM relève une frontière à 0,08 caractère près quand on lui
donne une règle graduée. Mais une planche par mot coûte un regard par mot :
inutilisable. Ici la règle couvre la ligne entière, le VLM relève les 2N bords
d'un coup. Le coût passe d'un regard par mot à un regard par ligne.

Noté sous les DEUX métriques :
  - celle de CRITERE.md (gelée) : distance de la frontière au blanc inter-mots
  - une métrique stricte : écart de chaque bord de boîte au bord du mot
La première dit si la césure est au bon endroit, la seconde si la boîte épouse
le mot. Une VT au mot a besoin des deux ; elles ne sont pas interchangeables et
les confondre a faussé B39-B41.
"""
from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def planche(image_path, line_box, sortie, pas=None, largeur_cible=1400, marge=6,
            segment=None):
    """Bande de ligne + règle graduée.

    `pas` est en pixels de l'image d'origine. Il doit valoir une fraction de
    caractère, pas une fraction de ligne : une graduation par 0,8 caractère ne
    permet aucun relevé fin (constaté B42, premier tir). `segment` = (a, b)
    découpe la ligne en abscisses d'origine — l'afficheur réduit toute planche
    large, donc mieux vaut deux planches nettes qu'une illisible."""
    im = Image.open(image_path).convert('RGB')
    x0, y0, x1, y1 = [int(v) for v in line_box]
    if segment is not None: x0, x1 = segment
    cx0, cy0 = max(0, x0-marge), max(0, y0-marge)
    cx1, cy1 = min(im.size[0], x1+marge), min(im.size[1], y1+marge)
    c = im.crop((cx0, cy0, cx1, cy1))
    if pas is None:
        pas = max(2, int(round((cx1-cx0)/50)))
    if largeur_cible/max(1, cx1-cx0) * pas < 22:
        # une graduation doit rester séparable à l'œil sur la planche rendue
        pas = max(2, int(round(22*(cx1-cx0)/largeur_cible)))
    z = largeur_cible/max(1, c.size[0])
    c = c.resize((int(c.size[0]*z), int(c.size[1]*z)), Image.LANCZOS)
    R = 40
    pl = Image.new('RGB', (c.size[0], c.size[1]+R+20), (255, 255, 255))
    pl.paste(c, (0, R)); d = ImageDraw.Draw(pl)
    try: f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)
    except Exception: f = ImageFont.load_default()
    # Le relevé ne se trompe pas sur les distances mais sur le COMPTAGE : sur une
    # planche dense (un chiffre tous les 5) l'origine a été lue une graduation
    # trop loin, d'où un biais systématique de 0,41 caractère sur tout le segment
    # (B42). On chiffre donc chaque graduation dès que la place le permet, et
    # l'origine porte une marque noire qu'on ne peut pas confondre avec un trait.
    total = len(range(0, cx1-cx0, pas))
    chaque = 1 if total <= 34 else (2 if total <= 70 else 5)
    n = 0
    for px in range(0, cx1-cx0, pas):
        X = int(px*z)
        gros = (n % chaque == 0)
        d.line((X, R-(14 if gros else 7), X, R+(c.size[1] if gros else 5)),
               fill=(255, 60, 60) if gros else (255, 175, 175), width=1)
        if gros:
            d.text((X+2, 1), str(n), fill=(200, 0, 0), font=f)
            d.text((X+2, R+c.size[1]+1), str(n), fill=(200, 0, 0), font=f)
        n += 1
    d.rectangle((0, 0, 4, R+c.size[1]+18), fill=(0, 0, 0))
    d.text((6, R+c.size[1]+1), '0', fill=(0, 0, 0), font=f)
    pl.save(sortie)
    return {'cx0': cx0, 'pas': pas, 'z': z, 'graduations': n, 'taille': pl.size}


#: écartement minimal des graduations sur la planche rendue, en pixels. En
#: dessous, le relevé cesse d'être fiable : mesuré B42, dispersion 0,13 caractère
#: à 34 px par graduation contre 0,32 à 22 px, sur les mêmes mots et le même œil.
ECART_MIN = 30
#: pas de graduation visé, en fraction de caractère. Plus fin ne sert à rien :
#: la dispersion du relevé domine.
PAS_CAR = 0.33


def decouper(vt_boxes, cw, largeur_cible=1400):
    """Découpe une ligne en segments tels que la planche reste lisible.

    Deux contraintes opposées : le pas doit valoir une fraction de caractère
    (sinon on ne peut pas relever finement) et les graduations doivent rester
    écartées d'au moins ECART_MIN pixels sur la planche (sinon on les compte de
    travers). Le nombre de mots par planche en découle — il n'est pas choisi.
    """
    pas = max(2.0, cw*PAS_CAR)
    # largeur d'origine maximale tenable sur une planche
    # les marges de part et d'autre comptent dans la largeur rendue
    max_larg = largeur_cible*pas/ECART_MIN - 2*cw*0.4
    segs, i = [], 0
    while i < len(vt_boxes):
        j = i
        while j+1 < len(vt_boxes) and \
                vt_boxes[j+1][2] - vt_boxes[i][0] <= max_larg:
            j += 1
        a = vt_boxes[i][0] - cw*0.4
        b = vt_boxes[j][2] + cw*0.4
        segs.append({'a': int(a), 'b': int(b), 'mots': list(range(i, j+1)),
                     'pas': int(round(pas))})
        i = j+1
    return segs


def vers_pixels(valeurs, meta):
    """Graduations relevées -> abscisses dans l'image d'origine."""
    return [meta['cx0'] + v*meta['pas'] for v in valeurs]


def noter(pred_x, vt_boxes, mots):
    """pred_x : liste plate [x0,x1, x0,x1, ...] par mot. Renvoie les deux
    métriques, avec les mêmes conventions que judge.py pour la gelée."""
    n = len(mots)
    span = vt_boxes[-1][2] - vt_boxes[0][0]
    cw = max(1.0, span/max(1, sum(len(w) for w in mots)))
    gelee, stricte = [], []
    for k in range(n-1):
        lo, hi = vt_boxes[k][2], vt_boxes[k+1][0]
        if hi < lo: lo, hi = hi, lo
        x = (pred_x[2*k+1] + pred_x[2*k+2])/2.0
        gelee.append((0.0 if lo <= x <= hi else (lo-x if x < lo else x-hi))/cw)
    for k in range(n):
        stricte.append(max(abs(pred_x[2*k]-vt_boxes[k][0]),
                           abs(pred_x[2*k+1]-vt_boxes[k][2]))/cw)
    return {'gelee': gelee, 'stricte': stricte, 'cw': cw}
