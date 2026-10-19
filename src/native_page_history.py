"""Récupération read-only d'une réponse de page dans l'historique agy local.

Le format du payload natif reste opaque. Seul un objet JSON complet validé,
portant le UUID exact après le prompt original exact, peut être récupéré.
Les autres requêtes et les réponses ambiguës ne sont jamais utilisées.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3

from lecture import ResponseError


def conversation_hint(cwd):
    if not cwd:
        return None
    path=Path.home()/'.gemini/antigravity-cli/cache/last_conversations.json'
    try:
        value=json.loads(path.read_text()).get(cwd)
        return value if isinstance(value,str) and re.fullmatch(r'[0-9a-f-]{36}',value) else None
    except (OSError,ValueError,AttributeError):
        return None


def identified_response(conversation, prompt, requests, job_id, validator, base=None):
    first,rows=_bound_steps(conversation,prompt,job_id,base)
    decoder=json.JSONDecoder()
    for idx,kind,status,payload in rows:
        if not isinstance(payload,bytes):
            raise ResponseError('Format de payload natif inconnu')
        if kind==14:
            if job_id.encode() not in payload:break
            continue
        if kind!=15 or status!=3:continue
        if len(payload)>2_000_000:raise ResponseError('Payload natif excessif ; inspection identifiée requise')
        text=payload.decode('utf-8',errors='replace')
        candidates=[]
        for match in re.finditer(r'\{',text):
            try:
                value,_=decoder.raw_decode(text[match.start():])
                readings=validator(value,requests,job_id)
            except (ValueError,TypeError):continue
            candidates.append((value,readings))
        if not candidates:continue
        signatures={json.dumps([(r.id,r.text,r.uncertain,r.provider,r.model) for r in readings],ensure_ascii=False)
                    for _,readings in candidates}
        if len(signatures)!=1:raise ResponseError('Réponses natives ambiguës dans une même étape')
        value,readings=candidates[0]
        proof=_proof(conversation,prompt,job_id,first,idx,payload)
        proof['equivalent_objects']=len(candidates)
        return value,readings,proof
    raise ResponseError('Aucune réponse native complète identifiée')


def _proof(conversation,prompt,job_id,first,idx,payload):
    return dict(source='agy_native_sqlite_read_only',conversation_id=conversation,
                request_step_index=first,response_step_index=idx,response_step_type=15,
                response_step_status=3,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                payload_sha256=hashlib.sha256(payload).hexdigest(),job_id=job_id,adapter_revision=1)


def _bound_steps(conversation,prompt,job_id,base,authorized_continuations=(),out_of_band=False,native_not_before=None):
    if not isinstance(conversation,str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',conversation):
        raise ResponseError('Conversation native non identifiée')
    if not re.fullmatch(r'[0-9a-f]{32}',job_id) or not out_of_band and job_id not in prompt:
        raise ResponseError('UUID/prompt original absent')
    if out_of_band and (not isinstance(native_not_before,(int,float)) or not math.isfinite(native_not_before)
                        or native_not_before<=0):
        raise ResponseError('Époque de soumission native minimale absente')
    base=Path(base) if base else Path.home()/'.gemini/antigravity-cli/conversations'
    database=base/f'{conversation}.db'
    try:
        with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True,timeout=2) as db:
            # Seules les lignes humaines contenant ce UUID sont lues. Le
            # prompt complet doit correspondre exactement, chemins compris.
            humans=db.execute('SELECT idx,step_payload FROM steps WHERE step_type=14 '
                              'AND instr(step_payload,?)>0 ORDER BY idx',
                              ((prompt if out_of_band else job_id).encode(),)).fetchall()
            first=None
            matches=[]
            for idx,payload in humans:
                if isinstance(payload,bytes) and prompt.encode() in payload:
                    if out_of_band:
                        root=_protobuf_fields(payload)
                        if root.get(1)!=[(0,14)] or root.get(4)!=[(0,3)]:continue
                        fields=_protobuf_fields(root[19][0][1])
                        if fields.get(2)!=[(2,prompt.encode())]:continue
                        if _protobuf_fields(fields[3][0][1]).get(1)!=fields[2]:continue
                        stamp=_protobuf_fields(_protobuf_fields(root[5][0][1])[1][0][1])
                        created=stamp[1][0][1]+stamp.get(2,[(0,0)])[0][1]/1e9
                        if created<native_not_before:continue
                        matches.append(idx)
                        continue
                    first=idx
                    break
            if out_of_band:
                if matches!=[0]:
                    raise ResponseError('Prompt minimal absent, répété ou conversation non vierge')
                first=0
            if first is None:
                raise ResponseError('Prompt exact absent de la conversation native')
            if not isinstance(authorized_continuations,(tuple,list)) or any(
                    not isinstance(p,dict) or type(p.get('resume_step_index')) is not int
                    for p in authorized_continuations):
                raise ResponseError('Preuves de reprise natives invalides')
            approved={p['resume_step_index']:p for p in authorized_continuations}
            if len(approved)!=len(authorized_continuations):
                raise ResponseError('Reprises natives dupliquées')
            boundary=None
            following=(db.execute('SELECT idx,step_payload FROM steps WHERE idx>? AND step_type=14 ORDER BY idx',
                                  (first,)).fetchall() if out_of_band else
                       db.execute('SELECT idx,step_payload FROM steps WHERE idx>? AND step_type=14 '
                                  'AND instr(step_payload,?)=0 ORDER BY idx',(first,job_id.encode())).fetchall())
            verified=set()
            for idx,payload in following:
                if idx not in approved:
                    boundary=idx;break
                error=db.execute('SELECT idx,step_type,status,step_payload FROM steps WHERE idx=?',
                                 (idx-1,)).fetchone()
                try:evidence=_resume_evidence(conversation,prompt,job_id,first,idx,payload,error)
                except (KeyError,IndexError,UnicodeError) as exc:
                    raise ResponseError('Schéma natif de reprise inconnu') from exc
                if evidence!=approved[idx]:
                    raise ResponseError('Preuve de reprise native modifiée')
                verified.add(idx)
            if verified!=set(approved):
                raise ResponseError('Preuve de reprise étrangère au travail identifié')
            rows=db.execute('SELECT idx,step_type,status,step_payload FROM steps '
                            'WHERE idx>? AND idx<? ORDER BY idx',
                            (first,boundary if boundary is not None else 2**63-1)).fetchall()
    except (OSError,sqlite3.Error) as exc:
        raise ResponseError('Historique natif indisponible') from exc
    return first,rows


def _resume_evidence(conversation,prompt,job_id,first,idx,payload,error):
    """Un « reprends » explicite, juste après l'erreur réseau du même travail."""
    root=_protobuf_fields(payload)
    if root.get(1)!=[(0,14)] or root.get(4)!=[(0,3)] or len(root.get(19,[]))!=1:
        raise ResponseError('Schéma natif de reprise humaine inconnu')
    wire,human=root[19][0]
    if wire!=2:raise ResponseError('Reprise humaine native invalide')
    fields=_protobuf_fields(human)
    if fields.get(2)!=[(2,b'reprends')] or len(fields.get(3,[]))!=1:
        raise ResponseError('Instruction de reprise humaine non reconnue')
    raw_wire,raw=fields[3][0]
    if raw_wire!=2 or _protobuf_fields(raw).get(1)!=fields[2]:
        raise ResponseError('Instruction de reprise humaine ambiguë')
    if not error or error[:3]!=(idx-1,17,3):
        raise ResponseError('Reprise sans erreur native précédente')
    error_root=_protobuf_fields(error[3])
    if error_root.get(1)!=[(0,17)] or error_root.get(4)!=[(0,3)]:
        raise ResponseError('Schéma natif d’erreur inconnu')
    details=_protobuf_fields(_protobuf_fields(error_root[24][0][1])[3][0][1])
    message=details.get(2,[]);identifier=details.get(6,[])
    if len(message)!=1 or message[0][0]!=2 or b'request failed:' not in message[0][1] or \
            b'write: broken pipe' not in message[0][1]:
        raise ResponseError('Erreur native non reconnue comme incident réseau')
    if len(identifier)!=1 or identifier[0][0]!=2:
        raise ResponseError('Erreur native non identifiée')
    error_id=identifier[0][1].decode('ascii')
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}-'+str(idx-1),error_id):
        raise ResponseError('Identifiant d’erreur native incompatible')
    return dict(conversation_id=conversation,job_id=job_id,request_step_index=first,
                original_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                resume_step_index=idx,resume_payload_sha256=hashlib.sha256(payload).hexdigest(),
                resume_text='reprends',error_step_index=idx-1,error_id=error_id,
                error_payload_sha256=hashlib.sha256(error[3]).hexdigest(),
                error_category='explicit_native_network_broken_pipe',
                authorization_basis='explicit_human_resume_in_same_bound_native_conversation',
                blind_timeout_retry=False)


