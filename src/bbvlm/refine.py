"""Foreground refinement constrained by native word intervals and line polygon.

Candidate family G01. No ground-truth word geometry is accepted by this API.
All bounds are half-open. No recognition network is run here.
"""
import cv2
import numpy as np
import unicodedata


def extend_crop_edges_to_connected_ink(gray, box, *, max_pad,
                                        min_area=3, min_side_pixels=2):
    """Extend a raster crop only where foreground crosses its exact edge.

    Otsu foreground is computed in a context ring bounded by ``max_pad``. A
    side moves only when one 8-connected component has enough pixels both in
    the native two-pixel inner strip and beyond that edge. Nearby disconnected
    ink therefore does not enlarge the crop. Connectivity remains geometric
    evidence, not proof that the ink belongs semantically to the crop.
    """
    if gray.ndim != 2:
        raise ValueError('gray must be a 2-D image')
    if len(box) != 4 or max_pad < 0 or min_area < 1 or min_side_pixels < 1:
        raise ValueError('invalid crop-extension parameter')
    h, w = gray.shape
    x0 = max(0, int(np.floor(box[0])))
    y0 = max(0, int(np.floor(box[1])))
    x1 = min(w, int(np.ceil(box[2])))
    y1 = min(h, int(np.ceil(box[3])))
    if x1 <= x0 or y1 <= y0:
        raise ValueError('empty crop')
    p = int(max_pad)
    ex0, ey0 = max(0, x0-p), max(0, y0-p)
    ex1, ey1 = min(w, x1+p), min(h, y1+p)
    context = gray[ey0:ey1, ex0:ex1]
    threshold, fg = cv2.threshold(
        context, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    lx0, ly0, lx1, ly1 = x0-ex0, y0-ey0, x1-ex0, y1-ey0
    strip_x, strip_y = min(2, x1-x0), min(2, y1-y0)
    accepted = {'left': [], 'top': [], 'right': [], 'bottom': []}
    candidate = [x0, y0, x1, y1]

    for component in range(1, n):
        xx, yy, ww, hh, area = [int(v) for v in stats[component]]
        if area < min_area:
            continue
        mask = labels == component
        tests = {
            'left': (mask[ly0:ly1, lx0:min(lx1, lx0+strip_x)].sum(),
                     mask[ly0:ly1, :lx0].sum()),
            'right': (mask[ly0:ly1, max(lx0, lx1-strip_x):lx1].sum(),
                      mask[ly0:ly1, lx1:].sum()),
            'top': (mask[ly0:min(ly1, ly0+strip_y), lx0:lx1].sum(),
                    mask[:ly0, lx0:lx1].sum()),
            'bottom': (mask[max(ly0, ly1-strip_y):ly1, lx0:lx1].sum(),
                       mask[ly1:, lx0:lx1].sum()),
        }
        gx0, gy0 = ex0+xx, ey0+yy
        gx1, gy1 = gx0+ww, gy0+hh
        for side, (inside, outside) in tests.items():
            if inside < min_side_pixels or outside < min_side_pixels:
                continue
            accepted[side].append({
                'component': component, 'area': area,
                'inside_pixels': int(inside), 'outside_pixels': int(outside),
                'bbox': [gx0, gy0, gx1, gy1],
            })
            if side == 'left': candidate[0] = min(candidate[0], gx0)
            elif side == 'top': candidate[1] = min(candidate[1], gy0)
            elif side == 'right': candidate[2] = max(candidate[2], gx1)
            else: candidate[3] = max(candidate[3], gy1)

    candidate = [max(ex0, candidate[0]), max(ey0, candidate[1]),
                 min(ex1, candidate[2]), min(ey1, candidate[3])]
    if (candidate[0] > x0 or candidate[1] > y0 or
            candidate[2] < x1 or candidate[3] < y1):
        raise AssertionError('crop extension shrank the native box')
    return candidate, {
        'native_box': [x0, y0, x1, y1], 'candidate_box': candidate,
        'max_pad': p, 'otsu_threshold': float(threshold),
        'changed_sides': [side for side, rows in accepted.items() if rows],
        'components': accepted,
        'warning': 'Connected foreground is geometric evidence, not semantic ownership.',
    }


def prepare_line_foreground(gray, polygon, line_box, binarization='otsu'):
    h,w=gray.shape
    x0,y0,x1,y1=line_box
    x0=max(0,int(np.floor(x0)));y0=max(0,int(np.floor(y0)))
    x1=min(w,int(np.ceil(x1)));y1=min(h,int(np.ceil(y1)))
    if x1<=x0 or y1<=y0:raise ValueError('empty line crop')
    crop=gray[y0:y1,x0:x1]
    if binarization=='otsu':
        _,fg=cv2.threshold(crop,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    elif binarization=='local':
        block=max(3,int(min(crop.shape)*.75)//2*2+1)
        fg=cv2.adaptiveThreshold(crop,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,block,11)
    else:raise ValueError('unknown binarization')
    mask=np.zeros_like(fg)
    pts=np.asarray(polygon,float)-np.array([x0,y0])
    cv2.fillPoly(mask,[np.rint(pts).astype(np.int32)],255)
    fg=cv2.bitwise_and(fg,mask)
    return fg,x0,y0


def refine_words(gray, native_boxes, line_polygon, line_box, *, mode='vertical',
                 margin=0, min_area=2, binarization='otsu', max_shrink=.5):
    if not native_boxes:return []
    fg,ox,oy=prepare_line_foreground(gray,line_polygon,line_box,binarization)
    line_h=line_box[3]-line_box[1]
    result=[]
    for i,box in enumerate(native_boxes):
        x0,y0,x1,y1=box
        # Shared separators prevent a word from absorbing its neighbour.
        left=(native_boxes[i-1][2]+x0)/2 if i else line_box[0]
        right=(x1+native_boxes[i+1][0])/2 if i+1<len(native_boxes) else line_box[2]
        if right<=left:result.append(list(box));continue
        a=max(0,int(np.floor(left-ox)));b=min(fg.shape[1],int(np.ceil(right-ox)))
        sub=fg[:,a:b]
        if sub.size==0:result.append(list(box));continue
        n,labels,stats,_=cv2.connectedComponentsWithStats(sub,8)
        kept=[]
        for k in range(1,n):
            xx,yy,ww,hh,area=stats[k]
            cx=ox+a+xx+ww/2
            if area>=min_area and x0<=cx<x1:
                kept.append((ox+a+xx,oy+yy,ox+a+xx+ww,oy+yy+hh))
        if not kept:result.append(list(box));continue
        tight=[min(v[0] for v in kept)-margin,min(v[1] for v in kept)-margin,
               max(v[2] for v in kept)+margin,max(v[3] for v in kept)+margin]
        # Reject excessive contractions; leave uncertain words untouched.
        if tight[3]-tight[1] < (1-max_shrink)*(y1-y0):
            result.append(list(box));continue
        if mode=='vertical':tight[0],tight[2]=x0,x1
        elif mode!='xy':raise ValueError('mode must be vertical or xy')
        tight=[max(0,tight[0]),max(0,tight[1]),min(gray.shape[1],tight[2]),min(gray.shape[0],tight[3])]
        if tight[2]<=tight[0] or tight[3]<=tight[1]:result.append(list(box))
        else:result.append([float(v) for v in tight])
    return result


def extend_words_to_foreground(gray, native_boxes, line_polygon, line_box, *,
                               min_area=2, binarization='otsu',
                               max_gap_height_ratio=.75, margin=0,
                               external_centroids_only=False):
    """Conservatively add nearby line ink to native word boxes.

    This is deliberately different from :func:`refine_words`: a returned box
    always contains its native input.  Connected components are assigned inside
    horizontal cells separated halfway through inter-word gaps, and must be no
    farther than a line-height-scaled distance from the native box.  The line
    polygon remains the hard foreground mask.

    The second return value is an audit record; it is not a confidence score or
    evidence that the enlarged box is ground truth.
    """
    if not native_boxes:
        return [], []
    if max_gap_height_ratio < 0 or min_area < 1 or margin < 0:
        raise ValueError('invalid ink-extension parameter')
    boxes = [[float(v) for v in box] for box in native_boxes]
    if any(len(box) != 4 or box[2] <= box[0] or box[3] <= box[1]
           for box in boxes):
        raise ValueError('invalid native word box')
    centers = [(box[0] + box[2]) / 2 for box in boxes]
    if any(b <= a for a, b in zip(centers, centers[1:])):
        raise ValueError('native word boxes are not in left-to-right order')

    fg, ox, oy = prepare_line_foreground(
        gray, line_polygon, line_box, binarization)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(fg, 8)
    components = []
    for k in range(1, n):
        xx, yy, ww, hh, area = stats[k]
        if area >= min_area:
            components.append({
                'bbox': [float(ox + xx), float(oy + yy),
                         float(ox + xx + ww), float(oy + yy + hh)],
                'centroid': [float(ox + centroids[k][0]),
                             float(oy + centroids[k][1])],
                'area': int(area),
            })

    max_gap = max(0.0, float(line_box[3] - line_box[1]) * max_gap_height_ratio)
    results, audit = [], []
    for i, native in enumerate(boxes):
        x0, y0, x1, y1 = native
        left = (boxes[i - 1][2] + x0) / 2 if i else float(line_box[0])
        right = (x1 + boxes[i + 1][0]) / 2 if i + 1 < len(boxes) else float(line_box[2])
        # Overlapping native intervals are uncommon but must not invert cells.
        left = min(left, centers[i])
        right = max(right, centers[i])
        owned = []
        for component in components:
            cx, cy = component['centroid']
            if not (left <= cx < right or (i + 1 == len(boxes) and cx == right)):
                continue
            if external_centroids_only and x0 <= cx < x1 and y0 <= cy < y1:
                continue
            bx0, by0, bx1, by1 = component['bbox']
            dx = max(x0 - bx1, bx0 - x1, 0.0)
            dy = max(y0 - by1, by0 - y1, 0.0)
            if dx <= max_gap and dy <= max_gap:
                owned.append(component)
        if owned:
            candidate = [
                min(x0, min(c['bbox'][0] for c in owned) - margin),
                min(y0, min(c['bbox'][1] for c in owned) - margin),
                max(x1, max(c['bbox'][2] for c in owned) + margin),
                max(y1, max(c['bbox'][3] for c in owned) + margin),
            ]
        else:
            candidate = native[:]
        candidate = [max(0.0, candidate[0]), max(0.0, candidate[1]),
                     min(float(gray.shape[1]), candidate[2]),
                     min(float(gray.shape[0]), candidate[3])]
        # Explicit containment invariant; this should also catch bad clipping.
        if (candidate[0] > x0 or candidate[1] > y0 or
                candidate[2] < x1 or candidate[3] < y1):
            raise ValueError('ink extension would shrink a native box')
        results.append(candidate)
        audit.append({
            'changed': candidate != native,
            'native_box': native,
            'candidate_box': candidate,
            'cell': [float(left), float(right)],
            'max_gap_pixels': float(max_gap),
            'assigned_components': len(owned),
            'assigned_ink_pixels': sum(c['area'] for c in owned),
            'external_centroids_only': bool(external_centroids_only),
        })
    return results, audit


def select_edge_punctuation_extensions(tokens, native_boxes, candidate_boxes):
    """Keep an additive candidate only when the token has edge punctuation.

    Text is used as a conservative routing signal, never as geometry evidence.
    The returned decision records therefore remain automatic proposals.
    """
    if not (len(tokens) == len(native_boxes) == len(candidate_boxes)):
        raise ValueError('token and geometry counts differ')
    selected, decisions = [], []
    for token, native, candidate in zip(tokens, native_boxes, candidate_boxes):
        if not isinstance(token, str) or not token:
            edge = False
        else:
            edge = (unicodedata.category(token[0]).startswith('P') or
                    unicodedata.category(token[-1]).startswith('P'))
        changed = list(candidate) != list(native)
        accept = bool(edge and changed)
        selected.append([float(v) for v in (candidate if accept else native)])
        decisions.append({'edge_punctuation': bool(edge),
                          'candidate_changed': changed, 'selected': accept})
    return selected, decisions
