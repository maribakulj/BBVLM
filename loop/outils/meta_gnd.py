"""M02 — formes GND (préférées + variantes) des personnes liées à une notice K10plus.
usage : python meta_gnd.py PPN → JSON {gnd_id: [formes]} sur la sortie standard."""
import json, re, subprocess, sys


def get(u):
    r = subprocess.run(['curl', '-sfL', '--max-time', '60', u], capture_output=True)
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else ''


def personnes(ppn):
    x = get(f'https://sru.k10plus.de/opac-de-627?version=1.1&operation=searchRetrieve&query=pica.ppn%3D{ppn}&maximumRecords=1&recordSchema=marcxml')
    out = {}
    for tag in ('100', '700'):
        for m in re.finditer(r'<datafield tag="%s"[^>]*>(.*?)</datafield>' % tag, x, re.S):
            sf = re.findall(r'<subfield code="(.)">([^<]*)</subfield>', m.group(1))
            roles = [v for c, v in sf if c == '4']
            if roles and not set(roles) & {'aut', 'pra', 'rsp', 'cmp', 'dgs'}: continue
            ids = [v.split(')')[1] for c, v in sf if c == '0' and v.startswith('(DE-588)')]
            nom = [v for c, v in sf if c == 'a']
            if ids: out[ids[0]] = nom
    for g in list(out):
        try:
            d = json.loads(get(f'https://lobid.org/gnd/{g}.json') or '{}')
            out[g] = sorted(set(out[g] + [d.get('preferredName', '')] + (d.get('variantName') or [])) - {''})
        except ValueError:
            pass
    return out


if __name__ == '__main__':
    print(json.dumps(personnes(sys.argv[1]), ensure_ascii=False))
