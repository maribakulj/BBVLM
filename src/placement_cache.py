"""Checkpoint des placements locaux, avant refus globaux et export.

Toutes les entrées sont des sorties de production ou des empreintes de code.
Les collisions interlignes et le seuil de document sont recalculés à la reprise.
"""
import hashlib
import json
from pathlib import Path


class PlacementCache:
    def __init__(self,directory,image_sha256,boxer_signature,implementation):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.signature=dict(version='local-placement-v1',image_sha256=image_sha256,
                            boxer=boxer_signature,implementation=implementation)
        self.hits=0;self.saved=0

    def key(self,request,reading,geometry):
        content=dict(**self.signature,id=request.id,source_bbox=list(request.bbox),
                     geometry=geometry,reading=reading.__dict__)
        return hashlib.sha256(json.dumps(content,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def load(self,key):
        path=self.directory/(key+'.json')
        if not path.exists():return None
        try:
            payload=json.loads(path.read_text())
            if payload['key']!=key or 'status' not in payload['annotation']:
                raise ValueError('Checkpoint de placement incomplet')
            if not isinstance(payload['lines'],list) or not isinstance(payload['refusals'],list):
                raise ValueError('Checkpoint de placement incohérent')
        except (ValueError,KeyError,TypeError):
            path.rename(path.with_suffix('.corrupt'));return None
        self.hits+=1;return payload

    def store(self,key,annotation,lines,refusals,retries):
        value=dict(key=key,annotation=annotation,lines=lines,refusals=refusals,retries=retries)
        path=self.directory/(key+'.json');temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2));temporary.replace(path)
        self.saved+=1
        state=self.directory/'state.json';temporary=state.with_suffix('.tmp')
        temporary.write_text(json.dumps(dict(signature=self.signature,hits=self.hits,saved=self.saved),ensure_ascii=False,indent=2));temporary.replace(state)
