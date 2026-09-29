"""M01 — signes suscrits rattachés à leur lettre dans le filtre de composantes.

Le filtre `connexe` garde une composante si son centre est à moins de
0,45·h du centre de la boîte de ligne. Il dépend donc de la boîte : trop
haute (jambages de la ligne du dessus, hackherz), il garde l'encre voisine ;
serrée sur le corps (G04b), il perd les points, accents et e suscrits
(culmsent : hauts de mots 6 px trop bas). Règle de rattachement (L14 :
une composante appartient à la ligne du corps qu'elle surmonte) : une
composante rejetée est rendue à la ligne si elle est petite (hauteur ≤ 0,5 h),
au-dessus du centre, et posée sur une composante gardée qu'elle chevauche
horizontalement, à moins de 0,35 h de son sommet.
"""
import numpy as np, cv2
import ink
import connexe


class ConnexeSat(connexe.Connexe):
    name = 'connexe+satellites'

    def _masque_serre(self, gray, line):
        keep, ax0, ay0 = super()._masque_serre(gray, line)
        if keep.size <= 1: return keep, ax0, ay0
        x0, y0, x1, y1 = line.line_box
        H, W = gray.shape
        s = ink.line_scale(line.line_box); h = s['h']
        # zone élargie vers le haut pour voir les signes suscrits
        up = int(0.6 * h)
        by0 = max(0, ay0 - up); crop = gray[by0:ay0 + keep.shape[0], ax0:ax0 + keep.shape[1]]
        if crop.size == 0: return keep, ax0, ay0
        blur = cv2.GaussianBlur(crop, (0, 0), s['sigma'])
        norm = cv2.divide(crop, blur, scale=255)
        _, bw = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        big_keep = np.zeros_like(bw); big_keep[ay0 - by0:, :] = keep
        n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
        cy = (y0 + y1) / 2 - by0
        kept_cols = big_keep > 0
        ajout = np.zeros_like(bw)
        for k in range(1, n):
            x, y, w, hh, a = (int(st[k, i]) for i in range(5))
            if hh > 0.5 * h or a < 2: continue
            comp = lab == k
            if (big_keep[comp] > 0).any(): continue            # déjà gardée
            if y + hh / 2 >= cy: continue                     # au-dessus du centre seulement
            # composante gardée sous elle, chevauchement horizontal, écart ≤ 0,35 h
            sous = kept_cols[:, x:x + w]
            ys = np.nonzero(sous.any(axis=1))[0]
            ys = ys[ys >= y + hh - 1]
            if len(ys) and ys.min() - (y + hh) <= 0.35 * h:
                ajout[comp] = 255
        out = np.maximum(big_keep, ajout)
        return out, ax0, by0
