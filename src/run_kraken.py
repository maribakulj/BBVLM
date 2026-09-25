"""Banc pour les boxers qui vivent dans le venv kraken."""
import sys, os, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
import corpora, judge
mod, cls = sys.argv[1].split(':')
b = getattr(importlib.import_module(mod), cls)()
r = judge.score(b, corpora.all_pages())
s = r.summary()
print(f"\n═══ {b.name} ═══")
print(f"  lignes {s['lignes']} (échec {s['lignes_en_echec']}) | frontières {s['frontieres']}")
print(f"  err médiane {s['err_med']}c | p90 {s['err_p90']}c | p99 {s['err_p99']}c | max {s['err_max']}c")
print(f"  ≤0,5 car : {s['pct_sous_0.5c']} % | IoU médian {s['iou_med']} | IoU p10 {s['iou_p10']}")
for c, cs in r.per_corpus.items():
    print(f"    {c:>14}: err_p90 {cs['err_p90']}c max {cs['err_max']}c ≤0,5c {cs['pct_sous_0.5c']}% IoU {cs['iou_med']} échec {cs['lignes_en_echec']}")
