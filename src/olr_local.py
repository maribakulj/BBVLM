"""Compréhension OLR locale puis réconciliation globale, sans VT ni références.

Diagnostic indépendant des étapes de transcription/placement. Tous les groupes
et candidats sont conservés ; les coupures de lots n'impliquent pas d'articles.
"""
import hashlib
import json
from pathlib import Path
from olr_groups import groups, infer, write_inputs


def batches(annotations,text_regions,regions,count=8):
    if count<1:raise ValueError('taille de lot positive requise')
    geometry=groups(annotations,text_regions)
    geometry=sorted(geometry,key=lambda g:(g['bbox'][0],g['bbox'][1],g['id']))
    by_id={a['id']:a for a in annotations};out=[]
    for start in range(0,len(geometry),count):
        selected=geometry[start:start+count]
        out.append(dict(annotations=[by_id[i] for g in selected for i in g['line_ids']],regions=[]))
    # Les candidats non textuels ont leurs propres vues ; aucun rejet implicite.
    for start in range(0,len(regions),count):
        out.append(dict(annotations=[],regions=list(regions[start:start+count])))
    assigned=[a['id'] for b in out for a in b['annotations']]
    if sorted(assigned)!=sorted(by_id):raise ValueError('Couverture locale des lignes incohérente')
    return out


def local_hints(result,batch_id):
    notes={n[0]:n[1:] for n in result.get('visual_notes',[])}
    return [dict(batch_id=batch_id,block_id=b['id'],type=b['type'],line_ids=b['line_ids'],
                 region_ids=b.get('region_ids',[]),uncertain=b['uncertain'],
                 visual_notes=notes.get(b.get('semantic_block_id',b['id']),[]),
                 reading_job_id=result['job_id'],model_claim=result['model'],
                 model_display_terminal=result.get('model_display_terminal'),
                 source='Gemini native local visual analysis; no VT or references') for b in result['blocks']]


def run(image,annotations,text_regions,regions,pane,directory,count=8,prepare_only=False):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    schedule=batches(annotations,text_regions,regions,count)
    signature=hashlib.sha256(Path(image).read_bytes()+json.dumps([annotations,text_regions,regions,count],sort_keys=True).encode()).hexdigest()
    metadata=directory/'local-config.json';config=dict(signature=signature,scope='OLR-only no VT',count=count,protocol='local-structure-no-vt-v1')
    if metadata.exists() and json.loads(metadata.read_text())!=config:raise ValueError('Configuration locale différente ; choisir un nouveau dossier')
    metadata.write_text(json.dumps(config,indent=2))
    hints=[]
    for i,batch in enumerate(schedule,1):
        bid=f'local-{i:03d}';out=directory/bid;out.mkdir(exist_ok=True)
        if prepare_only:
            geometry=groups(batch['annotations'],text_regions)
            files,overview=write_inputs(image,batch['annotations'],geometry,batch['regions'],out,'native')
            (out/'prepared.json').write_text(json.dumps(dict(files=files,overview=overview,submitted=False),indent=2))
            continue
        result=infer(image,batch['annotations'],pane,out/'jobs',regions=batch['regions'],text_regions=text_regions,
                     scope='local_structure_no_vt',visual_detail='native')
        (out/'olr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        hints.extend(local_hints(result,bid))
        (directory/'progress.json').write_text(json.dumps(dict(completed=i,total=len(schedule),last_batch=bid,criteria_met=False),indent=2))
    if prepare_only:
        return dict(local_batches=len(schedule),submitted=False,criteria_met=False,scope='input preparation only')
    (directory/'local-hints.json').write_text(json.dumps(hints,ensure_ascii=False,indent=2))
    result=infer(image,annotations,pane,directory/'global-jobs',regions=regions,text_regions=text_regions,
                 scope='layout_only_no_vt',hints=hints)
    result['local_analysis']=dict(batches=len(schedule),hints=len(hints),protocol=config['protocol'],scope='OLR-only no VT')
    (directory/'olr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return dict(blocks=len(result['blocks']),articles=len(result['articles']),local_batches=len(schedule),
                criteria_met=False,scope='OLR-only diagnostic; no VT/word geometry/training certificate')
