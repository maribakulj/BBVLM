"""Lecteurs à identifiants de lignes et relais Gemini via un terminal Herdr.

L'image et les boîtes de lignes sont les seules entrées visuelles. Le protocole
ne transporte ni texte de référence ni boîtes de mots. Les réponses sont
validées avant toute association texte/ligne.
"""
from __future__ import annotations

from dataclasses import dataclass,replace
import hashlib
import json
from pathlib import Path
import subprocess
import re
import unicodedata
import uuid

from PIL import Image, ImageDraw, ImageFont


class ResponseError(ValueError):
    """Réponse récupérée, mais impropre à l'association texte/ligne."""


class ReaderUnavailable(RuntimeError):
    """Relais indisponible ou agent bloqué ; ne pas resoumettre à l'aveugle."""


class ReaderQuotaExceeded(ReaderUnavailable):
    """Quota natif observé, avec date de reprise annoncée par le service."""
    def __init__(self,evidence):
        self.evidence=evidence
        self.retry_at=evidence['retry_at']
        super().__init__(f'Quota Gemini natif atteint ; reprise après {self.retry_at:.0f}, '
                         f'preuve {evidence["error_id"]}, aucune soumission pendant l’attente')


class MalformedResponse(ResponseError):
    """Objet de réponse complet et identifié, mais contrat invalide."""
    def __init__(self,reason,value):
        super().__init__(reason);self.value=value


@dataclass(frozen=True)
class LineRequest:
    id: str
    bbox: tuple[int, int, int, int]  # rectangle PIL, fin exclusive


@dataclass(frozen=True)
class Reading:
    id: str
    text: str
    uncertain: bool
    provider: str
    model: str
    linebreak: dict | None = None
    job_id: str | None = None
    model_display_terminal: str | None = None


def validate_response(value, requests, job_id=None):
    if not isinstance(value, dict) or not isinstance(value.get('lines'), list):
        raise ResponseError('Objet JSON avec liste lines requis')
    if job_id is not None and value.get('job_id') != job_id:
        raise ResponseError('Réponse d\'une autre requête')
    provider, model = value.get('provider'), value.get('model')
    if not isinstance(provider, str) or not provider.strip():
        raise ResponseError('Fournisseur absent')
    if not isinstance(model, str) or not model.strip() or model.startswith('<'):
        raise ResponseError('Modèle effectivement utilisé absent')
    expected = [r.id for r in requests]
    if len(set(expected)) != len(expected):
        raise ValueError('Identifiants de requête dupliqués')
    found = {}
    for row in value['lines']:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str):
            raise ResponseError('Identifiant de ligne absent')
        lid, text = row['id'], row.get('text')
        if lid not in expected or lid in found:
            raise ResponseError(f'Identifiant inconnu ou dupliqué : {lid}')
        if 'text_parts' in row:
            parts = row['text_parts']
            if 'text' in row or not isinstance(parts, list) or not parts or \
                    any(not isinstance(part, str) for part in parts):
                raise ResponseError(f'Segments de texte invalides : {lid}')
            text = ''.join(parts)
        if not isinstance(text, str) or any(c in text for c in '\r\n\t\x00'):
            raise ResponseError(f'Texte multiligne ou invalide : {lid}')
        if type(row.get('uncertain')) is not bool:
            raise ResponseError(f'Indicateur uncertain invalide : {lid}')
        linebreak=row.get('linebreak')
        if linebreak is not None:
            if not isinstance(linebreak,dict) or set(linebreak)!={'raw','role'} or \
                    linebreak['role'] not in {'hyphenation','other'} or \
                    not isinstance(linebreak['raw'],str) or not 1<=len(linebreak['raw'])<=2 or \
                    any(c.isspace() or c.isalnum() for c in linebreak['raw']):
                raise ResponseError(f'Évidence de césure invalide : {lid}')
            if linebreak['role']=='hyphenation' and not text.endswith('-') or \
                    linebreak['role']=='other' and not text.endswith(linebreak['raw']):
                raise ResponseError(f'Texte et marque terminale incohérents : {lid}')
        found[lid] = Reading(lid, unicodedata.normalize('NFC', text),
                             row['uncertain'], provider, model,linebreak,
                             value.get('job_id'),value.get('model_display_terminal'))
    if set(found) != set(expected):
        raise ResponseError(f'Lignes manquantes : {sorted(set(expected)-set(found))}')
    return [found[lid] for lid in expected]


