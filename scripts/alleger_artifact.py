#!/usr/bin/env python
"""Recompresse les vignettes JPEG embarquées d'un rapport HTML (publication en ligne).

Les rapports d'écarts dépassent 8 Mo et le dépôt en ligne expire (408) : vignettes
ramenées à 640 px de large, qualité 50. Le rapport local complet reste intact.
"""
import base64, io, re, sys
from PIL import Image


def lighten(match):
    im = Image.open(io.BytesIO(base64.b64decode(match.group(1))))
    if im.width > 640:
        im = im.resize((640, round(im.height * 640 / im.width)))
    buffer = io.BytesIO(); im.convert('RGB').save(buffer, 'JPEG', quality=50, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()


for path in sys.argv[1:]:
    text = open(path).read()
    new = re.sub(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', lighten, text)
    open(path, 'w').write(new); print(path, len(text), '->', len(new))
