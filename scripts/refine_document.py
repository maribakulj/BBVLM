"""Apply an explicitly frozen geometric candidate to an existing word graph.

Experimental: keeps review status; original coordinates and algorithm are logged.
This does not infer word coordinates for lines that lack an alignment.
"""
from pathlib import Path
import sys,json,argparse,copy,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import cv2
from bbvlm.document import load,save,children
from bbvlm.refine import refine_words
ap=argparse.ArgumentParser();ap.add_argument('document');ap.add_argument('image');ap.add_argument('page');ap.add_argument('output');ap.add_argument('--candidate',default='experiments/loop/geometry-g01/frozen_candidate.json');a=ap.parse_args()
d=load(a.document);c=json.loads(Path(a.candidate).read_text());root=Path(__file__).resolve().parents[1]
if c['source_sha256']!=hashlib.sha256((root/'src/bbvlm/refine.py').read_bytes()).hexdigest():raise ValueError('candidate implementation changed')
im=cv2.imread(a.image,0)
if im is None:raise ValueError('image unreadable')
page=next(n for n in d['nodes'] if n['id']==a.page and n['kind']=='page')
if list(im.shape[::-1])!=page['bbox'][2:]:raise ValueError('image dimensions differ')
changes=[]
for line in [n for n in d['nodes'] if n['kind']=='line' and n['page']==a.page]:
    words=children(d,line['id'],'word')
    if line['status']=='human_verified' or any(w['status']=='human_verified' for w in words):continue
    if line.get('needs_alignment') or not words:continue
    poly=line.get('polygon') or [[line['bbox'][0],line['bbox'][1]],[line['bbox'][2],line['bbox'][1]],[line['bbox'][2],line['bbox'][3]],[line['bbox'][0],line['bbox'][3]]]
    before=[w['bbox'][:] for w in words];after=refine_words(im,before,poly,line['bbox'],**c['config'])
    for w,b,z in zip(words,before,after):
        if b!=z:w['bbox']=z;w['status']='automatic';changes.append({'id':w['id'],'before':b,'after':z})
d['events'].append({'type':'experimental_word_box_refinement','candidate':c,'changes':changes,'certified_ground_truth':False})
save(d,a.output);print(len(changes),'words refined; no certification')
