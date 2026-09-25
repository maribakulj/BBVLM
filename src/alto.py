"""Génération ALTO 4.4 à partir des lignes transcrites et alignées."""
from lxml import etree

NS = 'http://www.loc.gov/standards/alto/ns-v4#'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def build(page_w, page_h, source_name, blocks, software, description):
    """blocks : liste de dicts {id, x0, y0, x1, y1, lines:[{id,bbox,words}]}"""
    root = etree.Element('{%s}alto' % NS, nsmap={None: NS, 'xsi': XSI})
    desc = etree.SubElement(root, '{%s}Description' % NS)
    etree.SubElement(desc, '{%s}MeasurementUnit' % NS).text = 'pixel'
    sd = etree.SubElement(desc, '{%s}sourceImageInformation' % NS)
    etree.SubElement(sd, '{%s}fileName' % NS).text = source_name
    proc = etree.SubElement(desc, '{%s}OCRProcessing' % NS, ID='OCRP_VLM_FRESH')
    step = etree.SubElement(proc, '{%s}ocrProcessingStep' % NS)
    ps = etree.SubElement(step, '{%s}processingSoftware' % NS)
    etree.SubElement(ps, '{%s}softwareName' % NS).text = software
    etree.SubElement(step, '{%s}processingStepDescription' % NS).text = description

    layout = etree.SubElement(root, '{%s}Layout' % NS)
    page = etree.SubElement(layout, '{%s}Page' % NS, ID='P1', PHYSICAL_IMG_NR='1',
                            WIDTH=str(page_w), HEIGHT=str(page_h))
    xs = [b['x0'] for b in blocks]; ys = [b['y0'] for b in blocks]
    xe = [b['x1'] for b in blocks]; ye = [b['y1'] for b in blocks]
    psp = etree.SubElement(page, '{%s}PrintSpace' % NS, ID='PS1',
                           HPOS=str(min(xs)), VPOS=str(min(ys)),
                           WIDTH=str(max(xe)-min(xs)+1), HEIGHT=str(max(ye)-min(ys)+1))
    for b in blocks:
        blk = etree.SubElement(psp, '{%s}TextBlock' % NS, ID=b['id'],
                               HPOS=str(b['x0']), VPOS=str(b['y0']),
                               WIDTH=str(b['x1']-b['x0']+1), HEIGHT=str(b['y1']-b['y0']+1))
        hyp1, hyp2 = _hyphens(b['lines'])
        for ln in b['lines']:
            x0, y0, x1, y1 = ln['bbox']
            tl = etree.SubElement(blk, '{%s}TextLine' % NS, ID=ln['id'],
                                  HPOS=str(x0), VPOS=str(y0),
                                  WIDTH=str(x1-x0+1), HEIGHT=str(y1-y0+1))
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
                                     WIDTH=str(max(1, ws[wi]['x0']-w['x1']-1)))
    return etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)


def _hyphens(lines):
    """Césures imprimées : dernier mot en '-' suivi d'un mot commençant en minuscule."""
    h1, h2 = {}, {}
    for a, b in zip(lines, lines[1:]):
        if not a['words'] or not b['words']: continue
        wa, wb = a['words'][-1]['text'], b['words'][0]['text']
        if wa.endswith('-') and wb and wb[0].islower():
            full = wa[:-1] + wb.rstrip('.,;:!?»')
            h1[a['id']] = full; h2[b['id']] = full
    return h1, h2
