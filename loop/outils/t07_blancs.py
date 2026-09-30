import sys, json, os, glob
sys.path.insert(0,'/home/user/BBVLM/loop/outils')
os.environ['BBVLM_VUE_ADJ']='glyphe'
import bilan_adj
from bilan_adj import reblanc
from cer import score
S='/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad'
meta=json.load(open(S+'/t07/meta.json')); A=json.load(open(S+'/t07/resA.json')); B=json.load(open(S+'/t07/resB.json'))
parpage={}
for m in meta:
    t=m['texte']; a=A.get(m['image']); b=B.get(m['image'])
    if not a or not b: continue
    na=reblanc(t.replace(' ',''), a); nb=reblanc(t.replace(' ',''), b)
    if na==nb and na!=t:
        # T07b : seuls les blancs entre deux lettres sont repris ; ceux qui touchent une ponctuation restent les nôtres
        g=t.replace(' ','')
        def blancs(x):
            p=set(); k=0
            for ch in x:
                if ch==' ': p.add(k)
                else: k+=1
            return p
        bt,bn=blancs(t),blancs(na)
        lettre=lambda k: 0<k<len(g) and g[k-1].isalnum() and g[k].isalnum()
        # T07c : changement confirmé par le contexte local (2 lettres de chaque côté) dans les DEUX lectures
        def conf(k, avec):
            if k < 2 or k > len(g) - 2: return False
            ctx = g[k-2:k] + (' ' if avec else '') + g[k:k+2]
            return ctx in a and ctx in b
        fin=set(bt)
        for k in (bn - bt):
            if lettre(k) and conf(k, True): fin.add(k)
        for k in (bt - bn):
            if lettre(k) and conf(k, False): fin.discard(k)
        nv=''.join((' ' if i in fin else '')+c for i,c in enumerate(g)).strip()
        if nv!=t: parpage.setdefault(m['page'],{})[t]=nv
tot=[0,0]
for nom,ch in sorted(parpage.items()):
    d=glob.glob(S+'/o*/'+nom+'/')[0]
    lec=[x for x in ('p3i_final.txt','p3_final.txt') if os.path.exists(d+x)][0]
    lu=[l for l in open(d+lec).read().splitlines() if l.strip() and not l.startswith('#')]
    new=[ch.get(l,l) for l in lu]
    adj,_=bilan_adj.reference_adjugee(d)
    a_=score(adj,lu,'glyphe')['editions']; b_=score(adj,new,'glyphe')['editions']; tot[0]+=a_; tot[1]+=b_
    print(nom[:14], a_,'→',b_, '| changements', [(o[:30],n[:30]) for o,n in ch.items()][:8])
    open(d+'p3t07c_final.txt','w').write('\n'.join(new)+'\n')
print('total',tot)
