"""E1 — prédictions G1a (têtes de localisation, sans entraînement) depuis les npz. usage : python e1_g1a.py A1_DIR FEAT_DIR PARTITION SORTIE.json"""
import json, sys, os
import numpy as np
a1, fd, part, out = sys.argv[1:5]; P = {}
for l in open(a1 + '/manifest.jsonl', encoding='utf-8'):
    m = json.loads(l)
    if m['partition'] == part and os.path.exists(f"{fd}/{m['id']}.npz"): P[m['id']] = np.load(f"{fd}/{m['id']}.npz")['g1a'].tolist()
json.dump(P, open(out, 'w')); print(len(P), 'blocs')
