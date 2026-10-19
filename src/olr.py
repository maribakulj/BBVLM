"""Compréhension Gemini par IDs ; toute coordonnée provient de la géométrie."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import uuid
from statistics import median
from lecture import HerdrGeminiReader, ReaderUnavailable, ResponseError, MalformedResponse, _terminal_text

TYPES={'text','heading','caption','advert','table','illustration','separator','other'}


def response_in_terminal(text,job_id,validator):
    decoder=json.JSONDecoder();malformed=None
    for pos,ch in enumerate(text):
        if ch!='{':continue
        try:raw,_=decoder.raw_decode(text[pos:])
        except ValueError:continue
        if not isinstance(raw,dict) or raw.get('job_id')!=job_id:continue
        try:result=validator(raw)
        except (ValueError,TypeError,KeyError) as exc:
            if raw.get('provider')=='gemini' and isinstance(raw.get('model'),str) and 'blocks' in raw:
                malformed=MalformedResponse(str(exc),raw)
            continue
        displays=re.findall(r'(Gemini\s+[\d.]+\s+(?:Flash|Pro)\s*·\s*\w+)\s*$',text,re.MULTILINE)
        if displays:raw['model_display_terminal']=displays[-1];result['model_display_terminal']=displays[-1]
        return raw,result
    if malformed is not None:raise malformed
    raise ResponseError('JSON OLR identifié absent ou incomplet')


def column_components(ids, by_id):
    """Composantes physiques, indépendantes d'un ordre de lecture déclaré."""
    components=[]
    median_width=median(by_id[lid]['bbox'][2]-by_id[lid]['bbox'][0] for lid in ids) if ids else 0
    for lid in ids:
        x0,y0,x1,y1=by_id[lid]['bbox']
        spanning=x1-x0>1.6*median_width
        linked=[]
        for ci,group in enumerate(components):
            for other in group:
                a,b,c,d=by_id[other]['bbox']
                if spanning!=(c-a>1.6*median_width):continue
                if max(0,y0-d,b-y1)>2*max(y1-y0,d-b):continue
                if max(0,min(c,x1)-max(a,x0))/max(1,min(c-a,x1-x0)) >= .5:
                    linked.append(ci);break
        group=[lid]
        for ci in reversed(linked):
            group.extend(components.pop(ci))
        components.append(group)
    return components


def column_parts(ids, by_id):
    """Scinde les colonnes disjointes en préservant l'ordre déclaré des lignes.

    Un article peut traverser plusieurs colonnes ; sa boîte de bloc ne doit
    pas englober les colonnes intermédiaires. Les articles restent inchangés.
    """
    components=column_components(ids,by_id)
    membership={lid:ci for ci,group in enumerate(components) for lid in group}
    parts=[];previous=None
    for lid in ids:
        if membership[lid] != previous:
            parts.append([]);previous=membership[lid]
        parts[-1].append(lid)
    return parts


