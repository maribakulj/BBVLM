"""Essai conservateur de complément de segmentation, sans référence.

Les rectangles de la première passe restent exacts. La seconde passe ne peut
ajouter qu'une ligne dont au moins 90 % de l'encre native n'est couverte par
aucun rectangle déjà conservé. Les décisions rejetées restent dans l'audit.
Cette politique expérimentale ne constitue pas une certification des glyphes.
"""
from __future__ import annotations
from copy import deepcopy
import math
import cv2
import numpy as np


def _bounds(row, width, height):
    box=row['bbox']
    if len(box)!=4 or not all(math.isfinite(v) for v in box):
        raise ValueError('Rectangle de segmentation non fini')
    x0,y0,x1,y1=box
    if not 0<=x0<x1<=width or not 0<=y0<y1<=height:
        raise ValueError('Rectangle de segmentation hors page')
    return math.floor(x0),math.floor(y0),math.ceil(x1),math.ceil(y1)


def _same_line(a,b):
    x0,y0,x1,y1=a;u0,v0,u1,v1=b
    xov=max(0,min(x1,u1)-max(x0,u0))/min(x1-x0,u1-u0)
    yov=max(0,min(y1,v1)-max(y0,v0))/min(y1-y0,v1-v0)
    center=abs((y0+y1-v0-v1)/2)
    return xov>=.8 and yov>=.5 and center<=.5*min(y1-y0,v1-v0)


def fuse(gray,primary,supplement,novel_fraction=.9,minimum_ink=8):
    if gray is None or gray.ndim!=2 or gray.dtype!=np.uint8:
        raise ValueError('Image native uint8 en niveaux de gris requise')
    if not 0<novel_fraction<=1 or minimum_ink<1:
        raise ValueError('Politique de complément invalide')
    if len({r['id'] for r in primary})!=len(primary) or len({r['id'] for r in supplement})!=len(supplement):
        raise ValueError('IDs source dupliqués')
    height,width=gray.shape
    # Un seul masque natif : les différences de binarisation des recadrages
    # ne doivent pas être prises pour de l'encre nouvelle.
    ink=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                             cv2.THRESH_BINARY_INV,75,12)>0
    covered=np.zeros(gray.shape,dtype=bool)
    output=deepcopy(primary);audit=[]
    for row in output:
        x0,y0,x1,y1=_bounds(row,width,height)
        covered[y0:y1,x0:x1]=True
        row['fusion_origin']={'pass':'primary','id':row['id']}
    for candidate in sorted(supplement,key=lambda r:(r['bbox'][1],r['bbox'][0],r['id'])):
        x0,y0,x1,y1=_bounds(candidate,width,height)
        view=ink[y0:y1,x0:x1]
        count=int(np.count_nonzero(view))
        novel=int(np.count_nonzero(view & ~covered[y0:y1,x0:x1]))
        fraction=novel/count if count else 0.
        duplicate=next((r for r in output if _same_line(candidate['bbox'],r['bbox'])),None)
        reason=('same_line_geometry' if duplicate else 'insufficient_native_ink' if count<minimum_ink
                else 'native_ink_already_covered' if fraction<novel_fraction else 'novel_native_ink')
        accepted=reason=='novel_native_ink'
        audit.append(dict(supplement_id=candidate['id'],bbox=list(candidate['bbox']),
                          ink_pixels=count,novel_pixels=novel,novel_fraction=fraction,
                          accepted=accepted,reason=reason,
                          canonical_origin=duplicate['fusion_origin'] if duplicate else None))
        if accepted:
            row=deepcopy(candidate)
            row['fusion_origin']={'pass':'supplement','id':candidate['id']}
            output.append(row);covered[y0:y1,x0:x1]=True
    output.sort(key=lambda r:(r['bbox'][1],r['bbox'][0],r['fusion_origin']['pass'],r['id']))
    for index,row in enumerate(output,1):row['id']=f'L{index:04d}'
    return output,dict(primary=len(primary),supplement=len(supplement),
                       added=sum(a['accepted'] for a in audit),decisions=audit,
                       policy=dict(novel_fraction=novel_fraction,minimum_ink=minimum_ink,
                                   native_threshold=dict(window=75,constant=12)),
                       scope='source-only conservative segmentation complement; primary coordinates preserved',
                       promoted=False,criteria_met=False)
