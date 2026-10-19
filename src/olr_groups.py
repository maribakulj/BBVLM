"""OLR compacte pour pages denses ; groupes exclusivement géométriques.

Gemini peut prendre des groupes entiers ou les scinder par IDs d'extrémités.
L'expansion contrôle toutes les lignes avant la validation OLR commune.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import uuid
from PIL import Image,ImageDraw,ImageFont
from lecture import HerdrGeminiReader,ReaderUnavailable,ResponseError,_terminal_text

COMPACT_INSTRUCTIONS=(
    'FORMAT COMPACT OBLIGATOIRE pour rester dans la capture native : '
    'format="bb-olr-tuples-v1", order_is_blocks=true. La liste blocks EST l’ordre de lecture. '
    'Chaque bloc est un tableau de7 éléments [id,type,group_ids,segments,region_ids,article_id,uncertain]. '
    'Chaque segment est [group_id,first_line_id,last_line_id]. Chaque article est [article_id,uncertain] ; '
    'ses blocs sont EXACTEMENT ceux dont article_id désigne cet article. Ne fournis pas reading_order '
    'ni block_ids redondants. rejected_regions est une liste de [region_id,motif_visuel_court]. '
    'Conserve job_id,provider,model à la racine. Un bloc/tableau par ligne, sans indenter chaque propriété. '
    'Aucune coordonnée ni texte de transcription. Exemple de bloc textuel : '
    '["B_1","heading",["G_0001"],[],[],"A_1",false]. Exemple non textuel : '
    '["B_S1","separator",[],[],["S_0001"],null,false]. '
    'Toutes les contraintes d’IDs, de couverture, d’articles et d’incertitude restent applicables. '
    'Cette représentation remplace seulement le schéma détaillé des objets, sans changer ton analyse.')


def decode_compact(value):
    if not isinstance(value,dict) or value.get('format')!='bb-olr-tuples-v1':return value
    allowed={'job_id','provider','model','format','order_is_blocks','blocks','articles','rejected_regions','model_display_terminal','visual_notes'}
    if set(value)-allowed or value.get('order_is_blocks') is not True:
        raise ResponseError('Ordre/champs OLR compact ambigus')
    blocks=[]
    if not isinstance(value.get('blocks'),list) or not isinstance(value.get('articles'),list):
        raise ResponseError('Listes OLR compact absentes')
    for row in value['blocks']:
        if not isinstance(row,list) or len(row)!=7 or not isinstance(row[3],list):
            raise ResponseError('Bloc compact doit contenir exactement7 éléments')
        segments=[]
        for segment in row[3]:
            if not isinstance(segment,list) or len(segment)!=3:raise ResponseError('Segment compact invalide')
            segments.append(dict(zip(('group_id','first','last'),segment)))
        blocks.append(dict(zip(('id','type','group_ids','segments','region_ids','article_id','uncertain'),
                               [*row[:3],segments,*row[4:]])))
    articles=[]
    for row in value['articles']:
        if not isinstance(row,list) or len(row)!=2:raise ResponseError('Article compact invalide')
        articles.append(dict(id=row[0],uncertain=row[1],block_ids=[b['id'] for b in blocks if b['article_id']==row[0]]))
    rejected=[]
    for row in value.get('rejected_regions',[]):
        if not isinstance(row,list) or len(row)!=2:raise ResponseError('Rejet compact invalide')
        rejected.append(dict(zip(('id','reason'),row)))
    return {**value,'blocks':blocks,'reading_order':[b['id'] for b in blocks],
            'articles':articles,'rejected_regions':rejected}


def groups(annotations,text_regions=()):
    from olr import column_components
    by_id={a['id']:a for a in annotations}
    if len(by_id)!=len(annotations):raise ValueError('IDs de ligne dupliqués')
    buckets={}
    for a in annotations:
        x0,y0,x1,y1=a['bbox'];area=max(1,(x1-x0)*(y1-y0));candidates=[]
        for region in text_regions:
            u0,v0,u1,v1=region['bbox']
            covered=max(0,min(x1,u1)-max(x0,u0))*max(0,min(y1,v1)-max(y0,v0))/area
            if covered>=.6:candidates.append(((u1-u0)*(v1-v0),region['id']))
        rid=min(candidates)[1] if candidates else 'unassigned'
        buckets.setdefault(rid,[]).append(a['id'])
    result=[]
    for rid,ids in buckets.items():
        ids=sorted(ids,key=lambda i:(by_id[i]['bbox'][1],by_id[i]['bbox'][0],i))
        # La hauteur des glyphes ne doit pas modifier la colonne d'une ligne.
        # Construire les composantes directement évite de fragmenter une même
        # colonne aux changements de corps, retrait ou ordre d'entrée.
        for part in column_components(ids,by_id):
            part=sorted(part,key=lambda i:(by_id[i]['bbox'][1],by_id[i]['bbox'][0],i))
            for start in range(0,len(part),40):
                line_ids=part[start:start+40];boxes=[by_id[i]['bbox'] for i in line_ids]
                result.append(dict(id=f'G_{len(result)+1:04d}',source_region=rid,line_ids=line_ids,
                    bbox=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]))
    if sorted(i for g in result for i in g['line_ids'])!=sorted(by_id):
        raise ValueError('Groupes ne couvrent pas exactement les lignes')
    return result


def expand(value,geometry,has_regions=False):
    compact=isinstance(value,dict) and value.get('format')=='bb-olr-tuples-v1'
    value=decode_compact(value)
    if not isinstance(value,dict) or not isinstance(value.get('blocks'),list):
        raise ResponseError('Réponse OLR groupée invalide')
    by_id={g['id']:g for g in geometry};blocks=[]
    for raw in value['blocks']:
        if not isinstance(raw,dict):raise ResponseError('Bloc groupé invalide')
        if 'line_ids' in raw or 'bbox' in raw:raise ResponseError('Bloc groupé contient coordonnées/ligne directe')
        full=raw.get('group_ids');segments=raw.get('segments')
        if not isinstance(full,list) or not isinstance(segments,list):
            raise ResponseError('Chaque bloc doit préciser group_ids et segments')
        ids=[]
        for gid in full:
            if gid not in by_id:raise ResponseError('Groupe inventé')
            ids.extend(by_id[gid]['line_ids'])
        for segment in segments:
            if not isinstance(segment,dict) or set(segment)!={'group_id','first','last'}:
                raise ResponseError('Segment doit référencer groupe et IDs de première/dernière ligne')
            if segment['group_id'] not in by_id:raise ResponseError('Groupe de segment inventé')
            source=by_id[segment['group_id']]['line_ids']
            if segment['first'] not in source or segment['last'] not in source:
                raise ResponseError('Extrémité de segment inventée')
            first,last=source.index(segment['first']),source.index(segment['last'])
            if last<first:raise ResponseError('Segment inversé')
            ids.extend(source[first:last+1])
        blocks.append({k:v for k,v in raw.items() if k not in ('group_ids','segments')})
        blocks[-1]['line_ids']=ids
        if compact and not has_regions and not blocks[-1].get('region_ids'):blocks[-1].pop('region_ids',None)
    return {**value,'blocks':blocks}


def validate_local_notes(raw,result):
    if result['articles'] or any(b['article_id'] is not None for b in result['blocks']):
        raise ResponseError('Passe locale : aucune appartenance globale aux articles autorisée')
    notes=raw.get('visual_notes')
    original_blocks=decode_compact(raw)['blocks']
    expected={b['id'] for b in original_blocks if b.get('group_ids') or b.get('segments')}
    if not isinstance(notes,list) or any(not isinstance(n,list) or len(n)!=4 or
            n[0] not in expected or any(not isinstance(s,str) or len(s)>160 for s in n[1:]) for n in notes):
        raise ResponseError('Notes visuelles locales absentes ou invalides')
    if len(notes)!=len({n[0] for n in notes}) or {n[0] for n in notes}!=expected:
        raise ResponseError('Notes locales : tous les blocs textuels exactement une fois')
    return notes


def write_inputs(image,annotations,geometry,regions,job,visual_detail='overview'):
    if visual_detail not in ('overview','native'):raise ValueError('Détail visuel OLR inconnu')
    by_id={a['id']:a for a in annotations};chunks=[];rows=[];size=0
    for group in geometry:
        lines=[{k:by_id[i][k] for k in ('id','bbox','text','uncertain','status')} for i in group['line_ids']]
        records=[dict(record='group',**group)]+[dict(record='line',group_id=group['id'],**line) for line in lines]
        encoded=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records)
        if rows and size+len(encoded.encode())>14000:
            chunks.append(''.join(rows));rows=[];size=0
        rows.append(encoded);size+=len(encoded.encode())
    if rows:chunks.append(''.join(rows))
    files=[]
    for i,chunk in enumerate(chunks,1):
        path=job/f'production-groups-{i:03d}.jsonl';path.write_text(chunk);files.append(str(path.resolve()))
    region_file=job/'production-regions.json';region_file.write_text(json.dumps(list(regions),ensure_ascii=False,indent=2));files.append(str(region_file.resolve()))
    im=Image.open(image).convert('RGB');scale=min(1,2048/max(im.size));im=im.resize((round(im.width*scale),round(im.height*scale)))
    draw=ImageDraw.Draw(im)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',14)
    except OSError:font=ImageFont.load_default()
    for group in geometry:
        box=[round(c*scale) for c in group['bbox']];draw.rectangle(box,outline='#b00000',width=2)
        label=group['id'];bb=draw.textbbox((box[0],box[1]),label,font=font);draw.rectangle(bb,fill='white');draw.text((box[0],box[1]),label,fill='#b00000',font=font)
    overview=job/'groups-overview.png';im.save(overview)
    if visual_detail=='native':
        from olr_views import write_native_views
        native=write_native_views(image,annotations,geometry,regions,job/'native-views')
        files.append(str((job/'native-views/manifest.json').resolve()))
        files.extend(v['path'] for v in native['views'])
    return files,str(overview.resolve())


def infer(image,annotations,pane,directory,timeout=900,regions=(),text_regions=(),scope='production',visual_detail='overview',hints=()):
    from olr import validate,repair_response,response_in_terminal
    if scope not in ('production','layout_only_no_vt','local_structure_no_vt'):raise ValueError('Portée OLR inconnue')
    directory=Path(directory);reader=HerdrGeminiReader(pane,directory,timeout)
    geometry=groups(annotations,text_regions)
    if visual_detail not in ('overview','native'):raise ValueError('Détail visuel OLR inconnu')
    signature=json.dumps([annotations,list(regions),geometry,scope],ensure_ascii=False,sort_keys=True).encode()+Path(image).read_bytes()
    protocol='olr-geometric-groups-v2' if visual_detail=='overview' else 'olr-geometric-groups-native-v1'
    if hints:
        signature+=json.dumps(list(hints),ensure_ascii=False,sort_keys=True).encode()
        protocol+='-local-hints-v1'
    job=directory/hashlib.sha256(protocol.encode()+signature).hexdigest()
    def parse(raw,job_id):
        result=validate(expand(raw,geometry,bool(regions)),annotations,job_id,regions)
        result['input_groups']=geometry;result['input_protocol']=protocol
        result['visual_detail']=visual_detail
        result['input_scope']=scope
        if scope=='local_structure_no_vt':
            result['visual_notes']=validate_local_notes(raw,result)
        return result
    def recover():
        job_id=json.loads((job/'request.json').read_text())['job_id']
        if (job/'response.json').exists():return parse(json.loads((job/'response.json').read_text()),job_id)
        def read_response():
            code,value,error=reader._call('read',pane,'--source','recent-unwrapped','--lines',str(max(1800,len(geometry)*30+400)))
            if code or value is None:raise ReaderUnavailable(error)
            terminal=_terminal_text(value.get('result',{}));reader.last_terminal=terminal;(job/'terminal.txt').write_text(terminal)
            return response_in_terminal(terminal,job_id,lambda raw:parse(raw,job_id))
        try:raw,result=read_response()
        except ResponseError as exc:
            raw,result=repair_response(reader,job,job_id,read_response,exc,COMPACT_INSTRUCTIONS)
        tmp=job/'response.tmp';tmp.write_text(json.dumps(raw,ensure_ascii=False,indent=2));tmp.replace(job/'response.json')
        reader._save_state(job,'completed');return result
    if (job/'request.json').exists():
        state=json.loads((job/'state.json').read_text()) if (job/'state.json').exists() else {}
        if state.get('phase') not in (None,'prepared'):return recover()
        job_id=json.loads((job/'request.json').read_text())['job_id'];prompt=(job/'prompt.txt').read_text()
    else:
        job.mkdir(parents=True);job_id=uuid.uuid4().hex
        files,overview=write_inputs(image,annotations,geometry,regions,job,visual_detail)
        if hints:
            hint_file=job/'production-local-hints.json';hint_file.write_text(json.dumps(list(hints),ensure_ascii=False,indent=2))
            files.append(str(hint_file.resolve()))
        prompt=(f'BBVLM OLR compacte, requête {job_id}. Lis UNIQUEMENT l’image {Path(image).resolve()}, '
            f'la vue avec IDs {overview} et TOUS les fichiers automatiques suivants : '+', '.join(files)+'. '
            'Aucun autre fichier, référence, recherche, shell, code ou écriture. Les groupes G sont des propositions '
            'géométriques, pas des articles : tu peux les fusionner/scinder. '+
            ('Les textes sont des lectures Gemini automatiques. ' if scope=='production' else
             'DIAGNOSTIC OLR SEUL : aucune VT n’a été produite ; les champs text vides ne sont pas des lectures. '
             'Déduis types/ordre/articles uniquement de l’image et des IDs géométriques automatiques. ')+
            'Ne modifie aucun texte ni coordonnée. Donne types, ordre de lecture des blocs et articles. '
            'Respecte les colonnes ; un article peut traverser plusieurs colonnes. Un titre est un bloc heading distinct. '
            'Pour chaque bloc, group_ids:[G fournis] prend des groupes entiers dans l’ordre désiré ; '
            'segments:[{group_id:G,first:ID première ligne,last:ID dernière ligne}] prend une séquence inclusive '
            'de lignes dans l’ordre géométrique du groupe. Pour inverser/réordonner, utilise plusieurs segments. '
            'Chaque ligne fournie doit être couverte EXACTEMENT UNE FOIS sur toute la réponse, même incertaine. '
            'Chaque candidat non textuel doit être accepté dans region_ids:[ID] ou rejected_regions:[{id,reason}]. '
            'Ne mélange pas lignes et régions dans un bloc. uncertain=true si type/ordre/article non résolu ; '
            'article_id=null pour éléments sans article. Aucun ID de ligne/groupe/région inventé, aucune coordonnée. '
            f'JSON indenté uniquement : job_id="{job_id}",provider="gemini",model=nom utilisé, '
            'blocks=[{id:"B_1",type:"text",group_ids:[],segments:[],region_ids:[],article_id:"A_1" ou null,uncertain:bool}], '
            'reading_order:[IDs B],articles:[{id:"A_1",block_ids:[IDs B],uncertain:bool}],rejected_regions:[]. '
            'Types : text,heading,caption,advert,table,illustration,separator,other. Une propriété/ID par ligne. '
            'Pour les blocs textuels, region_ids est vide. Si aucun candidat non textuel fourni, OMETS region_ids de tous les blocs. '
            'Un rejet de région exige un motif visuel, pas une faible certitude : conserve alors un bloc uncertain=true. '
            'Aucun texte hors JSON. '+COMPACT_INSTRUCTIONS)
        if visual_detail=='native':
            prompt+=(' Les vues PNG view-* et leur manifest sont des recadrages à pixels natifs, sans réduction. '
                     'Ouvre TOUTES ces vues pour analyser titres, frontières, colonnes et articles. '
                     'Leurs IDs sont dans une marge extérieure ; les parties se chevauchent et ne sont pas '
                     'de nouveaux blocs. Le JSONL garde les vrais groupes et IDs de ligne : une ligne reste '
                     'couverte exactement une fois, même si elle apparaît dans plusieurs vues. '
                     'La vue globale réduite sert uniquement à la navigation. Ne déclare pas toutes les '
                     'lignes incertaines parce que leur transcription est vide dans un diagnostic : '
                     'juge la structure visible dans les pixels ; conserve toute incertitude effectivement non résolue.')
        if scope=='local_structure_no_vt':
            prompt+=(' PORTÉE LOCALE : analyse seulement les frontières de blocs, leurs types et leur ordre '
                     'dans les groupes/candidats de cette requête. Il s’agit d’une partie de la page. '
                     'article_id=null pour TOUS les blocs et articles=[] : les articles globaux seront '
                     'analysés séparément. Ici uncertain juge seulement le type et l’ordre locaux, sans '
                     'incertitude artificielle causée par cette absence d’articles globaux. '
                     'Ajoute visual_notes, un tableau avec exactement un quadruplet par bloc textuel '
                     '[block_id,résumé_thématique_court,premiers_mots_visibles,derniers_mots_visibles]. '
                     'Chaque chaîne de note a au maximum160caractères ; conserve graphies visibles, ne '
                     'complète pas les mots coupés. Ces notes visuelles ne sont PAS une VT complète. '
                     'Si les mots sont illisibles, laisse la note correspondante vide et conserve '
                     'l’incertitude réellement non résolue. Une note par ligne, aucun autre champ.')
        if hints:
            prompt+=(' Le fichier production-local-hints contient des propositions issues de passes Gemini '
                     'locales sur pixels natifs, sans référence : types, IDs de lignes et notes visuelles. '
                     'Elles restent révisables ; réconcilie les frontières, titres, suites d’articles et '
                     'ordre GLOBAL de toute la page. Les notes ne sont pas une VT, ne modifie aucune '
                     'transcription de production, et n’invente aucun ID. Ne conserve pas les découpages '
                     'de lots comme frontières d’articles. Les articles peuvent traverser lots/colonnes.')
        (job/'prompt.txt').write_text(prompt)
        (job/'request.json').write_text(json.dumps(dict(job_id=job_id,geometry=geometry,image=str(Path(image).resolve()),inputs=files,overview=overview),indent=2))
        reader._save_state(job,'prepared')
    code,state,error=reader._call('get',pane);agent=(state or {}).get('result',{}).get('agent',{})
    if code or agent.get('agent') not in ('agy','gemini') or agent.get('agent_status') not in ('idle','done'):
        raise ReaderUnavailable('Gemini indisponible pour OLR groupée : '+error)
    reader._quota_guard();reader._save_state(job,'submission_intent')
    result=reader._call('prompt',pane,prompt,'--wait','--timeout',str(timeout*1000))
    reader._save_state(job,'submitted',code=result[0],result=result[1],error=result[2]);return recover()
