"""Réattribuer les composantes d'encre aux lignes avant de juger les collisions.

Les frontières horizontales restent celles du CTC. Les enveloppes verticales
viennent des pixels attribués à une ligne par proximité de sa trajectoire.
Les chevauchements de rectangles sont audités par les pixels effectivement
retenus, sans transformer un simple chemin CTC en certificat de lecture.
"""
from copy import deepcopy
import cv2
import numpy as np


VERSION = 'line-component-ownership-v3'


def _trajectory(row):
    box = row.get('reading_bbox', row['bbox'])
    points = np.asarray(row.get('baseline', []), dtype=float)
    if len(points) >= 2:
        points = points[np.argsort(points[:, 0])]
        def baseline(x):
            return np.interp(x, points[:, 0], points[:, 1])
        offsets = [(w['y0']+w['y1'])/2-baseline((w['x0']+w['x1'])/2)
                   for w in row.get('words', []) if w['y1']-w['y0'] >= (box[3]-box[1])*.3]
        offset = float(np.median(offsets)) if offsets else -(box[3]-box[1])*.4
        return lambda x: baseline(x)+offset
    return lambda x: np.zeros_like(x, dtype=float)+(box[1]+box[3])/2


def refine(gray, annotations, contrast='adaptive'):
    if contrast not in ('adaptive','otsu'):raise ValueError('Contraste inconnu')
    rows = deepcopy(annotations)
    placed = [r for r in rows if r.get('words')]
    trajectories = {r['id']: _trajectory(r) for r in placed}
    masks = {}
    failed=[]
    for row in placed:
        x0,y0,x1,y1 = map(int,row.get('reading_bbox',row['bbox']))
        h = y1-y0
        crop = gray[y0:y1,x0:x1]
        if min(crop.shape) < 3:
            failed.append(row['id']);continue
        if contrast=='otsu':
            _,binary=cv2.threshold(crop,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        else:
            binary = cv2.adaptiveThreshold(crop,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV,max(15,int(h*.75)|1),12)
        n, labels, stats, centers = cv2.connectedComponentsWithStats(binary,8)
        cx=centers[:,0]+x0;cy=centers[:,1]+y0
        distance=np.abs(cy-trajectories[row['id']](cx))
        owners=np.ones(n,dtype=bool);owners[0]=False
        owners &= (stats[:,cv2.CC_STAT_AREA] >= max(3,int(h*h*.0005)))
        owners &= stats[:,cv2.CC_STAT_WIDTH] <= 4*h
        for other in placed:
            if other['id']==row['id']:continue
            a,b,c,d=other.get('reading_bbox',other['bbox'])
            if c<=x0 or a>=x1 or b>y1+h or d<y0-h:continue
            competing=np.abs(cy-trajectories[other['id']](cx))
            inside=(cx>=a)&(cx<c)
            closer=competing<distance
            if other['id']<row['id']:closer |= competing==distance
            owners &= ~(inside&closer)
        owned=owners[labels]
        good=True
        for wi,word in enumerate(row['words']):
            left=max(0,word['x0']-x0);right=min(x1-x0,word['x1']-x0+1)
            piece=owned[:,left:right]
            yy,xx=np.where(piece)
            word['bbox_before_ownership']=[word[k] for k in ('x0','y0','x1','y1')]
            if not len(xx):
                word['ownership_status']='no_owned_ink';good=False;continue
            # Aucun pixel nouveau, aucune interpolation de boîte.
            word.update(x0=int(xx.min())+x0+left,x1=int(xx.max())+x0+left,
                        y0=int(yy.min())+y0,y1=int(yy.max())+y0,
                        owned_ink_pixels=int(len(xx)),ownership_status='observed')
            masks[(row['id'],wi)]=(piece.copy(),x0+left,y0)
        row['ink_ownership_version']=VERSION
        row['ink_ownership_complete']=good
        if not good:failed.append(row['id'])
    # Les seuils adaptatifs de deux crops peuvent morceler différemment un
    # même glyphe. Réconcilier leurs pixels communs par la même trajectoire
    # globale ; les égalités restent des conflits, elles ne sont pas masquées.
    redistributed=0;unowned=[]
    active=[]
    for row,wi,word in sorted(((r,i,w) for r in placed for i,w in enumerate(r['words'])),key=lambda t:t[2]['y0']):
        active=[entry for entry in active if entry[2]['y1']>=word['y0']]
        for other,oi,box in active:
            if row['id']==other['id']:continue
            x0=max(box['x0'],word['x0']);x1=min(box['x1'],word['x1'])+1
            y0=max(box['y0'],word['y0']);y1=min(box['y1'],word['y1'])+1
            if x1<=x0 or y1<=y0:continue
            a=masks.get((other['id'],oi));b=masks.get((row['id'],wi))
            if a is None or b is None:continue
            am,ax,ay=a;bm,bx,by=b
            av=am[y0-ay:y1-ay,x0-ax:x1-ax];bv=bm[y0-by:y1-by,x0-bx:x1-bx]
            yy,xx=np.where(av&bv)
            if not len(xx):continue
            da=np.abs(yy+y0-trajectories[other['id']](xx+x0))
            db=np.abs(yy+y0-trajectories[row['id']](xx+x0))
            a_wins=da+1<db;b_wins=db+1<da
            ambiguous=~(a_wins|b_wins)
            if ambiguous.any():
                # Les pixels à mi-distance peuvent être la pointe d'une
                # lettre clairement rattachée à une seule ligne. Examiner
                # sa composante entière dans l'union des deux observations.
                ux=min(ax,bx);uy=min(ay,by)
                union=np.zeros((max(ay+am.shape[0],by+bm.shape[0])-uy,
                                max(ax+am.shape[1],bx+bm.shape[1])-ux),np.uint8)
                union[ay-uy:ay-uy+am.shape[0],ax-ux:ax-ux+am.shape[1]]|=am
                union[by-uy:by-uy+bm.shape[0],bx-ux:bx-ux+bm.shape[1]]|=bm
                _,labels,stats,centers=cv2.connectedComponentsWithStats(union,8)
                ids=labels[yy+y0-uy,xx+x0-ux]
                cx=centers[ids,0]+ux;cy=centers[ids,1]+uy
                ac=np.abs(cy-trajectories[other['id']](cx))
                bc=np.abs(cy-trajectories[row['id']](cx))
                margin=max(2.,min(am.shape[0],bm.shape[0])*.1)
                a_wins|=ambiguous&(ac+margin<bc)
                b_wins|=ambiguous&(bc+margin<ac)
            bv[yy[a_wins],xx[a_wins]]=False
            av[yy[b_wins],xx[b_wins]]=False
            redistributed+=int(a_wins.sum()+b_wins.sum())
            # Quelques pixels à mi-distance (jambage qui touche une hampe) :
            # n'appartenant clairement à aucune des deux lignes, ils ne sont
            # attribués à AUCUNE. Rien n'est ajouté ; les deux mots gardent
            # leur encre propre. Au-delà d'une infime part, le conflit reste.
            left=~(a_wins|b_wins)
            if left.any() and left.sum()<=min(20,.02*min(int(am.sum()),int(bm.sum()))):
                av[yy[left],xx[left]]=False;bv[yy[left],xx[left]]=False
                unowned.append(dict(first=[other['id'],oi],second=[row['id'],wi],pixels=int(left.sum())))
        active.append((row,wi,word))
    for row in placed:
        for wi,word in enumerate(row['words']):
            saved=masks.get((row['id'],wi))
            if saved is None:continue
            mask,x,y=saved;yy,xx=np.where(mask)
            if not len(xx):
                word['ownership_status']='no_owned_ink';row['ink_ownership_complete']=False
                if row['id'] not in failed:failed.append(row['id'])
                continue
            word.update(x0=int(xx.min())+x,x1=int(xx.max())+x,
                        y0=int(yy.min())+y,y1=int(yy.max())+y,owned_ink_pixels=int(len(xx)))
        # Les enveloppes restent des unions de boîtes observées.
        box=row['bbox'];ws=row['words']
        row['bbox']=[min(box[0],min(w['x0'] for w in ws)),min(box[1],min(w['y0'] for w in ws)),
                     max(box[2],max(w['x1']+1 for w in ws)),max(box[3],max(w['y1']+1 for w in ws))]
    active=[];overlaps=[];safe=[];conflicts=[]
    for row,wi,word in sorted(((r,i,w) for r in placed for i,w in enumerate(r['words'])),key=lambda t:t[2]['y0']):
        active=[entry for entry in active if entry[2]['y1']>=word['y0']]
        for other,oi,box in active:
            if row['id']==other['id']:continue
            x0=max(box['x0'],word['x0']);x1=min(box['x1'],word['x1'])+1
            y0=max(box['y0'],word['y0']);y1=min(box['y1'],word['y1'])+1
            if x1<=x0 or y1<=y0:continue
            pair=dict(first=[other['id'],oi],second=[row['id'],wi])
            a=masks.get((other['id'],oi));b=masks.get((row['id'],wi))
            shared=None
            if a is not None and b is not None:
                am,ax,ay=a;bm,bx,by=b
                shared=int(np.count_nonzero(am[y0-ay:y1-ay,x0-ax:x1-ax]&bm[y0-by:y1-by,x0-bx:x1-bx]))
            pair['shared_owned_ink_pixels']=shared;overlaps.append(pair)
            (safe if shared==0 else conflicts).append(pair)
        active.append((row,wi,word))
    return rows,dict(version=VERSION,contrast=contrast,lines=len(placed),failed_lines=failed,
                     reconciled_shared_pixels=redistributed,
                     midway_pixels_left_unowned=unowned,
                     rectangle_overlaps=overlaps,safe_overlaps=safe,conflicts=conflicts,
                     text_modified=False,ctc_horizontal_partitions_preserved=True)
