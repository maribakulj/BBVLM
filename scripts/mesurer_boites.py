#!/usr/bin/env python
"""Justesse des boîtes de mots de notre ALTO contre les boîtes Word de la VT (évaluation seule).

Appariement un-à-un par recouvrement (IoU, affectation optimale sur les paires
qui se touchent). Rapporte : part des mots de la VT retrouvés à IoU >= 0,5 et
>= 0,7, IoU médian, et pour les paires de même texte (normalisation cer_vt)
l'écart signé de chaque bord en pixels (nous − VT) : médiane, p90 de la valeur
absolue. Les boîtes de la VT (Transkribus) ont leurs propres marges : un écart
constant peut venir d'une convention de tracé plutôt que d'une erreur.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evaluation import cer_vt, _points
from page_anchors import sha256


def reference_words(path):
    root = etree.parse(str(path))
    out = []
    for word in root.findall('.//{*}Word'):
        coords = word.find('{*}Coords')
        text = word.find('.//{*}Unicode')
        if coords is None:
            continue
        out.append(dict(bbox=list(_points(word)), text=(text.text or '') if text is not None else ''))
    return out


def reference_lines(path):
    out = []
    for line in etree.parse(str(path)).getroot().iter('{*}TextLine'):
        if line.find('{*}Coords') is None:
            continue
        text = line.find('{*}TextEquiv/{*}Unicode')
        out.append(dict(bbox=list(_points(line)), text=(text.text or '') if text is not None else ''))
    return out


def alto_lines(path):
    out = []
    for line in etree.parse(str(path)).getroot().iter('{*}TextLine'):
        x, y, w, h = (float(line.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
        text = ' '.join(s.get('CONTENT', '') for s in line.iter('{*}String'))
        out.append(dict(bbox=[x, y, x+w, y+h], text=text))
    return out


def alto_words(path):
    root = etree.parse(str(path))
    out = []
    for s in root.findall('.//{*}String'):
        x, y, w, h = (float(s.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
        out.append(dict(bbox=[x, y, x+w, y+h], text=s.get('CONTENT', '')))
    return out


def iou_matrix(a, b):
    a, b = np.asarray(a, float)[:, None, :], np.asarray(b, float)[None, :, :]
    ix = np.clip(np.minimum(a[..., 2], b[..., 2]) - np.maximum(a[..., 0], b[..., 0]), 0, None)
    iy = np.clip(np.minimum(a[..., 3], b[..., 3]) - np.maximum(a[..., 1], b[..., 1]), 0, None)
    inter = ix*iy
    area = lambda z: (z[..., 2]-z[..., 0])*(z[..., 3]-z[..., 1])
    return inter / np.maximum(area(a) + area(b) - inter, 1e-9)


def evaluate(manifest, alto, page_id):
    page = [p for p in json.loads(Path(manifest).read_text())['pages'] if p['id'] == page_id][0]
    if sha256(page['reference']) != page['reference_sha256']:
        raise ValueError('Référence modifiée')
    ref, ours, level = reference_words(page['reference']), alto_words(alto), 'mot'
    if not ref:
        # VT sans boîtes de mots (seulement des lignes) : mesure au niveau ligne
        ref, ours, level = reference_lines(page['reference']), alto_lines(alto), 'ligne'
    from scipy.optimize import linear_sum_assignment
    matrix = iou_matrix([r['bbox'] for r in ref], [o['bbox'] for o in ours])
    rows, cols = linear_sum_assignment(-matrix)
    pairs = [(i, j, matrix[i, j]) for i, j in zip(rows, cols) if matrix[i, j] > 0]
    ious = np.array([p[2] for p in pairs]) if pairs else np.array([])
    same = [(ref[i], ours[j]) for i, j, v in pairs if v > .3 and cer_vt(ref[i]['text']) == cer_vt(ours[j]['text'])
            and cer_vt(ref[i]['text'])]
    edges = {}
    for k, name in enumerate(('gauche', 'haut', 'droite', 'bas')):
        d = np.array([o['bbox'][k] - r['bbox'][k] for r, o in same]) if same else np.array([0.])
        edges[name] = dict(mediane_signee=float(np.median(d)), mediane_abs=float(np.median(np.abs(d))),
                           p90_abs=float(np.percentile(np.abs(d), 90)))
    heights = np.array([r['bbox'][3]-r['bbox'][1] for r, _ in same]) if same else np.array([1.])
    return dict(page=page_id, alto=str(alto), niveau=level, mots_vt=len(ref), mots_alto=len(ours),
                vt_retrouves_iou50=float((ious >= .5).sum()/len(ref)), vt_retrouves_iou70=float((ious >= .7).sum()/len(ref)),
                iou_median=float(np.median(ious)) if len(ious) else None,
                paires_meme_texte=len(same), hauteur_mot_vt_mediane=float(np.median(heights)), bords_px=edges)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest'); parser.add_argument('alto'); parser.add_argument('page_id')
    parser.add_argument('--output')
    args = parser.parse_args()
    report = evaluate(args.manifest, args.alto, args.page_id)
    if args.output:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps(report, ensure_ascii=False, indent=1))
