"""Isoler l'encre d'une ligne avant le CTC, sans créer de pixels sombres."""
import cv2
import numpy as np
from page_word_ownership import _trajectory


def owned_crop(gray,row,neighbors):
    x0,y0,x1,y1=map(int,row.get('reading_bbox',row['bbox']))
    crop=gray[y0:y1,x0:x1]
    h=y1-y0
    threshold,binary=cv2.threshold(crop,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    _,labels,stats,centers=cv2.connectedComponentsWithStats(binary,8)
    cx=centers[:,0]+x0;cy=centers[:,1]+y0
    distance=np.abs(cy-_trajectory(row)(cx))
    keep=np.ones(len(stats),bool);keep[0]=False
    keep &= stats[:,cv2.CC_STAT_AREA]>=max(3,int(h*h*.0005))
    for other in neighbors:
        if other['id']==row['id']:continue
        a,b,c,d=other.get('reading_bbox',other['bbox'])
        if c<=x0 or a>=x1 or b>y1+h or d<y0-h:continue
        competing=np.abs(cy-_trajectory(other)(cx))
        # Une composante indécise reste visible ; ne pas fabriquer un blanc
        # pour satisfaire le nombre de mots imposé.
        keep &= ~((cx>=a)&(cx<c)&(competing+max(2,h*.1)<distance))
    mask=keep[labels]
    clean=np.where(mask,crop,255).astype(np.uint8)
    return clean,dict(method='otsu_neighbor_baseline_component_filter_v2',threshold=float(threshold),
                      retained_dark_pixels=int(mask.sum()),
                      removed_dark_pixels=int(((binary>0)&~mask).sum()),
                      source_box=[x0,y0,x1,y1],new_dark_pixels=False)


class OwnedLineBoxer:
    """Adaptateur expérimental du même CTC forcé, après filtrage spatial."""
    def __init__(self,gray,rows,boxer):
        self.gray=gray.copy();self.rows=rows;self.boxer=boxer;self.current=None
        self.last_alignment=None;self.last_char_positions=None

    def boxes(self,gray,line):
        row=self.current
        clean,proof=owned_crop(gray,row,self.rows)
        x0,y0,x1,y1=proof['source_box']
        self.gray[y0:y1,x0:x1]=clean
        try:
            result=self.boxer.boxes(self.gray,line)
            self.last_alignment={**self.boxer.last_alignment,'input_ink_filter':proof}
            self.last_char_positions=self.boxer.last_char_positions
            return result
        finally:
            self.gray[y0:y1,x0:x1]=gray[y0:y1,x0:x1]
