"""Notation indépendante. Ne doit jamais être importé par la production."""
from __future__ import annotations
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import numpy as np
from scipy.optimize import linear_sum_assignment
from lxml import etree


def nfc(text):
    return unicodedata.normalize('NFC', text)


def convention(text):
    text = re.sub(r'\s+', ' ', nfc(text).replace('’', "'")).strip()
    return re.sub('[¬⸗]$', '-', text)


def convention_v2(text):
    """Accents/normalisations exclus à la demande utilisateur, protocole VT v2."""
    text = convention(text).translate(str.maketrans({'œ':'oe','Œ':'OE','æ':'ae','Æ':'AE'}))
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.category(c).startswith('M'))


HIPE_NORMALIZATION_SOURCE = (
    'https://github.com/hipe-eval/HIPE-OCRepair-scorer/blob/main/'
    'hipe_ocrepair_scorer/ocrepair_eval.py')
HIPE_NORMALIZATION_SOURCE_SHA256 = '6bfe8e135b42a3cf0eb027fddec5d0c9157cd739529fcaac1ca2adb4abeefbfe'


def hipe_ocrepair_2026(text):
    """Profil officiel norm(), relevé le 7 octobre 2026 ; accents conservés.

    Appliquer au document entier : les marqueurs de césure suivis d'un saut
    de ligne doivent encore être présents. La métrique CER reste distincte
    du cMER utilisé pour le classement de la compétition.
    """
    text = text.lower()
    for source, target in [('ß', 'ss'), ('ꝛ', 'r'), ('œ', 'oe'), ('æ', 'ae'),
                           ('aͤ', 'ä'), ('oͤ', 'ö'), ('uͤ', 'ü')]:
        text = text.replace(source, target)
    text = text.replace('—\n', '').replace('¬\n', '')
    return ' '.join(re.sub(r'[\W_]', ' ', text, flags=re.UNICODE).split())


def cer_vt(text):
    """CER « vérité terrain » demandé par Marcel (18/10/2026) : profil HIPE/ICDAR
    ci-dessus, plus formes de compatibilité (ligatures ﬁ ﬂ, exposants) et s long.
    Aucune ponctuation, apostrophe ni casse ne compte ; accents conservés."""
    text = unicodedata.normalize('NFKC', text).replace('ſ', 's')
    # Césure de fin de ligne : HIPE recolle « ¬ » et « — » ; le trait d'union
    # ordinaire suivi d'une minuscule à la ligne suivante est la même coupure
    # (Gemini l'écrit « - »). Même règle des deux côtés.
    text = re.sub(r'-[ \t]*\n[ \t]*(?=[a-zà-ÿœæ])', '', text)
    return hipe_ocrepair_2026(text)


def lev(a, b):
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    # Rapidfuzz is optional; avoid quadratic full-page Python scoring.
    try:
        from rapidfuzz.distance import Levenshtein
        return Levenshtein.distance(a, b)
    except ImportError:
        previous = list(range(len(b)+1))
        for i, ca in enumerate(a, 1):
            current = [i]
            for j, cb in enumerate(b, 1):
                current.append(min(previous[j]+1, current[j-1]+1,
                                   previous[j-1]+(ca != cb)))
            previous = current
        return previous[-1]


def iou(a, b):
    x0,y0,x1,y1 = a; u0,v0,u1,v1 = b
    intersection = max(0,min(x1,u1)-max(x0,u0))*max(0,min(y1,v1)-max(y0,v0))
    union = max(0,x1-x0)*max(0,y1-y0)+max(0,u1-u0)*max(0,v1-v0)-intersection
    return intersection/union if union else 0.0


def match_boxes(reference, prediction, threshold=.5):
    """Maximum de correspondances, puis IoU ; jamais le contenu textuel."""
    if not reference or not prediction:
        return []
    matrix = np.asarray([[iou(r,p) for p in prediction] for r in reference])
    weights = np.where(matrix >= threshold, min(matrix.shape)+1+matrix, 0)
    rr, pp = linear_sum_assignment(weights, maximize=True)
    return [(int(r),int(p),float(matrix[r,p])) for r,p in zip(rr,pp)
            if matrix[r,p] >= threshold]


