#!/usr/bin/env python
"""Comparaison fine de lectures en texte brut (sans ALTO) face à la VT.

Pour chaque lecteur : CER côté VT (appariement optimal des lignes, comme
cer_vt.line_matching), puis chaque erreur de caractère rangée par type :
- accent : même lettre de base, diacritique différent (é/e, à/a, ç/c) ;
- chiffre : un chiffre lu, manqué ou confondu ;
- espace : mots soudés ou coupés ;
- lettre : autre substitution, omission ou ajout dans une ligne lue ;
- ligne manquée : ligne de VT sans ligne lue correspondante (caractères comptés) ;
- texte en plus : ligne lue sans ligne de VT (hors CER côté VT ; à vérifier à l'image).
S'y ajoutent les confusions les plus fréquentes, le CER par région et les lignes
où les lecteurs divergent le plus. Évaluation seulement : la VT n'entre jamais
dans la chaîne.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT / 'scripts'))
from cer_vt import cer_vt, evaluate, markdown_text
from comparer_lecteurs import table_rows
from page_reference_text import load_page_reference

TYPES = ('accent', 'chiffre', 'espace', 'lettre', 'ligne_manquee')


def base(c):
    return unicodedata.normalize('NFD', c)[0]


def pairs(reference_lines, hypothesis_lines):
    """[(ligne VT normalisée, ligne lue normalisée ou None)], lignes lues orphelines."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from rapidfuzz.distance import Levenshtein
    from rapidfuzz.process import cdist
    ref = [x for x in (cer_vt(t) for t in reference_lines) if x]
    hyp = [x for x in (cer_vt(t) for t in hypothesis_lines) if x]
    out, used = [[r, None] for r in ref], set()
    if ref and hyp:
        dist = cdist(ref, hyp, scorer=Levenshtein.distance, workers=-1).astype(float)
        gain = np.array([[len(a)+len(b) for b in hyp] for a in ref], dtype=float) - dist
        for i, j in zip(*linear_sum_assignment(-gain)):
            if gain[i, j] > 0 and dist[i, j] <= .5*max(len(ref[i]), len(hyp[j])):
                out[i][1] = hyp[j]; used.add(j)
    return out, [h for j, h in enumerate(hyp) if j not in used]


def merge_tolerant(matched, extra):
    """Lignes recollées ou coupées autrement que dans la VT : une ligne lue qui contient
    plusieurs lignes de VT (ou une ligne de VT qui en contient plusieurs lues) est
    comparée au texte joint, sans pénaliser la coupure. Renvoie [(texte VT, texte lu)]."""
    from rapidfuzz import fuzz
    lines, owner = [], {}  # owner : ligne de VT -> indice de ligne lue
    for k, (ref, hyp) in enumerate(matched):
        if hyp is not None:
            owner[k] = len(lines); lines.append(hyp)
    lines += list(extra)
    for k, (ref, hyp) in enumerate(matched):
        if hyp is None and len(ref) >= 3:
            scores = [fuzz.partial_ratio(ref, h) if len(h) > len(ref) else 0 for h in lines]
            if scores and max(scores) >= 85:
                owner[k] = scores.index(max(scores))
    groups = {}
    for k, j in sorted(owner.items()):
        groups.setdefault(j, []).append(matched[k][0])
    out = [(' '.join(g), lines[j]) for j, g in groups.items()]
    out += [(matched[k][0], '') for k in range(len(matched)) if k not in owner]
    return out


def classify(ref, hyp):
    """Types d'erreur et confusions (« attendu→lu ») d'une ligne appariée."""
    from rapidfuzz.distance import Levenshtein
    types, confusions = Counter(), Counter()
    for op in Levenshtein.editops(ref, hyp):
        a = ref[op.src_pos] if op.tag != 'insert' else ''
        b = hyp[op.dest_pos] if op.tag != 'delete' else ''
        if ' ' in (a, b):
            kind = 'espace'
        elif any(c.isdigit() for c in a + b):
            kind = 'chiffre'
        elif a and b and base(a) == base(b):
            kind = 'accent'
        else:
            kind = 'lettre'
        types[kind] += 1
        confusions[f'{a or "∅"}→{b or "∅"}'] += 1
    return types, confusions


def reader_report(reference_lines, text):
    matched, extra = pairs(reference_lines, text.splitlines())
    types, confusions, lines = Counter(), Counter(), []
    from rapidfuzz.distance import Levenshtein
    for k, (ref, hyp) in enumerate(matched):
        if hyp is None:
            types['ligne_manquee'] += len(ref)
            lines.append(dict(k=k, errors=len(ref), hyp=None))
            continue
        t, c = classify(ref, hyp)
        types += t; confusions += c
        lines.append(dict(k=k, errors=Levenshtein.distance(ref, hyp), hyp=hyp))
    chars = sum(len(r) for r, _ in matched)
    # Types comptés sur les paires insensibles aux coupures : une ligne recollée n'est pas une erreur.
    tol_types, tol_conf = Counter(), Counter()
    for r, h in merge_tolerant(matched, extra):
        if not h:
            tol_types['ligne_manquee'] += len(r); continue
        t, c = classify(r, h); tol_types += t; tol_conf += c
    return dict(cer_sans_coupures=sum(tol_types.values())/chars,
                types_sans_coupures={t: tol_types[t] for t in TYPES},
                confusions_sans_coupures=tol_conf.most_common(25),
                characters=chars, errors=sum(types.values()), cer=sum(types.values())/chars,
                types={t: types[t] for t in TYPES}, extra_characters=sum(map(len, extra)),
                extra_lines=extra, confusions=confusions.most_common(25)), lines, matched


def compare(reference_xml, readings, manifest=None, regions=None):
    rows, _ = load_page_reference(reference_xml)
    reference = [r['text'] for r in rows if r['text'].strip()]
    reports, per_line = {}, {}
    for name, transcription in readings.items():
        text = markdown_text(table_rows((Path(transcription) / 'vt.gemini.md').read_text()))[0]
        reports[name], per_line[name], matched = reader_report(reference, text)
        if manifest:
            ev = evaluate(manifest, transcription, regions or Path(transcription) / 'regions.json')
            reports[name]['cer_line_matching'] = ev['page_line_matching']['cer_reference_side']
            reports[name]['words_recall'] = ev['page_bag_of_words']['recall']
            reports[name]['regions'] = {r['id']: (r['errors'], r['reference_characters']) for r in ev['regions']}
    names = list(readings)
    vt = [r for r, _ in matched]
    gaps = []
    for k, line in enumerate(vt):
        e = {n: per_line[n][k]['errors'] for n in names}
        if any(e.values()):
            gaps.append(dict(vt=line, **{n: per_line[n][k]['hyp'] for n in names},
                             **{f'err_{n}': e[n] for n in names}))
    return reports, gaps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('readings', nargs='+', help='nom=dossier_transcription')
    parser.add_argument('--manifest'); parser.add_argument('--regions')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    readings = dict(r.split('=', 1) for r in args.readings)
    reports, gaps = compare(args.reference, readings, args.manifest, args.regions)
    Path(args.output).write_text(json.dumps(dict(readers=reports, lines=gaps), ensure_ascii=False, indent=1))
    for n, r in reports.items():
        print(n, f"CER {r['cer']*100:.2f} %", r['types'], 'en plus', r['extra_characters'])
