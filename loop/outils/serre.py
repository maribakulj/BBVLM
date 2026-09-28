"""Écrit DOSSIER/kraken_serre.json : lignes kraken resserrées sur l'encre (G03)."""
import json, sys
import cv2
from g03 import resserre

for d in sys.argv[1:]:
    d = d.rstrip('/')
    k = json.load(open(f'{d}/kraken.json')); g = cv2.imread(f'{d}/page.png', cv2.IMREAD_GRAYSCALE)
    for l in k['lignes']:
        l['bbox_brut'] = l['bbox']; l['bbox'] = resserre(g, l['boundary'], l['bbox'])
    json.dump(k, open(f'{d}/kraken_serre.json', 'w'))
