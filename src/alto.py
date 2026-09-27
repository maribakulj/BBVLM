"""Génération ALTO 4.4 à partir des lignes transcrites et alignées."""
from lxml import etree

NS = 'http://www.loc.gov/standards/alto/ns-v4#'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'


def build(page_w, page_h, source_name, blocks, software, description, *,
          coordinate_mode='inclusive', hyphen_pairs=None):
    """Legacy adapter. New graph exports use half-open coordinates.

    Existing boxers historically return inclusive ink bounds. Callers must opt
    into half_open when supplying that convention. Hyphen links must be explicit
    {first_line_id: (second_line_id, joined_text)}; adjacency is not evidence.
    """
    if coordinate_mode not in {'inclusive', 'half_open'}:
        raise ValueError('coordinate_mode must be inclusive or half_open')
    delta = 1 if coordinate_mode == 'inclusive' else 0
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
    if any(w.get('synthetic') for b in blocks for ln in b['lines'] for w in ln['words']):
        tags = etree.SubElement(root, '{%s}Tags' % NS)
        etree.SubElement(tags, '{%s}OtherTag' % NS, ID='SYNTHETIC_WORD',
                         LABEL='synthetic', TYPE='provenance')

    layout = etree.SubElement(root, '{%s}Layout' % NS)
    page = etree.SubElement(layout, '{%s}Page' % NS, ID='P1', PHYSICAL_IMG_NR='1',
                            WIDTH=str(page_w), HEIGHT=str(page_h))
    xs = [b['x0'] for b in blocks] or [0]; ys = [b['y0'] for b in blocks] or [0]
    xe = [b['x1'] for b in blocks] or [page_w-delta]
    ye = [b['y1'] for b in blocks] or [page_h-delta]
    psp = etree.SubElement(page, '{%s}PrintSpace' % NS, ID='PS1',
                           HPOS=str(min(xs)), VPOS=str(min(ys)),
                           WIDTH=str(max(xe)-min(xs)+delta), HEIGHT=str(max(ye)-min(ys)+delta))
    for b in blocks:
        blk = etree.SubElement(psp, '{%s}TextBlock' % NS, ID=b['id'],
                               HPOS=str(b['x0']), VPOS=str(b['y0']),
                               WIDTH=str(b['x1']-b['x0']+delta), HEIGHT=str(b['y1']-b['y0']+delta))
        hyp1, hyp2 = {}, {}
        ids = {ln['id'] for ln in b['lines']}
        for first, (second, joined) in (hyphen_pairs or {}).items():
            if first in ids and second in ids:
                hyp1[first] = joined; hyp2[second] = joined
        for ln in b['lines']:
            x0, y0, x1, y1 = ln['bbox']
            tl = etree.SubElement(blk, '{%s}TextLine' % NS, ID=ln['id'],
                                  HPOS=str(x0), VPOS=str(y0),
                                  WIDTH=str(x1-x0+delta), HEIGHT=str(y1-y0+delta))
            ws = ln['words']
            for wi, w in enumerate(ws, 1):
                at = {'ID': f"{ln['id']}_W{wi:02d}", 'CONTENT': w['text'],
                      'HPOS': str(w['x0']), 'VPOS': str(w['y0']),
                      'WIDTH': str(w['x1']-w['x0']+delta), 'HEIGHT': str(w['y1']-w['y0']+delta)}
                if w.get('synthetic'): at['TAGREFS'] = 'SYNTHETIC_WORD'
                if w.get('confidence') is not None:
                    if not 0 <= w['confidence'] <= 1:
                        raise ValueError('word confidence outside [0,1]')
                    at['WC'] = str(w['confidence'])
                if wi == len(ws) and ln['id'] in hyp1:
                    at['SUBS_TYPE'] = 'HypPart1'; at['SUBS_CONTENT'] = hyp1[ln['id']]
                if wi == 1 and ln['id'] in hyp2:
                    at['SUBS_TYPE'] = 'HypPart2'; at['SUBS_CONTENT'] = hyp2[ln['id']]
                etree.SubElement(tl, '{%s}String' % NS, **at)
                if wi < len(ws):
                    etree.SubElement(tl, '{%s}SP' % NS, HPOS=str(w['x1']+delta),
                                     VPOS=str(w['y0']),
                                     WIDTH=str(max(0, ws[wi]['x0']-w['x1']-delta)))
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
