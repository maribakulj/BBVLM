"""S06 — lignes que kraken n'a pas trouvées : bandes d'encre hors lignes kraken (L11).

Profil de projection horizontal de l'encre (fond divisé, Otsu) après
effacement des zones déjà couvertes par les lignes kraken et des petites
composantes (bruit, ornements fins) ; une bande = suite de rangées encrées,
blancs courts fusionnés ; étendue horizontale = colonnes encrées de la bande.
Utilisé seulement quand des lignes lues restent sans ligne kraken : les
bandes deviennent des candidates pour l'ancrage Tesseract (S05).
"""
import numpy as np
import cv2


def bandes(gray, boites, marge=0.15):
    H, W = gray.shape
    hs = [b[3]-b[1] for b in boites] or [40]
    h = float(np.median(hs))
    g = gray.astype(np.float32)
    norm = cv2.divide(g, cv2.GaussianBlur(g, (0, 0), max(2.0, h)), scale=255).astype(np.uint8)
    # seuil d'encre calé sur l'encre des lignes kraken (évite verso transparent, fond)
    zone = np.zeros_like(norm, bool)
    for x0, y0, x1, y1 in boites: zone[y0:y1, x0:x1] = True
    t, _ = cv2.threshold(norm[zone].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) if zone.any() else (128, None)
    bw = np.where(norm < t, 255, 0).astype(np.uint8)
    # zone de texte : étendue horizontale des lignes kraken ± h
    if boites:
        xa = max(0, int(min(b[0] for b in boites) - h)); xb = min(W, int(max(b[2] for b in boites) + h))
        bw[:, :xa] = 0; bw[:, xb:] = 0
    for x0, y0, x1, y1 in boites:                   # zones déjà couvertes par kraken
        d = int(marge*(y1-y0))
        bw[max(0, y0-d):y1+d, max(0, x0-d):x1+d] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(bw, 8)
    garde = np.zeros(n, bool)
    for k in range(1, n):
        w, hh, a = st[k, 2], st[k, 3], st[k, 4]
        x, y = st[k, 0], st[k, 1]
        bord = x <= 2 or y <= 2 or x + w >= W-3 or y + hh >= H-3
        garde[k] = not bord and a >= (0.08*h)**2 and hh >= 0.3*h and w < 0.9*W and hh < 0.5*H
    bw = np.where(garde[lab], 255, 0).astype(np.uint8)
    rows = (bw > 0).sum(1)
    on = rows > max(3, 0.002*W)
    out, y = [], 0
    while y < H:
        if not on[y]: y += 1; continue
        y0 = y
        while y < H and (on[y] or on[min(H-1, y+int(0.2*h))]): y += 1
        y1 = y
        if y1 - y0 >= 0.5*h:
            cols = np.where((bw[y0:y1] > 0).any(0))[0]
            if len(cols) and cols[-1]-cols[0] >= h:
                out.append([int(cols[0]), int(y0), int(cols[-1]), int(y1)])
    return out
