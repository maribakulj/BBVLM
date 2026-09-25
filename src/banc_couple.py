"""Le banc qui tranche : le VLM mérite-t-il la plomberie géométrique ?

La question centrale de BBVLM n'est pas « quelle méthode fait les meilleures
boîtes » mais **« à quel moment le gain textuel du VLM justifie une seconde
brique géométrique ? »**

Si un recognizer classique lit à 2,1 % de CER et donne déjà un excellent ALTO,
bâtir toute cette chaîne pour gagner 0,2 point serait absurde. Si en revanche il
lit à 8-15 % sur du patrimonial difficile là où le VLM lit à 2-4 %, alors la
géométrie empruntée au CTC est le prix à payer pour garder le texte du VLM.

On mesure donc TEXTE et GÉOMÉTRIE sur les mêmes lignes, ce qui n'avait jamais
été fait ici : le banc de boîtes ignorait le texte, et les mesures de CER
ignoraient les boîtes.
"""
from __future__ import annotations
import os, sys, json, time, unicodedata, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxers'))
import numpy as np
import corpora


def norm(s: str) -> str:
    s = s.replace('ſ', 's').replace('’', "'").replace('⸗', '-')
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip()


def lev(a: str, b: str) -> int:
    if a == b: return 0
    p = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        c = [i]
        for j, cb in enumerate(b, 1):
            c.append(min(p[j]+1, c[j-1]+1, p[j-1]+(ca != cb)))
        p = c
    return p[-1]


def cer(ref: list[str], hyp: list[str]) -> float:
    A = "\n".join(norm(x) for x in ref); B = "\n".join(norm(x) for x in hyp)
    return 100*lev(A, B)/max(1, len(A))


def lire_kraken(pages, n_lignes=40):
    """Le recognizer classique, texte ET temps."""
    from kraken import rpred
    from kraken.lib import models
    from kraken.containers import Segmentation, BaselineLine
    from PIL import Image
    m = models.load_any(os.path.expanduser(
        '~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/'
        'catmus-print-fondue-large.mlmodel'))
    out = {}
    for p in pages:
        im = Image.fromarray(p.gray).convert('L')
        lines = p.lines[:n_lignes]
        bl = []
        for i, ln in enumerate(lines):
            x0, y0, x1, y1 = ln.line_box
            yb = int(y0 + (y1-y0)*0.78)
            bl.append(BaselineLine(id=f'l{i}', baseline=[(x0, yb), (x1, yb)],
                                   boundary=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
        seg = Segmentation(type='baselines', imagename='x', text_direction='horizontal-lr',
                           script_detection=False, lines=bl, regions={}, line_orders=[])
        t = time.time()
        hyp = [str(r.prediction or '') for r in rpred.rpred(m, im, seg)]
        out[p.name] = {'hyp': hyp, 'ref': [l.text for l in lines], 's': time.time()-t}
    return out


def lire_churro(pages, n_lignes=40):
    """Le VLM, par blocs — c'est son régime optimal (mesuré : 0 % de CER en bloc
    de 20 contre 13,5 % ligne à ligne)."""
    # le client VLM vit dans vlm-alto-fresh, pas ici
    sys.path.insert(0, os.path.expanduser('~/vlm-alto-fresh/src'))
    import vlm as V
    from PIL import Image
    be = V.OllamaVLM("hf.co/mradermacher/churro-3B-GGUF:Q4_K_M")
    out = {}
    for p in pages:
        pil = Image.open(p.image_path)
        lines = p.lines[:n_lignes]
        x0 = min(l.line_box[0] for l in lines); x1 = max(l.line_box[2] for l in lines)
        y0 = min(l.line_box[1] for l in lines); y1 = max(l.line_box[3] for l in lines)
        t = time.time()
        got, q = V.block_robuste(be, lambda d, n, j=0: pil.crop((x0, y0, x1, y1)),
                                 0, len(lines), essais=2)
        out[p.name] = {'hyp': got, 'ref': [l.text for l in lines], 's': time.time()-t}
    return out


if __name__ == '__main__':
    corp = sys.argv[1] if len(sys.argv) > 1 else 'Newseye'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    pages = [p for p in corpora.all_pages(max_lignes=n) if p.corpus == corp][:3]
    print(f"corpus {corp} — {len(pages)} pages, {n} lignes chacune\n")
    qui = sys.argv[3] if len(sys.argv) > 3 else 'kraken'
    r = lire_kraken(pages, n) if qui == 'kraken' else lire_churro(pages, n)
    tot_c = 0.0; tot_s = 0.0
    print(f"{'page':>22}{'CER':>9}{'lignes':>8}{'secondes':>10}")
    print('-'*50)
    for k, v in r.items():
        c = cer(v['ref'], v['hyp'])
        tot_c += c; tot_s += v['s']
        print(f"{k[:22]:>22}{c:>8.2f}%{len(v['hyp']):>8}{v['s']:>10.0f}")
    print('-'*50)
    print(f"{qui:>22}{tot_c/max(1,len(r)):>8.2f}%{'':>8}{tot_s:>10.0f}")
    json.dump({k: {'cer': cer(v['ref'], v['hyp']), 's': v['s']} for k, v in r.items()},
              open(f'state/couple_{corp}_{qui}.json', 'w'), indent=1)
