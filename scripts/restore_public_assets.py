"""Restore public corpus/model assets omitted from the portable checkpoint.

Use ``--only models/pero.zip`` to restore one measured dependency without
downloading every public corpus.  With no flag, the historical all-assets
behaviour is preserved.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--only',action='append',default=[],help='exact manifest path to restore; repeatable')
parser.add_argument('--chronicling-annotations',action='store_true',help='restore verified A58 XML only, without images/models')
args=parser.parse_args()
if args.chronicling_annotations:
    subprocess.run([sys.executable,str(ROOT/'scripts/restore_chronicling_a58.py')],cwd=ROOT,check=True)
    raise SystemExit(0)
entries=json.loads((ROOT/'experiments/loop/assets.json').read_text())['downloads']
if args.only:
    wanted=set(args.only);known={e['path'] for e in entries}
    unknown=wanted-known
    if unknown:raise SystemExit('unknown asset path(s): '+', '.join(sorted(unknown)))
    entries=[e for e in entries if e['path'] in wanted]
for entry in entries:
    dest=ROOT/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        tmp=dest.with_suffix('.download');urllib.request.urlretrieve(entry['url'],tmp);tmp.replace(dest)
    digest=hashlib.sha256()
    with dest.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    h=digest.hexdigest()
    if h!=entry['sha256']:raise RuntimeError('asset hash mismatch: '+entry['path'])
    if entry.get('extract_to'):
        target=ROOT/entry['extract_to'];target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(dest) as z:
            for info in z.infolist():
                path=(target/info.filename).resolve()
                if not path.is_relative_to(target.resolve()):raise ValueError('unsafe archive path')
            z.extractall(target)
    print('restored',entry['path'])
if not args.only:
    # Experiment assets are public but require verified repository/share logic
    # rather than a stable direct URL in assets.json.
    subprocess.run([sys.executable,str(ROOT/'scripts/download_bnf_corrected_archive_a26.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/open_bnf_impact_a26.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_bnf_olr_a27.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_bnf_olr_a29.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_bnf_region_ocr_a30.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/prepare_unmasked_a31.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/open_french_word_gt_a28.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/open_word_transfer_a34.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/restore_predicted_lines_a36_assets.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/restore_predicted_lines_a37_assets.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/fetch_bnl_independent_a45.py')],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/audit_bnl_independent_a45.py')],cwd=ROOT,check=True)
