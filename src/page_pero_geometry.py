"""Essai PERO géométrie seule, sans transcription ni alignement CTC.

Le détecteur tiers n'est chargé que dans run(). Les rapprochements avec la
segmentation existante sont des voisins géométriques, jamais une vérité terrain.
Les configurations et poids officiels restent traçables et inchangés.
"""
from __future__ import annotations

import hashlib
import configparser
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

import cv2
import numpy as np


VERSION = 'pero-layout-only-source-experiment-v1'
SAMPLE_IDS = ('L0010', 'L0014', 'L0100', 'L0106', 'L0217', 'L0225', 'L0231',
              'L0241', 'L0246', 'L0578', 'L0650', 'L0653', 'L0677', 'L0880',
              'L0920', 'L0926', 'L0956', 'L0960')
EXTRA_SAMPLE_IDS = ('L0622',)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry_rows(rows):
    allowed = {'id', 'bbox', 'detector_bbox', 'baseline', 'polygon', 'source'}
    return [{k: v for k, v in row.items() if k in allowed} for row in rows]


def geometric_neighbors(reference, candidate):
    """Voisinage mesuré ; recouvrement horizontal réciproque >= 0.5 fixé."""
    result = []
    for ref in reference:
        r = np.asarray(ref['baseline'], float)
        r = r[np.argsort(r[:, 0])]
        box = ref.get('detector_bbox') or ref['bbox']
        height = max(1., box[3]-box[1])
        options = []
        for row in candidate:
            c = np.asarray(row['baseline'], float)
            c = c[np.argsort(c[:, 0])]
            left, right = max(r[0, 0], c[0, 0]), min(r[-1, 0], c[-1, 0])
            width = right-left
            if width <= 0:
                continue
            overlap = width/max(r[-1, 0]-r[0, 0], c[-1, 0]-c[0, 0], 1.)
            if overlap < .5:
                continue
            x = np.linspace(left, right, 17)
            distance = float(np.median(np.abs(np.interp(x, r[:, 0], r[:, 1])-
                                              np.interp(x, c[:, 0], c[:, 1]))))
            options.append(dict(id=row['id'], baseline_distance_px=distance,
                reference_height=height, distance_in_reference_heights=distance/height,
                horizontal_reciprocal_overlap=overlap))
        options.sort(key=lambda item: (item['distance_in_reference_heights'], -item['horizontal_reciprocal_overlap']))
        result.append(dict(reference_id=ref['id'], nearest=options[0] if options else None,
            candidates_within_half_reference_height=sum(item['distance_in_reference_heights'] <= .5 for item in options),
            top_candidates=options[:3], correspondence_certified=False))
    return result


def reciprocal_matches(reference, candidate):
    """Unicité réciproque dans les voisinages fixés, sans certifier le texte."""
    forward = geometric_neighbors(reference, candidate)
    reverse = {r['reference_id']: r for r in geometric_neighbors(candidate, reference)}
    for row in forward:
        nearest = row['nearest']
        count = row['candidates_within_half_reference_height']
        if count == 0:
            status = 'no_close_geometry_neighbor'
        elif count > 1:
            status = 'ambiguous_geometry_neighbors'
        else:
            back = reverse[nearest['id']]
            status = ('unique_reciprocal_geometry_neighbor'
                if back['candidates_within_half_reference_height'] == 1
                and back['nearest']['id'] == row['reference_id'] else 'nonreciprocal_or_ambiguous_geometry_neighbor')
        row['reciprocal_status'] = status
        row['unique_reciprocal_neighbor'] = nearest['id'] if status == 'unique_reciprocal_geometry_neighbor' else None
    return forward


