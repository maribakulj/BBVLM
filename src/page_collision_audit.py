"""Classifier les collisions résiduelles sur pixels source, sans CTC ni référence.

Un chevauchement d'enveloppes n'est pas nommé partage d'encre s'il ne partage
aucun pixel des masques. Inversement, des masques disjoints ne rendent pas les
deux mots corrects : leur encre étrangère éventuelle est comptée séparément.
Ce diagnostic n'altère ni les seuils, ni les annotations, ni leur éligibilité.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

import ink
from page_line_ink_v2 import PolygonBaselineInkV2


VERSION = 'residual-collision-native-evidence-audit-v1'


def collision_pairs(annotations):
    active, pairs = [], []
    for lid, index, word in sorted(((a['id'], i, w) for a in annotations
                                   for i, w in enumerate(a.get('words') or [])), key=lambda row: row[2]['y0']):
        active = [(other, wi, box) for other, wi, box in active if box['y1'] >= word['y0']]
        for other, wi, box in active:
            if other == lid:
                continue
            x0, x1 = max(box['x0'], word['x0']), min(box['x1'], word['x1'])+1
            if x0 < x1:
                pairs.append(dict(line_a=other, word_a=wi, line_b=lid, word_b=index,
                                  intersection=[x0, max(box['y0'], word['y0']), x1, min(box['y1'], word['y1'])+1]))
        active.append((lid, index, word))
    return pairs


def support_kind(a, b):
    common = int(np.count_nonzero(a & b))
    counts = [int(np.count_nonzero(a)), int(np.count_nonzero(b))]
    return ('shared_mask_pixels' if common else 'disjoint_mask_pixels' if all(counts)
            else 'one_sided_mask_pixels' if any(counts) else 'no_mask_pixels'), counts, common


class NativeEvidence:
    def __init__(self, ownership):
        self.native = ownership
        self.votes, self.catalog = {}, {}
        height, width = ownership.labels.shape
        for li, row in enumerate(ownership.rows):
            poly = np.asarray(row['polygon'])
            x0, y0 = np.maximum(0, np.floor(poly.min(axis=0)).astype(int))
            x1, y1 = np.minimum([width, height], np.ceil(poly.max(axis=0)).astype(int)+1)
            if x1 <= x0 or y1 <= y0:
                continue
            area = np.zeros((y1-y0, x1-x0), np.uint8)
            cv2.fillPoly(area, [np.rint(poly-[x0, y0]).astype(np.int32)], 1)
            labels, counts = np.unique(ownership.labels[y0:y1, x0:x1][area > 0], return_counts=True)
            for label, count in zip(labels, counts):
                if label:
                    self.votes.setdefault(int(label), []).append((int(count), li))

    def component(self, label):
        label = int(label)
        if label in self.catalog:
            return self.catalog[label]
        native = self.native
        x, y, w, h, area = map(int, native.stats[label])
        votes = sorted(self.votes.get(label, []), reverse=True)
        candidates = []
        for count, li in votes:
            curve = native.curves[li]
            baseline = float(np.interp(x+w/2, curve[:, 0], curve[:, 1]))
            candidates.append(dict(id=native.rows[li]['id'], polygon_fraction=count/area,
                baseline_distance_line_heights=abs(y+h-1-baseline)/float(native.heights[li]),
                baseline_distance_component_heights=abs(y+h-1-baseline)/h,
                component_height_fraction_of_line=h/float(native.heights[li])))
        owner = int(native.owners[label])
        top_overlap = None
        if owner >= 0:
            kind = 'proved_native_line_ownership'
        elif area < 3:
            kind = 'native_component_too_small'
        elif not votes:
            kind = 'no_automatic_polygon_support'
        elif len(votes) > 1 and votes[1][0]/area > .10:
            masks = []
            for _, li in votes[:2]:
                poly = np.asarray(native.rows[li]['polygon'])-[x, y]
                region = np.zeros((h, w), np.uint8)
                cv2.fillPoly(region, [np.rint(poly).astype(np.int32)], 1)
                masks.append(region > 0)
            top_overlap = int(np.count_nonzero((native.labels[y:y+h, x:x+w] == label) & masks[0] & masks[1]))
            kind = 'overlapping_competing_polygons' if top_overlap else 'component_spans_adjacent_polygons'
        elif votes[0][0]/area < .90:
            kind = 'polygon_undercoverage'
        else:
            li = votes[0][1]
            curve, lh = native.curves[li], native.heights[li]
            if np.ptp(curve[:, 0]) < 1:
                kind = 'unsupported_vertical_baseline'
            elif not curve[0, 0]-.15*lh <= x+w/2 <= curve[-1, 0]+.15*lh:
                kind = 'outside_horizontal_baseline_support'
            elif h > 1.2*lh or w > 4*lh:
                kind = 'native_component_size_incompatible'
            elif candidates[0]['baseline_distance_line_heights'] > .35:
                kind = 'polygon_owner_baseline_too_far'
            else:
                kind = 'ownership_unexplained'
        value = dict(component=label, bbox=[x, y, x+w, y+h], pixels=area, kind=kind,
                     owner=native.rows[owner]['id'] if owner >= 0 else None,
                     candidates=candidates, top_two_polygon_shared_ink_pixels=top_overlap,
                     best_polygon_undercoverage=bool(votes and votes[0][0]/area < .90))
        self.catalog[label] = value
        return value


def audit(image, source, variant, output):
    image, source, variant, output = map(Path, (image, source, variant, output))
    annotations = json.loads((variant/'candidate-annotations.json').read_text())
    rows = json.loads((source/'segmentation.json').read_text())
    rows = [{k: v for k, v in row.items() if k in {'id', 'bbox', 'detector_bbox', 'source', 'baseline', 'polygon'}} for row in rows]
    image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    if json.loads((variant/'provenance.json').read_text())['image_sha256'] != image_hash:
        raise ValueError('Image différente du diagnostic')
    signature = json.loads((source/'geometry-cache/state.json').read_text())['signature']
    if (signature['image_sha256'] != image_hash
            or signature['implementation']['ink'] != hashlib.sha256(Path(ink.__file__).read_bytes()).hexdigest()):
        raise ValueError('Image ou masque différents des checkpoints historiques')
    gray = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
    native = PolygonBaselineInkV2(gray, rows)
    evidence = NativeEvidence(native)
    by_id = {a['id']: a for a in annotations}
    pairs = collision_pairs(annotations)
    implicated = {p[k] for p in pairs for k in ('line_a', 'line_b')}
    masks, local_components = {}, {}
    for lid in implicated:
        a = by_id[lid]
        if (a.get('alignment') or {}).get('word_geometry', {}).get('version') != 'ctc-ink-whitespace-v4':
            raise ValueError('Mode du masque historique non pris en charge')
        mask, ox, oy = ink.alignment_mask(gray, a['reading_bbox'], True, True, True)
        filtered, _ = native.filter_mask(lid, mask, ox, oy)
        _, labels, stats, _ = cv2.connectedComponentsWithStats((filtered > 0).astype(np.uint8), 8)
        masks[lid] = dict(mask=filtered > 0, ox=ox, oy=oy, labels=labels, stats=stats)

    def cut(lid, box, field='mask'):
        m = masks[lid]
        x0, y0, x1, y1 = box
        return m[field][y0-m['oy']:y1-m['oy'], x0-m['ox']:x1-m['ox']]

    def local_component(lid, component):
        key = lid+':'+str(component)
        if key in local_components:
            return key
        m = masks[lid]
        x, y, w, h, area = map(int, m['stats'][component])
        support = m['labels'][y:y+h, x:x+w] == component
        labels, counts = np.unique(native.labels[m['oy']+y:m['oy']+y+h, m['ox']+x:m['ox']+x+w][support], return_counts=True)
        owners, unknown, unresolved, cause_pixels = set(), 0, [], Counter()
        for label, count in zip(labels, counts):
            if label == 0:
                unknown += int(count)
                cause_pixels['native_threshold_disagreement'] += int(count)
                continue
            item = evidence.component(label)
            if item['owner'] is not None:
                owners.add(item['owner'])
                cause_pixels['proved_own_ink' if item['owner'] == lid else 'proved_foreign_ink'] += int(count)
            else:
                unresolved.append(int(label))
                cause_pixels[item['kind']] += int(count)
        reasons = []
        if len(owners) > 1:
            reasons.append('local_component_mixes_native_line_owners')
        if unknown:
            reasons.append('local_component_contains_unproved_threshold_pixels')
        if unresolved:
            reasons.append('local_component_contains_unassigned_native_components')
        local_components[key] = dict(line_id=lid, component=int(component), pixels=area,
            bbox=[m['ox']+x, m['oy']+y, m['ox']+x+w, m['oy']+y+h], native_components=[int(v) for v in labels if v],
            native_owners=sorted(owners), threshold_unknown_pixels=unknown, native_unassigned_components=unresolved,
            retention_reasons=reasons, pixel_causes=dict(cause_pixels))
        return key

    word_profiles = {}
    def word_profile(lid, wi):
        key = lid+':'+str(wi)
        if key in word_profiles:
            return key
        word = by_id[lid]['words'][wi]
        box = [word['x0'], word['y0'], word['x1']+1, word['y1']+1]
        support = cut(lid, box)
        x0, y0, x1, y1 = box
        labels, counts = np.unique(native.labels[y0:y1, x0:x1][support], return_counts=True)
        causes, fragmented = Counter(), []
        for label, count in zip(labels, counts):
            if not label:
                causes['native_threshold_disagreement'] += int(count)
                continue
            item = evidence.component(label)
            category = item['kind'] if item['owner'] is None else ('proved_own_ink' if item['owner'] == lid else 'proved_foreign_ink')
            causes[category] += int(count)
            if item['owner'] == lid and not (box[0] <= item['bbox'][0] and item['bbox'][2] <= box[2]):
                fragmented.append(int(label))
        local_ids = [local_component(lid, int(label)) for label in np.unique(cut(lid, box, 'labels')[support]) if label]
        word_profiles[key] = dict(line_id=lid, word_index=wi, text=word['text'], bbox=box, pixel_causes=dict(causes),
            native_owned_components_crossing_word_x_bounds=fragmented, local_components=local_ids)
        return key

    kinds, native_causes, reasons, cause_lines = Counter(), Counter(), Counter(), defaultdict(set)
    grouped = defaultdict(list)
    for pi, pair in enumerate(pairs):
        a, b, box = pair['line_a'], pair['line_b'], pair['intersection']
        ma, mb = cut(a, box), cut(b, box)
        kind, counts, common = support_kind(ma, mb)
        pair.update(index=pi, support_kind=kind, mask_pixels=counts, common_mask_pixels=common,
                    raw_dark_pixels=int(np.count_nonzero(gray[box[1]:box[3], box[0]:box[2]] < 160)))
        kinds[kind] += 1
        pa, pb = word_profile(a, pair['word_a']), word_profile(b, pair['word_b'])
        pair['word_profiles'] = [pa, pb]
        mx = (box[0]+box[2])/2
        baselines = [native.curves[native.index[lid]] for lid in (a, b)]
        distance = abs(float(np.interp(mx, baselines[0][:, 0], baselines[0][:, 1]))-
                       float(np.interp(mx, baselines[1][:, 0], baselines[1][:, 1])))
        pair['baseline_distance'] = distance
        pair['near_duplicate_baselines'] = bool(distance <= .1*min(native.heights[native.index[a]], native.heights[native.index[b]]))
        causes = Counter()
        if common:
            labels, pixels = np.unique(native.labels[box[1]:box[3], box[0]:box[2]][ma & mb], return_counts=True)
            pair['shared_native_components'] = [int(label) for label in labels]
            for label, count in zip(labels, pixels):
                if not label:
                    causes['native_threshold_disagreement'] += int(count)
                else:
                    item = evidence.component(label)
                    category = item['kind'] if item['owner'] is None else ('proved_owner_is_one_of_pair' if item['owner'] in (a, b) else 'proved_third_line_owner')
                    causes[category] += int(count)
        pair['shared_ink_causes'] = dict(causes)
        pair['foreign_ink_anywhere_in_words'] = [word_profiles[key]['pixel_causes'].get('proved_foreign_ink', 0) for key in (pa, pb)]
        pair_reasons = {reason for key in (pa, pb) for component in word_profiles[key]['local_components']
                        for reason in local_components[component]['retention_reasons']}
        pair['local_retention_reasons'] = sorted(pair_reasons)
        for cause, count in causes.items():
            native_causes[cause] += count
            cause_lines[cause].update((a, b))
        for reason in pair_reasons:
            reasons[reason] += 1
        grouped[tuple(sorted((a, b)))].append(pi)
    clean_envelope, foreign, uncertain = [], [], []
    for lid in implicated:
        profiles = [profile for profile in word_profiles.values() if profile['line_id'] == lid]
        if any(profile['pixel_causes'].get('proved_foreign_ink') for profile in profiles):
            foreign.append(lid)
        elif any(any(key not in {'proved_own_ink'} for key in profile['pixel_causes']) for profile in profiles):
            uncertain.append(lid)
        else:
            clean_envelope.append(lid)
    component_kinds = Counter(item['kind'] for item in evidence.catalog.values())
    competing = [item for item in evidence.catalog.values() if item['kind'] == 'overlapping_competing_polygons']
    separated = []
    for item in competing:
        distances = sorted(c['baseline_distance_line_heights'] for c in item['candidates'])
        if len(distances) > 1 and distances[0] <= .10 and distances[1] >= .50:
            separated.append(item['component'])
    summary = dict(version=VERSION, colliding_lines=len(implicated), line_pairs=len(grouped), word_pairs=len(pairs),
        pair_support_kinds=dict(kinds), shared_ink_pixel_causes=dict(native_causes),
        shared_ink_affected_lines={key: len(lines) for key, lines in cause_lines.items()},
        local_retention_reason_pairs=dict(reasons), native_component_kinds=dict(component_kinds),
        colliding_lines_with_proved_foreign_ink=len(foreign),
        colliding_lines_with_only_proved_own_ink_in_colliding_words=len(clean_envelope),
        colliding_lines_with_unresolved_native_evidence=len(uncertain),
        competing_polygon_components_with_baseline_distances_best_le_0_1_next_ge_0_5=len(separated),
        near_duplicate_baseline_word_pairs=sum(pair['near_duplicate_baselines'] for pair in pairs),
        words_with_native_owned_component_crossing_word_x_bounds=sum(bool(p['native_owned_components_crossing_word_x_bounds']) for p in word_profiles.values()),
        no_annotation_changes=True, ctc_calls=0, reading_calls=0, reference_inputs=False, promoted=False,
        scope='source-only explanation of existing refusals; pixel support is not lexical or glyph certification')
    output.mkdir(parents=True, exist_ok=True)
    payloads = {'summary': summary, 'word-pairs': pairs, 'word-profiles': word_profiles,
                'local-component-evidence': local_components, 'native-component-evidence': evidence.catalog,
                'line-pairs': [dict(lines=list(key), word_pair_indices=value) for key, value in grouped.items()],
                'line-classification': dict(proved_foreign_ink=foreign, only_proved_own_ink=clean_envelope,
                                            unresolved_native_evidence=uncertain),
                'competing-polygons-separated-baselines': separated,
                'provenance': dict(image_sha256=image_hash, source_directory=str(source.resolve()),
                    variant_directory=str(variant.resolve()), annotations_sha256=hashlib.sha256((variant/'candidate-annotations.json').read_bytes()).hexdigest(),
                    implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), reference_inputs=False)}
    for name, value in payloads.items():
        (output/(name+'.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    for name in ('image', 'source', 'variant', 'output'):
        parser.add_argument(name)
    args = parser.parse_args()
    print(json.dumps(audit(args.image, args.source, args.variant, args.output), ensure_ascii=False, indent=2))
