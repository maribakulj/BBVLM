"""Freeze source identities and reserve; do not repair upstream labels silently."""
import hashlib,json,re
from pathlib import Path
P=Path('experiments/loop/chronicling-a58'); scratch=Path('/workspace/scratch/cecc4cd83a9f')
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
a=json.loads((P/'audit.json').read_text());s={k:set(v) for k,v in json.loads((P/'official_split.json').read_text()).items()};names={Path(x['file']).stem for x in a['files_detail']}
assert s['OutOfDistribution']<=s['Test']
assert not s['Training']&s['Validation'] and not s['Training']&s['Test'] and not s['Validation']&s['Test']
title=lambda x:re.split(r'_\d{4}[-_]',x)[0]
ood={title(x) for x in s['OutOfDistribution']};seen={title(x) for x in s['Training']|s['Validation']};assert not ood&seen
checks={'counts':{k:len(v) for k,v in s.items()},'test_id':80,'primary_splits_disjoint':True,'ood_titles_disjoint':True,'ood_titles':sorted(ood),'split_names_missing_xml':sorted(set.union(*s.values())-names),'xml_names_missing_split':sorted(names-set.union(*s.values())),'reserved_test_pages':sorted(s['Test']),'all_test_images_unopened':True,'mapping_corrections_applied':False}
save(P/'reserve.json',checks)
source={'repository':'https://gitlab.uni-bonn.de/digital-history/Chronicling-Germany-Dataset','revision':'66b50f53ccdb581d29cc02f670e469bbf583e825','annotation_git_tree':'189eefb0e44dade0cd411cdf392e13ed19bcecce','split_git_blob':'92b74f0165668354f93ecb626c15b3aca3c8829f','archive_sha256':a['archive_sha256'],'archive_bytes':a['archive_bytes'],'verification':'all 801 XML blobs reconstruct exact published annotation tree; split bytes reconstruct Git blob; pinned tree API agrees','license':'CC BY-NC 4.0','paper':'https://arxiv.org/html/2401.16845v4','read_date':'2026-09-28'}
save(P/'source.json',source)
a['element_totals'].update({k:a['element_totals'].get(k,0) for k in ['Word','Glyph']});save(P/'audit.json',a)
summary='''# A58 — audit de 801 annotations Chronicling Germany

**371 575 TextLine, 0 Word, 0 Glyph** : les mots annoncés dans le papier sont des tokens, pas des boîtes de mots. 19 343 TextRegion, 11 506 SeparatorRegion, 1 306 TableRegion, 296 GraphicRegion, 63 ImageRegion. Les 32 514 régions et 371 575 lignes actuelles diffèrent des 32 451 / 371 642 du papier : citer la révision exacte.

456 Coords et 341 Baseline contiennent des points hors des dimensions déclarées ; 8 polygones dégénérés. Aucun ID dupliqué ni référence région pendante. Ce sont des alertes structurelles, à vérifier sur les images.

Splits : 651 train, 50 validation, 100 test dont 20 OoD ; splits principaux disjoints et cinq titres OoD absents de train/validation. **Une faute dans le split officiel** : Training contient `Koelnische_ZeiOut of distributiontung_1924_0035`, absent des XML ; `Koelnische_Zeitung_1924_0035` existe mais n’est assigné à aucun split. Aucune correction silencieuse. Les 100 pages test sont réservées ; aucune image ni valeur de transcription inspectée pour cette sélection.

Source : 60 036 720 octets téléchargés ; les 801 blobs XML reconstruisent exactement l’arbre Git publié, vérifié à la révision 66b50f53ccdb581d29cc02f670e469bbf583e825. Empreintes par fichier conservées.

Décision : retenir les régions comme référence candidate, texte à auditer selon ses conventions. Ne pas certifier les boîtes de mots ni l’ordre de lecture avec ce corpus. Le papier indique double contrôle des régions, simple correction du texte, correction sélective des lignes, ordre automatique non corrigé. Statuts Transkribus : 661 IN_PROGRESS,111 DONE,13 GT,13 NEW,3 autres/absents ; ce n’est pas une certification.

Coût : ~15 s CPU, aucune passe OCR/VLM ni image téléchargée. Objectif global non atteint. Prochaine expérience : Sol sur résidus OCR A54, crops source, IDs aveugles ; développement consommé, pas nouvelle validation.
'''
(P/'RESULTS.md').write_text(summary)
notes={
'REFERENCE_AUDIT.md':summary,
'LITERATURE.md':'## A58 — Chronicling Germany, relecture 2026-09-28\nhttps://arxiv.org/html/2401.16845v4 (13 juin 2025), §§3,A.4.2,A.5.5 : régions vérifiées par deux annotateurs ; texte corrigé une fois ; lignes seulement en cas de défaut majeur ; ordre automatique. Code script/download.py lu au tour précédent : téléchargement ciblé retenu pour éviter tous les modèles et images. Audit de version indispensable : XML actuels diffèrent des comptes du papier.\n',
'experiments/loop/PAPER_SUMMARIES.md':'## A58 — complément Chronicling Germany\nArticle v4 https://arxiv.org/html/2401.16845v4 ; §§A.4.2/A.5.5 lus le 28 septembre 2026. Régions vérifiées par deux humains ; texte relu une fois, seconde correction annoncée. Signes zodiacaux/géométriques omis, fractions transcrites avec slash, espace nombre-unité. Lignes scindées conservées. Apport BBVLM : conventions et qualité doivent être distinguées par couche ; CER et ordre ne peuvent pas être certifiés à partir du seul label GT. Audit A58 : aucun Word XML, 801 pages, réserve100 pages, défaut de nom train documenté.\n',
'experiments/loop/CLAUDE_BRANCH_AUDIT.md':'## A58 — 2026-09-28\nJOURNAL.md relu lignes210–257 SHA ba685e9b4c870e245d1d201381986178660abb4c ; comparaison 33 ahead/10 behind depuis f70b292. Aucun changement depuis A57 : I01 reste développé sur pages consommées, O13 attendu.\n',
'JOURNAL.md':summary,
'IMPLEMENTATION.md':'## A58\nAudit PAGE exhaustif sans afficher les transcriptions : scripts/audit_chronicling_a58.py ; provenance et reserve : scripts/finalize_chronicling_a58.py. Originaux conservés, faute de nom du split signalée mais non corrigée.\n',
'experiments/loop/README.md':'## A58 terminé\nVoir chronicling-a58/RESULTS.md : 801 XML audités, réserve100 pages ; aucun Word, ordre automatique, défaut de nom train. Aucun critère global validé.\n'}
for f,text in notes.items():
 with Path(f).open('a') as stream:stream.write('\n'+text+'\n')
cp=Path('experiments/loop/CHECKPOINT.json');c=json.loads(cp.read_text());c['evidence']['chronicling_a58']={k:v for k,v in a.items() if k not in ['files_detail','creators']};c['phases'].append({'id':'chronicling_a58','complete':True,'script':'scripts/audit_chronicling_a58.py','result':'chronicling-a58/audit.json'});c['next_research'].insert(0,'A58 complete: corpus geometry audit, test100 reserved. Next A59 targeted Sol on A54 residuals, consumed development only.');save(cp,c)
print(json.dumps({k:v for k,v in checks.items() if k!='reserved_test_pages'},indent=2))