def distribution(values):
    if not values:
        return dict(n=0, median=None, p10=None, p90=None, p99=None, maximum=None)
    return dict(n=len(values), median=float(np.median(values)),
                p10=float(np.percentile(values,10)), p90=float(np.percentile(values,90)),
                p99=float(np.percentile(values,99)), maximum=float(max(values)))


def article_pairwise(reference,prediction):
    """Paires sur toutes les appartenances, jamais l'intersection des IDs seule.

    Une ligne omise ne devient pas une paire correcte. Les IDs supplémentaires
    de production augmentent les faux positifs s'ils sont regroupés en article.
    """
    def pairs(counts):return sum(n*(n-1)//2 for n in counts.values())
    gt=pairs(Counter(reference.values()));pred=pairs(Counter(prediction.values()))
    joint=Counter((reference[i],prediction[i]) for i in reference.keys()&prediction.keys())
    tp=pairs(joint);precision=tp/pred if pred else 0.;recall=tp/gt if gt else None
    return dict(precision=precision,recall=recall,f1=2*tp/(gt+pred) if gt else None,
                tp=tp,pred=pred,gt=gt,reference_lines=len(reference),predicted_lines=len(prediction),
                assignment_coverage=len(reference.keys()&prediction.keys())/len(reference) if reference else None,
                status='measured_all_reference_pairs' if gt else 'no_positive_reference_pairs_not_certifiable')


def _points(el):
    c=el.find('{*}Coords')
    if c is None:
        return None
    if c.get('points'):
        p=[tuple(map(float,q.split(','))) for q in c.get('points').split()]
    else:
        p=[(float(q.get('x')),float(q.get('y'))) for q in c]
    return [min(x for x,y in p), min(y for x,y in p),
            max(x for x,y in p), max(y for x,y in p)] if p else None


def _alto_box(el,scale=1.):
    x,y,w,h=(float(el.get(k)) for k in ('HPOS','VPOS','WIDTH','HEIGHT'))
    return [v*scale for v in (x,y,x+w,y+h)]


def load_reference(path,*,dpi=None):
    root=etree.parse(str(path)).getroot()
    is_alto=etree.QName(root).localname.lower() == 'alto'
    lines=[]
    if is_alto:
        unit=root.findtext('{*}Description/{*}MeasurementUnit')
        if unit=='pixel':scale=1.
        elif unit in ('mm10','inch1200'):
            if dpi is None or not np.isfinite(dpi) or dpi<=0:
                raise ValueError(f'ALTO {unit} : résolution DPI documentée requise pour convertir en pixels')
            scale=float(dpi)/(254 if unit=='mm10' else 1200)
        else:raise ValueError('Unité ALTO absente/inconnue : géométrie de référence non mesurable')
        for line in root.findall('.//{*}TextLine'):
            words=[dict(text=nfc(w.get('CONTENT','')),bbox=_alto_box(w,scale))
                   for w in line.findall('{*}String')]
            text=' '.join(w['text'] for w in words).strip()
            if not text:
                continue
            lines.append(dict(id=line.get('ID'),bbox=_alto_box(line,scale),text=text,words=words,
                              reference_coordinates=dict(unit=unit,dpi=dpi if unit!='pixel' else None,pixels_per_unit=scale)))
    else:
        regions=root.findall('.//{*}TextRegion')
        # PAGE explicit order, then annotated custom order, then document order.
        refs=root.findall('.//{*}ReadingOrder//{*}RegionRefIndexed')
        ids=[e.get('regionRef') for e in sorted(refs,key=lambda e:int(e.get('index')))]
        def key(r):
            if r.get('id') in ids:
                return ids.index(r.get('id'))
            m=re.search(r'readingOrder\s*\{\s*index:\s*(\d+)',r.get('custom',''))
            return len(ids)+(int(m[1]) if m else regions.index(r))
        for region in sorted(regions,key=key):
            for line in region.findall('{*}TextLine'):
                bbox=_points(line)
                words=[]
                for w in line.findall('{*}Word'):
                    text=w.findtext('{*}TextEquiv/{*}Unicode')
                    if text and _points(w):
                        words.append(dict(text=nfc(text.strip()),bbox=_points(w)))
                text=line.findtext('{*}TextEquiv/{*}Unicode')
                text=nfc((text if text is not None else ' '.join(w['text'] for w in words)).strip())
                if not text or bbox is None:
                    continue
                coarse=any(len(w['text'].split())>1 for w in words)
                lines.append(dict(id=line.get('id'),bbox=bbox,text=text,
                                  words=[] if coarse else words,
                                  word_annotation_granularity='line_only' if coarse else 'word' if words else 'absent',
                                  region=region.get('id')))
    return lines


def segmentation(reference, prediction, threshold):
    matches=match_boxes([r['bbox'] for r in reference],[p['bbox'] for p in prediction],threshold)
    precision=len(matches)/len(prediction) if prediction else 0.0
    recall=len(matches)/len(reference) if reference else 0.0
    return dict(reference=len(reference),predicted=len(prediction),matched=len(matches),
                precision=precision,recall=recall,
                f1=2*precision*recall/(precision+recall) if precision+recall else 0.0,
                omitted_ids=[r['id'] for i,r in enumerate(reference) if i not in {m[0] for m in matches}],
                extra_ids=[p['id'] for i,p in enumerate(prediction) if i not in {m[1] for m in matches}])


def olr_detection(reference,prediction,threshold=.5):
    """Appariement géométrique indépendant des types, puis classification.

    Les séparateurs sont notés séparément : leur grand nombre ne peut pas
    masquer une mauvaise détection des blocs textuels et illustrations.
    """
    def measure(ref,pred):
        matches=match_boxes([b['bbox'] for b in ref],[b['bbox'] for b in pred],threshold)
        correct=sum(ref[r]['type']==pred[p]['type'] and not pred[p].get('uncertain',False) for r,p,_ in matches)
        confusion=Counter((ref[r]['type'],pred[p]['type']) for r,p,_ in matches)
        return dict(detection=segmentation(ref,pred,threshold),
                    classification=dict(matched=len(matches),correct=correct,
                        accuracy=correct/len(matches) if matches else None,
                        unresolved_matched=sum(pred[p].get('uncertain',False) for _,p,_ in matches),
                        confusion=[dict(reference=a,prediction=b,count=n) for (a,b),n in sorted(confusion.items())]),
                    matches=[dict(reference_id=ref[r]['id'],prediction_id=pred[p]['id'],iou=i,
                                  reference_type=ref[r]['type'],prediction_type=pred[p]['type']) for r,p,i in matches])
    main=measure([b for b in reference if b['type']!='separator'],[b for b in prediction if b['type']!='separator'])
    separators=measure([b for b in reference if b['type']=='separator'],[b for b in prediction if b['type']=='separator'])
    illustrations=measure([b for b in reference if b['type']=='illustration'],[b for b in prediction if b['type']=='illustration'])
    return dict(blocks=main,separators=separators,illustrations=illustrations,
                threshold=threshold,matching='untyped one-to-one rectangular IoU, then exact type; uncertainty is not correct classification')


def exported_annotations(annotations, directory):
    """Noter les lignes réellement exportées, y compris les refus de l'OLR."""
    directory=Path(directory)
    export_file=directory/'training.jsonl'
    if not export_file.exists():
        return annotations
    retained={json.loads(line)['line_id'] for line in export_file.read_text().splitlines() if line.strip()}
    result=[{**a,'geometry_stage_eligible':a.get('training_eligible',True),
             'training_eligible':a['id'] in retained,
             'status':a.get('status','unknown') if a['id'] in retained or not a.get('training_eligible',True)
                      else 'exclue_par_olr'} for a in annotations]
    if (directory/'olr.json').exists():
        olr=json.loads((directory/'olr.json').read_text())
        blocks={b['id']:b for b in olr['blocks']}
        ids=[lid for bid in olr['reading_order'] for lid in blocks[bid]['line_ids']]
        by_id={a['id']:a for a in result}
        if len(ids)!=len(set(ids)) or set(ids)!=set(by_id):
            raise ValueError('Sortie OLR incomplète : ordre non mesurable')
        result=[by_id[lid] for lid in ids]
    return result


def score(reference, prediction):
    matches=match_boxes([r['bbox'] for r in reference],[p['bbox'] for p in prediction])
    paired={r:p for r,p,_ in matches}; used=set(paired.values())
    text_scores={}
    modes=[('strict_NFC',nfc,'text'),('convention_v1',convention,'text')]
    if any(p.get('raw_text',p['text'])!=p['text'] for p in prediction):
        modes.append(('raw_source_strict_NFC',nfc,'raw_text'))
    for name,normalizer,hypfield in modes:
        errors=denom=conditional_errors=conditional_chars=covered=exact=0
        failures=[]
        for ri,r in enumerate(reference):
            p=prediction[paired[ri]] if ri in paired else None
            ref=normalizer(r['text']); denom+=len(ref)
            hyp=normalizer(p.get(hypfield,p['text'])) if p and p.get('training_eligible',True) else ''
            error=lev(ref,hyp);errors+=error;exact+=error == 0
            if error:
                failures.append(dict(reference_id=r['id'],prediction_id=p['id'] if p else None,
                                     errors=error,reference=r['text'],prediction=p.get(hypfield,p['text']) if p else '',
                                     exported=bool(p and p.get('training_eligible',True))))
            if p:
                conditional_errors+=lev(ref,normalizer(p.get(hypfield,p['text']))); conditional_chars+=len(ref)
                if p.get('training_eligible',True):
                    covered+=len(ref)
        insertions=sum(len(normalizer(p.get(hypfield,p['text']))) for pi,p in enumerate(prediction)
                       if pi not in used and p.get('training_eligible',True))
        errors+=insertions
        text_scores[name]=dict(errors=errors,characters=denom,cer=errors/denom if denom else None,
                               unmatched_insertions=insertions,exact_lines=exact,
                               covered_characters=covered,coverage=covered/denom if denom else 0,
                               conditional_cer=conditional_errors/conditional_chars if conditional_chars else None,
                               failures=failures)
    giou=[]; edges=[]; edges_c=[]; boundaries=[]; measured=0
    reference_words=sum(len(r.get('words',[])) for r in reference)
    for ri,pi,_ in matches:
        r,p=reference[ri],prediction[pi]
        if not p.get('training_eligible',True):
            continue
        rw=r.get('words',[]);pw=p.get('words',[])
        if not rw:
            continue
        scale=max(1.,(max(w['bbox'][2] for w in rw)-min(w['bbox'][0] for w in rw))/max(1,sum(len(w['text']) for w in rw)))
        matcher=SequenceMatcher(None,[w['text'] for w in rw],[w['text'] for w in pw],autojunk=False)
        lexical={}
        for a,b,size in matcher.get_matching_blocks():
            for k in range(size):
                lexical[a+k]=b+k
                gt=rw[a+k]['bbox']; pred=pw[b+k].get('bbox')
                if pred is None:
                    w=pw[b+k];pred=[w['x0'],w['y0'],w['x1']+1,w['y1']+1]
                giou.append(iou(gt,pred));measured+=1
                edges.extend(abs(u-v) for u,v in zip(gt,pred))
                edges_c.extend(abs(u-v)/scale for u,v in zip(gt,pred))
        for k in range(len(rw)-1):
            if k not in lexical or k+1 not in lexical:
                continue
            a,b=pw[lexical[k]],pw[lexical[k+1]]
            aa=a.get('bbox') or [a['x0'],a['y0'],a['x1']+1,a['y1']+1]
            bb=b.get('bbox') or [b['x0'],b['y0'],b['x1']+1,b['y1']+1]
            lo,hi=rw[k]['bbox'][2],rw[k+1]['bbox'][0]
            if hi < lo:
                continue  # anomalie de référence, signalée dans l'audit
            for border in (aa[2],bb[0]):
                boundaries.append(max(0,lo-border,border-hi)/scale)
    overlaps=[]
    for p in prediction:
        for a,b in zip(p.get('words',[]),p.get('words',[])[1:]):
            aa=a.get('bbox') or [a['x0'],a['y0'],a['x1']+1,a['y1']+1]
            bb=b.get('bbox') or [b['x0'],b['y0'],b['x1']+1,b['y1']+1]
            if aa[2] > bb[0]:
                overlaps.append(p['id'])
    audit=dict(overlapping_reference_words=sum(a['bbox'][2]>b['bbox'][0]
               for r in reference for a,b in zip(r.get('words',[]),r.get('words',[])[1:])))
    audit['word_annotation_granularity']=dict(Counter(r.get('word_annotation_granularity','word') for r in reference))
    audit['coordinate_transforms']=[json.loads(s) for s in sorted({json.dumps(r['reference_coordinates'],sort_keys=True) for r in reference if 'reference_coordinates' in r})]
    sequence=[r for r,p,_ in sorted(matches,key=lambda m:m[1]) if prediction[p].get('training_eligible',True)]
    pairs=len(sequence)*(len(sequence)-1)//2
    inversions=sum(a>b for i,a in enumerate(sequence) for b in sequence[i+1:])
    page_scores={}
    for name,normalizer in [('strict_NFC',nfc),('convention_v1',convention)]:
        ref='\n'.join(normalizer(r['text']) for r in reference)
        hyp='\n'.join(normalizer(p['text']) for p in prediction if p.get('training_eligible',True))
        page_scores[name]=dict(errors=lev(ref,hyp),characters=len(ref),cer=lev(ref,hyp)/len(ref) if ref else None)
    return dict(segmentation={str(t):segmentation(reference,prediction,t) for t in (.5,.75)},
                text=text_scores,refusals=dict(Counter(p.get('status','unknown') for p in prediction
                                                      if not p.get('training_eligible',True))),
                ordered_page_text=page_scores,
                order=dict(matched_lines=len(sequence),reference_lines=len(reference),
                           inversions=inversions,kendall=1-2*inversions/pairs if pairs else None),
                geometry=dict(reference_words=reference_words,measured_words=measured,
                              coverage=measured/reference_words if reference_words else None,
                              iou=distribution(giou),edges_pixels=distribution(edges),
                              edges_characters=distribution(edges_c),boundaries=distribution(boundaries),
                              boundaries_under_half=sum(b<=.5 for b in boundaries)/len(boundaries) if boundaries else None,
                              overlapping_prediction_lines=overlaps),reference_audit=audit,
                criteria_met=False)


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('reference');ap.add_argument('prediction');ap.add_argument('output')
    ap.add_argument('--reference-dpi',type=float)
    args=ap.parse_args()
    reference=load_reference(args.reference,dpi=args.reference_dpi)
    prediction=json.loads(Path(args.prediction).read_text())
    if Path(args.prediction).name=='annotations.json':
        prediction=exported_annotations(prediction,Path(args.prediction).parent)
    for p in prediction:
        p.setdefault('text','')
    result=score(reference,prediction)
    result['reference_sha256']=hashlib.sha256(Path(args.reference).read_bytes()).hexdigest()
    result['prediction_sha256']=hashlib.sha256(Path(args.prediction).read_bytes()).hexdigest()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'segmentation':{t:{k:v for k,v in s.items() if k not in ('omitted_ids','extra_ids')}
                                      for t,s in result['segmentation'].items()},
                      'refusals':result['refusals'],'reference_audit':result['reference_audit']},ensure_ascii=False))
