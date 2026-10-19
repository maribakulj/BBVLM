"""Diagnostic : retirer uniquement des composantes entières prouvées étrangères.

Différence avec baseline_ink : une baseline proche ne suffit pas. Une autre
ligne doit aussi contenir presque toute la composante dans son polygone BLLA,
sans support concurrent significatif. Le polygone n'est jamais un masque de
découpe. Accents/ponctuation ambigus restent entiers dans le masque historique.
Les bornes entre mots, caractères CTC et textes sauvegardés ne changent pas.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

import ink


VERSION = 'whole-components-polygon-baseline-proof-v1'


class PolygonBaselineInk:
    """Propriétaires prudents de composantes natives, sans texte ni référence."""

    def __init__(self, gray, rows):
        if gray is None or gray.dtype != np.uint8 or gray.ndim != 2:
            raise ValueError('Image native uint8 requise')
        rows = list(rows)
        if not rows or len({r['id'] for r in rows}) != len(rows):
            raise ValueError('Lignes absentes ou identifiants dupliqués')
        if any('text' in r or 'words' in r or not r.get('source', '').startswith('kraken-blla/') for r in rows):
            raise ValueError('Seule la géométrie du détecteur automatique est autorisée')
        self.rows, self.index = rows, {r['id']: i for i, r in enumerate(rows)}
        height, width = gray.shape
        heights, curves, polygons = [], [], []
        for row in rows:
            box = row.get('detector_bbox', row['bbox'])
            if len(box) != 4 or not 0 <= box[0] < box[2] <= width or not 0 <= box[1] < box[3] <= height:
                raise ValueError('Boîte de détecteur hors page')
            curve, poly = np.asarray(row.get('baseline'), float), np.asarray(row.get('polygon'), float)
            if (curve.ndim != 2 or curve.shape[1] != 2 or len(curve) < 2 or not np.isfinite(curve).all()
                    or poly.ndim != 2 or poly.shape[1] != 2 or len(poly) < 3 or not np.isfinite(poly).all()):
                raise ValueError('Baseline et polygone automatiques requis')
            order = np.argsort(curve[:, 0], kind='stable')
            curves.append(curve[order])
            polygons.append(poly)
            heights.append(box[3] - box[1])
        self.heights, self.curves = np.asarray(heights), curves
        window = max(15, int(float(np.median(heights)) * .75) | 1)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV, window, 12)
        _, self.labels, self.stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        self.owners = np.full(len(self.stats), -1, np.int32)
        self.proofs = {}
        votes = {}
        # Le nombre de pixels à l'intérieur sert uniquement de preuve ; tous
        # les pixels du masque et toutes les composantes restent non découpés.
        for li, poly in enumerate(polygons):
            x0, y0 = np.maximum(0, np.floor(poly.min(axis=0)).astype(int))
            x1, y1 = np.minimum([width, height], np.ceil(poly.max(axis=0)).astype(int) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            area = np.zeros((y1-y0, x1-x0), np.uint8)
            cv2.fillPoly(area, [np.rint(poly-[x0, y0]).astype(np.int32)], 1)
            labels, counts = np.unique(self.labels[y0:y1, x0:x1][area > 0], return_counts=True)
            for label, count in zip(labels, counts):
                if label:
                    votes.setdefault(int(label), []).append((int(count), li))
        ambiguous = 0
        for label, candidates in votes.items():
            x, y, w, h, area = self.stats[label]
            candidates.sort(reverse=True)
            best, li = candidates[0]
            runner_up = candidates[1][0] if len(candidates) > 1 else 0
            if area < 3 or best / area < .90 or runner_up / area > .10:
                ambiguous += 1
                continue
            curve, lh = curves[li], heights[li]
            if np.ptp(curve[:, 0]) < 1 or not curve[0, 0] - .15*lh <= x+w/2 <= curve[-1, 0]+.15*lh:
                continue
            baseline = float(np.interp(x+w/2, curve[:, 0], curve[:, 1]))
            distance = abs((y+h-1)-baseline) / lh
            if distance > .35 or h > 1.2*lh or w > 4*lh:
                continue
            self.owners[label] = li
            self.proofs[label] = dict(native_component=label, owner=rows[li]['id'],
                bbox=[int(x), int(y), int(x+w), int(y+h)], pixels=int(area),
                polygon_fraction=best / int(area), competing_polygon_fraction=runner_up / int(area),
                baseline_distance_in_line_heights=distance)
        self.audit = dict(version=VERSION, components=len(self.stats)-1,
            owned_components=int(np.count_nonzero(self.owners >= 0)),
            polygon_ambiguous_components=ambiguous, binarization_window=window,
            polygon_minimum_fraction=.90, competing_polygon_maximum_fraction=.10,
            baseline_maximum_distance_in_line_heights=.35,
            source_only=True, promoted=False, criteria_met=False)

    def filter_mask(self, lid, mask, ox, oy):
        """Retirer une composante locale entière, couverte à 100 % par la preuve."""
        if lid not in self.index:
            raise ValueError('Identifiant de ligne inconnu')
        h, w = mask.shape
        if not 0 <= ox < ox+w <= self.labels.shape[1] or not 0 <= oy < oy+h <= self.labels.shape[0]:
            raise ValueError('Masque hors page')
        _, local, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
        native = self.labels[oy:oy+h, ox:ox+w]
        keep = np.ones(len(stats), bool)
        keep[0] = False
        removed, ambiguous = [], 0
        for component, (x, y, cw, ch, area) in enumerate(stats[1:], 1):
            labels = np.unique(native[y:y+ch, x:x+cw][local[y:y+ch, x:x+cw] == component])
            owners = np.unique(self.owners[labels])
            if len(owners) != 1 or owners[0] < 0:
                ambiguous += 1
                continue
            if owners[0] == self.index[lid]:
                continue
            keep[component] = False
            removed.append(dict(local_component=component, pixels=int(area),
                foreign_line=self.rows[owners[0]]['id'],
                native_components=[self.proofs[int(label)] for label in labels]))
        filtered = keep[local].astype(np.uint8)*255
        assert not np.any((filtered > 0) & (mask == 0))
        return filtered, dict(removed=removed, removed_pixels=sum(r['pixels'] for r in removed),
            retained_ambiguous_components=ambiguous, component_cut_pixels=0,
            local_components_removed_whole=True, native_proof_coverage_required=1.0)


def refine_words(gray, annotation, ownership):
    """Soustraire l'encre étrangère sans déplacer les séparateurs CTC historiques."""
    result = deepcopy(annotation)
    audit = dict(id=result['id'], changed=False)
    if result['status'] != 'placee':
        audit['skipped'] = result['status']
        return result, audit
    geometry = (result.get('alignment') or {}).get('word_geometry') or {}
    if geometry.get('version') != 'ctc-ink-whitespace-v4':
        audit['refused'] = 'historical_mask_mode_unsupported'
        return result, audit
    mask, ox, oy = ink.alignment_mask(gray, result['reading_bbox'], clean_upper_branches=True,
                                     clean_below_baseline=True, local_baseline=True)
    filtered, audit_filter = ownership.filter_mask(result['id'], mask, ox, oy)
    audit.update(audit_filter)
    if not audit['removed_pixels']:
        return result, audit
    words = []
    for word in result['words']:
        x0, y0, x1, y1 = [word[k] for k in ('x0', 'y0', 'x1', 'y1')]
        before = mask[y0-oy:y1-oy+1, x0-ox:x1-ox+1]
        after = filtered[y0-oy:y1-oy+1, x0-ox:x1-ox+1]
        if not before.size or not before.any() or not after.any():
            audit['refused'] = 'word_without_ink_after_foreign_component_removal'
            return deepcopy(annotation), audit
        original_y, original_x = np.nonzero(before)
        if (original_x.min(), original_y.min(), original_x.max(), original_y.max()) != (0, 0, x1-x0, y1-y0):
            audit['refused'] = 'historical_word_envelope_does_not_replay_exactly'
            return deepcopy(annotation), audit
        yy, xx = np.nonzero(after)
        updated = dict(word, x0=x0+int(xx.min()), y0=y0+int(yy.min()),
                       x1=x0+int(xx.max()), y1=y0+int(yy.max()))
        words.append(updated)
    audit['changed'] = words != result['words']
    if audit['changed']:
        result['historical_words'] = result['words']
        result['words'] = words
        result['line_ink_diagnostic'] = dict(version=VERSION, promoted=False,
            foreign_pixels_removed=audit['removed_pixels'], source_chars_unchanged=True,
            word_separator_positions_unchanged=True, independent_glyph_validation=False)
    return result, audit


