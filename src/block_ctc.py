"""Appariement texte Gemini → lignes par vraisemblance CTC (sans lecture intermédiaire).

Entre deux lignes déjà ancrées d'une région, le texte Gemini libre est découpé
(aux espaces) en morceaux consécutifs, un par ligne, ou laissé sans ligne. Le
découpage retenu maximise la somme des log-vraisemblances CTC log P(morceau |
image de la ligne), calculées par l'algorithme forward sur les probabilités du
réseau ; laisser du texte sans ligne coûte ``skip_cost`` par caractère (ligne
non détectée). Une ligne sans texte reçoit log P(« » | image) : quasi nul pour
un filet ou une tache, très coûteux pour une ligne imprimée. Aucune lecture
CTC n'est utilisée comme texte ; le texte source n'est jamais modifié.
(Principe voisin : Peer, Scius-Bertrand, Fischer, ICCVW 2025, arXiv:2508.07904.)
"""
from __future__ import annotations
import json
from pathlib import Path
import unicodedata

import numpy as np

VISUAL_EQUIVALENTS = {'º': ('°', 'o'), '°': ('º', 'o'), 'ª': ('a',), '′': ("'",), '″': ('"',)}
NEG = -1e30


class Posteriors:
    def __init__(self, directory):
        directory = Path(directory)
        meta = json.loads((directory / 'posteriors.json').read_text())
        self.codec = {k: v for k, v in meta['codec'].items() if k}
        self.keys = sorted(self.codec, key=len, reverse=True)
        self.lines = meta['lines']
        self._npz = np.load(directory / 'posteriors.npz')

    def logp(self, line_id):
        if line_id not in self._npz.files:
            return None
        return self._npz[line_id].astype(np.float32)

    def encode(self, text):
        """Étiquettes CTC du texte ; espaces multiples réduits à un. Caractère
        absent du codec : NFD, puis glyphe de même dessin, sinon ignoré (compté)."""
        text = ' '.join(text.split())
        labels, missing, i = [], 0, 0
        while i < len(text):
            key = next((k for k in self.keys if text.startswith(k, i)), None)
            if key is not None:
                codes = self.codec[key]
                # Barre de fraction entre deux chiffres (« 1/4 ») : l'imprimé a
                # souvent un seul signe « ¼ », que le modèle lit « 14 » ; la
                # barre devient facultative (étiquette négative) pour le calcul.
                if key in '/⁄' and 0 < i < len(text)-1 and text[i-1].isdigit() and text[i+1].isdigit():
                    codes = [-c for c in codes]
                labels.extend(codes); i += len(key); continue
            options = [unicodedata.normalize('NFD', text[i]), unicodedata.normalize('NFKC', text[i]),
                       *VISUAL_EQUIVALENTS.get(text[i], ())]
            for alt in options:
                if alt != text[i] and all(ch in self.codec for ch in alt):
                    for ch in alt:
                        labels.extend(self.codec[ch])
                    break
            else:
                missing += 1
            i += 1
        return labels, missing


def _shift(values, k):
    """values décalé de k vers la droite, complété par NEG (même longueur)."""
    if len(values) <= k:
        return np.full(len(values), NEG)
    return np.concatenate((np.full(k, NEG), values[:-k]))


def prefix_loglik(logp, labels):
    """log P(labels[:l] | X) pour l = 0..L, en une passe forward (blanc = 0).
    Une étiquette négative est facultative : un chemin peut la sauter."""
    T = logp.shape[0]
    L = len(labels)
    optional = np.array([c < 0 for c in labels], dtype=bool)
    S = 2*L+1
    ext = np.zeros(S, dtype=np.int64)
    ext[1::2] = np.abs(np.asarray(labels, dtype=np.int64)) if L else []
    skip = np.zeros(S, dtype=bool)
    if L > 1:
        lab = ext[1::2]
        skip[3::2] = lab[1:] != lab[:-1]
    # sauter une étiquette facultative k : de l'étiquette k-1 (ou du blanc
    # qui la suit) directement vers l'étiquette k+1
    jump = np.zeros(S, dtype=bool)
    if L > 2:
        jump[5::2] = optional[1:-1] & (ext[5::2] != ext[1:-4:2])
    alpha = np.full(S, NEG)
    alpha[0] = logp[0, 0]
    if S > 1:
        alpha[1] = logp[0, ext[1]]
    if S > 3 and optional[0]:
        alpha[3] = logp[0, ext[3]]
    for t in range(1, T):
        prev = alpha
        a1 = _shift(prev, 1)
        a2 = np.where(skip, _shift(prev, 2), NEG)
        a3 = np.where(jump, _shift(prev, 3), NEG)
        a4 = np.where(jump, _shift(prev, 4), NEG)
        alpha = np.logaddexp(np.logaddexp(np.logaddexp(prev, a1), a2), np.logaddexp(a3, a4)) + logp[t, ext]
    out = np.empty(L+1)
    out[0] = alpha[0]
    if L:
        out[1:] = np.logaddexp(alpha[1::2], alpha[2::2])
        for l in range(1, L+1):
            if optional[l-1]:
                out[l] = np.logaddexp(out[l], out[l-1])
    return out


