"""CRITERE.md sur la chaîne finale : texte P3, lignes kraken resserrées, routeur G02."""
import sys
from e01 import e01
from g02 import Route
b = Route()
for arg in sys.argv[1:]:
    d, lec = arg.split('=')
    s, r = e01(d, lec, b, 'kraken_serre.json')
    ok = r['pct_sous_0.5c'] and r['pct_sous_0.5c'] >= 95 and r['err_max'] is not None and r['err_max'] <= 3 and r['iou_med'] >= .8 and r['lignes_en_echec'] == 0
    print(f"{d.rstrip('/').split('/')[-1][:10]:10s} lignes {r['lignes']:3d} échec {r['lignes_en_echec']:2d} | ≤0,5c {r['pct_sous_0.5c']:6} | pire {r['err_max']:5} | IoU méd {r['iou_med']} | {'CRITERE ✓' if ok else ''}", flush=True)
