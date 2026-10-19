"""Diagnostic v2 : variation de contour d'un pixel entre deux seuillages.

La règle v1 reste intacte. L'unique exception concerne une composante locale
dont tous les pixels natifs sont déjà attribués fermement à une autre ligne,
et dont chaque pixel supplémentaire est à un pixel de ces corps de lettres.
Le polygone étranger contient la composante locale entière ; le polygone de
la ligne courante n'en contient aucun pixel. Les petits signes n'obtiennent
jamais cette exception. Aucun seuil de couverture n'est abaissé.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

import page_line_ink as base


VERSION = 'whole-components-native-fringe-one-pixel-v2'
CRITERIA = dict(
    base_rule='v1 unchanged: native foreign owner polygon>=90%, competitors<=10%, nearby baseline',
    extra_local_pixels='only native-background pixels within one Chebyshev pixel of already proved foreign native components',
    foreign_polygon_local_coverage=1.0, own_polygon_local_coverage=0.0,
    native_body_minimum_height_fraction_of_foreign_line=.30,
    foreign_baseline_maximum_distance_fraction_of_native_body_height=.25,
    own_baseline_minimum_distance_in_native_body_heights=1.0,
    whole_local_components_only=True, punctuation_or_accent_exception=False,
    text_word_boundaries_and_ctc_unchanged=True, reference_inputs=False,
    calibration='fixed from native threshold disagreement in source-only L0956/L0960 crop before v2 replay or independent scoring')


class PolygonBaselineInkV2(base.PolygonBaselineInk):
    def filter_mask(self, lid, mask, ox, oy):
        filtered, audit = super().filter_mask(lid, mask, ox, oy)
        _, local, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
        h, w = mask.shape
        native = self.labels[oy:oy+h, ox:ox+w]
        current = self.index[lid]
        added = []
        for component, (x, y, cw, ch, area) in enumerate(stats[1:], 1):
            selected = local[y:y+ch, x:x+cw] == component
            if not np.any(filtered[y:y+ch, x:x+cw][selected]):
                continue
            native_crop = native[y:y+ch, x:x+cw]
            unknown = selected & (native_crop == 0)
            if not unknown.any():
                continue
            labels = np.unique(native_crop[selected])
            labels = labels[labels > 0]
            owners = np.unique(self.owners[labels])
            if len(owners) != 1 or owners[0] < 0 or owners[0] == current:
                continue
            foreign = int(owners[0])
            foreign_curve, own_curve = self.curves[foreign], self.curves[current]
            if np.ptp(own_curve[:, 0]) < 1:
                continue
            bodies = []
            for label in labels:
                a, b, bw, bh, _ = self.stats[label]
                bottom, center = b+bh-1, a+bw/2
                foreign_distance = abs(bottom-float(np.interp(center, foreign_curve[:, 0], foreign_curve[:, 1])))
                own_distance = abs(bottom-float(np.interp(center, own_curve[:, 0], own_curve[:, 1])))
                if (bh < .30*self.heights[foreign] or foreign_distance > .25*bh or own_distance < bh):
                    break
                bodies.append(dict(native_component=int(label), body_height=int(bh),
                                   foreign_baseline_distance=foreign_distance, own_baseline_distance=own_distance))
            if len(bodies) != len(labels):
                continue
            # Distance fixe d'un pixel de contour, pas une tolérance de perte
            # proportionnelle à l'aire ni une suppression de petits composants.
            core = np.isin(native_crop, labels).astype(np.uint8)
            halo = cv2.dilate(core, np.ones((3, 3), np.uint8), borderType=cv2.BORDER_CONSTANT)
            if not np.all(halo[unknown]):
                continue
            own_polygon, foreign_polygon = [], []
            for li in (current, foreign):
                poly = np.asarray(self.rows[li]['polygon']) - [ox+x, oy+y]
                area_mask = np.zeros((ch, cw), np.uint8)
                cv2.fillPoly(area_mask, [np.rint(poly).astype(np.int32)], 1)
                (own_polygon if li == current else foreign_polygon).extend(area_mask[selected].tolist())
            if any(own_polygon) or not all(foreign_polygon):
                continue
            filtered[y:y+ch, x:x+cw][selected] = 0
            entry = dict(local_component=component, pixels=int(area), foreign_line=self.rows[foreign]['id'],
                         native_components=[self.proofs[int(label)] for label in labels],
                         native_threshold_fringe=True, fringe_pixels=int(unknown.sum()), fringe_radius_pixels=1,
                         own_polygon_fraction=0., foreign_polygon_fraction=1., body_proofs=bodies)
            added.append(entry)
        audit['removed'].extend(added)
        audit['removed_pixels'] = sum(item['pixels'] for item in audit['removed'])
        audit['native_threshold_fringe_components'] = len(added)
        audit['native_threshold_fringe_pixels'] = sum(item['fringe_pixels'] for item in added)
        audit['criteria'] = deepcopy(CRITERIA)
        assert not np.any((filtered > 0) & (mask == 0))
        return filtered, audit


def replay(image, directory, output):
    """Worker séquentiel : réutiliser exactement le replay v1 sans l'éditer."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    criteria_path = output/'criteria-before-replay.json'
    if criteria_path.exists() and json.loads(criteria_path.read_text()) != CRITERIA:
        raise ValueError('Critères différents : utiliser un autre dossier expérimental')
    criteria_path.write_text(json.dumps(CRITERIA, ensure_ascii=False, indent=2))
    original_class, original_version = base.PolygonBaselineInk, base.VERSION
    try:
        base.PolygonBaselineInk, base.VERSION = PolygonBaselineInkV2, VERSION
        summary = base.replay(image, directory, output)
    finally:
        base.PolygonBaselineInk, base.VERSION = original_class, original_version
    audit = json.loads((output/'ownership-audit.json').read_text())
    summary['native_threshold_fringe_components'] = sum(line.get('native_threshold_fringe_components', 0) for line in audit['lines'])
    summary['native_threshold_fringe_pixels'] = sum(line.get('native_threshold_fringe_pixels', 0) for line in audit['lines'])
    summary['version'] = VERSION
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    provenance = json.loads((output/'provenance.json').read_text())
    provenance.update(variant_implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      frozen_criteria_sha256=hashlib.sha256(criteria_path.read_bytes()).hexdigest())
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('directory')
    parser.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(replay(args.image, args.directory, args.output), ensure_ascii=False, indent=2))
