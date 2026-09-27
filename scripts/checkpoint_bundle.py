"""Portable work checkpoint; omit reproducible heavyweight public assets/secrets."""
from pathlib import Path
import zipfile,json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/autonomous_loop.py')],check=True,stdout=subprocess.DEVNULL)
paths=[]
for name in ['src','scripts','tests','schemas','experiments']:
    for p in (ROOT/name).rglob('*'):
        public_spiritualist_image = (
            p.suffix.lower() == '.png'
            and 'spiritualist-v1' in p.parts
            and 'yolo-ocr-a13-0044' not in p.parts  # preserve the small exact blind OCR inputs
        )
        public_bnf_or_a28_binary = (
            ('bnf-impact-a26' in p.parts or 'bnf-impact-olr-a27' in p.parts
             or 'bnf-impact-olr-a29' in p.parts or 'bnf-region-ocr-a30' in p.parts or 'unmasked-a31' in p.parts
             or 'french-word-gt-a28' in p.parts)
            and (p.suffix.lower() in {'.zip','.tif','.tiff','.jpg','.jpeg','.png'})
        )
        public_a34_source_image = (
            'word-transfer-a34' in p.parts and 'source' in p.parts
            and p.suffix.lower() in {'.tif','.tiff','.jpg','.jpeg','.png'}
        )
        if (p.is_file() and '__pycache__' not in p.parts
                and p.suffix not in ['.pyc','.lock','.log']
                and not public_spiritualist_image
                and not public_bnf_or_a28_binary
                and not public_a34_source_image):
            paths.append(p)
paths += [p for p in ROOT.iterdir() if p.is_file() and (p.suffix in ['.md','.txt','.toml'] or p.name=='.gitignore')]
# Small source XMLs preserve the exact suspect references; image bytes can be restored.
paths += list((ROOT/'corpora/newseye-validation').rglob('*.xml'))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
dest=ROOT.parent/'BBVLM_autonomous_checkpoint.zip';tmp=dest.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(set(paths)):z.write(p,'BBVLM/'+str(p.relative_to(ROOT)))
    z.writestr('BBVLM/CHECKPOINT_FILES_SHA256.json',json.dumps(manifest,indent=2))
    z.writestr('BBVLM/PUBLIC_EXPERIMENT_ASSETS_OMITTED.json',json.dumps({
      'reason':'public or deterministically derived heavyweight assets',
      'restore':'python scripts/restore_public_assets.py',
      'omitted':['experiments/loop/bnf-impact-a26/source/impact.zip',
        'experiments/loop/bnf-impact-a26/opened/IMPACT/T/*',
        'experiments/loop/bnf-impact-olr-a27/opened/IMPACT/T/*',
        'experiments/loop/bnf-impact-olr-a27/visual-input/*',
        'experiments/loop/bnf-impact-olr-a29/opened/IMPACT/T/*',
        'experiments/loop/bnf-impact-olr-a29/visual-input/*',
        'experiments/loop/bnf-region-ocr-a30/visual-input/*',
        'experiments/loop/unmasked-a31/input/*',
        'experiments/loop/french-word-gt-a28/source/**/*.tif',
        'experiments/loop/word-transfer-a34/source/**/*.{tif,tiff,jpg,jpeg,png}']},indent=2))
tmp.replace(dest);print(dest,dest.stat().st_size)