def solve_gap(lines, text, posteriors, skip_cost=4.0, max_chars=220):
    """lines : lignes ordonnées (id, bbox) ; text : texte libre de l'intervalle.
    Renvoie [(index_ligne, début, fin, score_par_caractère)] en offsets de ``text``."""
    cuts = [0] + [i for i in range(1, len(text)) if text[i-1].isspace() and not text[i].isspace()] + [len(text)]
    cuts = sorted(set(cuts))
    nonspace = np.cumsum([0] + [not ch.isspace() for ch in text])
    m, n = len(lines), len(cuts)
    # vraisemblance de chaque morceau text[cuts[a]:cuts[b]] pour chaque ligne
    table = [dict() for _ in range(m)]
    empty = []
    for k, line in enumerate(lines):
        logp = posteriors.logp(line['id'])
        if logp is None:
            empty.append(None); continue
        empty.append(float(prefix_loglik(logp, [])[0]))
        for a in range(n-1):
            start = cuts[a]
            limit = start + max_chars
            ends = [b for b in range(a+1, n) if cuts[b] <= limit]
            if not ends:
                continue
            piece = text[start:cuts[ends[-1]]]
            # étiquettes de chaque fin de morceau : encoder incrémentalement
            labels, _ = posteriors.encode(piece)
            prefix = prefix_loglik(logp, labels)
            for b in ends:
                sub = text[start:cuts[b]].rstrip()
                lab, _ = posteriors.encode(sub)
                if not lab or len(lab) > len(labels) or labels[:len(lab)] != lab:
                    continue
                table[k][(a, b)] = float(prefix[len(lab)])
    # programmation dynamique : états (ligne k, coupure a)
    best = np.full((m+1, n), -np.inf)
    back = {}
    best[0, 0] = 0.
    for k in range(m+1):
        # sauter du texte sans ligne (avant la ligne k)
        for a in range(n):
            if best[k, a] == -np.inf:
                continue
            for b in range(a+1, n):
                cost = best[k, a] - skip_cost*(nonspace[cuts[b]]-nonspace[cuts[a]])
                if cost > best[k, b]:
                    best[k, b] = cost; back[(k, b)] = ('skip', k, a)
        if k == m:
            break
        for a in range(n):
            if best[k, a] == -np.inf:
                continue
            base = best[k, a]
            if empty[k] is None:
                if base > best[k+1, a]:
                    best[k+1, a] = base; back[(k+1, a)] = ('none', k, a)
                continue
            if base + empty[k] > best[k+1, a]:
                best[k+1, a] = base + empty[k]; back[(k+1, a)] = ('empty', k, a)
            for (a0, b), score in table[k].items():
                if a0 == a and base + score > best[k+1, b]:
                    best[k+1, b] = base + score; back[(k+1, b)] = ('take', k, a)
    result, state = [], (m, n-1)
    while state in back:
        kind, k, a = back[state]
        if kind == 'take':
            b = state[1]
            chars = max(1, nonspace[cuts[b]]-nonspace[cuts[a]])
            start = cuts[a]
            while start < cuts[b] and text[start].isspace():
                start += 1
            result.append((k, start, len(text[:cuts[b]].rstrip()), table[k][(a, b)]/chars))
        state = (k, a)
    return sorted(result)