def validate(value, annotations, job_id, regions=()):
    if not isinstance(value,dict) or value.get('job_id') != job_id:
        raise ResponseError('Requête OLR incohérente')
    if value.get('provider') != 'gemini' or not isinstance(value.get('model'),str) or not value['model'].strip():
        raise ResponseError('Provenance OLR absente')
    for key in ('blocks','reading_order','articles'):
        if not isinstance(value.get(key),list):
            raise ResponseError(f'OLR sans liste {key}')
    expected={a['id'] for a in annotations};region_by_id={r['id']:r for r in regions}
    blocks={};used=[];used_regions=[]
    for block in value['blocks']:
        if not isinstance(block,dict):
            raise ResponseError('Bloc OLR invalide')
        bid=block.get('id')
        if not isinstance(bid,str) or not re.fullmatch(r'B_[A-Za-z0-9_]+',bid) or bid in blocks:
            raise ResponseError('ID de bloc OLR invalide ou dupliqué')
        fields={'id','type','line_ids','article_id','uncertain'}
        if regions:fields.add('region_ids')
        if set(block) != fields:
            raise ResponseError('Champs de bloc OLR inattendus (aucune coordonnée autorisée)')
        if block['type'] not in TYPES or type(block['uncertain']) is not bool:
            raise ResponseError('Type/incertitude de bloc invalide')
        ids=block['line_ids']
        if not isinstance(ids,list) or any(i not in expected for i in ids):
            raise ResponseError('Lignes OLR absentes/inconnues')
        rids=block.get('region_ids',[])
        if not isinstance(rids,list) or any(i not in region_by_id for i in rids):
            raise ResponseError('Région géométrique OLR inconnue')
        if not ids and (len(rids) != 1 or block['type'] not in {'illustration','separator','other'}):
            raise ResponseError('Bloc OLR vide ou non-texte sans région unique')
        if ids and rids:
            raise ResponseError('Ne pas mélanger boîtes textuelles et régions non textuelles')
        used_regions.extend(rids)
        used.extend(ids);blocks[bid]=block
    if len(used) != len(set(used)) or set(used) != expected:
        raise ResponseError('OLR omet ou duplique des lignes')
    rejected=value.get('rejected_regions',[])
    if not isinstance(rejected,list) or any(not isinstance(r,dict) or set(r)!={'id','reason'} or
            r['id'] not in region_by_id or not isinstance(r['reason'],str) or not r['reason'].strip() for r in rejected):
        raise ResponseError('Refus de région OLR invalide')
    accounted=used_regions+[r['id'] for r in rejected]
    if len(accounted)!=len(set(accounted)) or set(accounted)!=set(region_by_id):
        raise ResponseError('OLR omet ou duplique des candidats non textuels')
    order=value['reading_order']
    if len(order) != len(set(order)) or set(order) != set(blocks):
        raise ResponseError('Ordre OLR incohérent')
    articles={};article_blocks=[]
    for article in value['articles']:
        if not isinstance(article,dict) or set(article) != {'id','block_ids','uncertain'}:
            raise ResponseError('Article OLR invalide')
        aid=article['id'];ids=article['block_ids']
        if not isinstance(aid,str) or not re.fullmatch(r'A_[A-Za-z0-9_]+',aid) or aid in articles:
            raise ResponseError('ID article invalide ou dupliqué')
        if type(article['uncertain']) is not bool or not isinstance(ids,list) or not ids:
            raise ResponseError('Article vide ou incertitude invalide')
        if any(b not in blocks or blocks[b]['article_id'] != aid for b in ids):
            raise ResponseError('Appartenance article/bloc incohérente')
        articles[aid]=article;article_blocks.extend(ids)
    if len(article_blocks) != len(set(article_blocks)):
        raise ResponseError('Bloc dans plusieurs articles')
    for bid,block in blocks.items():
        aid=block['article_id']
        if aid is not None and (aid not in articles or bid not in article_blocks):
            raise ResponseError('Référence article absente')
    by_id={a['id']:a for a in annotations}
    result={**value,'blocks':[]};replacements={}
    for bid in order:
        block=blocks[bid]
        parts=column_parts(block['line_ids'],by_id) if block['line_ids'] else [[]]
        replacements[bid]=[]
        for pi,ids in enumerate(parts,1):
            boxes=[by_id[i]['bbox'] for i in ids] if ids else [region_by_id[block['region_ids'][0]]['bbox']]
            bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),
                  max(b[2] for b in boxes),max(b[3] for b in boxes)]
            part_id=bid if len(parts)==1 else f'{bid}_G{pi}'
            replacements[bid].append(part_id)
            result['blocks'].append({**block,'id':part_id,'line_ids':ids,'bbox':bbox,
                                    'semantic_block_id':bid})
    result['reading_order']=[b['id'] for b in result['blocks']]
    if len(result['reading_order'])!=len(set(result['reading_order'])):
        raise ResponseError('Collision après scission des blocs géométriques')
    result['articles']=[{**a,'block_ids':[p for bid in a['block_ids'] for p in replacements[bid]]}
                        for a in value['articles']]
    result['geometry_source']='detected_line_boxes_and_image_only_nontext_candidates'
    result['scope']='text_and_nontext_candidates' if regions else 'text_lines_only; nontext detection remains unmeasured'
    result['nontext_candidates']=len(regions)
    result['nontext_rejected']=len(rejected)
    result['complete']=not any(b['uncertain'] for b in result['blocks']) and \
                       not any(a['uncertain'] for a in result['articles'])
    return result


def recover(reader, directory, annotations, regions=()):
    directory=Path(directory)
    manifest=json.loads((directory/'request.json').read_text())
    job_id=manifest['job_id']
    if (directory/'response.json').exists():
        return validate(json.loads((directory/'response.json').read_text()),annotations,job_id,regions)
    def read_response():
        code,value,error=reader._call('read',reader.pane,'--source','recent-unwrapped','--lines','1800')
        if code or value is None:raise ReaderUnavailable(error)
        text=_terminal_text(value.get('result',{}));reader.last_terminal=text
        (directory/'terminal.txt').write_text(text,encoding='utf-8')
        return response_in_terminal(text,job_id,lambda raw:validate(raw,annotations,job_id,regions))
    try:
        raw,result=read_response()
    except ResponseError as exc:
        raw,result=repair_response(reader,directory,job_id,read_response,exc)
    tmp=directory/'response.tmp';tmp.write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(directory/'response.json');reader._save_state(directory,'completed')
    return result


