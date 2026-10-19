"""Attribution expérimentale de composantes natives aux baselines automatiques.

Aucun polygone humain ni texte n'est reçu. Une composante est gardée entière
ou reste non attribuée ; les pixels ne sont jamais découpés pour faire disparaître
une superposition de rectangles. Les petites marques peuvent suivre un corps
de lettre proche plutôt que la baseline de la ligne supérieure.
"""
from __future__ import annotations
import cv2
import numpy as np
from scipy.spatial import cKDTree


class BaselineInk:
    def __init__(self,gray,rows):
        if gray is None or gray.ndim!=2 or gray.dtype!=np.uint8:
            raise ValueError('Pixels natifs uint8 requis')
        if len({r['id'] for r in rows})!=len(rows):raise ValueError('Baselines dupliquées par ID')
        if any('text' in r or 'words' in r or not r.get('source','').startswith('kraken-blla/') for r in rows):
            raise ValueError('Seules les baselines du détecteur automatique sont autorisées')
        self.rows=rows;self.index={r['id']:i for i,r in enumerate(rows)}
        heights=np.array([r['bbox'][3]-r['bbox'][1] for r in rows],float)
        if not len(rows) or (heights<=0).any():raise ValueError('Lignes automatiques vides ou invalides')
        self.heights=heights;points=[];point_lines=[];curves=[];unsupported=[]
        for i,row in enumerate(rows):
            curve=np.asarray(row.get('baseline'),float)
            if curve.ndim!=2 or curve.shape[1]!=2 or len(curve)<2 or not np.isfinite(curve).all():
                raise ValueError('Baseline automatique absente/non finie')
            curve=curve[np.argsort(curve[:,0],kind='stable')]
            x=np.unique(curve[:,0]);y=np.array([curve[curve[:,0]==xx,1].mean() for xx in x])
            curves.append((x,y))
            if len(x)<2:
                unsupported.append(row['id'])
                continue
            xx=np.linspace(x[0],x[-1],max(2,int(np.ceil((x[-1]-x[0])/12))+1))
            points.extend(zip(xx,np.interp(xx,x,y)));point_lines.extend([i]*len(xx))
        self.curves=curves;self.unsupported=set(unsupported)
        tree=cKDTree(points) if points else None;point_lines=np.array(point_lines,dtype=int)
        window=max(15,int(float(np.median(heights))*.75)|1)
        binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV,window,12)
        _,labels,stats,centers=cv2.connectedComponentsWithStats(binary,8)
        self.labels=labels;self.stats=stats;self.owners=np.full(len(stats),-1,np.int32)
        is_body=np.zeros(len(stats),bool);ambiguous=0
        targets=np.array([(x+w/2,y+h) for x,y,w,h,area in stats[1:]],float).reshape(-1,2)
        nearest=tree.query(targets,k=min(24,len(points)))[1] if tree is not None else np.empty((len(targets),0),int)
        if nearest.ndim==1:nearest=nearest[:,None]
        for k,(x,y,w,h,area) in enumerate(stats[1:],1):
            if area<3:continue
            candidates=np.unique(point_lines[nearest[k-1]])
            choices=[]
            for li in candidates:
                cx,cy=curves[li];lh=heights[li]
                if not cx[0]-.5*lh<=x+w/2<=cx[-1]+.5*lh or h>1.3*lh or w>4*lh:continue
                distance=abs(y+h-float(np.interp(x+w/2,cx,cy)))/lh
                if distance>.6:continue
                # À distance identique, le support horizontal complet prime.
                key=(distance,-(cx[-1]-cx[0]),int(li))
                choices.append((key,int(li)))
            choices.sort()
            if len(choices)>1 and choices[1][0][0]-choices[0][0][0]<.08:
                ambiguous+=1
                continue
            if choices:
                li=choices[0][1];self.owners[k]=li
                is_body[k]=h>=.3*heights[li]
        # Accents/points : corps voisin en x et espace vertical limité. On ne
        # décompose pas une composante reliant réellement deux lignes.
        bodies=np.flatnonzero(is_body)
        linked=0
        if len(bodies):
            body_tree=cKDTree(centers[bodies])
            small=np.flatnonzero((np.arange(len(stats))>0)&(stats[:,4]>=3)&~is_body&
                                (stats[:,3]<.3*np.median(heights)))
            _,neighbors=body_tree.query(centers[small],k=min(12,len(bodies)))
            if neighbors.ndim==1:neighbors=neighbors[:,None]
            for si,k in enumerate(small):
                x,y,w,h,_=stats[k];best=None
                current=self.owners[k]
                if current>=0:
                    lh=heights[current];cx,cy=curves[current]
                    baseline=float(np.interp(x+w/2,cx,cy))
                    # Un point/trait au pied de sa ligne ne suit pas le haut
                    # d'une lettre voisine. Les traits longs ne sont pas des
                    # accents à rattacher à un corps de lettre.
                    if w>.35*lh or y-.05*lh<=baseline<=y+h+.15*lh:continue
                for bi in np.atleast_1d(neighbors[si]):
                    body=bodies[bi];a,b,c,d,_=stats[body];li=self.owners[body];lh=heights[li]
                    xgap=max(0,a-(x+w),x-(a+c));ygap=max(0,b-(y+h),y-(b+d))
                    if xgap>.22*lh or ygap>.35*lh:continue
                    # Une marque au-dessus d'un corps est proche de son sommet,
                    # une ponctuation est proche de son bas.
                    distance=(xgap+ygap+.15*abs(x+w/2-a-c/2))/lh
                    if best is None or distance<best[0]:best=(distance,int(li))
                if best is not None and best[1]!=self.owners[k]:
                    self.owners[k]=best[1];linked+=1
        area=stats[:,4];unassigned=np.flatnonzero((self.owners<0)&(np.arange(len(stats))>0)&(area>=3))
        self.audit=dict(version='native-components-automatic-baseline-v1',window=window,constant=12,
                        components=len(stats)-1,assigned_components=int(np.count_nonzero(self.owners>=0)),
                        unassigned_components=len(unassigned),unassigned_ink_pixels=int(area[unassigned].sum()),
                        small_marks_reassigned=linked,ambiguous_baseline_components=ambiguous,
                        total_ink_pixels=int(area[1:].sum()),unsupported_baseline_ids=unsupported,
                        lines=len(rows),criteria_met=False,promoted=False,
                        scope='experimental image-only component ownership; no independent certificate')

    def mask(self,lid,box):
        if lid not in self.index:raise ValueError('ID de baseline inconnu')
        x0,y0,x1,y1=map(int,box)
        if not 0<=x0<x1<=self.labels.shape[1] or not 0<=y0<y1<=self.labels.shape[0]:
            raise ValueError('Recadrage natif hors page')
        selected=self.owners[self.labels[y0:y1,x0:x1]]==self.index[lid]
        return selected.astype(np.uint8)*255,x0,y0

    def component_box(self,lid,source_box):
        """Inclut les composantes attribuées entières, sans déplacer une baseline."""
        if lid not in self.index:raise ValueError('ID de baseline inconnu')
        selected=self.stats[self.owners==self.index[lid]]
        if not len(selected):return list(source_box)
        x,y,w,h,_=selected.T
        a,b,c,d=source_box
        return [int(min(a,x.min())),int(min(b,y.min())),
                int(max(c,(x+w).max())),int(max(d,(y+h).max()))]

    def filter_mask(self,lid,mask,ox,oy):
        """Retire une composante locale entière seulement sur preuve étrangère.

        Au moins 95 % de ses pixels doivent coïncider avec des composantes
        natives, toutes attribuées à UN autre ID. Une composante mixte ou
        ambiguë reste entière. Ceci ne change aucun critère de refus final.
        """
        if lid not in self.index:raise ValueError('ID de baseline inconnu')
        if lid in self.unsupported:
            return (mask.copy(),ox,oy),dict(removed=[],removed_pixels=0,unsupported_baseline=True,
                                           original_mask_preserved=True)
        h,w=mask.shape
        if not 0<=ox<ox+w<=self.labels.shape[1] or not 0<=oy<oy+h<=self.labels.shape[0]:
            raise ValueError('Recadrage natif hors page')
        _,local,stats,_=cv2.connectedComponentsWithStats((mask>0).astype(np.uint8),8)
        owners=self.owners[self.labels[oy:oy+h,ox:ox+w]]
        keep=np.ones(len(stats),bool);keep[0]=False;removed=[]
        for k,(x,y,cw,ch,area) in enumerate(stats[1:],1):
            pixels=owners[y:y+ch,x:x+cw][local[y:y+ch,x:x+cw]==k]
            observed=pixels[pixels>=0];unique=np.unique(observed)
            if len(unique)==1 and unique[0]!=self.index[lid] and len(observed)>=.95*area:
                keep[k]=False;removed.append(dict(component=k,pixels=int(area),foreign_line=self.rows[unique[0]]['id']))
        return (keep[local].astype(np.uint8)*255,ox,oy),dict(removed=removed,removed_pixels=sum(x['pixels'] for x in removed))