def run(image, reference_segmentation, model, pero_repository, output, threads=2, max_mp=5.):
    image, reference_segmentation, model, pero_repository, output = map(Path,
        (image, reference_segmentation, model, pero_repository, output))
    if output.exists() and any(output.iterdir()):
        raise ValueError('Un dossier vide est requis pour préserver chaque essai')
    if not model.name.endswith('.cpu'):
        raise ValueError('Ce diagnostic utilise uniquement le poids officiel CPU')
    sys.path.insert(0, str(pero_repository.resolve()))
    import torch
    from pero_ocr.layout_engines.cnn_layout_engine import LayoutEngine
    from pero_ocr.core.crop_engine import EngineLineCropper
    import pero_ocr
    if Path(pero_ocr.__file__).resolve().parent.parent != pero_repository.resolve():
        raise ValueError('Le module PERO chargé ne correspond pas au dépôt choisi')
    torch.set_num_threads(threads)
    np.random.seed(0)
    pixels = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if pixels is None:
        raise ValueError('Image illisible')
    reference = geometry_rows(json.loads(reference_segmentation.read_text()))
    output.mkdir(parents=True, exist_ok=True)
    (output/'samples').mkdir()
    (output/'extra-samples').mkdir()
    published = configparser.ConfigParser()
    config_path = model.parent/'config.ini'
    if not published.read(config_path):
        raise ValueError('Configuration publiée absente')
    layout_config, crop_config = published['LAYOUT_PARSER_1'], published['LINE_CROPPER']
    parameters = dict(device='cpu', threads=threads, downsample=layout_config.getint('DOWNSAMPLE'), max_mp=max_mp,
        detection_threshold=layout_config.getfloat('DETECTION_THRESHOLD'), adaptive_downsample=True,
        line_end_weight=layout_config.getfloat('LINE_END_WEIGHT'),
        vertical_line_connection_range=layout_config.getint('VERTICAL_LINE_CONNECTION_RANGE'),
        smooth_line_predictions=layout_config.getboolean('SMOOTH_LINE_PREDICTIONS'),
        paragraph_line_threshold=.3, crop_line_height=crop_config.getint('LINE_HEIGHT'),
        crop_poly=crop_config.getint('INTERP'), crop_scale=crop_config.getfloat('LINE_SCALE'),
        seed=0, horizontal_reciprocal_overlap_for_comparison=.5,
        recognition_enabled=False, ctc_enabled=False)
    (output/'parameters-before-inference.json').write_text(json.dumps(parameters, indent=2))
    engine = LayoutEngine(str(model)[:-4], torch.device('cpu'), **{k: parameters[k] for k in
        ('downsample', 'max_mp', 'detection_threshold', 'adaptive_downsample', 'line_end_weight',
         'vertical_line_connection_range', 'smooth_line_predictions', 'paragraph_line_threshold')})
    maps_run = []
    original_maps = engine.parsenet.get_maps

    def record_maps(img, downsample):
        start = time.monotonic()
        maps = original_maps(img, downsample)
        maps_run.append(dict(downsample=float(downsample), shape=list(maps.shape),
                             seconds=time.monotonic()-start))
        return maps

    engine.parsenet.get_maps = record_maps
    start = time.monotonic()
    regions, baselines, heights, polygons = engine.detect(pixels)
    elapsed = time.monotonic()-start
    detected = []
    for i, (baseline, line_heights, polygon) in enumerate(zip(baselines, heights, polygons), 1):
        detected.append(dict(id=f'P{i:04d}', baseline=np.asarray(baseline).tolist(),
            heights=np.asarray(line_heights).tolist(), polygon=np.asarray(polygon).tolist(),
            bbox=[float(np.min(polygon[:, 0])), float(np.min(polygon[:, 1])),
                  float(np.max(polygon[:, 0])), float(np.max(polygon[:, 1]))],
            source='official-pero-parsenet-296000-cpu', text=None,
            geometry_certified=False, training_eligible=False))
    (output/'detected-lines.json').write_text(json.dumps(detected, indent=2))
    (output/'detected-regions.json').write_text(json.dumps([np.asarray(r).tolist() for r in regions], indent=2))
    neighbors = reciprocal_matches(reference, detected)
    (output/'geometric-neighbors.json').write_text(json.dumps(neighbors, indent=2))
    ref_by_id = {r['id']: r for r in reference}
    candidate_by_id = {r['id']: r for r in detected}
    comparisons = {r['reference_id']: r for r in neighbors}
    cropper = EngineLineCropper(line_height=parameters['crop_line_height'],
        poly=parameters['crop_poly'], scale=parameters['crop_scale'])
    samples, extra_samples, omissions = [], [], []
    for lid in SAMPLE_IDS+EXTRA_SAMPLE_IDS:
        if lid not in comparisons or comparisons[lid]['nearest'] is None:
            omissions.append(dict(reference_id=lid, group='initial18' if lid in SAMPLE_IDS else 'additional',
                                  reason='no_geometric_neighbor'))
            continue
        ref = ref_by_id[lid]
        comparison = comparisons[lid]['nearest']
        candidate = candidate_by_id[comparison['id']]
        rpoly, cpoly = np.asarray(ref['polygon']), np.asarray(candidate['polygon'])
        both = np.concatenate([rpoly, cpoly])
        x0, y0 = np.maximum(0, np.floor(both.min(axis=0)).astype(int)-15)
        x1, y1 = np.minimum(pixels.shape[1::-1], np.ceil(both.max(axis=0)).astype(int)+16)
        source = pixels[y0:y1, x0:x1]
        overlay = source.copy()
        for row, color in ((ref, (0, 0, 255)), (candidate, (0, 160, 0))):
            poly = np.rint(np.asarray(row['polygon'])-[x0, y0]).astype(np.int32)
            base = np.rint(np.asarray(row['baseline'])-[x0, y0]).astype(np.int32)
            cv2.polylines(overlay, [poly], True, color, 1)
            cv2.polylines(overlay, [base], False, color, 2)
        rectified, mapping = cropper.crop(pixels, np.asarray(candidate['baseline']),
            np.asarray(candidate['heights']), return_forward_mapping=True)
        if not np.isfinite(mapping).all() or rectified.size == 0:
            raise ValueError('Rectification invalide')
        prefix = ('samples/' if lid in SAMPLE_IDS else 'extra-samples/')+lid
        cv2.imwrite(str(output/(prefix+'-source.png')), source)
        cv2.imwrite(str(output/(prefix+'-geometry.png')), overlay)
        cv2.imwrite(str(output/(prefix+'-pero-rectified.png')), rectified)
        np.savez_compressed(output/(prefix+'-mapping.npz'), source_xy=mapping)
        in_page = ((mapping[:, :, 0] >= 0) & (mapping[:, :, 0] <= pixels.shape[1]-1)
                   & (mapping[:, :, 1] >= 0) & (mapping[:, :, 1] <= pixels.shape[0]-1))
        sample = dict(reference_id=lid, pero_id=candidate['id'],
            crop_native_bbox=[int(v) for v in (x0, y0, x1, y1)],
            rectified_shape=list(rectified.shape), native_mapping_in_page_fraction=float(in_page.mean()),
            comparison=comparison, source=prefix+'-source.png', geometry=prefix+'-geometry.png',
            rectified=prefix+'-pero-rectified.png', mapping=prefix+'-mapping.npz',
            reciprocal_status=comparisons[lid]['reciprocal_status'],
            unique_reciprocal_neighbor=comparisons[lid]['unique_reciprocal_neighbor'])
        (samples if lid in SAMPLE_IDS else extra_samples).append(sample)
    (output/'samples.json').write_text(json.dumps(samples, indent=2))
    (output/'extra-samples.json').write_text(json.dumps(extra_samples, indent=2))
    (output/'sample-omissions.json').write_text(json.dumps(omissions, indent=2))
    valid_distances = [r['nearest']['baseline_distance_px'] for r in neighbors if r['nearest']]
    summary = dict(version=VERSION, detected_lines=len(detected), detected_regions=len(regions),
        reference_detector_lines=len(reference), geometric_neighbors=len(valid_distances),
        nearest_baseline_distance_px_quantiles=np.quantile(valid_distances, [0, .25, .5, .75, .9, 1]).tolist() if valid_distances else [],
        line_count_difference_is_not_quality_measure=True, maps_inference=maps_run,
        detector_seconds=elapsed, samples=len(samples), extra_samples=len(extra_samples), sample_omissions=omissions,
        unique_reciprocal_geometry_neighbors=sum(r['unique_reciprocal_neighbor'] is not None for r in neighbors),
        ctc_calls=0, recognition_calls=0,
        markdown_changed=False, reference_text_or_gold_inputs=False, promoted=False,
        word_geometry_produced=False, comparison_is_against_other_detector_not_ground_truth=True)
    (output/'summary.json').write_text(json.dumps(summary, indent=2))
    provenance = dict(image=dict(path=str(image.resolve()), sha256=sha(image)),
        reference_detector=dict(path=str(reference_segmentation.resolve()), sha256=sha(reference_segmentation)),
        model=dict(path=str(model.resolve()), sha256=sha(model)),
        published_config=dict(path=str(config_path.resolve()), sha256=sha(config_path)),
        repository=str(pero_repository.resolve()),
        repository_commit=subprocess.check_output(['git', '-C', str(pero_repository), 'rev-parse', 'HEAD'], text=True).strip(),
        repository_diff=subprocess.check_output(['git', '-C', str(pero_repository), 'diff', '--stat'], text=True),
        packages={name: importlib.metadata.version(name) for name in ['torch', 'numpy', 'opencv-python-headless', 'scipy', 'numba', 'shapely', 'lxml', 'scikit-image']},
        implementation_sha256=sha(__file__), python=sys.executable, parameters=parameters)
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'reference_segmentation', 'model', 'pero_repository', 'output'):
        parser.add_argument(name)
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--max-mp', type=float, default=5.)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2))
