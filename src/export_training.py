"""Export fidèle des annotations produites, vers PAGE, ALTO plat et IR Axel."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import unicodedata
from lxml import etree
import alto

PAGE_NS='http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15'


def polygon(bbox):
    x0,y0,x1,y1=bbox
    return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]


def points(poly):
    return ' '.join(f'{round(x)},{round(y)}' for x,y in poly)


def page_xml(ir, annotations):
    def element(parent,name,**attrs):
        return etree.SubElement(parent,'{'+PAGE_NS+'}'+name,**attrs)
    root=etree.Element('{'+PAGE_NS+'}PcGts',nsmap={None:PAGE_NS})
    metadata=element(root,'Metadata');element(metadata,'Creator').text='BBVLM Gemini/CTC'
    stamp=datetime.now(timezone.utc).isoformat()
    element(metadata,'Created').text=stamp;element(metadata,'LastChange').text=stamp
    page=element(root,'Page',imageFilename=Path(ir['image']).name,imageWidth=str(ir['width']),imageHeight=str(ir['height']))
    if ir['blocks']:
        order=element(page,'ReadingOrder');group=element(order,'OrderedGroup',id='RO1')
        for i,b in enumerate(ir['blocks']):
            element(group,'RegionRefIndexed',index=str(i),regionRef=b['id'])
    page_types={'text':'paragraph','heading':'heading','caption':'caption','advert':'advertisement','table':'other','other':'other'}
    by_id={a['id']:a for a in annotations}
    for bi,b in enumerate(ir['blocks']):
        attrs=dict(id=b['id'],custom=f'readingOrder {{index:{bi};}} structure {{type:{b["type"]};}}')
        kind='ImageRegion' if b['type']=='illustration' else 'SeparatorRegion' if b['type']=='separator' else 'TextRegion'
        if kind=='TextRegion':attrs['type']=page_types.get(b['type'],'other')
        region=element(page,kind,**attrs)
        element(region,'Coords',points=points(b['polygon']))
        for li,line in enumerate(b['lines']):
            custom=f'readingOrder {{index:{li};}}'
            if line['article']:
                custom+=f' structure {{id:{line["article"]}; type:article;}}'
            tl=element(region,'TextLine',id=line['id'],custom=custom)
            element(tl,'Coords',points=points(line['polygon']))
            if line['baseline']:
                element(tl,'Baseline',points=points(line['baseline']))
            for wi,word in enumerate(by_id[line['id']]['words'],1):
                w=element(tl,'Word',id=f'{line["id"]}_W{wi:02d}')
                box=[word['x0'],word['y0'],word['x1']+1,word['y1']+1]
                element(w,'Coords',points=points(polygon(box)))
                te=element(w,'TextEquiv');element(te,'Unicode').text=word['text']
            te=element(tl,'TextEquiv');element(te,'Unicode').text=line['text']
    data=etree.tostring(root,encoding='UTF-8',xml_declaration=True,pretty_print=True)
    schema=Path(__file__).resolve().parents[1]/'schemas/page-2019.xsd'
    etree.XMLSchema(etree.parse(str(schema))).assertValid(etree.fromstring(data))
    return data


def export(image, directory):
    directory=Path(directory)
    annotations=json.loads((directory/'annotations.json').read_text())
    provenance=json.loads((directory/'provenance.json').read_text())
    olr=json.loads((directory/'olr.json').read_text())
    layout={r['id']:r for r in json.loads((directory/'segmentation.json').read_text())} if (directory/'segmentation.json').exists() else {}
    by_id={a['id']:a for a in annotations}
    W,H=provenance['taille']
    target_image=directory/Path(image).name
    if target_image.resolve() != Path(image).resolve():
        if not target_image.exists() or hashlib.sha256(target_image.read_bytes()).hexdigest() != hashlib.sha256(Path(image).read_bytes()).hexdigest():
            shutil.copy2(image,target_image)
    image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest()
    page_id='P_'+image_sha256[:24]
    ir=dict(id=page_id,width=W,height=H,image=str(target_image.resolve()),blocks=[],articles=[],
            provenance={'reader':provenance['lecture'],'geometry':provenance['geometrie'],
                        'image_sha256':image_sha256,
                        'block_articles':json.dumps({b['id']:b['article_id'] for b in olr['blocks']},ensure_ascii=False,sort_keys=True),
                        'character_position_semantics':'CTC frame intervals or documented native ink components; observed gaps/ink components have unknown CTC support (=0); per-character sources in training.jsonl and annotations.json',
                        'alignment_provenance':'annotations.json',
                        'olr_model':olr['model'],'certification':'automatic; independent criteria not yet met'})
    if olr.get('model_display_terminal'):ir['provenance']['olr_model_display_terminal']=olr['model_display_terminal']
    blocks=[];training=[];excluded=[]
    articles={a['id']:a for a in olr['articles']};retained_articles=set()
    for block in olr['blocks']:
        lines=[];alto_lines=[]
        if not block['line_ids']:
            if block['uncertain']:
                continue
            bb=block['bbox']
            ir['blocks'].append(dict(id=block['id'],type=block['type'],polygon=polygon(bb),lines=[]))
            blocks.append(dict(id=block['id'],type=block['type'],article_id=block['article_id'],
                               x0=bb[0],y0=bb[1],x1=bb[2]-1,y1=bb[3]-1,lines=[]))
            if block['article_id']:retained_articles.add(block['article_id'])
            continue
        for lid in block['line_ids']:
            a=by_id[lid]
            if not a['training_eligible'] or block['uncertain'] or (block['article_id'] and articles[block['article_id']]['uncertain']):
                excluded.append(dict(id=lid,status=a['status'],text=a['text'],
                                     reason='unresolved reading/geometry/OLR'))
                continue
            text=a['text'];chars=a.get('chars') or []
            if text != unicodedata.normalize('NFC',text) or chars and len(chars) != len(text):
                raise ValueError(f'{lid} : texte/positions invalides')
            box=a['bbox'];words=a['words']
            expected=list(re.finditer(r'\S+',text))
            if [m.group() for m in expected] != [w['text'] for w in words]:
                raise ValueError(f'{lid} : mots différents de la transcription')
            for c in chars:
                if not (0 <= c[0] <= c[1] <= W and 0 <= c[2] <= 1):
                    raise ValueError(f'{lid} : position de caractère hors page')
            for word in words:
                if not (box[0]<=word['x0']<=word['x1']<box[2] and box[1]<=word['y0']<=word['y1']<box[3]):
                    raise ValueError(f'{lid} : mot hors de sa ligne')
            line=dict(id=lid,polygon=polygon(box),baseline=layout.get(lid,{}).get('baseline',[]),
                      text=text,chars=chars,article=block['article_id'])
            lines.append(line)
            wb=[min(w['x0'] for w in words),min(w['y0'] for w in words),
                max(w['x1'] for w in words),max(w['y1'] for w in words)]
            alto_lines.append(dict(id=lid,bbox=[box[0],box[1],box[2]-1,box[3]-1],
                                   words=words,text=text,baseline=line['baseline'],polygon=line['polygon']))
            training.append(dict(page_id=page_id,line_id=lid,block_id=block['id'],article_id=block['article_id'],
                                 image=ir['image'],image_relative=target_image.name,bbox=box,text=text,chars=chars,
                                 raw_text=a.get('raw_text',text),linebreak=a.get('linebreak'),
                                 reading_job_id=a.get('reading_job_id'),model_claim=a.get('model'),
                                 model_display_terminal=a.get('model_display_terminal'),
                                 character_scope=(a.get('alignment') or {}).get('character_scope','line'),
                                 character_position_sources=(a.get('alignment') or {}).get('character_position_sources',['line_ctc']*len(chars)),
                                 **({'character_position_repairs':a['character_position_repairs']} if a.get('character_position_repairs') else {}),
                                 words=[dict(text=w['text'],start=m.start(),end=m.end(),
                                             bbox=[w['x0'],w['y0'],w['x1']+1,w['y1']+1])
                                        for m,w in zip(expected,words)],
                                 coordinate_convention='xyxy half-open pixels',
                                 quality_status='pseudo_annotation; not independently certified'))
        if not lines:
            continue
        bb=[min(min(p[0] for p in l['polygon']) for l in lines),
            min(min(p[1] for p in l['polygon']) for l in lines),
            max(max(p[0] for p in l['polygon']) for l in lines),
            max(max(p[1] for p in l['polygon']) for l in lines)]
        ir['blocks'].append(dict(id=block['id'],type=block['type'],polygon=polygon(bb),lines=lines))
        blocks.append(dict(id=block['id'],type=block['type'],article_id=block['article_id'],
                           x0=bb[0],y0=bb[1],x1=bb[2]-1,y1=bb[3]-1,lines=alto_lines))
        if block['article_id']:
            retained_articles.add(block['article_id'])
    ir['articles']=[dict(id=a['id'],type='article',title='') for a in olr['articles'] if a['id'] in retained_articles]
    alto_data=alto.build(W,H,Path(image).name,blocks,'BBVLM Gemini/CTC','OLR par IDs ; géométrie de production ; provenance.json et annotations.json conservés. Non certifié comme VT parfaite.')
    alto_result=alto.validate(alto_data)
    page_data=page_xml(ir,annotations)
    (directory/'training.alto.xml').write_bytes(alto_data)
    (directory/'training.page.xml').write_bytes(page_data)
    primary=directory/'page.alto.xml'
    if primary.exists() and not (directory/'pre-olr.alto.xml').exists():
        shutil.copy2(primary,directory/'pre-olr.alto.xml')
    primary.write_bytes(alto_data)
    (directory/'page.page.xml').write_bytes(page_data)
    (directory/'axel-ir.json').write_text(json.dumps(ir,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'training.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in training),encoding='utf-8')
    (directory/'training-excluded.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(lines_total=len(annotations),lines_exported=len(training),excluded=len(excluded),
                coverage=len(training)/len(annotations) if annotations else 0,
                alto_validation=alto_result,page_validation=True,criteria_met=False,
                coordinate_convention='IR/PAGE: xyxy extents; JSONL: half-open; internal boxer: inclusive')
    report['nontext_blocks_exported']=sum(not b['lines'] for b in ir['blocks'])
    report['nontext_candidates']=olr.get('nontext_candidates',0)
    report['nontext_rejected']=olr.get('nontext_rejected',0)
    (directory/'training-export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('image');ap.add_argument('directory');args=ap.parse_args()
    print(json.dumps(export(args.image,args.directory)))
