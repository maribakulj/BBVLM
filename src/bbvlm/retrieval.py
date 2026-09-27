"""Deterministic lexical search with exact source evidence; no extra VLM pass.

Diplomatic text is stored unchanged. NFC/long-s normalization only affects the
search field; SQLite unicode61 folds case, but preserves accents. Summaries and
inferred metadata are not silently blended into the source-text index.
"""
import json
import sqlite3
from pathlib import Path
from .document import validate,digest,index
from .metrics import normalise


def build_index(document, path):
    validate(document)
    ix=index(document);members={}
    for article in document['articles']:
        for rid in article['regions']:members.setdefault(rid,[]).append(article['id'])
    db=sqlite3.connect(str(path))
    try:
        with db:
            db.execute('DROP TABLE IF EXISTS passages');db.execute('DROP TABLE IF EXISTS provenance')
            db.execute("CREATE VIRTUAL TABLE passages USING fts5(search_text, diplomatic UNINDEXED, evidence UNINDEXED, tokenize='unicode61 remove_diacritics 0')")
            db.execute('CREATE TABLE provenance(key TEXT PRIMARY KEY,value TEXT)')
            db.execute('INSERT INTO provenance VALUES(?,?)',('document_sha256',digest(document)))
            db.execute('INSERT INTO provenance VALUES(?,?)',('normalisation','NFC; ſ→s; unicode61 case folding; accents preserved'))
            count=0
            for n in document['nodes']:
                if n['kind']!='line' or not n.get('text') or n['status']=='rejected':continue
                evidence={'document':document['id'],'page':n['page'],'region':n['parent'],'line':n['id'],
                    'bbox':n['bbox'],'articles':members.get(n['parent'],[]),'status':n['status'],
                    'needs_alignment':n.get('needs_alignment',False),'image':ix[n['page']].get('image'),
                    'alto_file':n['page']+'.alto.xml','alto_id':n['id']}
                db.execute('INSERT INTO passages VALUES(?,?,?)',(normalise(n['text']),n['text'],json.dumps(evidence,ensure_ascii=False)))
                count+=1
        return {'passages':count,'document_sha256':digest(document),'unit':'line','semantic_retrieval':False}
    finally:db.close()


def search(path, query, limit=10):
    if not 1<=limit<=100:raise ValueError('limit must be 1..100')
    terms=normalise(query).split()
    if not terms:return []
    # Treat each user token as literal text, not an arbitrary FTS expression.
    expression=' AND '.join('"'+term.replace('"','""')+'"' for term in terms)
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    try:
        rows=db.execute('SELECT diplomatic,evidence,bm25(passages) FROM passages WHERE passages MATCH ? ORDER BY bm25(passages) LIMIT ?',(expression,limit)).fetchall()
        return [{'text':text,'evidence':json.loads(evidence),'score':score} for text,evidence,score in rows]
    finally:db.close()
