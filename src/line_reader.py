"""Relecture ligne par ligne par Gemini (agy -p), indépendante du XML de référence.

Chaque ligne détectée est découpée dans l'image source, agrandie et posée sur
une planche numérotée. Gemini transcrit chaque bande numérotée ; une session
neuve par planche (mode print), donc aucune mémoire des lectures précédentes.
Les planches ne portent que des pixels de la page et des numéros.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont

LINE_PROMPT = (
    'Cette image est une planche de bandes numérotées, chacune découpée autour d’UNE ligne '
    'imprimée d’un journal français ancien. Pour chaque numéro, transcris littéralement la ligne '
    'centrale de la bande, telle qu’elle est imprimée : graphies, coquilles, chiffres, accents, '
    'ponctuation et trait d’union de fin de ligne compris, sans corriger ni compléter. Ignore les '
    'morceaux de lignes voisines coupés en haut ou en bas de la bande. Si une bande ne contient '
    'aucun texte (filet, tache), réponds "". Si un passage est réellement indéchiffrable, écris '
    '[illisible]. N’exécute aucune commande et n’utilise aucun outil autre que la lecture de cette '
    'image : réponds directement, uniquement par un objet JSON {"1": "...", "2": "...", ...} '
    'avec exactement les numéros de la planche.'
)

SINGLE_PROMPT = (
    'Cette image montre un extrait de journal français ancien. La ligne à lire est encadrée en '
    'rouge ; les lignes voisines ne servent que de contexte. Transcris littéralement la ligne '
    'encadrée, telle qu’elle est imprimée : graphies, coquilles, chiffres, accents, ponctuation et '
    'trait d’union final compris, sans corriger ni compléter. Regarde chaque chiffre un par un. '
    'N’exécute aucune commande et n’utilise aucun outil autre que la lecture de cette image : '
    'réponds directement, uniquement par un objet JSON {"texte": "..."}.'
)


def _font(size):
    for path in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                 '/System/Library/Fonts/Helvetica.ttc'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def line_strip(image, bbox, target_height=64, pad=.35):
    x0, y0, x1, y1 = bbox
    h = max(1, y1 - y0)
    box = (max(0, int(x0 - 8)), max(0, int(y0 - pad * h)),
           min(image.width, int(x1 + 8)), min(image.height, int(y1 + pad * h)))
    crop = image.crop(box)
    scale = min(3.0, max(1.0, target_height / h))
    return crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
                       Image.LANCZOS), box


def make_planches(image_path, lines, directory, per_sheet=14, max_width=1900, gutter=80, offset=0):
    """lines : [{id, bbox}] dans l'ordre voulu. ``offset`` décale le découpage en
    planches (deuxième passe indépendante : autres voisinages)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert('RGB')
    groups, current = [], []
    for index, line in enumerate(lines):
        current.append(line)
        if (index + 1 + offset) % per_sheet == 0:
            groups.append(current); current = []
    if current:
        groups.append(current)
    sheets = []
    font = _font(30)
    for number, group in enumerate(groups, 1):
        strips = []
        for line in group:
            strip, box = line_strip(image, line['bbox'])
            if strip.width > max_width - gutter:
                ratio = (max_width - gutter) / strip.width
                strip = strip.resize((max_width - gutter, max(1, round(strip.height * ratio))), Image.LANCZOS)
            strips.append((line, strip, box))
        width = gutter + max(s.width for _, s, _ in strips)
        height = sum(s.height + 14 for _, s, _ in strips) + 14
        sheet = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(sheet)
        y = 14
        mapping = {}
        for k, (line, strip, box) in enumerate(strips, 1):
            sheet.paste(strip, (gutter, y))
            draw.rectangle([gutter - 2, y - 2, gutter + strip.width + 1, y + strip.height + 1], outline=(150, 150, 150))
            draw.text((8, y + strip.height // 2 - 16), str(k), fill=(200, 0, 0), font=font)
            mapping[str(k)] = dict(line_id=line['id'], crop_box=list(box))
            y += strip.height + 14
        name = f'p{number:03d}.jpg'
        sheet.save(directory / name, quality=92)
        sheets.append(dict(sheet=name, lines=mapping,
                           sha256=hashlib.sha256((directory / name).read_bytes()).hexdigest()))
    (directory / 'planches.json').write_text(json.dumps(sheets, ensure_ascii=False, indent=1))
    return sheets


def single_view(image_path, lines, index, path, context=2, target_height=72):
    """Ligne encadrée + ``context`` lignes au-dessus et au-dessous (même colonne)."""
    image = Image.open(image_path).convert('RGB')
    line = lines[index]
    x0, y0, x1, y1 = line['bbox']
    h = max(1, y1 - y0)
    top, bottom = y0 - (context + .4) * h * 1.25, y1 + (context + .4) * h * 1.25
    box = (max(0, int(x0 - 40)), max(0, int(top)), min(image.width, int(x1 + 40)), min(image.height, int(bottom)))
    crop = image.crop(box)
    scale = min(3.0, max(1.0, target_height / h))
    crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    draw = ImageDraw.Draw(crop)
    rx0, ry0 = (x0 - box[0]) * scale, (y0 - box[1]) * scale
    rx1, ry1 = (x1 - box[0]) * scale, (y1 - box[1]) * scale
    draw.rectangle([rx0 - 6, ry0 - 6, rx1 + 6, ry1 + 6], outline=(220, 0, 0), width=3)
    if crop.width > 2000:
        r = 2000 / crop.width
        crop = crop.resize((2000, round(crop.height * r)), Image.LANCZOS)
    crop.save(path, quality=92)
    return list(box)


def ask(directory, image_name, prompt, model=None, timeout=240, attempts=3, log=None):
    """Un appel agy -p, session neuve ; renvoie le dict JSON ou None.
    La sortie JSON d'agy donne aussi les tokens consommés (tracés dans ``log``)."""
    question = f'{prompt}\n\nImage : @{image_name}\nNe lis aucun autre fichier.'
    command = ['agy', '-p', question, '--print-timeout', f'{timeout - 30}s', '--output-format', 'json']
    if model:
        command += ['--model', model]
    for attempt in range(attempts):
        started = time.time()
        usage = None
        try:
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            output = 'TIMEOUT'
        else:
            output = result.stdout
            try:
                envelope = json.loads(output)
                usage, output = envelope.get('usage'), envelope.get('response') or ''
            except json.JSONDecodeError:
                pass
        if log is not None:
            log.append(dict(image=image_name, attempt=attempt, seconds=round(time.time() - started, 1),
                            usage=usage, output_tail=output[-300:]))
        match = re.search(r'\{.*\}', output, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def read_planches(directory, model=None, workers=3, label='lecture'):
    """Lit toutes les planches d'un dossier (reprise : saute celles déjà lues)."""
    from concurrent.futures import ThreadPoolExecutor
    directory = Path(directory)
    sheets = json.loads((directory / 'planches.json').read_text())
    out = directory / f'{label}.jsonl'
    done = set()
    if out.exists():
        for row in out.read_text().splitlines():
            done.add(json.loads(row)['sheet'])
    todo = [s for s in sheets if s['sheet'] not in done]

    def one(sheet):
        log = []
        answer = ask(directory, sheet['sheet'], LINE_PROMPT, model=model, log=log)
        return dict(sheet=sheet['sheet'], model=model or 'agy-default', answer=answer, log=log)

    with ThreadPoolExecutor(workers) as pool:
        for row in pool.map(one, todo):
            with out.open('a') as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
            print(row['sheet'], 'ok' if row['answer'] is not None else 'FAILED', flush=True)
    reads = {}
    for row in out.read_text().splitlines():
        row = json.loads(row)
        sheet = next(s for s in sheets if s['sheet'] == row['sheet'])
        if row['answer'] is None:
            continue
        for k, meta in sheet['lines'].items():
            value = row['answer'].get(k)
            if isinstance(value, str):
                reads[meta['line_id']] = value
    return reads
