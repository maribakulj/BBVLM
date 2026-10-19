"""B25 — alignement forcé CTC : on impose le texte, on ne le demande pas.

Défaut de `ctc.py`, signalé et vérifié : il demandait d'abord au recognizer
*quelle* transcription il préfère (`rec.prediction`), puis raccrochait cette
lecture au texte du VLM par `difflib.SequenceMatcher`. Ce n'est pas de
l'alignement forcé, c'est de l'appariement de deux lectures — et quand elles
divergent, il n'y a plus rien à quoi s'accrocher. D'où les 32 lignes en échec,
toutes sur des lignes dégradées (`bles. L r s personnes dont ces chemins des`).

L'alignement forcé ne pose jamais cette question. Il prend la matrice de
probabilités du réseau, construit le graphe CTC de la transcription **imposée** —
blank, c1, blank, c2, blank… avec les transitions propres aux caractères
répétés — et cherche par Viterbi le chemin qui explique le mieux CE texte. Le
réseau peut n'avoir que 0,42 sur « e » à une frame : le chemin global s'en
accommode, là où un décodage glouton aurait produit autre chose.

C'est la méthode que PERO applique dans `core/force_alignment.py`, et elle est
documentée — ce n'est pas une trouvaille de ce dépôt.

Ce qui reste propre à BBVLM et qu'on garde : les positions CTC servent de
**séparateurs**, pas de bords de glyphes (B19 : IoU 0,635 → 0,829 sans déplacer
une frontière), et l'étendue vient de l'encre observée.
"""
from __future__ import annotations
import os
import hashlib
from pathlib import Path
import re
import unicodedata
import numpy as np
import torch
import ink
from ink import alignment_mask

CHEMIN = os.path.expanduser(
    '~/Library/Application Support/htrmopo/d96caf7a-122e-5576-ab2b-a246c4e64221/'
    'catmus-print-fondue-large.mlmodel')
FALLBACK = os.path.expanduser('~/Library/Application Support/htrmopo/'
    '71d9d381-c404-53dc-97a2-a33024db3f57/german_print.mlmodel')
_M = None
IMPLEMENTATION_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def modele():
    global _M
    if _M is None:
        from kraken.lib import models
        _M = models.load_any(CHEMIN)
    return _M


PAD = 16


def _ligne_tenseur(gray, line, model):
    """Recadrage rectangulaire : conserve une transformation x explicite.

    Pas de rectification non linéaire, dont les positions ne pourraient pas
    être transportées par une simple règle de trois.
    """
    from PIL import Image
    from kraken import rpred
    x0, y0, x1, y1 = line.line_box
    if not (0 <= x0 < x1 <= gray.shape[1] and 0 <= y0 < y1 <= gray.shape[0]):
        raise ValueError('boîte de ligne hors image')
    crop = Image.fromarray(gray[y0:y1, x0:x1]).convert('L')
    tr = rpred.ImageInputTransforms(
        batch=1, height=model.nn.input[2], width=model.nn.input[3],
        channels=model.nn.input[1], pad=(PAD, 0), valid_norm=False)
    return tr(crop).unsqueeze(0)


def frame_x(frame, frames, input_width, x0, crop_width, pad=PAD):
    """Position au centre d'une frame ; soustrait les marges du réseau."""
    if frames <= 0 or input_width <= 2*pad:
        raise ValueError('dimensions de treillis invalides')
    return x0 + ((frame+0.5)*input_width/frames-pad)*crop_width/(input_width-2*pad)


VISUAL_EQUIVALENTS = {'º': ('°', 'o'), '°': ('º', 'o'), 'ª': ('a',), '′': ("'",), '″': ('"',)}