def attest_native_resume(conversation,prompt,job_id,resume_step_index,base=None,authorized_continuations=()):
    first,rows=_bound_steps(conversation,prompt,job_id,base,authorized_continuations)
    if not rows or rows[-1][0]!=resume_step_index-1:
        raise ResponseError('La reprise ne suit pas le travail identifié sans autre tâche')
    base=Path(base) if base else Path.home()/'.gemini/antigravity-cli/conversations'
    with sqlite3.connect((base/f'{conversation}.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
        human=db.execute('SELECT step_type,status,step_payload FROM steps WHERE idx=?',
                         (resume_step_index,)).fetchone()
    if not human or human[:2]!=(14,3):raise ResponseError('Reprise humaine absente')
    try:return _resume_evidence(conversation,prompt,job_id,first,resume_step_index,human[2],rows[-1])
    except (KeyError,IndexError,UnicodeError) as exc:
        raise ResponseError('Schéma natif de reprise inconnu') from exc


def resolve_conversation(candidates,prompt,job_id,base=None,out_of_band=False,native_not_before=None):
    """Un hint de session n'est accepté qu'après liaison au prompt exact."""
    found=[]
    for candidate in dict.fromkeys(candidates):
        try:first,_=_bound_steps(candidate,prompt,job_id,base,out_of_band=out_of_band,native_not_before=native_not_before)
        except ResponseError:continue
        found.append((candidate,first))
    if len(found)!=1:
        raise ResponseError('Conversation du prompt absente ou ambiguë')
    return found[0][0],dict(job_id=job_id,conversation_id=found[0][0],
                           request_step_index=found[0][1],basis=('exact_fresh_human_prompt_out_of_band_UUID' if out_of_band
                                                               else 'exact_original_prompt_and_UUID'),
                           supplied_hints=list(dict.fromkeys(candidates)))


def _protobuf_fields(data):
    """Fil de protobuf observé agy 1.2.17, sans dépendance aux pensées/rendu."""
    def varint(position):
        value=0
        for shift in range(0,70,7):
            if position>=len(data):break
            byte=data[position];position+=1;value|=(byte&127)<<shift
            if byte<128:return value,position
        raise ResponseError('Varint natif tronqué')
    fields={};position=0
    while position<len(data):
        tag,position=varint(position);number,wire=tag>>3,tag&7
        if number==0:raise ResponseError('Champ natif nul')
        if wire==0:value,position=varint(position)
        elif wire in (1,2,5):
            if wire==2:length,position=varint(position)
            else:length=8 if wire==1 else 4
            end=position+length
            if end>len(data):raise ResponseError('Champ natif tronqué')
            value=data[position:end];position=end
        else:raise ResponseError('Type de champ natif inconnu')
        fields.setdefault(number,[]).append((wire,value))
    return fields


def identified_markdown(conversation,prompt,job_id,base=None,authorized_continuations=(),prior_image_request=None,
                        out_of_band=False,native_not_before=None,allow_empty=False):
    first,rows=_bound_steps(conversation,prompt,job_id,base,authorized_continuations,out_of_band,native_not_before)
    saw_image_read=False
    prior_read=None
    if prior_image_request is not None:
        prior_first,prior_rows=_bound_steps(conversation,prior_image_request['prompt'],
                                          prior_image_request['job_id'],base)
        if prior_first>=first:raise ResponseError('Lecture image antérieure non établie')
        reads=[(i,p) for i,k,s,p in prior_rows if i<first and k==132 and s==3 and
               isinstance(p,bytes) and prior_image_request['image'].encode() in p]
        if not reads:raise ResponseError('Image source absente du travail antérieur identifié')
        read_idx,read_payload=reads[-1]
        prior_read=dict(request_step_index=prior_first,job_id=prior_image_request['job_id'],
                        image=prior_image_request['image'],read_step_index=read_idx,
                        read_payload_sha256=hashlib.sha256(read_payload).hexdigest())
        saw_image_read=True
    for idx,kind,status,payload in rows:
        if kind==14:
            continue
        if kind==132 and status==3:saw_image_read=True
        if kind!=15 or status!=3 or not saw_image_read:continue
        if not isinstance(payload,bytes) or len(payload)>2_000_000:
            raise ResponseError('Payload Markdown natif incompatible')
        root=_protobuf_fields(payload)
        if root.get(1)!=[(0,15)] or root.get(4)!=[(0,3)] or len(root.get(20,[]))!=1:
            raise ResponseError('Schéma natif de réponse inconnu')
        wire,planner=root[20][0]
        if wire!=2:raise ResponseError('Planner natif invalide')
        fields=_protobuf_fields(planner)
        if 7 in fields or 1 not in fields:continue  # appel outil/pensées, pas réponse finale
        if len(fields[1])!=1 or fields[1]!=fields.get(8) or fields[1][0][0]!=2:
            raise ResponseError('Texte final natif ambigu')
        try:text=fields[1][0][1].decode('utf-8')
        except UnicodeError as exc:raise ResponseError('Markdown natif non UTF-8') from exc
        if (not text.strip() and not allow_empty) or any(ord(c)<32 and c not in '\n\t\r' for c in text):
            raise ResponseError('Markdown natif vide/invalide')
        proof=_proof(conversation,prompt,job_id,first,idx,payload)
        if out_of_band:
            proof['request_binding']='exact_fresh_human_prompt_out_of_band_UUID'
            proof['native_request_not_before']=native_not_before
        proof.update(final_text_field='20.1',raw_final_text_field='20.8',equivalent_final_fields=True,
                     native_schema='agy-1.2.17-observed',format_reprompt=False)
        if not text.strip():proof['response_completeness']='native_empty_response_pending_review'
        if authorized_continuations:
            proof['authorized_continuations']=[p for p in authorized_continuations if p['resume_step_index']<idx]
        if prior_read:proof['prior_source_image_read']=prior_read
        trailing=[dict(step_index=i,step_type=k,status=s,payload_sha256=hashlib.sha256(p).hexdigest())
                  for i,k,s,p in rows if i>idx and k==17 and s==3 and isinstance(p,bytes)]
        if trailing:
            proof['trailing_native_errors']=trailing
            proof['response_completeness']='interrupted_native_generation'
        return text,proof
    raise ResponseError('Aucun Markdown final natif identifié après lecture image')


def input_view_audit(conversation,prompt,job_id,paths,base=None,authorized_continuations=(),out_of_band=False,
                     native_not_before=None):
    _,rows=_bound_steps(conversation,prompt,job_id,base,authorized_continuations,out_of_band,native_not_before)
    reads=[payload for _,kind,status,payload in rows if kind==132 and status==3 and isinstance(payload,bytes)]
    observed=[];missing=[]
    for path in paths:
        (observed if any(str(path).encode() in payload for payload in reads) else missing).append(str(path))
    return dict(expected=len(paths),observed=len(observed),observed_paths=observed,
                missing_paths=missing,coverage=len(observed)/len(paths) if paths else None,
                basis='exact_paths_in_completed_native_Read_steps')
