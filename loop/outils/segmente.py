"""Segmentation en lignes par kraken blla (modèle livré avec kraken 7.1.1).
Écrit DOSSIER/kraken.json : [{bbox, baseline, boundary}] dans l'ordre de kraken."""
import json, sys, time
from PIL import Image
from kraken import blla


def segmente(dossier):
    im = Image.open(f'{dossier}/page.png')
    t = time.time(); seg = blla.segment(im)
    out = []
    for l in seg.lines:
        xs = [p[0] for p in l.boundary]; ys = [p[1] for p in l.boundary]
        out.append({'bbox': [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
                    'baseline': [list(map(int, p)) for p in l.baseline],
                    'boundary': [list(map(int, p)) for p in l.boundary]})
    json.dump({'lignes': out, 'secondes': round(time.time()-t, 2)}, open(f'{dossier}/kraken.json', 'w'))
    return len(out), time.time()-t


if __name__ == '__main__':
    for d in sys.argv[1:]:
        print(d.split('/')[-2 if d.endswith('/') else -1], *segmente(d.rstrip('/')), flush=True)
