"""Foreground refinement constrained by native word intervals and line polygon.

Candidate family G01. No ground-truth word geometry is accepted by this API.
All bounds are half-open. No recognition network is run here.
"""
import cv2
import numpy as np
import unicodedata


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
