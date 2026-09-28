"""Chaîne complète → ALTO 4.4 : lignes kraken resserrées, texte lu, boîtes connexe.

Aucune donnée de référence en entrée. Pour chaque ligne lue : ligne kraken
alignée (`aligne.py`), mots placés par `connexe` (master). Une ligne lue sans
ligne kraken, ou dont le placement échoue, est écrite sans boîtes de mots mais
marquée `TAGREFS="NON_PLACE"` et comptée dans la provenance : on ne comble pas.
Coordonnées ALTO : HPOS/VPOS/WIDTH/HEIGHT en pixels, bornes inclusives.
usage : python vers_alto.py DOSSIER TEXTE SORTIE.xml
"""
import json, sys, os
from lxml import etree
import cv2
M = '/home/user/BBVLM/src'; sys.path[:0] = [M, M+'/boxers']
import connexe, corpora
from aligne import aligne

NS = 'http://www.loc.gov/standards/alto/ns-v4#'


def E(parent, tag, **at):
    return etree.SubElement(parent, f'{{{NS}}}{tag}', **{k: str(v) for k, v in at.items()})


def construit(dossier, texte, sortie, lecteur='Claude Opus (2 passes + arbitrage P3)'):
    lignes = [l for l in open(texte, encoding='utf-8').read().splitlines() if l.strip() and not l.startswith('#')]
    kr = json.load(open(f'{dossier}/kraken_serre.json'))['lignes']
    boites = [l['bbox'] for l in kr]
    g = cv2.imread(f'{dossier}/page.png', cv2.IMREAD_GRAYSCALE); H, W = g.shape
    loc = aligne(lignes, boites)
    bx = connexe.Connexe()
    root = etree.Element(f'{{{NS}}}alto', nsmap={None: NS, 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
    root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', NS+' http://www.loc.gov/standards/alto/v4/alto-4-4.xsd')
    d = E(root, 'Description'); E(d, 'MeasurementUnit').text = 'pixel'
    si = E(d, 'sourceImageInformation'); E(si, 'fileName').text = os.path.basename(dossier.rstrip('/'))+'.tif'
    p = E(d, 'OCRProcessing', ID='OCRP1'); st = E(p, 'ocrProcessingStep')
    E(st, 'processingStepDescription').text = ('texte : lecture VLM diplomatique OCR-D niveau 2 ; lignes : kraken blla resserré sur '
                                              "l'encre du polygone ; mots : connexe (BBVLM). Brouillon de vérité terrain : relecture humaine requise.")
    sw = E(st, 'processingSoftware'); E(sw, 'softwareName').text = f'BBVLM loop — {lecteur} + kraken 7.1.1 + connexe'
    tags = E(root, 'Tags'); E(tags, 'OtherTag', ID='NON_PLACE', LABEL='ligne lue non placée', TYPE='provenance')
    lay = E(root, 'Layout'); page = E(lay, 'Page', ID='P1', PHYSICAL_IMG_NR=1, WIDTH=W, HEIGHT=H)
    ps = E(page, 'PrintSpace', ID='PS1', HPOS=0, VPOS=0, WIDTH=W, HEIGHT=H)
    blk = E(ps, 'TextBlock', ID='B1')
    n_place = n_non = 0
    for i, t in enumerate(lignes):
        mots = t.split()
        if i in loc:
            x0, y0, x1, y1 = boites[loc[i]]
            tl = E(blk, 'TextLine', ID=f'L{i+1:04d}', HPOS=x0, VPOS=y0, WIDTH=x1-x0+1, HEIGHT=y1-y0+1)
            try:
                bs = bx.boxes(g, corpora.Line(t, mots, (x0, y0, x1, y1), []))
                ok = len(bs) == len(mots)
            except Exception:
                ok = False
        else:
            tl = E(blk, 'TextLine', ID=f'L{i+1:04d}', TAGREFS='NON_PLACE'); ok = False
        if ok:
            n_place += 1
            for k, (m, (a, b, c, e)) in enumerate(zip(mots, bs)):
                E(tl, 'String', ID=f'L{i+1:04d}_W{k+1:02d}', CONTENT=m, HPOS=a, VPOS=b, WIDTH=c-a+1, HEIGHT=e-b+1)
                if k < len(mots)-1:
                    E(tl, 'SP', HPOS=c+1, VPOS=b, WIDTH=max(1, bs[k+1][0]-c-1))
        else:
            n_non += 1
            tl.set('TAGREFS', 'NON_PLACE')
            for k, m in enumerate(mots):
                E(tl, 'String', ID=f'L{i+1:04d}_W{k+1:02d}', CONTENT=m)
                if k < len(mots)-1: E(tl, 'SP')
    xml = etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)
    open(sortie, 'wb').write(xml)
    return {'lignes': len(lignes), 'placees': n_place, 'non_placees': n_non}


def valide(chemin, xsd):
    s = etree.XMLSchema(etree.parse(xsd))
    ok = s.validate(etree.parse(chemin))
    return ok, [str(e) for e in s.error_log][:5]


if __name__ == '__main__':
    r = construit(*sys.argv[1:4])
    ok, err = valide(sys.argv[3], os.path.join(os.path.dirname(__file__), '..', 'schemas', 'alto-4-4-local.xsd'))
    print(r, 'XSD', 'valide' if ok else err)
