import glob, json, time, os, sys
from ultralytics import YOLO
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
m=YOLO(S+'/yolo/doclaynet26l.pt')
NOMS={1:'Caption',2:'Footnote',3:'Formula',4:'List-item',5:'Page-footer',6:'Page-header',7:'Picture',8:'Section-header',9:'Table',10:'Text'}
ds=sorted(glob.glob(S+'/o0[789]/*/')+glob.glob(S+'/o1[0-8]/*/')+glob.glob(S+'/o2[3-8]/*/'))
for d in ds:
    if os.path.exists(d+'yolo_zones.json') or not os.path.exists(d+'page.png'): continue
    t=time.time(); r=m.predict(d+'page.png',imgsz=1024,conf=0.25,device='cpu',verbose=False)[0]
    z=[{'classe':NOMS.get(int(c),'?'),'conf':round(float(p),3),'bbox':[round(float(v)) for v in b]} for b,c,p in zip(r.boxes.xyxy,r.boxes.cls,r.boxes.conf) if int(c)!=0]
    json.dump({'zones':z,'s':round(time.time()-t,2)},open(d+'yolo_zones.json','w'))
    print(d.split('/')[-2][:14],len(z),round(time.time()-t,1),flush=True)
