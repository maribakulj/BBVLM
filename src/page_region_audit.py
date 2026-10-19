"""Couverture des pixels des régions par les images réellement ouvertes."""
from pathlib import Path


def union_area(boxes):
    xs=sorted({x for a,b,c,d in boxes for x in (a,c)})
    total=0
    for x0,x1 in zip(xs,xs[1:]):
        spans=sorted((b,d) for a,b,c,d in boxes if a<=x0 and c>=x1)
        length=0;end=None
        for a,b in spans:
            length+=b-a if end is None else max(0,b-max(a,end))
            end=b if end is None else max(end,b)
        total+=(x1-x0)*length
    return total


def coverage(region,native_metadata):
    proof=native_metadata.get('native_history_provenance',{}).get('input_views')
    if proof is None:return dict(fraction=None,status='native_read_proof_missing')
    observed={str(Path(p).resolve()) for p in proof.get('observed_paths',[])}
    box=region['bbox'];total=(box[2]-box[0])*(box[3]-box[1])
    if str(Path(region['image']).resolve()) in observed:
        return dict(fraction=1.,status='whole_region_image_opened',source_pixels=total)
    boxes=[view['source_bbox'] for view in region['views'] if str(Path(view['path']).resolve()) in observed]
    for a,b,c,d in boxes:
        if not box[0]<=a<c<=box[2] or not box[1]<=b<d<=box[3]:raise ValueError('Vue hors région')
    seen=union_area(boxes)
    return dict(fraction=seen/total,status='native_detail_views',source_pixels=total,observed_pixels=seen,
                overview_required=False)
