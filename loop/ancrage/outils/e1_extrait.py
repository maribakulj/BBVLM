"""E1 — extraction (E1_PROTOCOLE.md). usage :
  python e1_extrait.py tetes A1_DIR SORTIE_DIR          # debug64 (train) : choix des 8 têtes G1a + ACP 256
  python e1_extrait.py extrait A1_DIR SORTIE_DIR [part] # tous les blocs : ACP fine, états L14/L28, boîtes G1a"""
import json, sys, os, time
import numpy as np, torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e0 import complete, CONSIGNE
Q = '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/qwen/Qwen3-VL-2B'
COUCHES = (14, 28)
torch.manual_seed(17); torch.set_num_threads(int(os.environ.get('FILS', '4')))
proc = AutoProcessor.from_pretrained(Q)
model = Qwen3VLForConditionalGeneration.from_pretrained(Q, dtype=getattr(torch, os.environ.get('DTYPE', 'bfloat16')), attn_implementation={'text_config': 'eager', 'vision_config': 'sdpa', '': 'eager'}).eval()
IMG = model.config.image_token_id
CAP = {}
def pre_merger(mod, args): CAP['fine'] = args[0].detach()
model.model.visual.merger.register_forward_pre_hook(pre_merger)
def crochet_attn(i):
    def f(mod, args, out):
        w = out[1] if isinstance(out, tuple) and len(out) > 1 else None
        if w is not None and 'rows' in CAP: CAP['attn'][i] = w[0][:, CAP['rows']][:, :, CAP['cols']].detach().float()
    return f
for i, lay in enumerate(model.model.language_model.layers): lay.self_attn.register_forward_hook(crochet_attn(i))
def prepare(m, a1):
    img = complete(Image.open(f"{a1}/crops/{m['id']}.png").convert('RGB'))
    msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': CONSIGNE}]},
            {'role': 'assistant', 'content': [{'type': 'text', 'text': m['texte']}]}]
    x = proc(text=[proc.apply_chat_template(msgs, tokenize=False)], images=[img], return_tensors='pt')
    ids = x['input_ids'][0].tolist(); enc = proc.tokenizer(m['texte'], add_special_tokens=False, return_offsets_mapping=True)
    sub = enc['input_ids']; d = next(i for i in range(len(ids) - len(sub) + 1) if ids[i:i + len(sub)] == sub)
    off = enc['offset_mapping']
    rows = [d + next(k for k, (a, b) in enumerate(off) if a < o['fin'] <= b) for o in m['occurrences']]
    cols = [i for i, t in enumerate(ids) if t == IMG]
    return x, rows, cols
def passe(m, a1):
    x, rows, cols = prepare(m, a1); CAP.clear(); CAP['rows'] = rows; CAP['cols'] = cols; CAP['attn'] = {}
    with torch.no_grad(): o = model(**x, output_hidden_states=True)
    thw = x['image_grid_thw'][0].tolist()
    etats = {c: o.hidden_states[c][0, rows].float().half().numpy() for c in COUCHES}
    return CAP['fine'].float().numpy(), {c: v.astype(np.float16) if v.dtype != np.float16 else v for c, v in etats.items()}, CAP['attn'], thw
def cellules(o, m, gh, gw):
    """masque des cellules fusionnées (32 px) dont le centre tombe dans la boîte VT du mot (repère crop)"""
    x0, y0 = m['crop'][0], m['crop'][1]; b = o['boite_page']; bx0, by0, bx1, by1 = b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0
    cy = (np.arange(gh) + .5) * 32; cx = (np.arange(gw) + .5) * 32
    return ((cy[:, None] >= by0) & (cy[:, None] < by1) & (cx[None] >= bx0) & (cx[None] < bx1)).reshape(-1)
def boite_g1a(carte, gh, gw):
    c = carte.reshape(gh, gw); mx = c.max(); s = c >= .5 * mx
    r0, c0 = np.unravel_index(c.argmax(), c.shape); vu = {(r0, c0)}; pile = [(r0, c0)]
    while pile:
        r, q = pile.pop()
        for dr, dq in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = r + dr, q + dq
            if 0 <= a < gh and 0 <= b < gw and s[a, b] and (a, b) not in vu: vu.add((a, b)); pile.append((a, b))
    rs = [r for r, _ in vu]; qs = [q for _, q in vu]
    return [min(qs) * 32, min(rs) * 32, (max(qs) + 1) * 32, (max(rs) + 1) * 32]
def main():
    mode, a1, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    M = {json.loads(l)['id']: json.loads(l) for l in open(a1 + '/manifest.jsonl', encoding='utf-8')}
    if mode == 'tetes':
        ids = json.load(open(a1 + '/debug64.json')); score = None; n = 0; F = []
        for bid in ids:
            m = M[bid]; fine, _, attn, thw = passe(m, a1); gh, gw = thw[1] // 2, thw[2] // 2
            F.append(fine[np.random.RandomState(17).choice(len(fine), min(len(fine), 400), replace=False)])
            A = np.stack([attn[i].numpy() for i in sorted(attn)])           # (couches, têtes, mots, cellules)
            if score is None: score = np.zeros(A.shape[:2])
            for k, o in enumerate(m['occurrences']):
                cm = cellules(o, m, gh, gw)
                if cm.any(): score += A[:, :, k][:, :, cm].sum(-1) / A[:, :, k].sum(-1).clip(1e-9); n += 1
            print(bid, flush=True)
        score /= n; top = np.dstack(np.unravel_index(np.argsort(-score, axis=None)[:8], score.shape))[0].tolist()
        X = np.concatenate(F).astype(np.float64); mu = X.mean(0); _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
        np.savez(out + '/acp.npz', mu=mu.astype(np.float32), V=Vt[:256].astype(np.float32))
        json.dump({'tetes': top, 'scores_top': [float(score[a, b]) for a, b in top], 'mots': n,
                   'variance_expliquee_256': float(((X - mu) @ Vt[:256].T).var(0).sum() / (X - mu).var(0).sum())}, open(out + '/tetes.json', 'w'))
        print(open(out + '/tetes.json').read())
    else:
        part = sys.argv[4] if len(sys.argv) > 4 else None
        acp = np.load(out + '/acp.npz'); T = json.load(open(out + '/tetes.json'))['tetes']
        import hashlib
        ordre = sorted(M, key=lambda b: ({'test': 0, 'dev': 1, 'train': 2}[M[b]['partition']], hashlib.sha256(b.encode()).hexdigest()))
        for bid in ordre:
            m = M[bid]
            if part and m['partition'] != part: continue
            f = f'{out}/{bid}.npz'
            if os.path.exists(f): continue
            t0 = time.time(); fine, etats, attn, thw = passe(m, a1); gh, gw = thw[1] // 2, thw[2] // 2
            carte = np.mean([attn[l].numpy()[h] for l, h in T], 0)               # (mots, cellules)
            g1a = np.array([boite_g1a(carte[k], gh, gw) for k in range(len(m['occurrences']))], dtype=np.int32)
            fp = ((fine - acp['mu']) @ acp['V'].T).astype(np.float16)
            np.savez_compressed(f, fine=fp, grille=np.array(thw[1:]), l14=etats[14], l28=etats[28], g1a=g1a)
            print(bid, m['partition'], round(time.time() - t0, 1), flush=True)
main()