def repair_response(reader,directory,job_id,read_response,error,format_instructions=''):
    """Reprise native établie, puis réparations bornées de format/contrat.

    Les résultats et UUID restent sauvegardés. Une intention de réparation
    ambiguë n'est jamais renvoyée ; aucune référence ne participe au contrat.
    """
    directory=Path(directory)
    resumed=reader._resume_after_native_quota(directory,[],job_id,response_callback=read_response)
    if resumed is not None:return resumed
    resumed=reader._resume_after_cancelled_shell(directory,[],job_id,response_callback=read_response)
    if resumed is not None:return resumed
    prompt=(directory/'prompt.txt').read_text()
    resumed=reader._resume_after_native_auth_refresh(directory,[],job_id,
                   response_callback=read_response,resume_instructions=prompt)
    if resumed is not None:return resumed
    code,state,native_error=reader._call('get',reader.pane)
    agent=(state or {}).get('result',{}).get('agent',{})
    if code or agent.get('agent') not in ('agy','gemini') or agent.get('agent_status') not in ('idle','done'):
        raise ReaderUnavailable(f'OLR {job_id} encore active ou bloquée ; conserver la requête : {native_error}') from error
    saved=json.loads((directory/'state.json').read_text()) if (directory/'state.json').exists() else {}
    terminal=reader.last_terminal or ''
    delivered=saved.get('code')==0 and saved.get('result',{}).get('result',{}).get('agent',{}).get('agent_status') in ('idle','done')
    identified=isinstance(error,MalformedResponse) and error.value.get('job_id')==job_id
    if not delivered and not (job_id in terminal and (saved.get('phase')=='submitted' or identified)):
        raise ReaderUnavailable(f'Livraison OLR {job_id} non établie ; aucune resoumission après timeout') from error
    path=directory/'olr-format-recovery.json';stage='format';details=''
    if path.exists():
        # Un second tour exige une réponse compacte complète et identifiée
        # après la réparation terminée. Il ne récupère pas un timeout aveugle.
        if not (identified and delivered and saved.get('phase') in ('olr_format_requested','controlled_tool_resumed')
                and error.value.get('format')=='bb-olr-tuples-v1' and error.value.get('blocks')):
            raise ReaderUnavailable(f'Réparation OLR {job_id} déjà tentée ; récupérer son résultat, sans renvoi') from error
        stage='contract';path=directory/'olr-contract-recovery.json'
        if path.exists():
            raise ReaderUnavailable(f'Réparation de contrat OLR {job_id} déjà tentée ; récupérer son résultat, sans renvoi') from error
        from collections import Counter
        ids=[b[0] for b in error.value['blocks'] if isinstance(b,list) and b]
        duplicates=[bid for bid,n in Counter(ids).items() if n>1]
        if duplicates:details=' IDs de blocs répétés dans ton retour : '+', '.join(map(str,duplicates))+'.'
        for key in ('blocks','articles','rejected_regions'):
            if key in error.value and not isinstance(error.value[key],list):
                details+=f' {key} est un {type(error.value[key]).__name__} ; ce champ doit être un tableau JSON.'
        raw=json.dumps(error.value,ensure_ascii=False,indent=2)
        (directory/'olr-contract-invalid-response.json').write_text(raw)
    evidence=dict(job_id=job_id,error=str(error),native_state=state,previous_state=saved,
                  terminal_sha256=hashlib.sha256(terminal.encode()).hexdigest(),blind_timeout_retry=False,
                  stage=stage,identified_response_sha256=hashlib.sha256(json.dumps(error.value,sort_keys=True).encode()).hexdigest() if identified else None)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(evidence,ensure_ascii=False,indent=2));tmp.replace(path)
    fallback=(f'Réparation de format de la requête OLR {job_id}, dont le retour natif est terminé. '
              f'Le JSON ne satisfait pas son contrat : {error}.{details} Réaffiche une réponse complète en respectant '
              'exactement les IDs et les champs ci-dessous, toutes les lignes et candidats une fois. '
              'Conserve ton analyse visuelle, sans inventer texte ni coordonnées. Aucun shell, journal interne '
              'ou fichier hors des entrées autorisées. Une propriété ou ID par ligne.\n'+prompt)
    if format_instructions:fallback+='\nPOUR CETTE REPRISE : '+format_instructions
    (directory/f'olr-{stage}-prompt.txt').write_text(fallback)
    reader._save_state(directory,f'olr_{stage}_intent')
    result=reader._call('prompt',reader.pane,fallback,'--wait','--timeout',str(reader.timeout*1000))
    reader._save_state(directory,f'olr_{stage}_requested',code=result[0],result=result[1],error=result[2])
    try:return read_response()
    except ResponseError as exc:
        raise ReaderUnavailable(f'OLR {job_id} reste invalide après réparation ; preuves conservées dans {directory}') from exc