def encode_text(codec, texte, visual_fallback=False):
    """Encode sans perdre de caractères ; NFD accepté si équivalent au NFC.

    Les séquences multicaractères du codec sont conservées. Les codes d'une
    ligature sont attribués à toutes ses positions dans la transcription.
    """
    codes, positions = [], []
    i = 0
    keys = sorted((key for key in codec.c2l if key), key=len, reverse=True)
    while i < len(texte):
        key = next((key for key in keys if texte.startswith(key, i)), None)
        if key is not None:
            labels = list(codec.c2l[key])
            original_positions = tuple(range(i, i+len(key)))
            step = len(key)
        else:
            decomposed = unicodedata.normalize('NFD', texte[i])
            if decomposed == texte[i] and visual_fallback:
                # Glyphe absent du modèle mais de même dessin qu'un autre
                # (« 90º » / « 90° », « nº ») : seul l'ENCODAGE pour le
                # placement emprunte ce code ; le texte livré reste inchangé.
                decomposed = next((alt for alt in [unicodedata.normalize('NFKC', texte[i]),
                                                   *VISUAL_EQUIVALENTS.get(texte[i], ())]
                                   if alt != texte[i] and alt and all(
                                       any(alt.startswith(k, j) for k in keys) for j in range(len(alt)))),
                                  None)
            if decomposed is None or decomposed == texte[i]:
                raise ValueError(f'caractère hors alphabet CTC : {texte[i]!r}')
            labels, j = [], 0
            while j < len(decomposed):
                key = next((key for key in keys if decomposed.startswith(key, j)), None)
                if key is None:
                    raise ValueError(f'caractère hors alphabet CTC : {texte[i]!r}')
                labels.extend(codec.c2l[key]); j += len(key)
            original_positions, step = (i,), 1
        if not labels or any(int(c) <= 0 for c in labels):
            raise ValueError('encodage CTC vide ou contenant un blank')
        codes.extend(int(c) for c in labels)
        positions.extend([original_positions]*len(labels))
        i += step
    return codes, positions


def graphe_ctc(codes: list[int], blank: int = 0) -> list[int]:
    """blank c1 blank c2 blank … — la forme canonique du graphe CTC."""
    g = [blank]
    for c in codes:
        g.append(c); g.append(blank)
    return g


def viterbi(logp: np.ndarray, etats: list[int]) -> np.ndarray:
    """Chemin de coût maximal contraint au graphe. logp : (frames, alphabet).
    Rend, pour chaque état, la frame de plus forte probabilité qui lui est
    attribuée. Transitions CTC : rester, avancer d'un, et sauter un blank quand
    les deux caractères encadrants diffèrent."""
    T, _ = logp.shape
    S = len(etats)
    if T == 0 or S < 2: return None
    required = (S-1)//2 + sum(etats[s] == etats[s-2] for s in range(3, S, 2))
    if T < required: return None
    NEG = -1e30
    dp = np.full((T, S), NEG, dtype=np.float64)
    bk = np.zeros((T, S), dtype=np.int32)
    dp[0, 0] = logp[0, etats[0]]
    if S > 1: dp[0, 1] = logp[0, etats[1]]
    for t in range(1, T):
        for s in range(S):
            best, arg = dp[t-1, s], s
            if s >= 1 and dp[t-1, s-1] > best: best, arg = dp[t-1, s-1], s-1
            if s >= 2 and etats[s] != 0 and etats[s] != etats[s-2] and dp[t-1, s-2] > best:
                best, arg = dp[t-1, s-2], s-2
            if best <= NEG/2: continue
            dp[t, s] = best + logp[t, etats[s]]
            bk[t, s] = arg
    fin = S-1 if dp[T-1, S-1] >= dp[T-1, S-2] else S-2
    if dp[T-1, fin] <= NEG/2: return None
    chemin = np.zeros(T, dtype=np.int32)
    s = fin
    for t in range(T-1, -1, -1):
        chemin[t] = s; s = bk[t, s]
    # meilleure frame par état non-blank
    pos = np.full(S, -1, dtype=np.int32)
    for t in range(T):
        s = chemin[t]
        if etats[s] == 0: continue
        if pos[s] < 0 or logp[t, etats[s]] > logp[pos[s], etats[s]]: pos[s] = t
    return pos


def body_white_columns(mask):
    """Colonnes sans encre dans la bande du corps des lettres.

    Bande = rangées dont la densité d'encre atteint la moitié du maximum ;
    les composantes de moins de 2 % de h² (poussières) sont ignorées.
    """
    import cv2
    binary=(mask>0).astype(np.uint8)
    rows=binary.mean(axis=1)
    if not rows.max():
        return np.arange(mask.shape[1])
    on=np.flatnonzero(rows>=.5*rows.max());b0,b1=int(on.min()),int(on.max())+1
    h=mask.shape[0]
    n,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    keep=np.zeros(n,bool);keep[1:]=stats[1:,cv2.CC_STAT_AREA]>=.02*h*h
    return np.flatnonzero(~keep[labels[b0:b1]].any(axis=0))


