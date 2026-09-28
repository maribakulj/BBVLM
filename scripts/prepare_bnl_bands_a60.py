"""Create disjoint native bands using image whitespace only; no reference access."""
import hashlib,json
from pathlib import Path
from PIL import Image
P=Path('experiments/loop/bnl-bands-a60');P.mkdir(exist_ok=True);B=P/'blind';B.mkdir(exist_ok=True)
src=Path('experiments/loop/bnl-sol-a59/blind/R003.png');im=Image.open(src);gray=im.convert('L');w,h=im.size
# Select least dark row in each +/-80px window around thirds. Nearest target breaks ties.
cuts=[0]
for t in [h//3,2*h//3]:
 candidates=[]
 for y in range(t-80,t+81):
  hist=gray.crop((0,y,w,y+1)).histogram();candidates.append((sum(hist[:110]),abs(y-t),y))
 cuts.append(min(candidates)[2])
cuts.append(h);items=[]
for i,(top,bottom) in enumerate(zip(cuts,cuts[1:])):
 rid=['K843','K206','K591'][i];path=B/(rid+'.png');im.crop((0,top,w,bottom)).save(path);items.append({'id':rid,'image':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
req={'task':'Transcribe the printed text from each image faithfully. Preserve visible spelling, accents, punctuation and physical line breaks. Do not modernize, expand abbreviations, or fix author errors. Inspect every image with view_image at original detail. If unclear, record the uncertainty separately with the literal best reading in text. The images are text blocks at original source resolution. You may inspect them again. Return exactly the three opaque IDs, one full text per item, no extra IDs. Do not inspect any other files beyond this request and these three images; no references, prior outputs or scores.','items':sorted(items,key=lambda x:x['id']),'output_schema':{'items':[{'id':'K206','text':'full transcription','uncertain_spans':[{'text':'literal','reason':'visual uncertainty'}]}],'inspected_images':['absolute paths']}}
(B/'request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n');(P/'private-map.json').write_text(json.dumps({'source_id':'0455','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'cuts':cuts,'order':[x['id'] for x in items],'source_size':[w,h]},indent=2)+'\n')
# Verify complete exact pixel reconstruction, not a heuristic text merge.
reassembled=Image.new(im.mode,im.size)
for it,top in zip(items,cuts):reassembled.paste(Image.open(it['image']),(0,top))
assert reassembled.tobytes()==im.tobytes()
(P/'PROTOCOL.md').write_text('''# A60 — trois bandes natives du bloc0455

Figé avant réponse. Diagnostic sur le bloc A54 consommé où A59 a régressé. Même modèle Sol, nouveau contexte aveugle, même consigne diplomatique et aucun candidat textuel. Trois bandes disjointes produites aux espaces horizontaux proches des tiers, sans XML ni texte, zéro interpolation. Reconstruction des pixels vérifiée exacte. IDs opaques, ordre fourni au scoreur seulement. Concaténation déterministe par ordre vertical avec un retour ligne ; search_v1 et lexical_alnum identiques à A54. Comparer A59 entier et A60 bandes. Pas de correction de référence ni promotion indépendante. Cette ablation change aussi la session stochastique : un résultat unique ne prouvera pas seul la causalité résolution.

Claude JOURNAL relu avant préparation (ba685e9b4c870e245d1d201381986178660abb4c), I01 inchangé. Source primaire lue : Inoue arXiv2503.23667v1, étude contrôlée de la taille de caractères, limitée aux kanjis synthétiques et modèles2025. Hypothèse BBVLM : éviter la réduction apparente d’un bloc3059px de hauteur. Aucun accès aux pixels internes du modèle, donc pas de résolution encodée inventée.
''')
print(cuts)
