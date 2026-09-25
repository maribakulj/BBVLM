#!/usr/bin/env python
"""Chaîne de production de vérité terrain — image → ALTO relu.

Trois propriétés distinguent une sortie de VT d'une sortie d'OCR, et elles sont
ici des exigences de code, pas des intentions :

1. **Elle refuse.** Une ligne douteuse est signalée et retirée de l'ALTO, jamais
   comblée. Deux contrôles sans vérité terrain : le compte de lignes annoncé par
   la géométrie, et le coût d'ajustement du texte à l'encre observée.
2. **Elle est relue.** Un overlay accompagne chaque page, les lignes écartées y
   sont distinguées. Sans relecture humaine ce n'est pas une VT.
3. **Elle déclare sa provenance.** Quel modèle a lu, quel moteur a placé,
   combien de lignes reprises, combien écartées, sur quel critère.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'boxers'))
import numpy as np
from PIL import Image, ImageDraw
import cv2
import corpora, ink, alto, correct


def lignes_kraken(image: str, seuil_lignes: int | None = None):
    """Segmentation par lignes de base — robuste à l'inclinaison, contrairement
    à une détection par pics qui suppose des lignes horizontales régulières."""
    from kraken import blla
    from kraken.lib import vgsl
    im = Image.open(image).convert('L')
    seg = blla.segment(im)
    out = []
    for l in seg.lines:
        pts = np.asarray(l.boundary, float)
        x0, y0 = pts[:, 0].min(), pts[:, 1].min()
        x1, y1 = pts[:, 0].max(), pts[:, 1].max()
        out.append((int(x0), int(y0), int(x1), int(y1)))
    out.sort(key=lambda b: (b[1], b[0]))
    return out[:seuil_lignes] if seuil_lignes else out


class Ligne:
    """Ce qu'un boxer attend : du texte et une boîte de ligne, jamais de VT."""
    def __init__(self, texte, boite):
        self.text = texte
        self.words = texte.split()
        self.line_box = boite
        self.word_boxes = []


