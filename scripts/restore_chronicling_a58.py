#!/usr/bin/env python3
"""Restore only A58 XML, verifying every file against the audited snapshot."""
import argparse,hashlib,json,shutil,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path);a=p.parse_args()
report=json.loads((ROOT/'experiments/loop/chronicling-a58/audit.json').read_text());source=json.loads((ROOT/'experiments/loop/chronicling-a58/source.json').read_text())
target=ROOT/'corpora/chronicling-germany';target.mkdir(parents=True,exist_ok=True);archive=target/'annotations.zip'
if a.archive:
 if a.archive.resolve()!=archive.resolve():shutil.copyfile(a.archive,archive)
elif not archive.exists():
 rev=source['revision'];url=f"{source['repository']}/-/archive/{rev}/Chronicling-Germany-Dataset-{rev}.zip?path=data/annotations"
 tmp=archive.with_suffix('.download')
 with urllib.request.urlopen(url,timeout=120) as response,tmp.open('wb') as stream:shutil.copyfileobj(response,stream)
 tmp.replace(archive)
expected={x['file']:x['sha256'] for x in report['files_detail']};blobs=[]
with zipfile.ZipFile(archive) as z:
 members=[x for x in z.namelist() if x.endswith('.xml')]
 assert len(members)==len(expected) and {Path(x).name for x in members}==set(expected),'XML inventory changed'
 for member in sorted(members,key=lambda x:Path(x).name):
  data=z.read(member);name=Path(member).name
  assert hashlib.sha256(data).hexdigest()==expected[name],f'XML digest mismatch: {name}'
  sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).digest();blobs.append(b'100644 '+name.encode()+b'\0'+sha)
 content=b''.join(blobs);digest=hashlib.sha1(b'tree '+str(len(content)).encode()+b'\0'+content).hexdigest()
 assert digest==source['annotation_git_tree'],'Git tree mismatch'
 # Extract only after all checks; fixed basename avoids archive traversal.
 out=target/'annotations';out.mkdir(exist_ok=True)
 for member in members:(out/Path(member).name).write_bytes(z.read(member))
print(json.dumps({'files':len(expected),'git_tree':digest,'verified':True,'images_downloaded':0,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
