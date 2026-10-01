"""E0 — instrumentation Qwen3-VL-2B (CPU) : trace tokens↔offsets, grille des patches, parité native, coût.
usage : python e0.py A1_DIR N_BLOCS SORTIE.jsonl"""
import json, sys, time, resource, math
import numpy as np, torch
from PIL import Image
from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
Q = '/tmp/claude-0/-home-user-BBVLM/84210bd8-ec20-5b45-a7f8-f35608b01c8d/scratchpad/qwen/Qwen3-VL-2B'
CONSIGNE = 'Transcribe the printed text in this image exactly, line by line, keeping historical spelling and punctuation.'
torch.manual_seed(17); torch.set_num_threads(4)
proc = AutoProcessor.from_pretrained(Q)
model = Qwen3VLForConditionalGeneration.from_pretrained(Q, dtype=torch.float32).eval()
vis = model.model.visual
CAP = {}
def crochet(mod, args): CAP['pre_merger'] = args[0].detach().clone()
def complete(img, f=32):
    """complément blanc à droite/en bas jusqu'à un multiple de 32 : transformation crop→entrée = identité (aucun ré-échantillonnage)"""
    W, H = img.size; W2, H2 = -(-W // f) * f, -(-H // f) * f
    if W2 * H2 < 65536: H2 = -(-65536 // W2 // f) * f                       # minimum du processor (sinon agrandissement)
    while W2 * H2 < 65536: H2 += f
    if (W2, H2) == (W, H): return img
    n = Image.new('RGB', (W2, H2), (255, 255, 255)); n.paste(img, (0, 0)); return n
def entrees(img, texte):
    msgs = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': CONSIGNE}]},
            {'role': 'assistant', 'content': [{'type': 'text', 'text': texte}]}]
    s = proc.apply_chat_template(msgs, tokenize=False)
    return proc(text=[s], images=[img], return_tensors='pt'), s
def trace(ids, texte):
    """positions des tokens de la réponse et leurs offsets de caractères dans texte (vérifiée par reconstruction exacte)"""
    tok = proc.tokenizer
    enc = tok(texte, add_special_tokens=False, return_offsets_mapping=True)
    sub = enc['input_ids']; L = ids.tolist()
    debut = next((i for i in range(len(L) - len(sub) + 1) if L[i:i + len(sub)] == sub), None)
    if debut is None: return None
    off = [tuple(o) for o in enc['offset_mapping']]
    ok = tok.decode(sub) == texte and ''.join(texte[a:b] for a, b in off) == texte.replace('', '')[:]
    return {'debut': debut, 'offsets': off, 'reconstruction_exacte': tok.decode(sub) == texte}
def grille(pv, thw, img_redim):
    """reconstruit l'image normalisée depuis pixel_values selon l'ordre supposé [h/m][w/m][m][m] ; renvoie l'écart max"""
    t, h, w = (int(x) for x in thw); m, P, T = 2, 16, 2
    x = pv.reshape(t, h // m, w // m, m, m, 3, T, P, P)
    x = x.permute(0, 6, 5, 1, 3, 7, 2, 4, 8).reshape(t * T, 3, h * P, w * P)[0]
    ref = torch.tensor(np.asarray(img_redim, dtype=np.float32) / 255.).permute(2, 0, 1)
    ref = (ref - 0.5) / 0.5
    return float((x - ref).abs().max())
def main(a1, n, sortie):
    M = {json.loads(l)['id']: json.loads(l) for l in open(a1 + '/manifest.jsonl', encoding='utf-8')}
    ids = json.load(open(a1 + '/debug64.json'))[:n]
    out = open(sortie, 'w')
    for bid in ids:
        m = M[bid]; img = complete(Image.open(f'{a1}/crops/{bid}.png').convert('RGB'))
        x, s = entrees(img, m['texte'])
        thw = x['image_grid_thw'][0]; H, W = int(thw[1]) * 16, int(thw[2]) * 16
        e_grille = grille(x['pixel_values'], thw, img)
        tr = trace(x['input_ids'][0], m['texte'])
        t0 = time.time()
        with torch.no_grad(): ref = model(**x).logits
        t_nat = time.time() - t0
        h = vis.merger.register_forward_pre_hook(crochet)
        t0 = time.time()
        with torch.no_grad(): o = model(**x, output_hidden_states=True)
        t_ins = time.time() - t0; h.remove()
        parite = float((o.logits - ref).abs().max())
        # mots dont la fin tombe au milieu d'un token
        coupes = 0
        if tr:
            fins = {b for _, b in tr['offsets']}
            coupes = sum(1 for oc in m['occurrences'] if oc['fin'] not in fins)
        r = {'id': bid, 'crop_hw': [img.height, img.width], 'entree_hw': [H, W], 'patches': int(thw[1] * thw[2]),
             'pre_merger': list(CAP['pre_merger'].shape), 'ecart_grille': e_grille, 'trace': bool(tr), 'reconstruction': tr and tr['reconstruction_exacte'],
             'mots': len(m['occurrences']), 'mots_coupes_mi_token': coupes, 'parite_logits_max': parite, 's_natif': round(t_nat, 1), 's_instrumente': round(t_ins, 1),
             'rss_go': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2), 'tokens': int(x['input_ids'].shape[1])}
        out.write(json.dumps(r) + '\n'); out.flush(); print(r, flush=True)
if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
