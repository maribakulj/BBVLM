"""B24 — resserrer le filtre de composantes plutôt qu'ajouter un mécanisme.

B23 a échoué en coupant dans le profil d'encre : hampes et jambages partaient
avec les voisines. Le bon discriminant existe déjà dans `ink.line_mask`, qui
écarte les composantes dont le centre s'éloigne du centre de ligne de plus de
0,85 × sa hauteur. Sur Newseye, dont les boîtes de lignes valent 1,5 fois la
hauteur des mots, ce seuil laisse passer les voisines.

Une composante appartient à la ligne si son centre est proche du centre — et une
hampe reste centrée même si elle dépasse en hauteur. Resserrer le seuil garde
donc les hampes et écarte les voisines, là où couper dans le profil faisait
l'inverse.
"""
from __future__ import annotations
import numpy as np
import ink
from compose import Compose

SERRAGE = 0.45      # au lieu de 0,85


class Connexe:
    name = 'connexe'

    def __init__(self):
        self.base = Compose()

    def boxes(self, gray: np.ndarray, line):
        brut = self.base.boxes(gray, line)
        orig = ink.line_scale
        def serre(bx):
            s = orig(bx); s['cc_dy'] = SERRAGE; return s
        # masque strict : même extraction, critère de centrage resserré
        mask, ox, oy = self._masque_serre(gray, line)
        if mask.size <= 1: return brut
        out = []
        for (x0, y0, x1, y1) in brut:
            a = max(0, min(mask.shape[1]-1, x0-ox))
            b = max(0, min(mask.shape[1]-1, x1-ox))
            rows = np.where((mask[:, a:b+1] > 0).any(axis=1))[0]
            if len(rows) == 0:
                out.append((x0, y0, x1, y1)); continue
            out.append((x0, oy+int(rows.min()), x1, oy+int(rows.max())))
        return out

    def _masque_serre(self, gray, line):
        import cv2
        x0, y0, x1, y1 = line.line_box
        H, W = gray.shape
        s = ink.line_scale(line.line_box)
        dy = int(s['h']*0.10)
        ax0, ay0 = max(0, x0), max(0, y0-dy)
        ax1, ay1 = min(W, x1), min(H, y1+dy)
        if ax1-ax0 < 4 or ay1-ay0 < 4: return np.zeros((1, 1), np.uint8), ax0, ay0
        crop = gray[ay0:ay1, ax0:ax1]
        blur = cv2.GaussianBlur(crop, (0, 0), s['sigma'])
        norm = cv2.divide(crop, blur, scale=255)
        _, bw = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
        cy = (y0+y1)/2 - ay0
        keep = np.zeros_like(bw)
        for k in range(1, n):
            x, y, w, h, a = (int(st[k, i]) for i in range(5))
            if a < s['cc_area_min'] or h > s['cc_h_max'] or w > s['cc_w_max']: continue
            if abs((y+h/2) - cy) > s['h']*SERRAGE: continue      # ← resserré
            keep[lab == k] = 255
        return keep, ax0, ay0
