"""Diagnostic CRAFT source-only, sans OCR ni appariement de texte.

Ce module ne produit aucune annotation d'entraînement. Les scores CRAFT sont
des cartes de régions/affinités, et non des masques de glyphes certifiés.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time


VERSION = 'craft-source-geometry-experiment-v2'
REPOSITORY_COMMIT = 'e332dd8b718e291f51b66ff8f9ef2c98ee4474c8'
SAMPLE_IDS = ('L0010', 'L0014', 'L0100', 'L0106', 'L0217', 'L0225', 'L0231',
              'L0241', 'L0246', 'L0578', 'L0650', 'L0653', 'L0677', 'L0880',
              'L0920', 'L0926', 'L0956', 'L0960')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry_rows(rows):
    """Ne faire entrer dans le diagnostic que les coordonnées du détecteur."""
    allowed = {'id', 'bbox', 'detector_bbox', 'baseline', 'polygon'}
    result, seen = [], set()
    for row in rows:
        if not isinstance(row.get('id'), str) or not row['id'] or row['id'] in seen:
            raise ValueError('Identifiant détecteur absent ou dupliqué')
        seen.add(row['id'])
        result.append({k: v for k, v in row.items() if k in allowed})
    return result


def crop_bbox(box, image_size, horizontal_padding=16, vertical_padding_heights=1.):
    """Rectangle natif demi-ouvert ; aucune rotation ni rectification."""
    width, height = image_size
    if len(box) != 4 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in box):
        raise ValueError('Rectangle détecteur invalide')
    if not 0 <= box[0] < box[2] <= width or not 0 <= box[1] < box[3] <= height:
        raise ValueError('Rectangle détecteur hors image')
    line_h = math.ceil(box[3]-box[1])
    vertical = math.ceil(line_h*vertical_padding_heights)
    return [max(0, math.floor(box[0])-horizontal_padding),
            max(0, math.floor(box[1])-vertical),
            min(width, math.ceil(box[2])+horizontal_padding),
            min(height, math.ceil(box[3])+vertical)]


def resize_geometry(source_shape, input_shape, ratio, score_shape):
    """Décrire exactement le resize officiel et sa convention de retour.

    imgproc tronque H*ratio et W*ratio puis ajoute du noir jusqu'au multiple
    de 32 suivant. L'inverse officiel 2/ratio reste la convention de sortie ;
    les échelles réalisées distinctes sont exposées, pas substituées en secret.
    Les pixels OpenCV redimensionnés suivent une convention de centres ; les
    quadrilatères de score ne constituent pas des contours de pixels natifs.
    """
    shapes = (source_shape[:2], input_shape[:2], score_shape[:2])
    if any(len(s) != 2 or any(type(v) is not int or v <= 0 for v in s) for s in shapes):
        raise ValueError('Dimensions positives entières requises')
    if not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio <= 0:
        raise ValueError('Ratio CRAFT invalide')
    height, width = source_shape[:2]
    scaled_h, scaled_w = int(height*ratio), int(width*ratio)
    if min(scaled_h, scaled_w) < 1:
        raise ValueError('Resize CRAFT vide')
    padded_h, padded_w = ((v+31)//32*32 for v in (scaled_h, scaled_w))
    if list(input_shape[:2]) != [padded_h, padded_w] or list(score_shape[:2]) != [padded_h//2, padded_w//2]:
        raise ValueError('Dimensions incompatibles avec resize/padding/stride CRAFT')
    return dict(source_shape_yx=[height, width], resized_content_shape_yx=[scaled_h, scaled_w],
        padded_input_shape_yx=[padded_h, padded_w], score_shape_yx=list(score_shape[:2]),
        padding_ltrb=[0, 0, padded_w-scaled_w, padded_h-scaled_h],
        nominal_resize_ratio=float(ratio), realized_resize_ratio_xy=[scaled_w/width, scaled_h/height],
        official_score_to_crop_scale_xy=[2/ratio, 2/ratio],
        official_mapping_includes_half_pixel_offset=False,
        opencv_resized_pixel_center_to_source='(resized_index + 0.5) / realized_axis_ratio - 0.5',
        padding_value_rgb=[0, 0, 0], score_stride=2,
        score_cell_native_support_is_receptive_field=False,
        coordinates_are_certified_glyph_edges=False)


def score_native_support(resize):
    """Part native de cellules nominales 2×2, pas de champ réceptif neuronal."""
    import numpy as np
    height, width = resize['resized_content_shape_yx']
    sh, sw = resize['score_shape_yx']
    xs = np.clip(width-2*np.arange(sw), 0, 2)/2
    ys = np.clip(height-2*np.arange(sh), 0, 2)/2
    return np.outer(ys, xs).astype(np.float32)


def native_detection(score_polygon, ratio, crop_box, detector_box, *, identifier):
    """Retour officiel score×2/ratio + origine crop, sans arrondi ni clipping."""
    import numpy as np
    score = np.asarray(score_polygon, dtype=float)
    if score.shape != (4, 2) or not np.isfinite(score).all():
        raise ValueError('Quadrilatère CRAFT invalide')
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError('Ratio CRAFT invalide')
    native = score*(2/ratio)+crop_box[:2]
    x0, y0, x1, y1 = crop_box
    within = bool((native[:, 0] >= x0).all() and (native[:, 0] <= x1).all()
                  and (native[:, 1] >= y0).all() and (native[:, 1] <= y1).all())
    cx, cy = native.mean(axis=0)
    return dict(id=identifier, score_polygon=score.tolist(), polygon=native.tolist(),
        bbox=[*native.min(axis=0).tolist(), *native.max(axis=0).tolist()],
        bbox_convention='continuous extrema of quadrilateral vertices; not pixel support bounds',
        within_source_crop=within,
        center_in_detector_bbox=bool(detector_box[0] <= cx <= detector_box[2]
                                    and detector_box[1] <= cy <= detector_box[3]),
        text=None, geometry_certified=False)


def run(image, segmentation, model, repository, output, threads=2):
    import cv2
    import numpy as np
    import torch
    import torchvision

    image, segmentation, model, repository, output = map(Path,
        (image, segmentation, model, repository, output))
    if type(threads) is not int or threads < 1:
        raise ValueError('Nombre de threads positif requis')
    commit = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', 'HEAD'], text=True).strip()
    changed = subprocess.check_output(['git', '-C', str(repository), 'diff', 'HEAD', '--name-only'], text=True).splitlines()
    if commit != REPOSITORY_COMMIT or set(changed)-{'basenet/vgg16_bn.py'}:
        raise ValueError('Dépôt CRAFT différent du commit/patch de compatibilité audité')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choisir un dossier vide pour préserver les essais')
    output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repository.resolve()))
    import craft
    import craft_utils
    import imgproc
    for module in (craft, craft_utils, imgproc):
        if Path(module.__file__).resolve().parent != repository.resolve():
            raise ValueError('Module CRAFT chargé différent du dépôt déclaré')
    if hashlib.md5(model.read_bytes()).hexdigest() != '2f8227d2def4037cdb3b34389dcf9ec1':
        raise ValueError('Poids différents du CRAFT général publié par EasyOCR')
    parameters = dict(version=VERSION, source_only=True, text_input=False,
        ctc_calls=0, recognition_calls=0, sample_ids=list(SAMPLE_IDS),
        selection='same fixed diagnostic detector IDs as PERO, not a representative benchmark',
        text_threshold=.7, low_text=.4, link_threshold=.4,
        magnification=1.5, crop_horizontal_padding_px=16,
        crop_vertical_padding_in_detector_heights=1.,
        canvas='large enough for magnification; no source downsampling',
        postprocessing='official getDetBoxes; connected components area >=10 score pixels; adaptive dilation',
        padding='official black RGB at right/bottom; scores retained without clipping',
        image_decoder='cv2 BGR, EXIF orientation ignored to preserve native coordinates; converted to RGB',
        poly=False, refiner=False, device='cpu', threads=threads,
        status='diagnostic_only', training_eligible=False, promoted=False)
    provenance = dict(image=dict(path=str(image.resolve()), sha256=sha(image)),
        segmentation=dict(path=str(segmentation.resolve()), sha256=sha(segmentation)),
        model=dict(path=str(model.resolve()), sha256=sha(model),
            url='https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip',
            published_md5='2f8227d2def4037cdb3b34389dcf9ec1'),
        repository=str(repository.resolve()),
        repository_commit=commit,
        repository_patch=subprocess.check_output(['git', '-C', str(repository), 'diff', 'HEAD'], text=True),
        implementation_sha256=sha(__file__),
        packages=dict(torch=torch.__version__, torchvision=torchvision.__version__, cv2=cv2.__version__, numpy=np.__version__),
        parameters=parameters)
    (output/'provenance-before-inference.json').write_text(json.dumps(provenance, indent=2))
    torch.set_num_threads(threads)
    torch.manual_seed(0)
    net = craft.CRAFT(pretrained=False)
    state = torch.load(str(model), map_location='cpu', weights_only=True)
    net.load_state_dict({key.removeprefix('module.'): val for key, val in state.items()}, strict=True)
    net.eval()
    pixels = cv2.imread(str(image), cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
    if pixels is None:
        raise ValueError('Source image illisible')
    height, width = pixels.shape[:2]
    # Geometry only; no auxiliary OCR strings are passed to any detector.
    detector = {row['id']: row for row in geometry_rows(json.loads(segmentation.read_text()))}
    samples = []
    for lid in SAMPLE_IDS:
        if lid not in detector:
            samples.append(dict(id=lid, status='detector_id_absent'))
            continue
        row = detector[lid]
        box = row.get('detector_bbox') or row['bbox']
        x0, y0, x1, y1 = crop_bbox(box, (width, height),
            parameters['crop_horizontal_padding_px'], parameters['crop_vertical_padding_in_detector_heights'])
        crop = pixels[y0:y1, x0:x1]
        if not crop.size:
            raise ValueError('Crop source vide')
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        canvas = int(np.ceil(max(rgb.shape[:2])*parameters['magnification']))
        resized, ratio, heatmap_size = imgproc.resize_aspect_ratio(rgb, canvas,
            interpolation=cv2.INTER_LINEAR, mag_ratio=parameters['magnification'])
        tensor = torch.from_numpy(imgproc.normalizeMeanVariance(resized)).permute(2, 0, 1).unsqueeze(0)
        started = time.monotonic()
        with torch.inference_mode():
            scores, features = net(tensor)
        elapsed = time.monotonic()-started
        text_map = scores[0, :, :, 0].cpu().numpy().copy()
        link_map = scores[0, :, :, 1].cpu().numpy().copy()
        resize = resize_geometry(list(crop.shape), list(resized.shape), float(ratio), list(text_map.shape))
        if tuple(text_map.shape) != (heatmap_size[1], heatmap_size[0]) or link_map.shape != text_map.shape \
                or not np.isfinite(text_map).all() or not np.isfinite(link_map).all():
            raise ValueError('Cartes CRAFT incohérentes ou non finies')
        native_support = score_native_support(resize)
        boxes, _ = craft_utils.getDetBoxes(text_map, link_map,
            parameters['text_threshold'], parameters['link_threshold'], parameters['low_text'], False)
        adjusted = craft_utils.adjustResultCoordinates(boxes, 1/ratio, 1/ratio)
        overlay = crop.copy()
        detections = []
        for idx, quadrilateral in enumerate(adjusted):
            detection = native_detection(boxes[idx], float(ratio), [x0, y0, x1, y1], box,
                                         identifier=f'{lid}_D{idx:03d}')
            # Verify helper agrees with the pinned upstream coordinate routine.
            if not np.allclose(np.asarray(detection['polygon'])-[x0, y0], quadrilateral, atol=1e-4):
                raise ValueError('Mapping natif différent du retour CRAFT officiel')
            detections.append(detection)
            cv2.polylines(overlay, [np.rint(quadrilateral).astype(np.int32)], True,
                (0, 160, 0) if detection['center_in_detector_bbox'] else (0, 128, 255), 1)
        if row.get('polygon'):
            cv2.polylines(overlay, [np.rint(np.asarray(row['polygon'])-[x0, y0]).astype(np.int32)], True, (255, 0, 0), 1)
        folder = output/lid
        folder.mkdir()
        cv2.imwrite(str(folder/'source.png'), crop)
        cv2.imwrite(str(folder/'detections.png'), overlay)
        cv2.imwrite(str(folder/'region-affinity.png'), imgproc.cvt2HeatmapImg(np.hstack([text_map, link_map])))
        np.savez_compressed(folder/'scores.npz', region=text_map, affinity=link_map,
                            nominal_cell_native_support_fraction=native_support)
        result = dict(id=lid, crop_native_bbox=[x0, y0, x1, y1],
            detector_geometry=row, source_shape=list(crop.shape), input_shape=list(resized.shape),
            score_shape=list(text_map.shape), resize_ratio=float(ratio),
            resize_geometry=resize,
            score_cells=dict(fully_native=int(np.count_nonzero(native_support == 1)),
                partly_native=int(np.count_nonzero((native_support > 0) & (native_support < 1))),
                padding_only=int(np.count_nonzero(native_support == 0)),
                warning='Nominal stride cells only; neural receptive fields may extend beyond them'),
            score_to_input_stride=2., coordinate_convention='official CRAFT 2/ratio mapping; no box clipping',
            inference_seconds=elapsed, detections=detections,
            detector_centered_count=sum(d['center_in_detector_bbox'] for d in detections),
            recognition_calls=0, ctc_calls=0)
        (folder/'result.json').write_text(json.dumps(result, indent=2))
        samples.append({key: result[key] for key in ('id', 'crop_native_bbox', 'inference_seconds', 'detector_centered_count')})
        (output/'state.json').write_text(json.dumps(dict(completed=len(samples), total=len(SAMPLE_IDS)), indent=2))
        print(lid, 'regions', len(detections), 'centered', result['detector_centered_count'], flush=True)
        del tensor, scores, features
    summary = dict(parameters, samples=samples, inference_seconds=sum(s.get('inference_seconds', 0) for s in samples))
    (output/'summary.json').write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('image', 'segmentation', 'model', 'repository', 'output'):
        parser.add_argument(name)
    parser.add_argument('--threads', type=int, default=2)
    print(json.dumps(run(**vars(parser.parse_args())), indent=2))
