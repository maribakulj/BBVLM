"""Freeze a diverse image-unseen Training transfer set without opening XML."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/loop/next-a69'
NAMES=[
 'no_title_1617-08-16_0001',
 'Reichs_Post_Reuter_1700-11-16_0001',
 'Leipziger_Zeitung_1748-10-29_0001',
 'Holzmindisches_Wochenblatt_1785-07-30_0002',
 'Fraenkischer_Kurier_1834-10-15_0002',
 'Neue_Berliner_Musikzeitung_1866-07-18_0002',
 'Mode_und_Haus_Illustrirte_Kinderwelt_1889-09-15_0001',
 'Muenchner_Neueste_Nachrichten_1917-04-10_0001',
 'Koelnische_Zeitung_1924_0001',
 'Vossische_Zeitung_1933-03-04_0002']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 split_path=ROOT/'experiments/loop/chronicling-a58/official_split.json'
 split=json.loads(split_path.read_text()); names=set(NAMES)
 assert len(names)==10 and names<=set(split['Training'])
 assert not names&set(split['Validation']) and not names&set(split['Test'])
 assert all(not (ROOT/'corpora/chronicling-germany/images'/f'{n}.jpg').exists() for n in NAMES)
 OUT.mkdir(exist_ok=True)
 payload={'schema':'bbvlm.a69.split/1','pages':NAMES,'official_split':'Training',
  'official_split_sha256':sha(split_path),'a68_rule':'unchanged',
  'previous_exposure':['A58 corpus-wide structural XML audit'],
  'excluded_exposure':['A65 Validation geometry','A66/A68 images and detector predictions'],
  'test_pages_opened':0}
 (OUT/'split.json').write_text(json.dumps(payload,indent=2)+'\n')
 print(json.dumps({'frozen':len(NAMES),'test_pages_opened':0}))
if __name__=='__main__':main()
