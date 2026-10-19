"""Génération ALTO 4.4 à partir des lignes transcrites et alignées."""
from lxml import etree
from pathlib import Path
import hashlib
import unicodedata

NS = 'http://www.loc.gov/standards/alto/ns-v4#'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def validate(xml, schema_path=None, permitted_word_overlaps=()):
    path=Path(schema_path) if schema_path else Path(__file__).resolve().parents[1]/'schemas/alto-4-4.xsd'
    class Local(etree.Resolver):
        def resolve(self,url,public,context):
            local=path.parent/Path(url).name
            if local.exists():
                return self.resolve_filename(str(local),context)
    parser=etree.XMLParser(no_network=True)
    parser.resolvers.add(Local())
    schema=etree.XMLSchema(etree.parse(str(path),parser))
    root=etree.fromstring(xml)
    schema.assertValid(root)
    ids=root.xpath('//@ID')
    if len(ids) != len(set(ids)):
        raise ValueError('IDs ALTO dupliqués')
    for el in root.iter():
        for name in ('TAGREFS','REF','IDNEXT','PROCESSINGREFS'):
            if any(ref not in ids for ref in el.get(name,'').split()):
                raise ValueError(f'Référence ALTO absente : {name}')
    def box(el):
        x,y,w,h=(float(el.get(k)) for k in ('HPOS','VPOS','WIDTH','HEIGHT'))
        return x,y,x+w,y+h
    strings=[]
    permitted={frozenset(pair) for pair in permitted_word_overlaps}
    for page in root.findall('.//{%s}Page' % NS):
        W,H=float(page.get('WIDTH')),float(page.get('HEIGHT'))
        for el in page.iter():
            if all(k in el.attrib for k in ('HPOS','VPOS','WIDTH','HEIGHT')):
                a,b,c,d=box(el)
                if not 0<=a<c<=W or not 0<=b<d<=H:
                    raise ValueError('Élément ALTO hors page ou vide')
        for word in page.findall('.//{%s}String' % NS):
            bbox=box(word);x0,y0,x1,y1=bbox
            if not 0<=x0<x1<=W or not 0<=y0<y1<=H:
                raise ValueError('Mot ALTO hors page ou vide')
            text=word.get('CONTENT','')
            if not text or text != unicodedata.normalize('NFC',text):
                raise ValueError('Mot ALTO vide ou non NFC')
            for parent in word.iterancestors():
                if parent.tag in ('{%s}TextLine' % NS,'{%s}TextBlock' % NS,'{%s}PrintSpace' % NS):
                    a,b,c,d=box(parent)
                    if not a<=x0<x1<=c or not b<=y0<y1<=d:
                        raise ValueError('Mot ALTO hors de son conteneur')
            strings.append((word.get('ID'),bbox))
    active=[];audited_overlaps=0
    for wid,word in sorted(strings,key=lambda b:b[1][1]):
        active=[(bid,b) for bid,b in active if b[3]>word[1]]
        for bid,b in active:
            if min(b[2],word[2])>max(b[0],word[0]):
                if frozenset((wid,bid)) not in permitted:
                    raise ValueError('Mots ALTO superposés')
                audited_overlaps+=1
        active.append((wid,word))
    result=dict(valid=True,schema=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if permitted:result['audited_rectangle_overlaps']=audited_overlaps
    return result


def build(page_w, page_h, source_name, blocks, software, description):
    """blocks : liste de dicts {id, x0, y0, x1, y1, lines:[{id,bbox,words}]}"""
    root = etree.Element('{%s}alto' % NS, nsmap={None: NS, 'xsi': XSI})
    desc = etree.SubElement(root, '{%s}Description' % NS)
    etree.SubElement(desc, '{%s}MeasurementUnit' % NS).text = 'pixel'
    sd = etree.SubElement(desc, '{%s}sourceImageInformation' % NS)
    etree.SubElement(sd, '{%s}fileName' % NS).text = source_name
    proc = etree.SubElement(desc, '{%s}OCRProcessing' % NS, ID='OCRP_VLM_FRESH')
    step = etree.SubElement(proc, '{%s}ocrProcessingStep' % NS)
    etree.SubElement(step, '{%s}processingStepDescription' % NS).text = description
    ps = etree.SubElement(step, '{%s}processingSoftware' % NS)
    etree.SubElement(ps, '{%s}softwareName' % NS).text = software

    tagged=[b for b in blocks if b.get('type') or b.get('article_id')]
    if tagged:
        tags=etree.SubElement(root,'{%s}Tags' % NS)
        for kind in sorted({b['type'] for b in tagged if b.get('type')}):
            etree.SubElement(tags,'{%s}LayoutTag' % NS,ID='TYPE_'+kind,LABEL=kind)
        for aid in sorted({b['article_id'] for b in tagged if b.get('article_id')}):
            etree.SubElement(tags,'{%s}OtherTag' % NS,ID='ART_'+aid,TYPE='article',LABEL=aid)
        ro=etree.SubElement(root,'{%s}ReadingOrder' % NS)
        group=etree.SubElement(ro,'{%s}OrderedGroup' % NS,ID='RO1')
        for i,b in enumerate(blocks,1):
            etree.SubElement(group,'{%s}ElementRef' % NS,ID=f'ROREF_{i}',REF=b['id'])

    layout = etree.SubElement(root, '{%s}Layout' % NS)
    page = etree.SubElement(layout, '{%s}Page' % NS, ID='P1', PHYSICAL_IMG_NR='1',
                            WIDTH=str(page_w), HEIGHT=str(page_h))
    xs = [b['x0'] for b in blocks] or [0]; ys = [b['y0'] for b in blocks] or [0]
    xe = [b['x1'] for b in blocks] or [page_w-1]; ye = [b['y1'] for b in blocks] or [page_h-1]
    psp = etree.SubElement(page, '{%s}PrintSpace' % NS, ID='PS1',
                           HPOS=str(min(xs)), VPOS=str(min(ys)),
                           WIDTH=str(max(xe)-min(xs)+1), HEIGHT=str(max(ye)-min(ys)+1))
    for b in blocks:
        element='Illustration' if b.get('type')=='illustration' else 'GraphicalElement' if b.get('type')=='separator' else 'TextBlock'
        blk = etree.SubElement(psp, '{%s}%s' % (NS,element), ID=b['id'],
                               HPOS=str(b['x0']), VPOS=str(b['y0']),
                               WIDTH=str(b['x1']-b['x0']+1), HEIGHT=str(b['y1']-b['y0']+1))
        refs=[]
        if b.get('type'):refs.append('TYPE_'+b['type'])
        if b.get('article_id'):refs.append('ART_'+b['article_id'])
        if refs:blk.set('TAGREFS',' '.join(refs))
        hyp1, hyp2 = _hyphens(b['lines'])
        for ln in b['lines']:
            x0, y0, x1, y1 = ln['bbox']
            tl = etree.SubElement(blk, '{%s}TextLine' % NS, ID=ln['id'],
                                  HPOS=str(x0), VPOS=str(y0),
                                  WIDTH=str(x1-x0+1), HEIGHT=str(y1-y0+1))
            if ln.get('baseline'):
                tl.set('BASELINE',' '.join(f'{a:.3f},{b:.3f}' for a,b in ln['baseline']))
            if ln.get('polygon'):
                shape=etree.SubElement(tl,'{%s}Shape' % NS)
                etree.SubElement(shape,'{%s}Polygon' % NS,
                                 POINTS=' '.join(f'{a:.3f},{b:.3f}' for a,b in ln['polygon']))
            ws = ln['words']
            for wi, w in enumerate(ws, 1):
                at = {'ID': f"{ln['id']}_W{wi:02d}", 'CONTENT': w['text'],
                      'HPOS': str(w['x0']), 'VPOS': str(w['y0']),
                      'WIDTH': str(w['x1']-w['x0']+1), 'HEIGHT': str(w['y1']-w['y0']+1)}
                if w.get('synthetic'): at['WC'] = '0.50'
                if wi == len(ws) and ln['id'] in hyp1:
                    at['SUBS_TYPE'] = 'HypPart1'; at['SUBS_CONTENT'] = hyp1[ln['id']]
                if wi == 1 and ln['id'] in hyp2:
                    at['SUBS_TYPE'] = 'HypPart2'; at['SUBS_CONTENT'] = hyp2[ln['id']]
                etree.SubElement(tl, '{%s}String' % NS, **at)
                if wi < len(ws):
                    etree.SubElement(tl, '{%s}SP' % NS, HPOS=str(w['x1']+1),
                                     VPOS=str(w['y0']),
                                     WIDTH=str(max(0, ws[wi]['x0']-w['x1']-1)))
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def _hyphens(lines):
    """Césures imprimées : dernier mot en '-' suivi d'un mot commençant en minuscule."""
    h1, h2 = {}, {}
    for a, b in zip(lines, lines[1:]):
        if a.get('hyphen_next_id') != b['id']:
            continue
        if not a['words'] or not b['words']: continue
        wa, wb = a['words'][-1]['text'], b['words'][0]['text']
        if wa.endswith('-') and wb and wb[0].islower():
            full = wa[:-1] + wb.rstrip('.,;:!?»')
            h1[a['id']] = full; h2[b['id']] = full
    return h1, h2
