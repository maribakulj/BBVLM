import sys, glob, numpy as np
sys.path.insert(0,'/home/user/BBVLM/loop/outils')
from eval_alto import mots_alto, mots_page
from segeval import iou
from scipy.optimize import linear_sum_assignment
for d in sys.argv[1:]:
    P,R=mots_alto(d+'/page.alto.xml'),mots_page(d+'/page.xml')
    M=np.array([[iou(r[1],p[1]) for p in P] for r in R]); a,b=linear_sum_assignment(-M)
    ok=[(R[i],P[j],M[i,j]) for i,j in zip(a,b) if R[i][0]==P[j][0] and M[i,j]>.3]
    h=np.array([r[1][3]-r[1][1] for r,_,_ in ok])
    dt=np.array([(p[1][1]-r[1][1]) for r,p,_ in ok])/h; db=np.array([(p[1][3]-r[1][3]) for r,p,_ in ok])/h
    dl=np.array([(p[1][0]-r[1][0]) for r,p,_ in ok])/h; dr=np.array([(p[1][2]-r[1][2]) for r,p,_ in ok])/h
    io=np.array([x for _,_,x in ok])
    f=lambda v: f"{np.median(v):+.2f}[{np.percentile(v,10):+.2f},{np.percentile(v,90):+.2f}]"
    print(d.rstrip('/').split('/')[-1][:12], 'n',len(ok),'/',len(R),'iou',f"{np.median(io):.3f}",'haut',f(dt),'bas',f(db),'g',f(dl),'d',f(dr),'hVT',int(np.median(h)))
