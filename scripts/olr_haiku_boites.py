#!/usr/bin/env python
"""OLR sans coordonnées : Haiku range les boîtes de PP-DocLayout dans l'ordre de lecture.

Les boîtes (détecteur, coordonnées exactes) sont dessinées et numérotées sur la page
réduite ; la page est aussi donnée en bandes plus lisibles. Haiku rend, en JSON, les
articles dans l'ordre de lecture : type et liste ordonnée des numéros de boîtes,
plus les boîtes à ignorer (images, filets) et les zones de texte sans boîte. Il ne
transcrit rien et ne donne aucune coordonnée.
Usage : olr_haiku_boites.py image boites.json sortie [--model claude-haiku-5-5]
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from region_agy import run_agy
from region_claude import _parse

Image.MAX_IMAGE_PIXELS = None
COLORS = {'text': (0, 90, 220), 'paragraph_title': (220, 40, 40), 'doc_title': (200, 0, 160),
          'table': (0, 150, 60), 'image': (130, 130, 130)}


def draw(image, boxes, output, side=1568, bands=3):
    im = Image.open(image).convert('RGB')
    scale = side / max(im.size)
    small = im.resize((round(im.width*scale), round(im.height*scale)), Image.LANCZOS)
    pages = [('page', small, 0, scale)]
    # bandes horizontales à meilleure résolution (recouvrement 4 %)
    h = im.height / bands
    for b in range(bands):
        y0, y1 = max(0, round(b*h - .04*im.height)), min(im.height, round((b+1)*h + .04*im.height))
        crop = im.crop((0, y0, im.width, y1)); s = min(side / max(crop.size), (1.15e6 / (crop.width*crop.height))**.5)
        pages.append((f'bande{b+1}', crop.resize((round(crop.width*s), round(crop.height*s)), Image.LANCZOS), y0, s))
    paths = []
    for name, canvas, y0, s in pages:
        d = ImageDraw.Draw(canvas)
        font = ImageFont.load_default(size=max(14, round(canvas.width / 70)))
        for n, box in enumerate(boxes, 1):
            x0, by0, x1, by1 = box['bbox']
            r = [x0*s, (by0-y0)*s, x1*s, (by1-y0)*s]
            if r[3] < 0 or r[1] > canvas.height:
                continue
            c = COLORS.get(box['label'], (230, 120, 0))
            d.rectangle(r, outline=c, width=2)
            t = str(n); tw = d.textlength(t, font=font)
            cx, cy = (r[0]+r[2])/2 - tw/2, max(0, (r[1]+r[3])/2 - font.size/2)
            d.rectangle([cx-2, cy-1, cx+tw+2, cy+font.size+2], fill=(255, 255, 210))
            d.text((cx, cy), t, fill=c, font=font)
        path = output / f'{name}.png'; canvas.save(path); paths.append(str(path))
    return paths


PROMPT = (
    'Ouvre avec l’outil Read, dans l’ordre : {paths}. La première image est une page entière de journal '
    'français ancien ; les suivantes sont la même page en bandes horizontales plus lisibles, de haut en bas. '
    'Chaque zone détectée est encadrée et porte un NUMÉRO (bleu : texte, rouge : titre, vert : tableau, '
    'gris : image). Décris la STRUCTURE LOGIQUE de la page sans rien transcrire : liste les articles '
    'dans l’ordre de lecture (bandeau d’abord, puis colonne par colonne de haut en bas, en suivant un '
    'article qui passe d’une colonne à la suivante). Pour chaque article : "type" parmi "en-tete", '
    '"article", "annonces", "tableau", "feuilleton", "autre", et "boites" = la liste ORDONNÉE des numéros '
    'de ses zones dans l’ordre de lecture (titre puis paragraphes). Chaque numéro de texte, titre ou '
    'tableau apparaît une seule fois. Ajoute "ignorees" (numéros qui ne sont pas du texte, ou doublons '
    'd’une autre zone) et "manques" (description courte de tout texte imprimé qui n’est dans aucune zone, '
    'par exemple « colonne 3, bas »). Si tu ne peux pas voir les images, réponds uniquement '
    'IMAGE_ABSENTE. Réponds uniquement par un objet JSON {{"articles": [...], "ignorees": [...], '
    '"manques": [...]}}. N’utilise aucun autre outil et ne lis aucun autre fichier.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image'); parser.add_argument('boxes'); parser.add_argument('output')
    parser.add_argument('--model', default='claude-haiku-5-5')
    args = parser.parse_args()
    output = Path(args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    boxes = json.loads(Path(args.boxes).read_text())
    boxes = sorted(boxes, key=lambda b: (b['bbox'][0] // 400, b['bbox'][1]))  # numéros stables, sans valeur d'ordre
    (output / 'boites.json').write_text(json.dumps(boxes, ensure_ascii=False, indent=1))
    paths = draw(args.image, boxes, output)
    question = PROMPT.format(paths=', '.join(paths))
    log, result = [], None
    for attempt in range(3):
        t0 = time.time()
        out = run_agy(['claude', '-p', question, '--model', args.model, '--allowedTools', 'Read',
                       '--output-format', 'stream-json', '--verbose'], output, 900)
        text, status, opened, usage, cost = _parse(out or '')
        seen = all(p in opened for p in paths)
        log.append(dict(attempt=attempt, seconds=round(time.time()-t0, 1), status=status, opened=len(opened),
                        all_images_opened=seen, cost_usd=cost))
        match = re.search(r'\{.*\}', text, re.S)
        if status == 'SUCCESS' and seen and match:
            try:
                result = json.loads(match.group(0)); break
            except json.JSONDecodeError:
                pass
    (output / 'olr-haiku.json').write_text(json.dumps(dict(model=args.model, calls=log, complete=result is not None,
                                                           **(result or {})), ensure_ascii=False, indent=1))
    print(json.dumps(log), 'articles', len((result or {}).get('articles', [])))


if __name__ == '__main__':
    main()
