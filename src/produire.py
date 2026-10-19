#!/usr/bin/env python
"""Annotations automatiques : lecture identifiée → placement → ALTO.

Les reprises portent sur les vrais recadrages concernés. Une ligne non résolue
reste dans annotations.json avec son texte et son statut, et est exclue de
l'ALTO destiné à l'entraînement. Aucun contrôle ne certifie un CER nul.
"""
from __future__ import annotations
import argparse, json, os, sys, time
import hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'boxers'))
import numpy as np
from PIL import Image, ImageDraw
import cv2
import ink, alto, correct
from lecture import LineRequest, Reading, ResponseError, HerdrGeminiReader, JSONReader

IMPLEMENTATION_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def lignes_kraken(image: str, seuil_lignes: int | None = None):
    """Segmentation par lignes de base — robuste à l'inclinaison, contrairement
    à une détection par pics qui suppose des lignes horizontales régulières."""
    from kraken import blla
    from kraken.lib import vgsl
    im = Image.open(image).convert('L')
    seg = blla.segment(im)
    out = []
    for l in seg.lines:
        pts = np.asarray(l.boundary, float)
        x0, y0 = pts[:, 0].min(), pts[:, 1].min()
        x1, y1 = pts[:, 0].max(), pts[:, 1].max()
        out.append((int(x0), int(y0), int(x1), int(y1)))
    out.sort(key=lambda b: (b[1], b[0]))
    return out[:seuil_lignes] if seuil_lignes else out


class Ligne:
    """Ce qu'un boxer attend : du texte et une boîte de ligne, jamais de VT."""
    def __init__(self, texte, boite):
        self.text = texte
        self.words = texte.split()
        self.line_box = boite
        self.word_boxes = []


