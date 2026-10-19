#!/usr/bin/env python
"""Probabilités CTC (log-softmax, trames × classes) de chaque ligne détectée.

À lancer avec le Python de kraken, via ~/outils-seg/lourd.sh. Sortie : un .npz
(une entrée par ligne, float16) + le codec du modèle (caractère → étiquettes),
pour l'alignement par bloc (src/block_ctc.py) sans relancer le réseau.
Image seule : aucune donnée de référence.
"""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'src' / 'boxers'))
from forcectc import _ligne_tenseur, PAD

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('image')
parser.add_argument('annotations', help='annotations.json (id + bbox des lignes)')
parser.add_argument('output', help='dossier de sortie')
parser.add_argument('--model', required=True)
args = parser.parse_args()

import torch
from kraken.lib.models import load_any
model = load_any(args.model)
gray = np.asarray(Image.open(args.image).convert('L'))
lines = json.loads(Path(args.annotations).read_text())
out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
arrays, meta = {}, {}
for line in lines:
    x0, y0, x1, y1 = (int(round(v)) for v in line['bbox'])
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(gray.shape[1], x1), min(gray.shape[0], y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        continue
    t = _ligne_tenseur(gray, SimpleNamespace(line_box=(x0, y0, x1, y1)), model)
    with torch.no_grad():
        logits, _ = model.nn.nn(t, None)
    logp = torch.log_softmax(logits[0, :, 0, :], dim=0).T.float().numpy()
    arrays[line['id']] = logp.astype(np.float16)
    meta[line['id']] = dict(box=[x0, y0, x1, y1], input_width=int(t.shape[-1]), frames=int(logp.shape[0]))
np.savez_compressed(out / 'posteriors.npz', **arrays)
codec = {k: [int(c) for c in v] for k, v in model.codec.c2l.items()}
(out / 'posteriors.json').write_text(json.dumps(dict(model=args.model, pad=PAD, codec=codec, lines=meta),
                                                ensure_ascii=False))
print(len(arrays), 'lignes')
