"""B10 — caractériser les lignes dont l'erreur dépasse 3 caractères."""
import sys, os, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
import numpy as np, corpora, judge

def main(spec='band:BandGaps'):
    mod, cls = spec.split(':')
    b = getattr(importlib.import_module(f'boxers.{mod}'), cls)()
    pages = corpora.all_pages()
    mauvaises = []
    for p in pages:
        g = p.gray
        if g is None: continue
        for li, ln in enumerate(p.lines):
            try: pred = b.boxes(g, ln)
            except Exception: continue
            if len(pred) != len(ln.words): continue
            gt = ln.word_boxes
            span = max(x[2] for x in gt) - min(x[0] for x in gt)
            cw = max(1.0, span/max(1, sum(len(w) for w in ln.words)))
            for k in range(len(gt)-1):
                lo, hi = gt[k][2], gt[k+1][0]
                if hi < lo: lo, hi = hi, lo
                x = (pred[k][2]+pred[k+1][0])/2
                d = (lo-x if x < lo else (x-hi if x > hi else 0))/cw
                if d > 3.0:
                    mauvaises.append({'corpus': p.corpus, 'page': p.name, 'ligne': li,
                        'k': k, 'err': round(d, 2), 'gauche': ln.words[k], 'droite': ln.words[k+1],
                        'lg': len(ln.words[k]), 'ld': len(ln.words[k+1]),
                        'nmots': len(ln.words), 'blanc_vt': hi-lo,
                        'h_ligne': ln.line_box[3]-ln.line_box[1],
                        'texte': ln.text[:70]})
    print(f"frontières à plus de 3 caractères : {len(mauvaises)}")
    if mauvaises:
        import collections
        print("\npar corpus :", dict(collections.Counter(m['corpus'] for m in mauvaises)))
        lg = [m['lg'] for m in mauvaises]; ld = [m['ld'] for m in mauvaises]
        print(f"longueur du mot GAUCHE : médiane {np.median(lg):.0f} (corpus ~5-6)")
        print(f"longueur du mot DROITE : médiane {np.median(ld):.0f}")
        print(f"blanc VT médian : {np.median([m['blanc_vt'] for m in mauvaises]):.0f} px")
        print(f"mots par ligne  : médiane {np.median([m['nmots'] for m in mauvaises]):.0f}")
        court = sum(1 for m in mauvaises if m['lg'] <= 2 or m['ld'] <= 2)
        print(f"impliquant un mot de ≤2 caractères : {court}/{len(mauvaises)} ({100*court/len(mauvaises):.0f} %)")
        print("\n10 pires :")
        for m in sorted(mauvaises, key=lambda x: -x['err'])[:10]:
            print(f"  {m['err']:>6}c  {m['corpus']:>13} «{m['gauche']}» | «{m['droite']}»  blanc {m['blanc_vt']}px")
    json.dump(mauvaises, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'state', 'pires.json'), 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'band:BandGaps')
