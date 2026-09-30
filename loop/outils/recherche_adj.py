"""R02b : recherche mesurée contre la référence adjugée auditée (mêmes boîtes PAGE,
texte des mots pris dans la ligne adjugée quand le nombre de mots concorde)."""
import json
from collections import defaultdict
from lxml import etree
from recherche import index, terme
from segeval import iou
from bilan_adj import reference_adjugee
import corpora


def mots_adj(dossier):
    adj, _ = reference_adjugee(dossier)
    r = etree.parse(f'{dossier}/page.xml').getroot(); N = {'p': r.tag.split('}')[0][1:]}
    out = []
    for i, tl in enumerate(r.findall('.//p:TextLine', N)):
        ws = [(w.find('p:TextEquiv/p:Unicode', N), w.find('p:Coords', N)) for w in tl.findall('p:Word', N)]
        ws = [(u.text, corpora._box(c.get('points'))) for u, c in ws if u is not None and u.text and c is not None]
        a = adj[i].split() if i < len(adj) and adj[i] else []
        if len(a) == len(ws): ws = [(t, b) for t, (_, b) in zip(a, ws)]
        out += ws
    return out


def mesure(alto, dossier):
    idx = index(alto, 'p')
    ref = [(terme(t), b) for t, b in mots_adj(dossier)]
    par_terme = defaultdict(list)
    for t, b in ref: par_terme[t].append(b)
    trouve = sum(1 for t, b in ref if any(iou(b, rb) >= .5 for _, rb in idx.get(t, [])))
    rendus = sum(len(idx.get(t, [])) for t in par_terme)
    justes = sum(1 for t in par_terme for _, rb in idx.get(t, []) if any(iou(b, rb) >= .5 for b in par_terme[t]))
    return {'occurrences_ref': len(ref), 'retrouvees': trouve, 'rappel': round(trouve/len(ref), 4),
            'precision': round(justes/max(1, rendus), 4)}