PUNCTUATION_ONLY = re.compile(r'[.,;:!?…·•\-–—»«"\'’()\[\]/|]+')


def word_geometry(gray, line_box, texte, char_centers, boundary_mode='ink'):
    """Place les mots sur l'encre, guidé par les pics du texte imposé.

    Une moyenne de pics CTC peut traverser un glyphe large : ce n'est pas
    une frontière observée. En mode ink, la coupure doit passer dans une
    colonne blanche située entre les deux caractères adjacents. On garde
    la plus proche du milieu CTC et on refuse une frontière sans blanc.
    Aucune largeur de police, lecture OCR ou référence n'intervient ici.
    """
    if boundary_mode not in ('ink','ink_clean','ink_clean_baseline','ink_clean_local','midpoint'):
        raise ValueError('mode de frontières inconnu')
    cleaned=boundary_mode in ('ink_clean','ink_clean_baseline','ink_clean_local')
    mask,ox,oy=alignment_mask(gray,line_box,clean_upper_branches=cleaned,
                            clean_below_baseline=boundary_mode in ('ink_clean_baseline','ink_clean_local'),
                            local_baseline=boundary_mode=='ink_clean_local')
    occ=(mask>0).any(axis=0)
    words=list(re.finditer(r'\S+',texte))
    if not words:
        raise ValueError('texte vide')
    edges=[0]; boundaries=[]; fallbacks=[]; fallback_runs=[]
    white=np.flatnonzero(~occ)
    if cleaned:
        # La boîte rectangulaire peut inclure l'encre d'une autre ligne à
        # gauche/droite. Les extrémités suivent le premier/dernier caractère
        # imposé, avec une vraie séparation blanche ; pas le bord du crop.
        before=white[white+ox<float(char_centers[words[0].start()])]
        if len(before):edges[0]=int(before[-1])+1
    for left,right in zip(words,words[1:]):
        a=float(char_centers[left.end()-1]);b=float(char_centers[right.start()])
        if b<=a:
            raise ValueError('pics de mots non croissants')
        midpoint=(a+b)/2
        if boundary_mode!='midpoint':
            choices=white[(white+ox>a)&(white+ox<b)]
            if not len(choices) and cleaned:
                # Repli : jambage d'une ligne voisine ou poussière du papier dans
                # le blanc inter-mots. On cherche alors le blanc dans la seule
                # bande du corps des lettres, sans les composantes minuscules
                # (à la Tesseract). Toujours un blanc observé, jamais un milieu.
                body=body_white_columns(mask)
                choices=body[(body+ox>a)&(body+ox<b)]
                if len(choices):fallbacks.append(len(boundaries));fallback_runs.append(body)
            if not len(choices) and (PUNCTUATION_ONLY.fullmatch(left.group())
                                     or PUNCTUATION_ONLY.fullmatch(right.group())):
                # Points de conduite écrits espacés (« . . . ») contre des points
                # imprimés serrés : un « mot » fait de ponctuation seule n'a pas
                # toujours de blanc observable ; coupure au milieu CTC, tracée.
                edge=int(np.clip(np.ceil(midpoint-ox),0,len(occ)))
                edges.append(edge)
                boundaries.append(dict(ctc_midpoint=midpoint,x=ox+edge,shift=ox+edge-midpoint,
                                       ink_free=not bool(occ[edge]) if edge<len(occ) else True,
                                       punctuation_midpoint=True))
                continue
            if not len(choices):
                raise ValueError('frontière de mots sans séparation d’encre observée')
            distance=np.abs(choices+ox-midpoint)
            edge=int(choices[int(np.argmin(distance))])
        else:
            edge=int(np.clip(np.ceil(midpoint-ox),0,len(occ)))
        edges.append(edge)
        boundaries.append(dict(ctc_midpoint=midpoint,x=ox+edge,
                               shift=ox+edge-midpoint,ink_free=not bool(occ[edge]) if edge<len(occ) else True))
    end=mask.shape[1]
    if cleaned:
        after=white[white+ox>float(char_centers[words[-1].end()-1])]
        if len(after):end=int(after[0])
    edges.append(end)
    if any(b<=a for a,b in zip(edges,edges[1:])):
        raise ValueError('cellules de mots non croissantes')
    # Autour d'une frontière de repli, la bande blanche du corps des lettres
    # borne aussi l'étendue x des deux mots : l'encre intruse (jambage de la
    # ligne voisine) n'appartient à aucun des deux. Les boîtes restent des
    # étendues d'encre observée ; la propriété des pixels les recalcule ensuite.
    occ_box=occ.copy()
    for k,body in zip(fallbacks,fallback_runs):
        edge=edges[k+1];inside=set(body.tolist())
        lo=edge
        while lo-1 in inside:lo-=1
        hi=edge
        while hi in inside:hi+=1
        occ_box[lo:hi]=False
    boxes=[];estimated=[]
    for k,(a,end) in enumerate(zip(edges,edges[1:])):
        nz=np.flatnonzero(occ_box[a:end])
        if not len(nz) and PUNCTUATION_ONLY.fullmatch(words[k].group()):
            # Point de conduite trop petit pour survivre au nettoyage : boîte
            # minimale à la position CTC, dans la bande basse du corps ; tracée.
            cx=int(np.clip(round(float(char_centers[words[k].start()])-ox),a,max(a,end-1)))
            h=mask.shape[0]
            boxes.append((ox+cx,oy+int(.55*h),ox+cx+1,oy+int(.8*h)));estimated.append(k)
            continue
        if not len(nz):
            raise ValueError('mot aligné sans encre observée')
        xa,xb=a+int(nz.min()),a+int(nz.max())
        ya,yb=ink.vertical_extent(mask,xa,xb)
        boxes.append((ox+xa,oy+ya,ox+xb,oy+yb))
    return boxes,dict(version={'ink':'ctc-ink-whitespace-v1','ink_clean':'ctc-ink-whitespace-v2',
                              'ink_clean_baseline':'ctc-ink-whitespace-v3','ink_clean_local':'ctc-ink-whitespace-v4',
                              'midpoint':'ctc-midpoint-v1'}[boundary_mode],
                      boundaries=boundaries,words=len(words),source_box=list(line_box),
                      body_band_fallback_boundaries=fallbacks,estimated_punctuation_boxes=estimated)


