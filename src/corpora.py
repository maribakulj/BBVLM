"""Chargement des corpus à boîtes de mots vérifiées.

La vérité terrain ici, ce sont les boîtes de mots du producteur ou de
l'annotateur — jamais une sortie de notre chaîne. On s'en sert pour NOTER,
jamais pour construire : aucun boxer ne reçoit une boîte de VT en entrée.
Entrée d'un boxer = l'image + le texte de la ligne + la boîte de LIGNE.
"""
from __future__ import annotations
import glob, os
from dataclasses import dataclass
import numpy as np
import cv2
from lxml import etree


@dataclass
class Line:
    text: str
    words: list[str]
    line_box: tuple[int, int, int, int]        # x0,y0,x1,y1
    word_boxes: list[tuple[int, int, int, int]]  # VT — pour la notation SEULEMENT


@dataclass
class Page:
    name: str
    corpus: str
    image_path: str
    lines: list[Line]
    _g: np.ndarray | None = None

    @property
    def gray(self) -> np.ndarray:
        if self._g is None:
            self._g = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        return self._g


def _box(pts_attr: str) -> tuple[int, int, int, int]:
    pts = [tuple(map(int, q.split(','))) for q in pts_attr.split()]
    xs = [a for a, _ in pts]; ys = [b for _, b in pts]
    return min(xs), min(ys), max(xs), max(ys)


def load_page_xml(xml: str, image: str, corpus: str, name: str) -> Page | None:
    """PAGE XML avec <Word><Coords>."""
    try:
        r = etree.parse(xml).getroot()
    except Exception:
        return None
    ns = r.tag.split('}')[0].strip('{'); N = {'p': ns}
    lines: list[Line] = []
    for tl in r.findall('.//p:TextLine', N):
        c = tl.find('p:Coords', N)
        if c is None: continue
        words, boxes = [], []
        for w in tl.findall('p:Word', N):
            u = w.find('p:TextEquiv/p:Unicode', N)
            wc = w.find('p:Coords', N)
            if u is None or not u.text or wc is None: continue
            words.append(u.text.strip()); boxes.append(_box(wc.get('points')))
        if len(words) < 2: continue      # une seule "Word" = la ligne entière, pas des mots
        lines.append(Line(' '.join(words), words, _box(c.get('points')), boxes))
    return Page(name, corpus, image, lines) if lines else None


def load_alto(xml: str, image: str, corpus: str, name: str) -> Page | None:
    """ALTO avec <String HPOS WIDTH VPOS HEIGHT>."""
    try:
        r = etree.parse(xml).getroot()
    except Exception:
        return None
    ns = r.tag.split('}')[0].strip('{'); N = {'a': ns}
    lines: list[Line] = []
    for tl in r.findall('.//a:TextLine', N):
        words, boxes = [], []
        for s in tl.findall('a:String', N):
            t = s.get('CONTENT')
            if not t: continue
            try:
                x, y = int(s.get('HPOS')), int(s.get('VPOS'))
                w, h = int(s.get('WIDTH')), int(s.get('HEIGHT'))
            except (TypeError, ValueError):
                continue
            words.append(t); boxes.append((x, y, x + w, y + h))
        if len(words) < 2: continue
        lx0 = min(b[0] for b in boxes); ly0 = min(b[1] for b in boxes)
        lx1 = max(b[2] for b in boxes); ly1 = max(b[3] for b in boxes)
        try:
            lx0 = int(tl.get('HPOS')); ly0 = int(tl.get('VPOS'))
            lx1 = lx0 + int(tl.get('WIDTH')); ly1 = ly0 + int(tl.get('HEIGHT'))
        except (TypeError, ValueError):
            pass
        lines.append(Line(' '.join(words), words, (lx0, ly0, lx1, ly1), boxes))
    return Page(name, corpus, image, lines) if lines else None


HOME = os.path.expanduser('~')


def gt_is_geometric(page: 'Page', thr_gap: float = 0.06, min_empty: float = 0.30) -> bool:
    """Une VT est utilisable comme vérité GÉOMÉTRIQUE seulement si ses blancs
    inter-mots sont effectivement vides d'encre. Mesuré : BNL a 0,179 d'encre
    dans ses blancs contre 0,184 dans ses boîtes, et 7 % de blancs vides — ses
    boîtes ne délimitent pas les mots. Noter un boxer contre elle revient à le
    mesurer avec une règle faussée."""
    import cv2
    g = page.gray
    if g is None: return False
    small = cv2.resize(g, (0, 0), fx=.3, fy=.3)
    t = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    gaps, empty = [], 0
    for ln in page.lines[:60]:
        for k in range(len(ln.word_boxes)-1):
            a, b = ln.word_boxes[k], ln.word_boxes[k+1]
            if b[0] <= a[2]+1: continue
            sub = g[max(0, min(a[1], b[1])):max(a[3], b[3]), a[2]:b[0]]
            if not sub.size: continue
            d = float((sub < t).mean()); gaps.append(d)
            if d < 0.02: empty += 1
    if len(gaps) < 20: return False
    import statistics
    return statistics.median(gaps) <= thr_gap and empty/len(gaps) >= min_empty


