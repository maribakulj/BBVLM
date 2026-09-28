"""Recherche plein texte sur les ALTO produits, avec retour aux coordonnées.

Deux vues du même mot, jamais confondues : diplomatique (CONTENT tel quel) et
recherche (NFC, ligatures MUFI décomposées, ſ→s, e suscrit→tréma, ꝛ→r, casse
et ponctuation de bord retirées). L'index renvoie pour chaque terme la liste
(page, ligne, mot, boîte). Césure de fin de ligne (⸗ ou -) : le mot est aussi
indexé recollé à son suite sur la ligne suivante.

Mesure (R01) : chaque mot de la référence PAGE, mis dans la vue recherche, est
une requête ; une occurrence est retrouvée si l'index rend, sur la même page,
une boîte d'IoU ≥ 0,5 avec la boîte de référence. Rappel des occurrences,
précision des réponses (occurrences rendues qui correspondent à une occurrence
de référence du même terme), par page.
"""
import re, sys, unicodedata
from collections import defaultdict
from lxml import etree
from cer import vue
from segeval import iou
from eval_alto import mots_page

BORD = re.compile(r'^[^\w]+|[^\w]+$')


def terme(mot):
    t = vue(mot, 'norm').replace('ꝛ', 'r').lower()
    t = unicodedata.normalize('NFC', t)
    return BORD.sub('', t)


def index(alto, page_id):
    r = etree.parse(alto).getroot(); N = r.tag.split('}')[0][1:]
    idx = defaultdict(list)
    lignes = list(r.iter(f'{{{N}}}TextLine'))
    for li, tl in enumerate(lignes):
        ss = [s for s in tl.iter(f'{{{N}}}String')]
        for s in ss:
            if s.get('HPOS') is None: continue
            x, y, w, h = (int(s.get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
            b = (x, y, x+w-1, y+h-1)
            idx[terme(s.get('CONTENT'))].append((page_id, b))
        # césure : dernier mot + premier mot de la ligne suivante
        if ss and li+1 < len(lignes) and re.search(r'[⸗\-¬]$', ss[-1].get('CONTENT') or ''):
            suiv = [s for s in lignes[li+1].iter(f'{{{N}}}String')]
            if suiv and ss[-1].get('HPOS') is not None:
                x, y, w, h = (int(ss[-1].get(k)) for k in ('HPOS', 'VPOS', 'WIDTH', 'HEIGHT'))
                idx[terme(re.sub(r'[⸗\-¬]$', '', ss[-1].get('CONTENT')) + suiv[0].get('CONTENT'))].append((page_id, (x, y, x+w-1, y+h-1)))
    return idx


def mesure(alto, page_xml):
    idx = index(alto, 'p')
    ref = [(terme(t), b) for t, b in mots_page(page_xml)]
    par_terme = defaultdict(list)
    for t, b in ref: par_terme[t].append(b)
    trouve = sum(1 for t, b in ref if any(iou(b, rb) >= .5 for _, rb in idx.get(t, [])))
    rendus = sum(len(idx.get(t, [])) for t in par_terme)
    justes = sum(1 for t in par_terme for _, rb in idx.get(t, []) if any(iou(b, rb) >= .5 for b in par_terme[t]))
    return {'occurrences_ref': len(ref), 'retrouvees': trouve, 'rappel': round(trouve/len(ref), 4),
            'precision': round(justes/max(1, rendus), 4), 'termes': len(par_terme)}


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        a, p = arg.split('=')
        print(a.split('/')[-2][:10] if '/' in a else a, mesure(a, p))
