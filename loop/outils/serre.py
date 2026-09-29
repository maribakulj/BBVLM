"""Écrit DOSSIER/kraken_serre.json : lignes kraken resserrées sur l'encre (G03)."""
import json, sys
import cv2
from g03 import resserre

for d in sys.argv[1:]:
    d = d.rstrip('/')
    k = json.load(open(f'{d}/kraken.json')); g = cv2.imread(f'{d}/page.png', cv2.IMREAD_GRAYSCALE)
    for i, l in enumerate(k['lignes']):
        b = l['bbox']; h = b[3] - b[1]
        # polygones voisins (recouvrement vertical à ± une hauteur) : propriétaires possibles de l'encre (G04b)
        autres = [m['boundary'] for j, m in enumerate(k['lignes']) if j != i and m['bbox'][1] < b[3] + h and m['bbox'][3] > b[1] - h
                  and m['bbox'][0] < b[2] and m['bbox'][2] > b[0]]
        l['bbox_brut'] = l['bbox']; l['bbox'] = resserre(g, l['boundary'], l['bbox'], baseline=l.get('baseline'), autres=autres)
    import os
    json.dump(k, open(f"{d}/{os.environ.get('BBVLM_LIGNES', 'kraken_serre.json')}", 'w'))
