"""Pré-calcul W03 : positions CTC Calamari (gt4histocr, ensemble) des lignes d'une page.
usage : venvc/bin/python cala_page.py DOSSIER... ; écrit DOSSIER/calamari.json {clé boîte: {s, f, n}}"""
import sys, os, json, glob
import cv2

def main():
    from calamari_ocr.ocr.predict.predictor import MultiPredictor, PredictorParams
    params = PredictorParams(silent=True, progress_bar=False)
    params.pipeline.num_processes = 1
    M = sorted(glob.glob('/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/calamari_models/gt4histocr/*.ckpt.json'))
    p = MultiPredictor.from_paths(checkpoints=M, params=params)
    for d in sys.argv[1:]:
        f = os.path.join(d, 'kraken_crit2.json')
        if not os.path.exists(f): continue
        out = os.path.join(d, 'calamari.json')
        cache = json.load(open(out)) if os.path.exists(out) else {}
        g = cv2.imread(os.path.join(d, 'page.png'), 0)
        bx = [tuple(int(v) for v in l['bbox']) for l in json.load(open(f))['lignes']]
        bx = [b for b in bx if f'{b[0]},{b[1]},{b[2]},{b[3]}' not in cache]
        crops = [g[max(0, b[1]):b[3] + 1, max(0, b[0]):b[2] + 1] for b in bx]
        ok = [(b, c) for b, c in zip(bx, crops) if c.size and c.shape[1] > 4 and c.shape[0] > 4]
        if ok:
            for (b, c), r in zip(ok, p.predict_raw([c for _, c in ok])):
                v = r.outputs[1]
                cache[f'{b[0]},{b[1]},{b[2]},{b[3]}'] = {'s': v.sentence, 'g': [int(q.global_start) for q in v.positions]}
        json.dump(cache, open(out, 'w'), ensure_ascii=False)
        print(os.path.basename(d.rstrip('/')), len(cache), flush=True)

if __name__ == '__main__':
    main()