def all_pages(limit_per_corpus: int | None = None, only_geometric: bool = True,
              max_lignes: int | None = None) -> list[Page]:
    """`max_lignes` borne le nombre de lignes par page — pour itérer vite sans
    changer le critère. La validation finale se fait toujours sans borne."""
    out: list[Page] = []
    # XVIIe français, PAGE XML, boîtes de mots humaines
    n = 0
    for d in sorted(glob.glob(f'{HOME}/corpus-vt/raw/*_corrected_*')):
        ref, img = os.path.join(d, 'ref.page.xml'), os.path.join(d, 'image.png')
        if not (os.path.exists(ref) and os.path.exists(img)): continue
        if os.path.getsize(ref) < 200: continue
        p = load_page_xml(ref, img, 'OCR17', os.path.basename(d)[:24])
        if p: out.append(p); n += 1
        if limit_per_corpus and n >= limit_per_corpus: break
    # ATR Newseye — presse française, PAGE XML avec Word + Coords
    n = 0
    for x in sorted(glob.glob(f'{HOME}/Downloads/ATR_TrainingSet_BnF_Newseye_M2+/*.xml')):
        img = next((x[:-4]+e for e in ('.tif', '.jpg', '.png') if os.path.exists(x[:-4]+e)), None)
        if not img: continue
        p = load_page_xml(x, img, 'Newseye', os.path.basename(x)[:-4][:20])
        if p: out.append(p); n += 1
        if n >= (limit_per_corpus or 12): break
    # BNL complet — même famille que le sous-ensemble cinoc, testé à part
    n = 0
    for x in sorted(glob.glob(f'{HOME}/Downloads/bnl-ground-truth-newspapers-before-1878-raw/*/*.xml')):
        img = x[:-4] + '.png'
        if not os.path.exists(img): continue
        p = load_alto(x, img, 'BNLfull', os.path.basename(os.path.dirname(x))+'/'+os.path.basename(x)[:-4])
        if p: out.append(p); n += 1
        if n >= (limit_per_corpus or 40): break
    # Presse française 1900, VT vérifiée à la main (786 String)
    pp = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/corpora/petitparisien'
    if os.path.exists(f'{pp}/page.alto.xml'):
        p = load_alto(f'{pp}/page.alto.xml', f'{pp}/page.jpg', 'PetitParisien', 'col2')
        if p: out.append(p)
    bnf = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/corpora/bnf'
    if os.path.exists(f'{bnf}/page.alto.xml'):
        p = load_alto(f'{bnf}/page.alto.xml', f'{bnf}/page.jpg', 'BnF', 'X0000002')
        if p: out.append(p)
    # Presse luxembourgeoise, ALTO, dont du Fraktur
    n = 0
    for x in sorted(glob.glob(f'{HOME}/cinoc/corpus/37-GT-BNL/*.xml')):
        img = x[:-4] + '.png'
        if not os.path.exists(img): continue
        p = load_alto(x, img, 'BNL', os.path.basename(x)[:-4])
        if p: out.append(p); n += 1
        if limit_per_corpus and n >= limit_per_corpus: break
    if max_lignes:
        for p in out: p.lines = p.lines[:max_lignes]
    if only_geometric:
        keep, rejected = [], {}
        for p in out:
            if gt_is_geometric(p): keep.append(p)
            else: rejected[p.corpus] = rejected.get(p.corpus, 0) + 1
        if rejected:
            import sys
            print(f"[corpora] VT non géométrique, écartée : {rejected}", file=sys.stderr)
        out = keep
    return out


if __name__ == '__main__':
    ps = all_pages()
    from collections import Counter
    c = Counter(p.corpus for p in ps)
    print("pages :", dict(c))
    print("lignes :", sum(len(p.lines) for p in ps))
    print("mots   :", sum(len(l.words) for p in ps for l in p.lines))
    for p in ps[:3]:
        l = p.lines[0]
        print(f"  {p.corpus}/{p.name}: {len(p.lines)} lignes | ex. {len(l.words)} mots {l.words[:4]}")