class ForceCTC:
    name = 'force_ctc'

    def __init__(self, model_path=None, fallback_model_path=None, boundary_mode='ink',char_alignment='line'):
        self.model_path = model_path
        self._model = None
        self.last_alignment = None
        self.last_char_positions = None
        self.fallback_model_path=fallback_model_path or (FALLBACK if os.path.exists(FALLBACK) else None)
        self._fallback_model=None
        self.boundary_mode=boundary_mode
        if char_alignment not in ('line','word'):raise ValueError('portée d’alignement de caractères inconnue')
        self.char_alignment=char_alignment

    @property
    def cache_signature(self):
        if not hasattr(self,'_cache_signature'):
            paths=[self.model_path or CHEMIN,self.fallback_model_path]
            self._cache_signature=dict(implementation_sha256=IMPLEMENTATION_SHA256,
                models=[dict(path=str(p),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest()) for p in paths if p],
                boundary_mode=self.boundary_mode,character_scope=self.char_alignment)
        return self._cache_signature

    def _get_model(self):
        if self.model_path is None:
            return modele()
        if self._model is None:
            from kraken.lib.models import load_any
            self._model = load_any(self.model_path)
        return self._model

    def _encode_with_model(self, texte):
        """Glyphe exact d'abord (modèle principal puis secours), puis seulement
        un glyphe de même dessin (VISUAL_EQUIVALENTS) ; le texte reste inchangé."""
        models = [(self._get_model, self.model_path or CHEMIN)]
        if self.fallback_model_path:
            def fallback():
                if self._fallback_model is None:
                    from kraken.lib.models import load_any
                    self._fallback_model = load_any(self.fallback_model_path)
                return self._fallback_model
            models.append((fallback, self.fallback_model_path))
        error = None
        for visual in (False, True):
            for get, selected in models:
                m = get()
                try:
                    codes, pos_car = encode_text(m.codec, texte, visual_fallback=visual)
                except ValueError as exc:
                    if 'hors alphabet' not in str(exc):
                        raise
                    error = exc
                    continue
                return m, codes, pos_car, selected
        raise error

    def align(self, gray: np.ndarray, line):
        self.last_alignment = None
        self.last_char_positions = None
        texte = line.text
        m,codes,pos_car,selected=self._encode_with_model(texte)
        t = _ligne_tenseur(gray, line, m)
        with torch.no_grad():
            logits, _ = m.nn.nn(t.to(m.device) if m.device else t, None)
        if logits.ndim != 4 or logits.shape[2] != 1:
            raise ValueError('forme de logits CTC inattendue')
        # [N, alphabet, 1, frames] : ne jamais deviner l'axe par sa taille.
        logp = torch.log_softmax(logits[0, :, 0, :], dim=0).T.float().cpu().numpy()

        if not codes: raise ValueError('texte vide')
        etats = graphe_ctc(codes)
        pos = viterbi(logp, etats)
        if pos is None: raise ValueError('alignement forcé impossible')

        T = logp.shape[0]
        x0, _, x1, _ = line.line_box
        def frame_vers_x(f): return frame_x(f, T, t.shape[-1], x0, x1-x0)

        # x de chaque POSITION DE CARACTÈRE du texte d'origine
        par_car: dict[int, float] = {}
        for j in range(len(codes)):
            f = pos[2*j + 1]
            if f < 0: continue
            for original_position in pos_car[j]:
                par_car.setdefault(original_position, frame_vers_x(f))
        if len(par_car) != len(texte):
            raise ValueError('caractères non alignés')
        support = [float(np.exp(logp[pos[2*j+1], c])) for j, c in enumerate(codes)]
        char_frames = {i:[] for i in range(len(texte))}
        char_support = {i:[] for i in range(len(texte))}
        for j,positions in enumerate(pos_car):
            for i in positions:
                char_frames[i].append(pos[2*j+1])
                char_support[i].append(support[j])
        frame_width=t.shape[-1]/T*(x1-x0)/(t.shape[-1]-2*PAD)
        self.last_char_positions=[[float(np.clip(min(frame_vers_x(f) for f in char_frames[i])-frame_width/2,x0,x1)),
                                   float(np.clip(max(frame_vers_x(f) for f in char_frames[i])+frame_width/2,x0,x1)),
                                   float(min(char_support[i]))] for i in range(len(texte))]
        self.last_alignment = {'encoded_characters': len(texte), 'codes': len(codes),
                               'implementation_sha256':IMPLEMENTATION_SHA256,
                               'model_path':selected,
                               'support_median': float(np.median(support)),
                               'support_min': min(support), 'padding': PAD,
                               'input_width': int(t.shape[-1]), 'frames': T}
        self._selected_model=m
        return par_car

    def boxes(self, gray: np.ndarray, line):
        centers=self.align(gray,line)
        out_b,geometry=word_geometry(gray,line.line_box,line.text,centers,self.boundary_mode)
        self.last_alignment['word_geometry']=geometry
        if self.char_alignment=='word':
            from types import SimpleNamespace
            words=list(re.finditer(r'\S+',line.text));original=self.last_char_positions
            refined=list(original);sources=['line_ctc']*len(line.text);details=[]
            child=ForceCTC(self.last_alignment['model_path'])
            child._model=self._selected_model
            for match,box in zip(words,out_b):
                # Même hauteur de ligne : la ponctuation garde sa position
                # verticale dans le réseau, seule l'étendue x est contrainte.
                crop=(box[0],line.line_box[1],box[2]+1,line.line_box[3])
                child.align(gray,SimpleNamespace(text=match.group(),line_box=crop))
                for i,pos in enumerate(child.last_char_positions,match.start()):
                    refined[i]=pos;sources[i]='word_ctc'
                details.append(dict(start=match.start(),end=match.end(),source_box=list(crop),
                                    alignment=child.last_alignment))
            for wi,(left,right) in enumerate(zip(words,words[1:])):
                a,b=out_b[wi][2]+1,out_b[wi+1][0]
                if b<=a:
                    if not (PUNCTUATION_ONLY.fullmatch(left.group()) or PUNCTUATION_ONLY.fullmatch(right.group())):
                        raise ValueError('espace sans intervalle géométrique observé')
                    b=a  # points serrés : espace de largeur nulle (ponctuation seulement)
                for i in range(left.end(),right.start()):
                    if not line.text[i].isspace():raise ValueError('séquence de mots incohérente')
                    # Intervalle blanc MESURÉ, confiance CTC inconnue (=0).
                    # Aucun pic CTC situé dans un glyphe voisin n'est recyclé.
                    refined[i]=[float(a),float(b),0.];sources[i]='observed_word_gap'
            self.last_char_positions=refined
            self.last_alignment.update(character_scope='word',word_alignments=details,
                                       character_position_sources=sources,line_char_positions=original)
        else:self.last_alignment['character_scope']='line'
        return out_b
