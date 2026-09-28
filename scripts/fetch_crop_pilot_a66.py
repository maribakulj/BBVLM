"""Fetch five frozen validation images, verify Git-LFS SHA256 and XML hashes."""
import base64, concurrent.futures, hashlib, json, re, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=['Berliner_Boersen_Zeitung_1857-04-06_0001','Bonner_Zeitung_1891-09-16_0001','Der_Bazar_1856-01-15_0004','Dresdner_Journal_1898-05-27_0001','Hildener_Rundschau_Illustrierte_1930-10-26_0006']
REV='66b50f53ccdb581d29cc02f670e469bbf583e825'
API='https://gitlab.uni-bonn.de/api/v4/projects/digital-history%2FChronicling-Germany-Dataset/repository/files/'
def fetch(name):
    started=time.perf_counter()
    url=API+urllib.parse.quote('data/images/'+name+'.jpg',safe='')+'/raw?ref='+REV
    metadata_url=url.replace('/raw?','?')
    with urllib.request.urlopen(metadata_url,timeout=120) as r: metadata=json.load(r)
    blob=base64.b64decode(metadata['content'])
    assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()==metadata['blob_id']
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        pointer=blob.decode()
        digest=re.search(r'oid sha256:([a-f0-9]{64})',pointer).group(1)
        size=int(re.search(r'size (\d+)',pointer).group(1))
    else:
        digest=hashlib.sha256(blob).hexdigest();size=len(blob)
    dest=ROOT/'corpora/chronicling-germany/images'/f'{name}.jpg'
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        with urllib.request.urlopen(url+'&lfs=true',timeout=180) as r: data=r.read()
        assert len(data)==size and hashlib.sha256(data).hexdigest()==digest, 'LFS mismatch '+name
        dest.write_bytes(data)
    data=dest.read_bytes()
    assert len(data)==size and hashlib.sha256(data).hexdigest()==digest
    return {'page':name,'path':str(dest.relative_to(ROOT)),'sha256':digest,'bytes':size,'git_blob_id':metadata['blob_id'],'source':url+'&lfs=true','seconds':time.perf_counter()-started}
def main():
    split=json.loads((ROOT/'experiments/loop/chronicling-a58/official_split.json').read_text())
    assert set(NAMES)<=set(split['Validation']) and not set(NAMES)&set(split['Test'])
    out=ROOT/'experiments/loop/next-a66';out.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(fetch,NAMES))
    report={'revision':REV,'test_pages_opened':0,'images':rows}
    (out/'assets-v2.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'verified_images':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
if __name__=='__main__':main()
