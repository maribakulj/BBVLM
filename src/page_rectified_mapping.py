"""Reporter un placement dans un crop rectifié vers les pixels de la source.

La grille PERO/cv2.remap contient les centres source (x, y), pour chaque
échantillon du crop. Une enveloppe de leurs supports d'interpolation n'est
pas un masque d'encre : aucune certification de glyphe n'est déduite ici.
"""
from __future__ import annotations

import math
import numpy as np


VERSION = 'rectified-source-sampling-envelope-v1'


def map_rectified_box(source_xy, bbox, *, image_size):
    """Mapper une boîte entière INCLUSIVE de pixels du crop.

    Tous les échantillons sont examinés : les extrema d'une ligne courbe
    peuvent être entre les coins, voire à l'intérieur. Le support bilinéaire
    conservateur est demi-ouvert dans la source. Un débordement n'est jamais
    masqué par un clamp ; le diagnostic est renvoyé sans boîte admissible.
    """
    mapping = np.asarray(source_xy)
    if mapping.ndim != 3 or mapping.shape[2] != 2 or min(mapping.shape[:2]) < 1:
        raise ValueError('Grille attendue : hauteur × largeur × coordonnées xy')
    if not np.issubdtype(mapping.dtype, np.number) or np.issubdtype(mapping.dtype, np.complexfloating):
        raise ValueError('Coordonnées source réelles requises')
    if (not isinstance(image_size, (tuple, list)) or len(image_size) != 2
            or any(type(v) is not int or v <= 0 for v in image_size)):
        raise ValueError('Dimensions source entières positives requises')
    if (not isinstance(bbox, (tuple, list, np.ndarray)) or len(bbox) != 4
            or any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.number))
                   or not np.isfinite(v) or int(v) != v for v in bbox)):
        raise ValueError('Boîte de crop entière inclusive requise')
    x0, y0, x1, y1 = map(int, bbox)
    h, w = mapping.shape[:2]
    if not 0 <= x0 <= x1 < w or not 0 <= y0 <= y1 < h:
        raise ValueError('Boîte hors du crop rectifié')
    selected = mapping[y0:y1+1, x0:x1+1].astype(np.float64, copy=False)
    report = dict(version=VERSION, rectified_bbox_inclusive=[x0, y0, x1, y1],
        rectified_shape=[h, w], sample_count=int(selected.shape[0]*selected.shape[1]),
        source_image_size=list(image_size), source_xy_order='x,y',
        examines_all_samples=True, interpolation='bilinear conservative support',
        coordinate_convention='source sample centers; support bbox half-open',
        glyph_mask_produced=False, word_geometry_certified=False,
        source_clipping_performed=False, eligible_for_geometric_comparison=False)
    if not np.isfinite(selected).all():
        return dict(report, status='nonfinite_source_mapping', source_support_bbox=None,
                    invalid_samples=int((~np.isfinite(selected).all(axis=2)).sum()))
    minimum = selected.min(axis=(0, 1))
    maximum = selected.max(axis=(0, 1))
    centers = [float(minimum[0]), float(minimum[1]), float(maximum[0]), float(maximum[1])]
    support = [math.floor(minimum[0]), math.floor(minimum[1]),
               math.ceil(maximum[0])+1, math.ceil(maximum[1])+1]
    width, height = image_size
    out = ((selected[..., 0] < 0) | (selected[..., 0] > width-1)
           | (selected[..., 1] < 0) | (selected[..., 1] > height-1))
    report.update(source_center_envelope=centers,
                  unclipped_source_support_bbox=support,
                  out_of_page_samples=int(out.sum()))
    if out.any():
        return dict(report, status='source_mapping_out_of_page', source_support_bbox=None)
    return dict(report, status='mapped_sampling_support', source_support_bbox=support,
                eligible_for_geometric_comparison=True)