def response_in_text(text, requests, job_id=None, validator=validate_response):
    """Extrait un objet complet sans accepter un exemple ou une réponse passée."""
    decoder = json.JSONDecoder()
    malformed=None
    for pos, ch in enumerate(text):
        if ch != '{':
            continue
        try:value,_=decoder.raw_decode(text[pos:])
        except (ValueError,TypeError):continue
        try:
            readings = validator(value, requests, job_id)
            return value, readings
        except (ValueError,TypeError) as exc:
            if isinstance(value,dict) and value.get('job_id')==job_id and \
                    {'provider','model','lines'}.issubset(value):
                malformed=MalformedResponse(str(exc),value)
    if malformed is not None:raise malformed
    raise ResponseError('Aucune réponse JSON complète pour cette requête')


def native_detail_sheets(crops,requests,directory,gutter,font):
    """Planchettes ≤1024 px, composées exclusivement de pixels natifs."""
    width=max(256,1024-gutter);stride=max(128,width-128)
    total=max(c.width for c in crops);starts=list(range(0,max(1,total-width+1),stride))
    if starts[-1]!=max(0,total-width):starts.append(max(0,total-width))
    sheets=[]
    for start in starts:
        groups=[];current=[];height=0
        for request,crop in zip(requests,crops):
            if start>=crop.width:continue
            rh=max(48,crop.height)+24
            if current and height+rh>1024:
                groups.append((current,height));current=[];height=0
            current.append((request,crop,height));height+=rh
        if current:groups.append((current,height))
        for group,height in groups:
            sheet=Image.new('RGB',(gutter+width,height),'white');draw=ImageDraw.Draw(sheet);rows=[]
            for request,crop,y in group:
                end=min(crop.width,start+width)
                draw.text((8,y+6),request.id,font=font,fill='black')
                draw.text((8,y+29),f'{start}:{end}',font=font,fill='black')
                sheet.paste(crop.crop((start,0,end,crop.height)),(gutter,y))
                draw.line((0,y+max(48,crop.height)+12,sheet.width,y+max(48,crop.height)+12),fill='#aaaaaa')
                rows.append(dict(id=request.id,x_start=start,x_end=end,source_pixels=True))
            path=Path(directory)/f'detail-sheet-{len(sheets)+1:03d}.png';sheet.save(path)
            sheets.append(dict(path=str(path.resolve()),rows=rows,gutter=gutter,size=list(sheet.size)))
    return sheets


