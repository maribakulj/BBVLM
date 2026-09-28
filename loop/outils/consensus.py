"""Consensus de plusieurs lectures d'une même page, sans référence.

Lignes : la première lecture sert de pivot ; chaque autre lecture est appariée
à ses lignes (Hongrois sur la distance normalisée). Par ligne :
- `medoide` : la lecture qui minimise la somme des distances aux autres ;
- `vote` : alignement caractère à caractère sur le médoïde (difflib), et vote
  majoritaire par position (ROVER simplifié, Fiscus 1997), égalité → médoïde.
"""
import difflib, sys
from collections import Counter
from cer import lev
from accord import apparie


def medoide(vs):
    return min(vs, key=lambda v: sum(lev(v, w) for w in vs))


def vote(vs):
    m = medoide(vs)
    # pour chaque position du médoïde (et chaque interstice), les propositions
    props = [[Counter() for _ in range(len(m))], [Counter() for _ in range(len(m)+1)]]
    for v in vs:
        sm = difflib.SequenceMatcher(None, m, v, autojunk=False)
        ins = [''] * (len(m)+1); sub = list(m)
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == 'equal': continue
            if op == 'insert': ins[i1] += v[j1:j2]
            elif op == 'delete':
                for i in range(i1, i2): sub[i] = ''
            else:
                seg = v[j1:j2]
                for k, i in enumerate(range(i1, i2)):
                    sub[i] = seg[k] if k < len(seg) else ''
                if len(seg) > i2-i1: ins[i2] += seg[i2-i1:]
        for i in range(len(m)): props[0][i][sub[i]] += 1
        for i in range(len(m)+1): props[1][i][ins[i]] += 1
    out = []
    for i in range(len(m)+1):
        c, n = props[1][i].most_common(1)[0]
        if n*2 > len(vs): out.append(c)
        if i < len(m):
            c, n = props[0][i].most_common(1)[0]
            out.append(c if n*2 > len(vs) else m[i])
    return ''.join(out)


def consensus(lectures, mode='vote'):
    pivot = [l for l in lectures[0] if l.strip()]
    autres = [apparie(pivot, [l for l in L if l.strip()]) for L in lectures[1:]]
    f = vote if mode == 'vote' else medoide
    return [f([p] + [a[i] for a in autres if i in a]) for i, p in enumerate(pivot)]


if __name__ == '__main__':
    mode = sys.argv[1]
    L = [open(p, encoding='utf-8').read().splitlines() for p in sys.argv[2:]]
    print('\n'.join(consensus(L, mode)))
