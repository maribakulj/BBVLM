import sys, json, importlib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
import corpora, judge

def get(name):
    mod, cls = name.split(':')
    m = importlib.import_module(f'boxers.{mod}')
    return getattr(m, cls)()

if __name__ == '__main__':
    pages = corpora.all_pages(max_lignes=int(os.environ.get('BBVLM_MAX_LIGNES','0')) or None)
    names = sys.argv[1:] or ['proportional:Proportional', 'inkgap:InkGapDP']
    # Périmètre de la mesure. Un pct05 sans le nombre de pages et de lignes sur
    # lesquelles il a été obtenu n'est pas une référence : la comparaison de B46
    # a buté une heure là-dessus, le corpus ayant gagné des pages Newseye entre
    # l'enregistrement du champion et sa vérification.
    from collections import Counter
    perimetre = {'pages': len(pages),
                 'par_corpus': {c: {'pages': sum(1 for p in pages if p.corpus == c),
                                    'lignes': sum(len(p.lines) for p in pages if p.corpus == c)}
                                for c in sorted({p.corpus for p in pages})}}
    print("périmètre :", json.dumps(perimetre['par_corpus'], ensure_ascii=False))
    res = {'_perimetre': perimetre}
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
