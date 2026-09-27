"""Coarse column context windows from detector proposals, never word boxes.

No source text, XML labels or reference geometry may enter this module.
Context windows cover the page, overlap at gutters, and retain every detection.
Spanning items require separate handling, not assignment by a forced total order.
"""
from math import isfinite

from .order import infer_column_major_order


def route_lines_to_columns(lines, windows, page_bbox, *, min_owner_fraction=0.8):
    """Attach whole lines to column context; never crop or rewrite geometry.

    Input line IDs are unique opaque identifiers. A low-overlap line abstains
    from a primary column. The returned crop covers its complete bbox within
    the image; source geometry outside the image is retained and flagged.
    This is routing, not a detector or a certified reading-order algorithm.
    """
    from copy import deepcopy
    def box_ok(b):
        return len(b)==4 and all(isfinite(v) for v in b) and b[2]>b[0] and b[3]>b[1]
    if not box_ok(page_bbox) or not windows or not 0.5<min_owner_fraction<=1:
        raise ValueError('invalid routing parameters')
    if len({l['id'] for l in lines})!=len(lines) or len({w['id'] for w in windows})!=len(windows):
        raise ValueError('duplicate IDs')
    for w in windows:
        if not box_ok(w['core_bbox']) or not box_ok(w['context_bbox']):
            raise ValueError('invalid window')
    def intersect(a,b):
        return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    result=[]
    for line in lines:
        b=line['bbox']
        if not box_ok(b): raise ValueError('invalid line bbox')
        size=(b[2]-b[0])*(b[3]-b[1])
        scores=[intersect(b,w['core_bbox'])/size for w in windows]
        best=max(range(len(windows)),key=lambda i:(scores[i],windows[i]['id']))
        owner=windows[best] if scores[best]>=min_owner_fraction else None
        context=windows[best]['context_bbox']
        context_contains=intersect(b,context)>=size-1e-6
        crop=[max(page_bbox[0],b[0]),max(page_bbox[1],b[1]),
              min(page_bbox[2],b[2]),min(page_bbox[3],b[3])]
        reasons=[]
        if owner is None: reasons.append('ambiguous_or_spanning_column')
        if not context_contains: reasons.append('line_exceeds_column_context')
        if intersect(b,page_bbox)<size-1e-6: reasons.append('source_geometry_outside_image')
        result.append({'id':line['id'],'source_line':deepcopy(line),
            'column_id':owner['id'] if owner else None,'owner_fraction':scores[best],
            'column_memberships':[w['id'] for w,s in zip(windows,scores) if s>0],
            'context_contains_line':context_contains,
            'crop_bbox':crop if box_ok(crop) else None,
            'crop_policy':'whole_line_from_original_image',
            'review_reasons':reasons})
    return {'schema':'bbvlm.whole-line-column-routing/1','lines':result,
            'parameters':{'min_owner_fraction':min_owner_fraction},
            'geometry_modified':False,'reading_order_certified':False}


def propose_column_windows(detections, page_bbox, *, order_parameters,
                           context_margin_ratio=0.004):
    x0, y0, x1, y1 = map(float, page_bbox)
    width, height = x1-x0, y1-y0
    if not all(isfinite(v) for v in (x0,y0,x1,y1)) or width <= 0 or height <= 0:
        raise ValueError('invalid page bbox')
    if not isfinite(context_margin_ratio) or not 0 <= context_margin_ratio < .1:
        raise ValueError('invalid context margin')
    ids = [d['id'] for d in detections]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate detection IDs')
    for d in detections:
        box=d['bbox']
        if len(box)!=4 or not all(isfinite(v) for v in box) or box[2]<=box[0] or box[3]<=box[1]:
            raise ValueError('invalid detection bbox')
        if box[0]<x0 or box[1]<y0 or box[2]>x1 or box[3]>y1:
            raise ValueError('detection bbox outside page')
    # Classes influence anchor selection only; even "abandon" is retained.
    anchors=[d for d in detections if d.get('class_name')=='plain text']
    fallback=not anchors
    inferred=infer_column_major_order(anchors,page_bbox,**order_parameters) if anchors else None
    spans=inferred['column_spans_x'] if inferred else [[x0,x1]]
    cuts=[(a[1]+b[0])/2 for a,b in zip(spans,spans[1:])]
    unsafe=any(a[1]>b[0] for a,b in zip(spans,spans[1:]))
    if any(a>=b for a,b in zip([x0]+cuts,cuts+[x1])):
        unsafe=True
        cuts=[]
    boundaries=[x0]+cuts+[x1]
    margin=context_margin_ratio*width
    windows=[]
    for i,(left,right) in enumerate(zip(boundaries,boundaries[1:])):
        windows.append({'id':f'C{i+1}',
                        'core_bbox':[left,y0,right,y1],
                        'context_bbox':[max(x0,left-margin),y0,min(x1,right+margin),y1]})
    memberships={}; spanning=[]; review=[]
    for d in detections:
        box=d['bbox']
        memberships[d['id']]=[w['id'] for w in windows
            if min(box[2],w['core_bbox'][2])>max(box[0],w['core_bbox'][0])]
        if len(memberships[d['id']])>1:
            spanning.append(d['id'])
            review.append({'id':d['id'],'reason':'crosses_column_boundary',
                           'action':'retain_full_region_context; do not force column order'})
        if d.get('class_name')!='plain text':
            review.append({'id':d['id'],'reason':'non_body_detector_class',
                           'action':'retain; class is not permission to delete content'})
    return {'schema':'bbvlm.detector-column-windows/1','windows':windows,
            'anchor_spans_x':spans,'anchor_ids':[d['id'] for d in anchors],
            'region_column_memberships':memberships,'spanning_region_ids':spanning,
            'retained_detection_ids':ids,'review':review,
            'requires_layout_review':fallback or unsafe,
            'parameters':{'order':order_parameters,'context_margin_ratio':context_margin_ratio},
            'status':'proposal_not_verified','word_boxes':None}
