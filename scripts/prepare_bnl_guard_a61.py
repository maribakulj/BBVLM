"""Prepare same-source guard diagnostic without reading reference XML."""
import sys,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_bnl_vlm_a54 import validate_and_apply
P=Path('experiments/loop/bnl-guard-a61');P.mkdir(exist_ok=True);B=P/'blind';B.mkdir(exist_ok=True);A=Path('experiments/loop/bnl-independent-a54')
q=json.loads((A/'vlm-input/request.json').read_text());r=json.loads((A/'luna-response.json').read_text());cand=next(x['pero_candidate'] for x in q['items'] if x['id']=='T004');ans=next(x for x in r['items'] if x['id']=='T004');candidate,guard=validate_and_apply(cand,ans)
images=[]
for i,k in enumerate(['K843','K206','K591'],1):
 src=Path('experiments/loop/bnl-bands-a60/blind')/(k+'.png');dest=B/f'V{i}.png';shutil.copyfile(src,dest);images.append(str(dest.resolve()))
req={'task':'Inspect all three images at original detail. They are consecutive native bands of one printed block. Correct the candidate only where the printed pixels clearly justify a change. Preserve historic spelling and accents; do not modernize, expand abbreviations or infer a word from plausibility. If unclear retain the existing candidate and mark uncertain. Every change must be an exact uniquely occurring before substring and replacement after, with a visual reason. Output the full text reconstructed by applying those edits in order. No edits is allowed. Never inspect other files, references, scores or agents.','items':[{'id':'V417','images':images,'candidate':candidate,'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest()}],'output_schema':{'items':[{'id':'V417','text':'full resulting text','decision':'keep|edit','uncertain':False,'edits':[{'before':'exact unique substring','after':'replacement','visual_reason':'visible evidence'}]}],'inspected_images':images}}
(B/'request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n')
(P/'PROTOCOL.md').write_text('''# A61 — garder le candidat, corriger seulement les glyphes prouvés

Bloc0455 consommé. Geler le texte accepté par la garde A54 (sans référence), mêmes trois bandes image A60, nouveau Sol. Un item V417 avec trois images. Garde validate_and_apply A54 inchangée : substrings uniques, reconstruction search_v1 exacte, tous IDs et images attendus. Mesurer strict/search/lexical contre originaux sans les corriger. Pas de seuil rechoisi après lecture. Comparaison principale : Luna guard8 écarts lexicaux ; A59/A60 aveugles45/36. Ce diagnostic ne mesure pas un routage automatique ni la généralisation.

Branche Claude relue avant préparation : JOURNAL I01 inchangé SHA ba685e9b4c870e245d1d201381986178660abb4c. Littérature de résolution Inoue2503.23667 complète lue A59 ; protocole de correction limité motivé par erreurs sémantiques et diacritiques observées, pas par règle linguistique. Code actuel validate_and_apply lu et réutilisé, aucun nouvel outil lourd.
''')