def replay(image, directory, output):
    """Relire tous les checkpoints, jamais le recognizer ni une vérité terrain."""
    from page_geometry import _global_checks
    image, directory, output = Path(image), Path(directory), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    state = json.loads((directory/'geometry-cache/state.json').read_text())
    image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    if state['signature']['image_sha256'] != image_hash:
        raise ValueError('Image différente de celle des checkpoints')
    if state['signature']['implementation']['ink'] != hashlib.sha256(Path(ink.__file__).read_bytes()).hexdigest():
        raise ValueError('Le masque historique ne correspond pas au code courant')
    rows = json.loads((directory/'segmentation.json').read_text())
    geometry_rows = [{k: v for k, v in row.items() if k in {'id', 'bbox', 'detector_bbox', 'source', 'baseline', 'polygon'}} for row in rows]
    local, hashes = {}, {}
    for path in sorted((directory/'geometry-cache').glob('*.json')):
        if path.name == 'state.json':
            continue
        row = json.loads(path.read_text())['annotation']
        if row['id'] in local:
            raise ValueError('Checkpoints concurrents pour ' + row['id'])
        local[row['id']] = row
        hashes[row['id']] = hashlib.sha256(path.read_bytes()).hexdigest()
    if set(local) != {r['id'] for r in rows}:
        raise ValueError('Rejeu exhaustif requis, tous les IDs automatiques')
    raw = [local[r['id']] for r in rows]
    (output/'raw-cache.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2))
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    ownership = PolygonBaselineInk(gray, geometry_rows)
    candidate, audits = [], []
    for annotation in raw:
        updated, audit = refine_words(gray, annotation, ownership)
        candidate.append(updated)
        audits.append(audit)
    baseline = deepcopy(raw)
    summary = {}
    for name, annotations in [('baseline', baseline), ('candidate', candidate)]:
        threshold = _global_checks(annotations)
        assert [(a['id'], a['text'], a.get('chars')) for a in annotations] == [(a['id'], a['text'], a.get('chars')) for a in raw]
        summary[name] = dict(lines=len(annotations), statuses=dict(Counter(a['status'] for a in annotations)),
                             retained=sum(bool(a.get('training_eligible')) for a in annotations), threshold=threshold)
        (output/(name+'-annotations.json')).write_text(json.dumps(annotations, ensure_ascii=False, indent=2))
    summary.update(changed_lines=sum(a['changed'] for a in audits),
        removed_pixels=sum(a.get('removed_pixels', 0) for a in audits if not a.get('refused')),
        refused_replays=sum('refused' in a for a in audits), all_ids_texts_chars_unchanged=True,
        ctc_calls=0, reading_calls=0, source_only=True, promoted=False, criteria_met=False,
        scope='paired source-only subtraction of proved foreign whole components; historical word/character anchoring; no independent glyph validation')
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    (output/'ownership-audit.json').write_text(json.dumps(dict(native=ownership.audit, lines=audits), ensure_ascii=False, indent=2))
    (output/'provenance.json').write_text(json.dumps(dict(version=VERSION, image_sha256=image_hash,
        source_directory=str(directory.resolve()), cache_sha256=hashes,
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        segmentation_sha256=hashlib.sha256((directory/'segmentation.json').read_bytes()).hexdigest(),
        reference_inputs=False, ctc_calls=0, promoted=False), indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('directory')
    parser.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(replay(args.image, args.directory, args.output), ensure_ascii=False, indent=2))