def produire(image, sortie, lire, boxer, max_lignes=None, par_bloc=20, verbose=True):
    out = Path(sortie); out.mkdir(parents=True, exist_ok=True)
    g = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    H, W = g.shape
    pil = Image.open(image)
    t0 = time.time()

    boites = lignes_kraken(image, max_lignes)
    if verbose: print(f"{W}×{H} | {len(boites)} lignes détectées", flush=True)

    # ── lecture par blocs, avec relance sur bloc suspect ──
    textes, journal = [], []
    for s in range(0, len(boites), par_bloc):
        n = min(par_bloc, len(boites)-s)
        x0 = min(b[0] for b in boites[s:s+n]); x1 = max(b[2] for b in boites[s:s+n])
        y0 = min(b[1] for b in boites[s:s+n]); y1 = max(b[3] for b in boites[s:s+n])
        t = time.time()
        got, q = lire(pil.crop((x0, y0, x1, y1)), n)
        journal.append({'bloc': f'{s+1}-{s+n}', 'attendu': n, 'obtenu': len(got),
                        'qualite': round(q, 3), 's': round(time.time()-t, 1)})
        textes += got[:n] + ['']*max(0, n-len(got))
        if verbose: print(f"  bloc {s+1}-{s+n} : {len(got)} lignes, qualité {q:.2f}", flush=True)

    # ── boîtes, et REFUS plutôt que comblement ──
    cal = None
    lignes, ecartes = [], []
    for i, (bx, txt) in enumerate(zip(boites, textes)):
        lid = f'L{i+1:04d}'
        if not txt.strip():
            ecartes.append({'ligne': lid, 'motif': 'aucun texte rendu'}); continue
        ln = Ligne(txt, bx)
        try:
            bs = boxer.boxes(g, ln)
        except Exception as e:
            ecartes.append({'ligne': lid, 'motif': f'placement impossible : {type(e).__name__}',
                            'texte': txt[:80]}); continue
        if len(bs) != len(ln.words):
            ecartes.append({'ligne': lid, 'motif': 'compte de mots incohérent',
                            'texte': txt[:80]}); continue
        # contrôle sans vérité terrain : le texte s'ajuste-t-il à l'encre ?
        cal = cal or {'demi_bande': max(6, (bx[3]-bx[1])//2)}
        c, _, _ = correct.cout_ligne(g, bx[0], bx[2], bx[1], bx[3],
                                     (bx[1]+bx[3])//2, txt, ink.line_scale(bx))
        cw = c/max(1, len(ln.words)) if c < 1e8 else 99.0
        mots = [{'text': w, 'x0': q[0], 'y0': q[1], 'x1': q[2], 'y1': q[3],
                 'synthetic': False} for w, q in zip(ln.words, bs)]
        lignes.append({'id': lid, 'text': txt, 'words': mots, 'cout': round(cw, 3),
                       'bbox': (min(m['x0'] for m in mots), min(m['y0'] for m in mots),
                                max(m['x1'] for m in mots), max(m['y1'] for m in mots))})

    # seuil de suspicion calibré sur CE document, pas sur une valeur figée
    couts = [l['cout'] for l in lignes]
    seuil = correct.seuil_auto(couts) if len(couts) >= 8 else 1.0
    gardees = []
    for l in lignes:
        if l['cout'] > seuil*2.0:
            ecartes.append({'ligne': l['id'], 'motif': f"texte inajustable à l'encre "
                            f"(coût {l['cout']} > {round(seuil*2,2)})", 'texte': l['text'][:80]})
        else:
            gardees.append(l)

    bloc = [{'id': 'B1', 'lines': gardees,
             'x0': min(l['bbox'][0] for l in gardees), 'y0': min(l['bbox'][1] for l in gardees),
             'x1': max(l['bbox'][2] for l in gardees), 'y1': max(l['bbox'][3] for l in gardees)}] if gardees else []
    xml = alto.build(W, H, Path(image).name, bloc,
                     software=getattr(lire, 'nom', 'VLM') + ' + ' + boxer.name,
                     description="Vérité terrain semi-automatique : lignes par kraken, texte par "
                     "VLM, géométrie des mots par projection d'encre. Les lignes douteuses sont "
                     "ÉCARTÉES et consignées, jamais comblées. Relecture humaine requise.")
    (out/'page.alto.xml').write_bytes(xml)

    im = pil.convert('RGB'); d = ImageDraw.Draw(im)
    for l in gardees:
        for m in l['words']:
            d.rectangle((m['x0'], m['y0'], m['x1'], m['y1']), outline=(0, 90, 255), width=2)
        d.rectangle(l['bbox'], outline=(0, 190, 0), width=2)
    for e in ecartes:
        i = int(e['ligne'][1:])-1
        if i < len(boites): d.rectangle(boites[i], outline=(230, 0, 0), width=4)
    im.save(out/'overlay.jpg', quality=82)

    prov = {'image': Path(image).name, 'taille': [W, H],
            'lecture': getattr(lire, 'nom', 'VLM'), 'geometrie': boxer.name,
            'lignes_detectees': len(boites), 'lignes_retenues': len(gardees),
            'lignes_ecartees': len(ecartes),
            'taux_relecture': round(100*len(ecartes)/max(1, len(boites)), 1),
            'seuil_suspicion': round(seuil*2, 3), 'blocs': journal,
            'ecartees': ecartes, 'secondes': round(time.time()-t0, 1)}
    (out/'provenance.json').write_text(json.dumps(prov, ensure_ascii=False, indent=1))
    (out/'transcription.txt').write_text(
        "\n".join(f"{l['id']}\t{l['text']}" for l in gardees), encoding='utf-8')
    if verbose:
        print(f"\nALTO   → {out/'page.alto.xml'}")
        print(f"overlay→ {out/'overlay.jpg'}")
        print(f"{len(gardees)} lignes retenues · {len(ecartes)} écartées "
              f"({prov['taux_relecture']} % à relire) · {prov['secondes']} s")
    return prov


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('sortie')
    ap.add_argument('--max-lignes', type=int, default=None)
    ap.add_argument('--par-bloc', type=int, default=20)
    a = ap.parse_args()
    sys.path.insert(0, os.path.expanduser('~/vlm-alto-fresh/src'))
    import vlm as V
    from connexe import Connexe
    be = V.OllamaVLM("hf.co/mradermacher/churro-3B-GGUF:Q4_K_M")
    def lire(crop, n):
        return V.block_robuste(be, lambda d, m, j=0: crop, 0, n, essais=3)
    lire.nom = 'churro-3B'
    produire(a.image, a.sortie, lire, Connexe(),
             max_lignes=a.max_lignes, par_bloc=a.par_bloc)