def produire(image, sortie, lire, boxer, max_lignes=None, par_bloc=12, verbose=True,
             requests=None, segmentation_strategy='auto',line_refinement='none'):
    if par_bloc < 1:
        raise ValueError('par_bloc doit être positif')
    out = Path(sortie); out.mkdir(parents=True, exist_ok=True)
    g = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    if g is None:
        raise ValueError(f'image illisible : {image}')
    H, W = g.shape
    pil = Image.open(image)
    t0 = time.time()
    automatic_segmentation = requests is None
    image_sha256 = hashlib.sha256(Path(image).read_bytes()).hexdigest()

    if requests is None:
        from segmentation import segment
        cache=out/'segmentation.json'
        config=out/'segmentation-config.json'
        signature={'image_sha256':image_sha256,'strategy':segmentation_strategy,
                   'version':'blla-rectangles-v1'}
        if line_refinement!='none':signature['line_refinement']=line_refinement
        if cache.exists() and config.exists() and json.loads(config.read_text()) == signature:
            layout=json.loads(cache.read_text())
        else:
            layout=segment(image,segmentation_strategy,cache_directory=out/'segmentation-tiles')
            if line_refinement=='ink':
                from segmentation import refine_lines
                layout=refine_lines(image,layout)
            cache.write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
            config.write_text(json.dumps(signature,indent=2),encoding='utf-8')
        if max_lignes:
            layout=layout[:max_lignes]
        requests=[LineRequest(row['id'],tuple(row.get('detector_bbox',row['bbox']))) for row in layout]
    else:
        requests = list(requests[:max_lignes] if max_lignes else requests)
        layout=[]
    layout_by_id={row['id']:row for row in layout}
    if len({r.id for r in requests}) != len(requests):
        raise ValueError('identifiants de ligne dupliqués')
    boites = [r.bbox for r in requests]
    for r in requests:
        x0, y0, x1, y1 = r.bbox
        if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H):
            raise ValueError(f'boîte hors image : {r.id}')
    if verbose: print(f"{W}×{H} | {len(boites)} lignes détectées", flush=True)

    # ── IDs pour les lecteurs structurés ; une vraie ligne par ancien appel ──
    journal, reprises = [], 0
    structured = hasattr(lire, 'read_lines')

    def read_batch(batch, scale=1):
        t = time.time()
        if structured:
            try:
                got = lire.read_lines(pil, batch, scale=scale)
                if [r.id for r in got] != [r.id for r in batch]:
                    raise ResponseError('association de lignes incohérente')
            except ResponseError as e:
                journal.append({'ids': [r.id for r in batch], 'error': str(e), 'scale': scale})
                if len(batch) > 1:
                    h = len(batch)//2
                    return read_batch(batch[:h], scale) + read_batch(batch[h:], scale)
                return [Reading(batch[0].id, '', True, getattr(lire, 'nom', 'VLM'), 'inconnu')]
        else:
            got = []
            for request in batch:
                crop = pil.crop(request.bbox)
                if scale > 1:
                    crop = crop.resize((crop.width*scale, crop.height*scale), Image.Resampling.NEAREST)
                texts, quality = lire(crop, 1)
                valid = len(texts) == 1 and isinstance(texts[0], str) and '\n' not in texts[0]
                got.append(Reading(request.id, texts[0] if valid else '',
                                   not valid or quality > .15, getattr(lire, 'nom', 'VLM'),
                                   getattr(lire, 'nom', 'VLM')))
        journal.append({'ids': [r.id for r in batch], 'attendu': len(batch),
                        'obtenu': len(got), 'scale': scale,
                        's': round(time.time()-t, 1)})
        if verbose: print(f"  lecture {batch[0].id}–{batch[-1].id} : {len(got)} lignes", flush=True)
        return got

    readings = []
    for s in range(0, len(requests), par_bloc):
        readings.extend(read_batch(requests[s:s+par_bloc]))
        (out/'readings.json').write_text(json.dumps([r.__dict__ for r in readings],ensure_ascii=False,indent=2),encoding='utf-8')

    # ── boîtes, et REFUS plutôt que comblement ──
    lignes, ecartes, annotations = [], [], []
    from placement_cache import PlacementCache
    boxer_signature=getattr(boxer,'cache_signature',None)
    placement_cache=PlacementCache(out/'geometry-cache',image_sha256,boxer_signature,dict(
        producer=IMPLEMENTATION_SHA256,ink=hashlib.sha256(Path(ink.__file__).read_bytes()).hexdigest(),
        correct=hashlib.sha256(Path(correct.__file__).read_bytes()).hexdigest())) if boxer_signature else None
    for request, reading in zip(requests, readings):
        bx, lid = request.bbox, request.id
        geometry_box=layout_by_id.get(lid,{}).get('bbox',list(bx))
        key=placement_cache.key(request,reading,dict(bbox=geometry_box,layout=layout_by_id.get(lid))) if placement_cache else None
        saved=placement_cache.load(key) if placement_cache else None
        if saved is not None:
            annotations.append(saved['annotation']);lignes.extend(saved['lines']);ecartes.extend(saved['refusals']);reprises+=saved['retries']
            if verbose:print(f'  géométrie {lid} : cache',flush=True)
            continue
        annotation=None;nlines=len(lignes);nrefusals=len(ecartes);nretries=reprises
        try:
            if reading.uncertain or not reading.text.strip():
                reading = read_batch([request], scale=2)[0]
                reprises += 1
            txt = reading.text
            annotation = {'id': lid, 'bbox': list(geometry_box), 'reading_bbox':list(bx),'text': txt,
                          'provider': reading.provider, 'model': reading.model,
                          'uncertain': reading.uncertain, 'training_eligible': False}
            if reading.job_id:annotation['reading_job_id']=reading.job_id
            if reading.model_display_terminal:annotation['model_display_terminal']=reading.model_display_terminal
            if reading.linebreak:
                annotation['linebreak']=reading.linebreak
                annotation['raw_text']=txt[:-1]+reading.linebreak['raw'] if reading.linebreak['role']=='hyphenation' else txt
            annotations.append(annotation)
            if reading.uncertain:
                annotation['status'] = 'lecture_non_resolue'
                ecartes.append({'ligne': lid, 'motif': 'lecture non résolue après reprise'}); continue
            if not txt.strip():
                annotation['status'] = 'texte_absent'
                ecartes.append({'ligne': lid, 'motif': 'aucun texte rendu'}); continue
            ln = Ligne(txt, bx)
            try:
                bs = boxer.boxes(g, ln)
            except Exception as e:
                if 'hors alphabet' in str(e):
                    # Relire un caractère exact ne répare pas l'alphabet du modèle.
                    # Le garder intact et exposer l'erreur pour le prochain aligneur.
                    annotation['status']='alphabet_aligneur_incompatible'
                    annotation['reason']=str(e)
                    ecartes.append({'ligne':lid,'motif':str(e),'texte':txt})
                    continue
                # Relecture ciblée, jamais remplacement par le décodage du CTC.
                retry = read_batch([request], scale=2)[0]
                reprises += 1
                annotation['retry_text'] = retry.text
                if not retry.uncertain and retry.text.strip() and retry.text != txt:
                    txt, ln = retry.text, Ligne(retry.text, bx)
                    annotation.update(text=txt, provider=retry.provider, model=retry.model)
                    if retry.job_id:annotation['reading_job_id']=retry.job_id
                    if retry.model_display_terminal:annotation['model_display_terminal']=retry.model_display_terminal
                    annotation.pop('linebreak',None);annotation.pop('raw_text',None)
                    if retry.linebreak:
                        annotation['linebreak']=retry.linebreak
                        annotation['raw_text']=txt[:-1]+retry.linebreak['raw'] if retry.linebreak['role']=='hyphenation' else txt
                    try:
                        bs = boxer.boxes(g, ln)
                    except Exception as retry_error:
                        e = retry_error
                        bs = None
                else:
                    bs = None
                if bs is None:
                    annotation['status'] = 'alignement_non_resolu'
                    annotation['reason'] = str(e)
                    ecartes.append({'ligne': lid, 'motif': f'placement impossible : {type(e).__name__}',
                                    'texte': txt[:80]}); continue
            if len(bs) != len(ln.words):
                annotation['status'] = 'compte_mots_incoherent'
                ecartes.append({'ligne': lid, 'motif': 'compte de mots incohérent',
                                'texte': txt[:80]}); continue
            bs = [tuple(int(v) for v in b) for b in bs]
            if any(not (0 <= a <= c < W and 0 <= b <= d < H) for a, b, c, d in bs) or \
                    any(a[2] >= b[0] for a, b in zip(bs, bs[1:])):
                annotation['status'] = 'geometrie_invalide'
                ecartes.append({'ligne': lid, 'motif': 'boîtes hors page ou mots superposés'}); continue
            annotation['alignment'] = getattr(boxer, 'last_alignment', None)
            annotation['chars'] = getattr(boxer, 'last_char_positions', None)
            # La rétraction de ligne et le masque du boxer sont indépendants.
            # Si un glyphe observé dépasse le rectangle rétracté, son encre doit
            # rester dans sa ligne ; élargir aux bords mesurés, jamais le couper.
            measured=[min(b[0] for b in bs),min(b[1] for b in bs),
                      max(b[2] for b in bs)+1,max(b[3] for b in bs)+1]
            expanded=[min(geometry_box[0],measured[0]),min(geometry_box[1],measured[1]),
                      max(geometry_box[2],measured[2]),max(geometry_box[3],measured[3])]
            if expanded!=list(geometry_box):
                annotation['geometry_bbox_before_words']=list(geometry_box)
                geometry_box=expanded;annotation['bbox']=expanded
            # Le coût d'encre signale une anomalie ; il ne mesure pas le CER.
            c, _, _ = correct.cout_ligne(g, bx[0], bx[2], bx[1], bx[3],
                                         (bx[1]+bx[3])//2, txt, ink.line_scale(bx))
            cw = c/max(1, len(ln.words)) if c < 1e8 else 99.0
            mots = [{'text': w, 'x0': q[0], 'y0': q[1], 'x1': q[2], 'y1': q[3],
                     'synthetic': False} for w, q in zip(ln.words, bs)]
            annotation.update(words=mots, cout=round(cw, 3), status='placee')
            lignes.append({'id': lid, 'text': txt, 'words': mots, 'cout': round(cw, 3),
                           'baseline':layout_by_id.get(lid,{}).get('baseline',[]),
                           'polygon':[[geometry_box[0],geometry_box[1]],[geometry_box[2],geometry_box[1]],
                                      [geometry_box[2],geometry_box[3]],[geometry_box[0],geometry_box[3]]],
                           'bbox': (geometry_box[0],geometry_box[1],geometry_box[2]-1,geometry_box[3]-1)})

        finally:
            # Un arrêt au milieu de l'alignement n'enregistre aucune donnée partielle.
            if placement_cache and sys.exc_info()[0] is None and annotation is not None and 'status' in annotation:
                placement_cache.store(key,annotation,lignes[nlines:],ecartes[nrefusals:],reprises-nretries)
                if verbose:print(f'  géométrie {lid} : {annotation["status"]}',flush=True)

    # seuil de suspicion calibré sur CE document, pas sur une valeur figée
    # Contrôle global : une segmentation dupliquée peut produire deux lignes
    # individuellement valides avec les mêmes mots sur les mêmes pixels.
    active=[];collisions=set()
    for lid,word in sorted(((l['id'],w) for l in lignes for w in l['words']),
                           key=lambda item:item[1]['y0']):
        active=[(other,box) for other,box in active if box['y1']>=word['y0']]
        for other,box in active:
            if other != lid and min(box['x1'],word['x1'])>=max(box['x0'],word['x0']):
                collisions.update((lid,other))
        active.append((lid,word))
    by_id={a['id']:a for a in annotations}
    for lid in sorted(collisions):
        by_id[lid]['status']='superposition_inter_lignes'
        ecartes.append({'ligne':lid,'motif':'mots superposés entre lignes détectées'})
    lignes=[l for l in lignes if l['id'] not in collisions]
    couts = [l['cout'] for l in lignes]
    seuil = correct.seuil_auto(couts) if len(couts) >= 8 else 1.0
    gardees = []
    by_id = {a['id']: a for a in annotations}
    for l in lignes:
        if l['cout'] > seuil*2.0:
            by_id[l['id']]['status'] = 'ajustement_encre_suspect'
            ecartes.append({'ligne': l['id'], 'motif': f"texte inajustable à l'encre "
                            f"(coût {l['cout']} > {round(seuil*2,2)})", 'texte': l['text'][:80]})
        else:
            gardees.append(l)
            by_id[l['id']].update(status='retenue', training_eligible=True)

    # Aucune appartenance à un article ni adjacency entre deux lignes ne peut
    # être déduite de leur seule position dans une liste de travail.
    bloc = [{'id': f'B_{l["id"]}', 'lines': [l],
             'x0': l['bbox'][0], 'y0': l['bbox'][1],
             'x1': l['bbox'][2], 'y1': l['bbox'][3]} for l in gardees]
    xml = alto.build(W, H, Path(image).name, bloc,
                     software=getattr(lire, 'nom', 'VLM') + ' + ' + boxer.name,
                     description="Pseudo-annotations automatiques : texte VLM et placement "
                     "géométrique contrôlé. Les lignes non résolues sont conservées dans "
                     "annotations.json et exclues de cet ALTO. CER nul non certifié. "
                     "Ordre de lecture et articles non inférés à cette étape.")
    schema_validation=alto.validate(xml)
    (out/'page.alto.xml').write_bytes(xml)

    im = pil.convert('RGB'); d = ImageDraw.Draw(im)
    for l in gardees:
        for m in l['words']:
            d.rectangle((m['x0'], m['y0'], m['x1'], m['y1']), outline=(0, 90, 255), width=2)
        d.rectangle(l['bbox'], outline=(0, 190, 0), width=2)
    for e in ecartes:
        b = next(r.bbox for r in requests if r.id == e['ligne'])
        d.rectangle(b, outline=(230, 0, 0), width=4)
    im.save(out/'overlay.jpg', quality=82)

    prov = {'image': Path(image).name, 'image_sha256':image_sha256, 'taille': [W, H],
            'lecture': getattr(lire, 'nom', 'VLM'), 'geometrie': boxer.name,
            'lignes_detectees': len(boites), 'lignes_retenues': len(gardees),
            'lignes_ecartees': len(ecartes),
            'lignes_reprises': reprises,
            'taux_non_resolu': round(100*len(ecartes)/max(1, len(boites)), 1),
            'mode': 'automatique', 'cer_zero_certifie': False, 'olr': 'non_execute',
            'schema_validation':schema_validation,
            'segmentation':segmentation_strategy if automatic_segmentation else 'external_diagnostic',
            'line_refinement':line_refinement,
            'implementation_sha256':IMPLEMENTATION_SHA256,
            'word_boundary_mode':getattr(boxer,'boundary_mode','not_ctc'),
            'geometry_cache':dict(hits=placement_cache.hits,saved=placement_cache.saved,version='local-placement-v1') if placement_cache else None,
            'diagnostic_only':not automatic_segmentation or bool(max_lignes),
            'complet': bool(boites) and len(gardees) == len(boites) and not max_lignes,
            'modeles_lecture': sorted({a['model'] for a in annotations}),
            'modeles_geometrie':sorted({a['alignment']['model_path'] for a in annotations
                                       if a.get('alignment') and a['alignment'].get('model_path')}),
            'requetes_lecture': getattr(lire, 'journal', []),
            'seuil_suspicion': round(seuil*2, 3), 'blocs': journal,
            'ecartees': ecartes, 'secondes': round(time.time()-t0, 1)}
    (out/'provenance.json').write_text(json.dumps(prov, ensure_ascii=False, indent=1))
    (out/'annotations.json').write_text(json.dumps(annotations, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'transcription.txt').write_text(
        "\n".join(f"{l['id']}\t{l['text']}" for l in gardees), encoding='utf-8')
    if verbose:
        print(f"\nALTO   → {out/'page.alto.xml'}")
        print(f"overlay→ {out/'overlay.jpg'}")
        print(f"{len(gardees)} lignes retenues · {len(ecartes)} écartées "
              f"({prov['taux_non_resolu']} % non résolues) · {prov['secondes']} s")
    return prov


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('sortie')
    ap.add_argument('--max-lignes', type=int, default=None)
    ap.add_argument('--par-bloc', type=int, default=12)
    ap.add_argument('--lecteur', choices=('churro', 'gemini', 'json'), default='churro')
    ap.add_argument('--gemini-pane', help='ID Herdr du terminal Gemini ouvert par l\'utilisateur')
    ap.add_argument('--reading-revision',default='v1',help='Révision de lecture : nouveau cache, aucun texte attendu fourni')
    ap.add_argument('--transcription-json', help='Réponse structurée à rejouer')
    ap.add_argument('--lignes-json', help='Liste de {id,bbox} pour isoler la lecture de la segmentation')
    ap.add_argument('--segmentation',choices=('full','tiles','auto','auto-v2'),default='auto')
    ap.add_argument('--boxer', choices=('connexe', 'forcectc'), default='connexe')
    ap.add_argument('--ctc-model', help='Modèle Kraken de placement forcé')
    a = ap.parse_args()
    if a.lecteur == 'gemini':
        if not a.gemini_pane: ap.error('--gemini-pane requis pour Gemini')
        lire = HerdrGeminiReader(a.gemini_pane, Path(a.sortie)/'lecture-jobs',revision=a.reading_revision)
    elif a.lecteur == 'json':
        if not a.transcription_json: ap.error('--transcription-json requis')
        lire = JSONReader(a.transcription_json)
    else:
        sys.path.insert(0, os.path.expanduser('~/vlm-alto-fresh/src'))
        import vlm as V
        be = V.OllamaVLM("hf.co/mradermacher/churro-3B-GGUF:Q4_K_M")
        def lire(crop, n):
            # L'appel ne porte que sur UNE ligne ; aucune récursion sur un
            # recadrage de bloc constant n'est possible.
            return V.block_robuste(be, lambda d, m, j=0: crop, 0, n, essais=3)
        lire.nom = 'churro-3B'
    if a.boxer == 'forcectc':
        from forcectc import ForceCTC
        boxer = ForceCTC(a.ctc_model)
    else:
        from connexe import Connexe
        boxer = Connexe()
    requests = None
    if a.lignes_json:
        rows = json.loads(Path(a.lignes_json).read_text(encoding='utf-8'))
        requests = [LineRequest(row['id'], tuple(row['bbox'])) for row in rows]
    produire(a.image, a.sortie, lire, boxer,
             max_lignes=a.max_lignes, par_bloc=a.par_bloc, requests=requests,
             segmentation_strategy=a.segmentation)
