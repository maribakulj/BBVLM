"""Vues de détail : chaque bande coupée en deux moitiés recouvrantes, agrandies.

Idée empruntée au zoom multi-résolution des VLM (Dragonfly 2024, ZoomEye 2025) :
agrandir au-delà de la résolution native pour les signes fins (suscrits).
usage : python vues_zoom.py DOSSIER [facteur=1.6] — lit DOSSIER/page.png, écrit
DOSSIER/vues/zoom_{k}_{g|d}.png pour les bandes de prep_sbb (600 px, 120 de recouvrement).
"""
import sys
import cv2


def main(dossier, facteur=1.6, bande=600, recouvrement=120, marge=0.12):
    img = cv2.imread(f'{dossier}/page.png'); H, W = img.shape[:2]
    y, k = 0, 1
    m = int(W*marge/2)
    while True:
        y1 = min(H, y+bande)
        for cote, (a, b) in (('g', (0, W//2+m)), ('d', (W//2-m, W))):
            t = cv2.resize(img[y:y1, a:b], None, fx=facteur, fy=facteur, interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(f'{dossier}/vues/zoom_{k}_{cote}.png', t)
        k += 1
        if y1 == H: break
        y = y1-recouvrement
    print(k-1, 'bandes zoomées')


if __name__ == '__main__':
    main(sys.argv[1], *(float(x) for x in sys.argv[2:3]))