def prepare_job(image, requests, directory, scale=1,input_style='legacy'):
    """Planche de lignes isolées : jamais de réduction des pixels d'origine."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    if not requests:
        raise ValueError('Requête sans lignes')
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 20)
    except OSError:
        font = ImageFont.load_default()
    gutter = max(120, max(int(font.getlength(r.id)) for r in requests)+20)
    crops = []
    details = []
    for request in requests:
        x0, y0, x1, y1 = request.bbox
        if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
            raise ValueError(f'Boîte hors image : {request.id}')
        crop = image.crop(request.bbox).convert('RGB')
        if scale > 1:
            crop = crop.resize((crop.width*scale, crop.height*scale), Image.Resampling.NEAREST)
        # Noms dérivés des positions, jamais d'un identifiant externe.
        crop.save(directory / f'crop-{len(crops)+1:04d}.png')
        pieces=[]
        if (input_style=='lines' or input_style=='legacy' and scale>1) and crop.width > 1024:
            starts=list(range(0,max(1,crop.width-1024+1),896))
            if starts[-1] != max(0,crop.width-1024):
                starts.append(max(0,crop.width-1024))
            for j,start in enumerate(starts,1):
                path=directory/f'detail-{len(crops)+1:04d}-{j:02d}.png'
                crop.crop((start,0,min(crop.width,start+1024),crop.height)).save(path)
                pieces.append(dict(path=str(path),x_start=start,x_end=min(crop.width,start+1024)))
        details.append(pieces)
        crops.append(crop)
    width = gutter + max(c.width for c in crops)
    height = sum(max(48, c.height)+24 for c in crops)
    sheet = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(sheet)
    y = 0
    for request, crop in zip(requests, crops):
        h = max(48, crop.height)
        draw.text((8, y+8), request.id, font=font, fill='black')
        sheet.paste(crop, (gutter, y+(h-crop.height)//2))
        draw.line((0, y+h+12, width, y+h+12), fill='#aaaaaa')
        y += h+24
    sheet.save(directory / 'lecture.png')
    job_id = uuid.uuid4().hex
    manifest = {'job_id': job_id, 'image': str(directory/'lecture.png'),
                'lines': [{'id': r.id, 'bbox': list(r.bbox),
                           'crop': str(directory/f'crop-{i:04d}.png')}
                          for i, r in enumerate(requests, 1)], 'scale': scale}
    for row,pieces in zip(manifest['lines'],details):
        row['detail_crops']=pieces
    if input_style=='sheets':
        manifest['detail_sheets']=native_detail_sheets(crops,requests,directory,gutter,font)
    manifest['input_style']=input_style
    (directory/'request.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    prompt = (
        f'Lecture OCR BBVLM, requête {job_id}. Lis visuellement uniquement '
        f'{directory / "lecture.png"} et, si utile, ces recadrages exacts : '
        f'{json.dumps({row["id"]: row["crop"] for row in manifest["lines"]}, ensure_ascii=False)}. '
        f'Détails à résolution source : {json.dumps({row["id"]:row["detail_crops"] for row in manifest["lines"] if row["detail_crops"]},ensure_ascii=False)}. '
        'Pour toute ligne possédant ces détails, ouvre TOUS ses détails : la '
        'planche sert au contexte et les détails servent à vérifier les glyphes. '
        'Ces détails se chevauchent et vont de gauche à droite ; reconstitue '
        'une seule ligne, sans répéter les chevauchements. Respecte les espaces '
        'entre mots ; ne crée pas un mot espace devant la virgule ou le point '
        'attaché à un mot. Distingue visuellement tilde, macron et accent aigu. '
        'Une ligne principale par bande ; ignore les fragments des lignes voisines '
        'et les étiquettes. Copie exactement les caractères visibles, accents, casse, '
        'ponctuation et césures inclus. Ne corrige pas le français et ne complète '
        'aucun mot coupé. Préserve les graphies anciennes, dont le s long ſ '
        '(U+017F), les ligatures et le u/v : aucun remplacement typographique. '
        'Tu es uniquement lecteur visuel : ne lis AUCUN autre fichier que les '
        'images explicitement listées ici, ni code, ni protocole, ni référence. '
        'Aucun shell, recherche, OCR externe, corpus, écriture ni modification '
        'de fichier. Les conventions de notation sont hors de ta tâche. '
        'Réponds par un objet JSON complet '
        f'avec job_id="{job_id}", provider="gemini", model=nom effectivement utilisé '
        'et lines=[{"id":identifiant,"text_parts":segments,"uncertain":booléen}]. '
        'Pour résister aux retours du terminal : JSON indenté, une propriété '
        'par ligne, text_parts est une liste de segments de 16 caractères au '
        'maximum, chaque segment seul sur sa ligne. Leur concaténation reproduit '
        'exactement la transcription, espaces inclus. '
        f'Identifiants exacts : {json.dumps([r.id for r in requests])}. '
        'Une entrée par identifiant, même si illisible : text_parts=[""], uncertain=true. '
        'Signale uncertain=true dès qu\'un caractère reste ambigu. '
        'Aucun commentaire hors JSON.'
    )
    if input_style=='sheets':
        prompt=(f'Lecture OCR BBVLM, requête {job_id}. Ouvre TOUTES les planchettes '
                f'natives listées ici : {json.dumps(manifest["detail_sheets"],ensure_ascii=False)}. '
                'Chaque ligne porte son ID dans la marge. x_start/x_end sont les '
                'positions dans la ligne source ; les bandes se chevauchent. '
                'Reconstitue chaque ligne sans répéter les chevauchements, puis '
                'vérifie espaces, accents et ponctuation. La planche entière '
                f'{manifest["image"]} est seulement un contexte facultatif. '
                'Ne réduis ni ne modifie les images. Copie les caractères NFC '
                'visibles, casse, graphies anciennes, s long ſ, ligatures et '
                'u/v inclus. Aucun français corrigé, aucun mot coupé complété. '
                'Ne crée pas un espace de mot devant une virgule/point attaché. '
                'Une césure visuellement identifiée comme coupure de mot en fin '
                'de ligne est transcrite - ; ajoute linebreak={raw:lecture '
                'littérale de la marque,role:"hyphenation"}. Ce rôle doit être '
                'établi à partir des pixels et du contexte. Une vraie égalité '
                'reste =, avec role:"other" ; aucune substitution aveugle. '
                'Si la marque n’a pas de rôle certain, uncertain=true. '
                'Pour les lignes sans marque terminale de ce type, linebreak=null. '
                'Tu peux lire UNIQUEMENT les images explicitement listées ici. '
                'Aucun autre fichier, code, référence, shell, recherche, OCR '
                'externe ni écriture. Les conventions de notation sont hors tâche. '
                f'JSON indenté : job_id="{job_id}", provider="gemini", model=nom utilisé, '
                'lines=[{id:ID,text_parts:segments de 16 caractères maximum, '
                'uncertain:bool,linebreak:objet ou null}]. Une propriété par ligne '
                'et un segment par ligne, espaces exacts dans les segments. '
                f'IDs exacts : {json.dumps([r.id for r in requests])}. '
                'Toutes les lignes doivent apparaître ; pour une ligne illisible, '
                'text_parts=[""], uncertain=true. Aucun texte hors JSON.')
    (directory/'prompt.txt').write_text(prompt, encoding='utf-8')
    return manifest, prompt


class HerdrGeminiReader:
    """Réutilise l'agent que l'utilisateur a ouvert, sans lancer d'autre agent."""
    nom = 'gemini-herdr'
    validate_response = staticmethod(validate_response)
    terminal_lines = 600
    text_part_length = 16
    allow_format_recovery = True

    def __init__(self, pane, directory, timeout=900, revision='v1',input_style='legacy'):
        self.pane = pane
        self.directory = Path(directory)
        self.timeout = timeout
        self.journal = []
        self.last_terminal = None
        self.revision = revision
        if input_style not in {'legacy','lines','sheets'}:raise ValueError('entrée visuelle inconnue')
        self.input_style=input_style

    def _call(self, *args):
        if args[0]=='prompt':self._quota_guard()
        try:
            proc = subprocess.run(['herdr', 'agent', *args], capture_output=True,
                                  text=True, timeout=self.timeout+10, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ReaderUnavailable(f'Accès à Herdr impossible : {exc}') from exc
        if args[0] == 'read' and proc.returncode == 0:
            # Les commandes de contrôle rendent du JSON ; `agent read` rend
            # directement le texte du terminal dans la CLI Herdr courante.
            value = {'result': {'text': proc.stdout}}
        else:
            try:
                value = json.loads(proc.stdout)
            except ValueError:
                value = None
        return proc.returncode, value, proc.stderr.strip()

    def _quota_guard(self):
        from native_quota import pending
        evidence=pending(self.pane)
        if evidence is not None:raise ReaderQuotaExceeded(evidence)

    def _native_auth_failure(self,job_id):
        """Un 401 doit suivre cet ID, sans autre requête entre les deux."""
        terminal=self.last_terminal or '';failed=terminal.rfind('UNAUTHENTICATED (code 401)')
        position=terminal.rfind(job_id)
        if not 0<=position<failed:return False
        between=terminal[position+len(job_id):failed]
        return re.search(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])',between) is None

    def _resume_after_native_quota(self,directory,requests,job_id,response_callback=None):
        """Même UUID seulement après quota explicite, échéance et fin native."""
        from native_quota import observe,save
        directory=Path(directory)
        marker=directory/'quota-interruption.json'
        # Un écran ancien contient un compte à rebours figé : sa relecture ne
        # doit pas déplacer l'échéance déjà observée pour cette requête.
        evidence=(json.loads(marker.read_text()) if marker.exists() else
                  observe(self.pane,directory,self.last_terminal or '',job_id))
        if evidence is None:return None
        if evidence['job_id']!=job_id:raise ReaderUnavailable('Quota d’une autre requête')
        self._quota_guard()
        code,state,error=self._call('get',self.pane)
        agent=(state or {}).get('result',{}).get('agent',{})
        if code or agent.get('agent') not in ('agy','gemini') or agent.get('agent_status') not in ('idle','done'):
            raise ReaderUnavailable('Quota expiré ; attendre la fin native sans resoumettre : '+error)
        attempts=directory/'quota-resume-attempts.json'
        history=json.loads(attempts.read_text()) if attempts.exists() else []
        if any(h['error_id']==evidence['error_id'] for h in history):
            # Le quota déjà repris peut être suivi d'un NOUVEAU 401. Sa
            # réparation conserve ses propres preuves/limites ; aucun second
            # envoi de quota n'est autorisé par ce passage.
            if self._native_auth_failure(job_id):return None
            raise ReaderUnavailable('Reprise de ce quota déjà soumise ; récupérer ce UUID sans nouveau renvoi')
        proof=dict(job_id=job_id,error_id=evidence['error_id'],retry_at=evidence['retry_at'],
                   native_settled_state=state,blind_timeout_retry=False)
        history.append(proof);save(attempts,history)
        prompt=(f'La requête identifiée {job_id} a rencontré un quota natif explicite. '
                'Le délai de remise à zéro affiché est écoulé et la fin native a été constatée. '
                'Continue CETTE même requête, mêmes IDs et entrées autorisées ; aucun historique '
                'ou journal interne à consulter. La tâche complète est ci-dessous.\n'+
                (directory/'prompt.txt').read_text())
        (directory/f'quota-resume-{len(history):02d}.txt').write_text(prompt)
        self._save_state(directory,'controlled_quota_resume_intent',**proof)
        result=self._call('prompt',self.pane,prompt,'--wait','--timeout',str(self.timeout*1000))
        self._save_state(directory,'submitted',code=result[0],result=result[1],error=result[2])
        try:return response_callback() if response_callback else self._read(requests,job_id)
        except ResponseError as exc:
            observe(self.pane,directory,self.last_terminal or '',job_id)
            self._quota_guard()
            raise ReaderUnavailable('Résultat absent après reprise identifiée du quota ; conserver ce UUID') from exc
        finally:
            if self.last_terminal:(directory/'terminal.txt').write_text(self.last_terminal)

    def _read(self, requests, job_id):
        code, value, error = self._call('read', self.pane, '--source',
                                      'recent-unwrapped', '--lines', str(min(1000,max(self.terminal_lines,len(requests)*32+200))))
        if code or value is None:
            raise ReaderUnavailable(f'Lecture du terminal impossible : {error}')
        self.last_terminal = json.dumps(value, ensure_ascii=False) if not isinstance(value.get('result'), dict) else _terminal_text(value['result'])
        return response_in_text(self.last_terminal, requests, job_id,self.validate_response)

    def _prepare(self,image,requests,directory,scale):
        return prepare_job(image,requests,directory,scale,self.input_style)

    def read_lines(self, image, requests, scale=1):
        if not requests:
            return []
        # Cache des pixels réellement lus, des IDs, des boîtes et du protocole.
        # Une intention soumise reste récupérable après arrêt du processus.
        fingerprint = hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()
        signature={'pixels': fingerprint, 'size': image.size,
            'requests': [(r.id, r.bbox) for r in requests], 'scale': scale,
            'protocol': 'gemini-diplomatic-'+self.revision, 'pane': self.pane}
        if self.input_style!='legacy':signature['input_style']=self.input_style
        key = hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
        directory = self.directory / key
        if (directory/'request.json').is_file():
            if (directory/'state.json').is_file():
                state = json.loads((directory/'state.json').read_text())
                if state['phase'] != 'prepared':
                    return self.recover_job(directory)
            if (directory/'response.json').is_file():
                return self.recover_job(directory)
        self._quota_guard()
        code, state, error = self._call('get', self.pane)
        if code or state is None:
            raise ReaderUnavailable(f'Agent introuvable : {error}')
        agent = state.get('result', {}).get('agent', {})
        if agent.get('agent') not in ('agy', 'gemini'):
            raise ReaderUnavailable('Le terminal ne contient pas Gemini')
        if agent.get('agent_status') not in ('idle', 'done'):
            raise ReaderUnavailable('Gemini est occupé ou attend une approbation')
        self.native_cwd=agent.get('cwd')
        if (directory/'request.json').is_file():
            manifest = json.loads((directory/'request.json').read_text())
            prompt = (directory/'prompt.txt').read_text()
        else:
            manifest, prompt = self._prepare(image, requests, directory, scale)
            self._save_state(directory, 'prepared')
        job_id = manifest['job_id']
        self._save_state(directory, 'submission_intent')
        code, result, error = self._call('prompt', self.pane, prompt, '--wait',
                                       '--timeout', str(self.timeout*1000))
        self._save_state(directory, 'submitted', code=code, result=result, error=error)
        return self.recover_job(directory, submission=(code, result, error))

    def _save_state(self, directory, phase, **fields):
        target = Path(directory)/'state.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps({'phase': phase, **fields}, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(target)

    def _resume_after_native_auth_refresh(self, directory, requests, job_id,
                                          response_callback=None,resume_instructions=None):
        """Continuer le même job seulement après une réparation native observée.

        Aucune lecture/export de secrets. Le seul signal utilisé du journal
        est l'événement de rafraîchissement postérieur à l'erreur d'exécution.
        """
        terminal=self.last_terminal or ''
        if not self._native_auth_failure(job_id):return None
        code,state,_=self._call('get',self.pane)
        if code or (state or {}).get('result',{}).get('agent',{}).get('agent_status') not in ('idle','done'):
            return None
        logs=sorted((Path.home()/'.gemini/antigravity-cli/log').glob('cli-*.log'),
                    key=lambda p:p.stat().st_mtime,reverse=True)
        observed=None
        for log in logs[:3]:
            with log.open('rb') as handle:
                handle.seek(max(0,log.stat().st_size-262144))
                tail=handle.read().decode('utf-8',errors='replace')
            failed=tail.rfind('UNAUTHENTICATED (code 401)')
            refreshed=tail.rfind('token refreshed, new expiry=')
            if 0 <= failed < refreshed:
                line=tail[tail.rfind('\n',0,refreshed)+1:tail.find('\n',refreshed)]
                observed=hashlib.sha256(line.encode()).hexdigest()
                break
        if observed is None:
            return None
        marker=Path(directory)/'native-auth-repairs.json'
        history=json.loads(marker.read_text()) if marker.exists() else []
        if observed in history or len(history)>=3:
            return None
        history.append(observed);marker.write_text(json.dumps(history,indent=2))
        prompt=(f'Continue la même requête OCR {job_id} après l\'erreur 401 ; '
                'le rafraîchissement natif a été observé après cette erreur. '
                'Termine le JSON déjà demandé, mêmes IDs, provider=gemini, model, '
                f'text_parts de {self.text_part_length} caractères par segment seul sur sa ligne et '
                'uncertain booléen. Si nécessaire, seulement les images de cette '
                'requête sont autorisées. Aucun autre fichier, shell, code, '
                'référence ou écriture. Ne change aucune convention ni graphie. '
                'Aucun texte hors JSON.')
        if resume_instructions:
            prompt=(f'Continue la même requête OLR {job_id} après l’erreur 401 ; '
                    'le rafraîchissement natif a été observé après cette erreur. '
                    'Termine cette requête identifiée sans en créer une autre. '+resume_instructions)
        elif (Path(directory)/'prompt.txt').exists():
            prompt+='\nTâche originale, mêmes entrées autorisées :\n'+(Path(directory)/'prompt.txt').read_text()
        (Path(directory)/f'auth-resume-{len(history):02d}.txt').write_text(prompt,encoding='utf-8')
        self._save_state(directory,'controlled_resume_intent',reason='native_auth_refresh_observed',refresh_event=observed)
        result=self._call('prompt',self.pane,prompt,'--wait','--timeout',str(self.timeout*1000))
        self._save_state(directory,'submitted',code=result[0],result=result[1],error=result[2])
        try:
            return response_callback() if response_callback else self._read(requests,job_id)
        except ResponseError as exc:
            raise ReaderUnavailable('Résultat absent après reprise contrôlée de l\'authentification') from exc
        finally:
            if self.last_terminal:
                (Path(directory)/'terminal.txt').write_text(self.last_terminal,encoding='utf-8')

    def recover_job(self, directory, submission=None):
        """Récupère une requête déjà soumise, sans refaire la lecture."""
        directory = Path(directory).resolve()
        self.current_job_directory=directory
        manifest = json.loads((directory/'request.json').read_text(encoding='utf-8'))
        requests = [LineRequest(row['id'], tuple(row['bbox'])) for row in manifest['lines']]
        job_id, scale = manifest['job_id'], manifest['scale']
        rejected=directory/'rejected-response.json'
        if rejected.exists() and not (directory/'quota-interruption.json').exists():
            failure=json.loads(rejected.read_text())
            if failure['job_id']!=job_id:raise ReaderUnavailable('Rejet sauvegardé d’une autre requête')
            raise ResponseError(f'Réponse rejetée sauvegardée : {failure["reason"]}')
        target = directory/'response.json'
        if target.is_file():
            value = json.loads(target.read_text(encoding='utf-8'))
            readings = self.validate_response(value, requests, job_id)
            self.journal.append({'job_id': job_id, 'directory': str(directory),
                                 'ids': [r.id for r in requests], 'model': value['model'],
                                 'scale': scale, 'cached': True,
                                 **({'provider_claim_original':value['provider_claim_original'],
                                     'provider_normalization':value['provider_normalization']}
                                    if 'provider_normalization' in value else {})})
            return readings
        code, result, error = submission if submission is not None else self._call('get', self.pane)
        try:
            value, readings = self._read(requests, job_id)
        except ResponseError as initial_error:
            if self.last_terminal:(directory/'terminal.txt').write_text(self.last_terminal)
            resumed=self._resume_after_native_quota(directory,requests,job_id)
            if resumed is not None:
                value,readings=resumed
                return self._store_response(directory,requests,scale,value,readings)
            resumed=self._resume_after_cancelled_shell(directory,requests,job_id)
            if resumed is not None:
                value,readings=resumed
                return self._store_response(directory,requests,scale,value,readings)
            resumed=self._resume_after_native_auth_refresh(directory,requests,job_id)
            if resumed is not None:
                value,readings=resumed
                # Retour par le chemin de sauvegarde/validation commun.
                return self._store_response(directory,requests,scale,value,readings)
            if self._native_auth_failure(job_id):
                raise ReaderUnavailable('401 natif pour ce UUID ; attendre une réparation authentifiée observée, sans renvoi ni repli de format')
            if code or result is None or result.get('result', {}).get('agent', {}).get('agent_status') not in ('idle', 'done'):
                raise ReaderUnavailable(f'Gemini non terminé ou bloqué : {error}')
            saved = directory/'state.json'
            phase = json.loads(saved.read_text()).get('phase') if saved.is_file() else None
            if phase in ('submission_intent', 'format_intent', 'format_requested') and \
                    not (phase=='submission_intent' and isinstance(initial_error,MalformedResponse)):
                if isinstance(initial_error,MalformedResponse) and phase=='format_requested':
                    self._reject_response(directory,job_id,initial_error)
                    raise ResponseError(str(initial_error)) from initial_error
                raise ReaderUnavailable(f'Requête {job_id} déjà soumise, résultat absent. '
                                        f'Inspecter {directory}, sans resoumission ambiguë ({phase}).')
            # Repli sans écriture par Gemini : chaînes courtes dans un JSON
            # indenté, pour résister aux retours à la ligne du terminal.
            if not self.allow_format_recovery:
                raise ReaderUnavailable('Réponse native absente/incompatible ; récupérer cet UUID sans reformatage ni nouvel OCR')
            fallback = (f'La réponse JSON de la requête {job_id} ne peut pas être '
                        'récupérée intégralement depuis le terminal. Affiche le '
                        'même objet JSON, avec job_id, provider, model, lines et '
                        'les mêmes identifiants et uncertain. Remplace seulement '
                        'chaque champ text par text_parts, une liste de segments '
                        f'de {self.text_part_length} caractères au maximum dont la concaténation '
                        'reproduit EXACTEMENT ta transcription, espaces compris. '
                        'Une propriété JSON par ligne ; chaque segment doit être '
                        'seul sur sa propre ligne dans le tableau text_parts. '
                        'Ne relis pas l\'image et ne crée ni modifie de fichier. '
                        'Aucun texte hors de l\'objet JSON.')
            self._save_state(directory, 'format_intent')
            code, result, error = self._call('prompt', self.pane, fallback, '--wait',
                                           '--timeout', str(self.timeout*1000))
            self._save_state(directory, 'format_requested', code=code, result=result, error=error)
            try:
                value, readings = self._read(requests, job_id)
            except ResponseError as exc:
                if self.last_terminal:(directory/'terminal.txt').write_text(self.last_terminal)
                resumed=self._resume_after_native_quota(directory,requests,job_id)
                if resumed is not None:
                    value,readings=resumed
                    return self._store_response(directory,requests,scale,value,readings)
                if code or result is None or result.get('result', {}).get('agent', {}).get('agent_status') not in ('idle', 'done'):
                    raise ReaderUnavailable(f'Résultat Gemini non récupérable : {error}') from exc
                self._reject_response(directory,job_id,exc)
                raise
        return self._store_response(directory,requests,scale,value,readings)

    def _resume_after_cancelled_shell(self,directory,requests,job_id,response_callback=None):
        """Annuler une commande hors périmètre, puis reprendre l'UUID établi.

        Un timeout, une question ou une approbation inconnue ne suffit jamais.
        Les pixels et chemins viennent exclusivement de la requête sauvegardée.
        """
        directory=Path(directory)
        terminal=self.last_terminal or ''
        if job_id not in terminal or 'Bash(' not in terminal:
            return None
        current_ui=terminal[-2000:]
        dialog='Requesting permission for:' in current_ui and 'Run this command?' in current_ui and 'Bash(' in current_ui
        cancelled='Interrupted · What should Antigravity CLI do instead?' in current_ui and 'Bash(' in current_ui
        if not (dialog or cancelled):return None
        code,state,error=self._call('get',self.pane)
        agent=(state or {}).get('result',{}).get('agent',{})
        status=agent.get('agent_status')
        if code or agent.get('agent') not in ('agy','gemini'):return None
        if status=='blocked' and dialog:
            code,_,error=self._call('send-keys',self.pane,'esc')
            if code:raise ReaderUnavailable('Annulation de la commande Gemini impossible : '+error)
            code,state,error=self._call('get',self.pane)
            agent=(state or {}).get('result',{}).get('agent',{})
            status=agent.get('agent_status')
        if code or status not in ('idle','done'):
            raise ReaderUnavailable('Commande hors périmètre annulée ; attendre la fin native sans resoumettre')
        evidence=directory/'cancelled-native-tool.json'
        if evidence.exists():
            if json.loads(evidence.read_text())['job_id']!=job_id:
                raise ReaderUnavailable('Preuve d’annulation issue d’une autre requête')
            if response_callback is None:
                failure=ResponseError('Deux commandes shell hors périmètre ; requête native annulée, découper les vrais recadrages')
                self._reject_response(directory,job_id,failure)
                raise failure
            raise ReaderUnavailable('Reprise après annulation déjà tentée ; conserver la requête et sa preuve')
        saved=directory/'state.json'
        previous=json.loads(saved.read_text()) if saved.exists() else {}
        proof=dict(job_id=job_id,reason='native shell outside visual-reading scope explicitly cancelled',
                   terminal_sha256=hashlib.sha256(terminal.encode()).hexdigest(),previous_state=previous,
                   native_settled_state=state,blind_timeout_retry=False)
        temporary=evidence.with_suffix('.tmp');temporary.write_text(json.dumps(proof,ensure_ascii=False,indent=2));temporary.replace(evidence)
        (directory/'cancelled-native-tool.terminal.txt').write_text(terminal)
        prompt=(directory/'prompt.txt').read_text()
        manifest=json.loads((directory/'request.json').read_text())
        # Les IDs et intervalles source sont déjà imprimés sur chaque planche.
        # Éviter de répéter 32 descriptions de lignes par bande dans le prompt.
        if manifest.get('detail_sheets') and 'Chaque ligne porte son ID' in prompt:
            prompt=(f'Lecture OCR BBVLM, requête {job_id}. Ouvre TOUTES ces planchettes natives : '+
                    json.dumps([s['path'] for s in manifest['detail_sheets']],ensure_ascii=False)+'. '+
                    prompt[prompt.index('Chaque ligne porte son ID'):])
        prompt=(f'La commande shell de la requête {job_id} a été annulée. La tâche actuelle est entièrement décrite '
                'ci-dessous : aucun historique ni journal interne à consulter. Utilise uniquement la lecture des '
                'images/fichiers explicitement autorisés, sans outil Bash, shell, code, recherche ou écriture. '
                'Même requête identifiée après annulation native constatée.\n'+prompt)
        (directory/'controlled-native-tool-prompt.txt').write_text(prompt)
        self._save_state(directory,'controlled_tool_resume_intent',reason=proof['reason'])
        result=self._call('prompt',self.pane,prompt,'--wait','--timeout',str(self.timeout*1000))
        self._save_state(directory,'controlled_tool_resumed',code=result[0],result=result[1],error=result[2])
        return response_callback() if response_callback else self._read(requests,job_id)

    def _reject_response(self,directory,job_id,error):
        directory=Path(directory)
        previous=json.loads((directory/'state.json').read_text()) if (directory/'state.json').exists() else {}
        failure=dict(job_id=job_id,reason=str(error),response=getattr(error,'value',None),
                     scope='settled native request lacks a validated response after bounded format recovery',
                     native_completion=previous.get('result'),
                     terminal_sha256=hashlib.sha256((self.last_terminal or '').encode()).hexdigest())
        temporary=directory/'rejected-response.tmp';temporary.write_text(json.dumps(failure,ensure_ascii=False,indent=2))
        temporary.replace(directory/'rejected-response.json')
        self._save_state(directory,'rejected_response',reason=str(error))

    def _store_response(self,directory,requests,scale,value,readings):
        directory=Path(directory);target=directory/'response.json';job_id=value['job_id']
        from gemini_provenance import normalize_provider
        try:value=normalize_provider(value,self.last_terminal or '')
        except ValueError as exc:
            raise ReaderUnavailable('Fournisseur natif non établi ; préserver cette requête : '+str(exc)) from exc
        if value['provider'] != 'gemini':
            raise ReaderUnavailable('Fournisseur différent de Gemini ; erreur de provenance, pas refus de lecture')
        displays=re.findall(r'(Gemini\s+[\d.]+\s+(?:Flash|Pro)\s*·\s*\w+)\s*$',self.last_terminal or '',re.MULTILINE)
        if displays:value['model_display_terminal']=displays[-1]
        readings=[replace(r,provider=value['provider'],job_id=job_id,
                          model_display_terminal=value.get('model_display_terminal')) for r in readings]
        value['lines'] = [{'id': r.id, 'text': r.text, 'uncertain': r.uncertain,
                           **({'linebreak':r.linebreak} if r.linebreak else {})} for r in readings]
        temporary = directory/'response.tmp'
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(target)
        self._save_state(directory, 'completed')
        self.journal.append({'job_id': job_id, 'directory': str(directory),
                             'ids': [r.id for r in requests], 'model': value['model'], 'scale': scale,
                             'model_display_terminal':value.get('model_display_terminal'),
                             **({'provider_claim_original':value['provider_claim_original'],
                                 'provider_normalization':value['provider_normalization']}
                                if 'provider_normalization' in value else {})})
        return readings


def _terminal_text(value):
    """Le nom du champ texte varie selon la version du relais Herdr."""
    texts = []
    def walk(item):
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    return '\n'.join(texts)


class JSONReader:
    """Rejoue une transcription validée pour vérifier le placement séparément."""
    nom = 'json-replay'

    def __init__(self, path):
        self.value = json.loads(Path(path).read_text(encoding='utf-8'))

    def read_lines(self, image, requests, scale=1):
        wanted = {r.id for r in requests}
        value = {**self.value, 'lines': [r for r in self.value['lines'] if r['id'] in wanted]}
        return validate_response(value, requests)