def infer(image, annotations, pane, directory, timeout=900, regions=(),text_regions=(),scope='production'):
    """Ne reçoit que des sorties de production, aucune annotation de référence."""
    if len(annotations)>128:
        from olr_groups import infer as infer_groups
        return infer_groups(image,annotations,pane,directory,timeout,regions,text_regions,scope)
    if scope!='production':raise ValueError('Le diagnostic layout-only exige la voie groupée explicite')
    directory=Path(directory);reader=HerdrGeminiReader(pane,directory,timeout)
    payload=[{k:a[k] for k in ('id','bbox','text','uncertain','status')} for a in annotations]
    signature=json.dumps([payload,list(regions)] if regions else payload,ensure_ascii=False,sort_keys=True).encode()+Path(image).read_bytes()
    key=hashlib.sha256((b'olr-regions-v2' if regions else b'olr-ids-v1')+signature).hexdigest();job=directory/key
    if (job/'request.json').exists():
        return recover(reader,job,annotations,regions)
    code,state,error=reader._call('get',pane)
    agent=(state or {}).get('result',{}).get('agent',{})
    if code or agent.get('agent') not in ('agy','gemini') or agent.get('agent_status') not in ('idle','done'):
        raise ReaderUnavailable('Gemini indisponible pour OLR : '+error)
    job.mkdir(parents=True,exist_ok=False);job_id=uuid.uuid4().hex
    source=job/'production-lines.json';source.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    region_source=job/'production-regions.json'
    region_source.write_text(json.dumps(list(regions),ensure_ascii=False,indent=2),encoding='utf-8')
    (job/'request.json').write_text(json.dumps(dict(job_id=job_id,image=str(Path(image).resolve()),input=str(source.resolve())),indent=2))
    prompt=(f'BBVLM OLR, requête {job_id}. Tu peux lire UNIQUEMENT cette image '
            f'{Path(image).resolve()} et ces sorties automatiques {source.resolve()}. '
            'Aucun autre fichier, shell, code, recherche, référence ni écriture. '
            'Ne modifie ni texte ni coordonnées. Regroupe les IDs de lignes en '
            'blocs typés, ordonne les blocs et les lignes de chacun, attribue les '
            'blocs à des articles. Respecte les colonnes et les titres traversants. '
            'Toutes les lignes fournies doivent apparaître exactement une fois, '
            'même refusées. Si le regroupement est douteux, uncertain=true ; '
            'article_id=null pour les éléments sans article (numéro, bandeau…). '
            'Tu ne dois inventer aucun ID de ligne ni fournir des coordonnées. '
            f'Rends du JSON indenté : job_id="{job_id}", provider="gemini", '
            'model=nom utilisé, blocks=[{id:"B_1",type:"text",line_ids:[IDs],'
            'article_id:"A_1" ou null,uncertain:bool}], reading_order=[IDs des blocs], '
            'articles=[{id:"A_1",block_ids:[IDs],uncertain:bool}]. '
            'Types possibles : text, heading, caption, advert, table, other. '
            'Une propriété ou un ID par ligne pour éviter les retours du terminal. '
            'Aucun texte hors JSON.')
    if regions:
        prompt+=(f' Lis aussi UNIQUEMENT les candidats géométriques automatiques {region_source.resolve()}. '
                 'Chaque bloc ajoute region_ids:[]. Pour un candidat non textuel accepté, '
                 'crée un bloc avec line_ids:[], region_ids:[un ID fourni], type illustration, '
                 'separator ou other. Ne mélange pas lignes et candidats dans un bloc. '
                 'Chaque candidat doit apparaître une fois, dans un bloc ou dans '
                 'rejected_regions:[{id:ID,reason:motif visuel}]. Un motif de rejet ne '
                 'peut être une faible certitude : conserve alors un bloc uncertain=true. '
                 'Aucune coordonnée ni ID inventé.')
    (job/'prompt.txt').write_text(prompt,encoding='utf-8');reader._quota_guard();reader._save_state(job,'submission_intent')
    result=reader._call('prompt',pane,prompt,'--wait','--timeout',str(timeout*1000))
    reader._save_state(job,'submitted',code=result[0],result=result[1],error=result[2])
    return recover(reader,job,annotations,regions)


if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('output_directory');ap.add_argument('--gemini-pane',required=True)
    args=ap.parse_args();out=Path(args.output_directory)
    annotations=json.loads((out/'annotations.json').read_text())
    result=infer(args.image,annotations,args.gemini_pane,out/'olr-jobs')
    (out/'olr.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(blocks=len(result['blocks']),articles=len(result['articles']),complete=result['complete'])))
