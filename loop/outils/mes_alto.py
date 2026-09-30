import sys, glob, os, statistics
sys.path.insert(0,'/home/user/BBVLM/loop/outils'); sys.path[:0]=['/home/user/BBVLM/src','/home/user/BBVLM/src/boxers']
from lxml import etree
from segeval import evalue
from recherche import mesure
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
def lignes_page(p):
    r=etree.parse(p).getroot(); N={'p':r.tag.split('}')[0][1:]}; out=[]
    for tl in r.iter('{%s}TextLine'%N['p']):
        pts=[tuple(map(int,q.split(','))) for q in tl.find('p:Coords',N).get('points').split()]
        out.append((min(a for a,_ in pts),min(b for _,b in pts),max(a for a,_ in pts),max(b for _,b in pts)))
    return out
def lignes_alto(p):
    r=etree.parse(p).getroot(); ns=r.tag.split('}')[0][1:]; out=[]
    for tl in r.iter('{%s}TextLine'%ns):
        if tl.get('HPOS') is None: continue
        x,y,w,h=(int(float(tl.get(k))) for k in ('HPOS','VPOS','WIDTH','HEIGHT')); out.append((x,y,x+w,y+h))
    return out
fic=sys.argv[1] if len(sys.argv)>1 else 'page.alto.xml'
L=[];R=[]
for d in sorted(glob.glob(S+'/o0[789]/*/')+glob.glob(S+'/o1[0-8]/*/')+glob.glob(S+'/o2[345]/*/')):
    if not os.path.exists(d+fic): continue
    s=evalue(lignes_page(d+'page.xml'), lignes_alto(d+fic)); m=mesure(d+fic, d+'page.xml')
    L.append((s['rappel'],d.split('/')[-2][:12])); R.append((m['rappel'],d.split('/')[-2][:12]))
print('pages',len(L),'| lignes rappel méd',round(statistics.median(x for x,_ in L),3),'≥0,95:',sum(x>=.95 for x,_ in L),'pires',sorted(L)[:3])
print('recherche rappel méd',round(statistics.median(x for x,_ in R),3),'≥0,95:',sum(x>=.95 for x,_ in R),'pires',sorted(R)[:3])
