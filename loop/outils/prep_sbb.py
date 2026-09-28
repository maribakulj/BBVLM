"""Télécharge une page OCR-D-GT-VD-SBB épinglée et prépare les vues du lecteur.

usage : python prep_sbb.py OUVRAGE PAGE DOSSIER
Écrit DOSSIER/ref.json (lignes de référence, jamais montrées au lecteur hors
de ce dossier-là : le lecteur ne reçoit que DOSSIER/vues/) et DOSSIER/vues/*.png.
"""
import json, os, sys, urllib.request
import cv2, numpy as np
from lxml import etree

REV = '481f7235acfc1f78e88b3c2f22f551595c3f2032'
BASE = f'https://raw.githubusercontent.com/OCR-D/OCR-D-GT-VD-SBB/{REV}/data/'


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def main(ouvrage, page, out, hauteur=1350, bande=600, recouvrement=120):
    os.makedirs(f'{out}/vues', exist_ok=True)
    xml = get(f'{BASE}{ouvrage}/OCR-D-GT-PAGE/OCR-D-GT-PAGE_{page}.xml')
    img = cv2.imdecode(np.frombuffer(get(f'{BASE}{ouvrage}/OCR-D-IMG/OCR-D-IMG_{page}.tif'), np.uint8), cv2.IMREAD_COLOR)
    r = etree.fromstring(xml); N = {'p': r.tag.split('}')[0][1:]}
    lignes = [(tl.find('p:TextEquiv/p:Unicode', N).text or '') for tl in r.findall('.//p:TextLine', N)]
    json.dump(lignes, open(f'{out}/ref.json', 'w'), ensure_ascii=False, indent=0)
    H, W = img.shape[:2]
    cv2.imwrite(f'{out}/vues/vue_0_page.png', cv2.resize(img, (int(W*hauteur/H), hauteur), interpolation=cv2.INTER_AREA))
    y, k = 0, 1
    while True:
        y1 = min(H, y+bande); cv2.imwrite(f'{out}/vues/vue_{k}_bande.png', img[y:y1]); k += 1
        if y1 == H: break
        y = y1-recouvrement
    print(f'{W}x{H}, {len(lignes)} lignes, {k-1} bandes')


if __name__ == '__main__':
    main(*sys.argv[1:4])
