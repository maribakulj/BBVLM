import sys, json, importlib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
import corpora, judge

def get(name):
    mod, cls = name.split(':')
    m = importlib.import_module(f'boxers.{mod}')
    return getattr(m, cls)()

if __name__ == '__main__':
    pages = corpora.all_pages()
    names = sys.argv[1:] or ['proportional:Proportional', 'inkgap:InkGapDP']
    res = {}
    for n in names:
        b = get(n)
        r = judge.score(b, pages)
        res[b.name] = {'global': r.summary(), 'par_corpus': r.per_corpus}
        s = r.summary()
        print(f"\n═══ {b.name} ═══")
        print(f"  lignes {s['lignes']} (échec {s['lignes_en_echec']}) | frontières {s['frontieres']}")
        print(f"  err médiane {s['err_med']}c | p90 {s['err_p90']}c | p99 {s['err_p99']}c | max {s['err_max']}c")
        print(f"  ≤0,5 car : {s['pct_sous_0.5c']} % | IoU médian {s['iou_med']} | IoU p10 {s['iou_p10']}")
        for c, cs in r.per_corpus.items():
            print(f"    {c:>14}: err_p90 {cs['err_p90']}c max {cs['err_max']}c ≤0,5c {cs['pct_sous_0.5c']}% IoU {cs['iou_med']}")
    json.dump(res, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state', 'last_run.json'), 'w'), indent=1, ensure_ascii=False)
