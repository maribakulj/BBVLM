"""CPU-only document workflow: python -m bbvlm --help."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from . import document as D
from .formats import (import_xml, export_alto, export_mets, validate_xml,
                      audit_mets_package, validate_embedded_profiles)
from .metrics import text_scores, word_scores


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def export_package(d, out, schemas=None):
    """Validate all projections before publishing any package files."""
    D.validate(d)
    files = {p["id"]: p["id"]+".alto.xml" for p in d["nodes"] if p["kind"] == "page"}
    xmls = {name: export_alto(d, pid) for pid, name in files.items()}
    out = Path(out)
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        D.save(d, temp/'document.json')
        from .retrieval import build_index
        retrieval = build_index(d, temp/'retrieval.sqlite')
        records = {}
        for pid, filename in files.items():
            content = xmls[filename]
            records['FILE_'+pid] = {'href': filename, 'mimetype': 'application/xml',
                'size': len(content), 'checksum': hashlib.sha256(content).hexdigest()}
        for fid, name, mime in [('FILE_GRAPH','document.json','application/json'),
                                ('FILE_RETRIEVAL','retrieval.sqlite','application/vnd.sqlite3')]:
            content = (temp/name).read_bytes()
            records[fid] = {'href': name, 'mimetype': mime, 'size': len(content),
                            'checksum': hashlib.sha256(content).hexdigest()}
        xmls['mets.xml'] = export_mets(d, files, retrieval_file='retrieval.sqlite', file_records=records)
        profile_validation = None
        if schemas:
            for name, content in xmls.items():
                validate_xml(content, Path(schemas)/("mets.xsd" if name == "mets.xml" else "alto-4-4.xsd"))
            profile_validation = validate_embedded_profiles(xmls['mets.xml'], schemas)
        out.mkdir(parents=True, exist_ok=True)
        (out/'document.json').write_bytes((temp/'document.json').read_bytes())
        (out/'retrieval.sqlite').write_bytes((temp/'retrieval.sqlite').read_bytes())
    write_json(out/"review.json", D.review_queue(d))
    for name, content in xmls.items():
        (out/name).write_bytes(content)
    integrity = audit_mets_package(xmls['mets.xml'], out)
    summary = {"pages": len(files), "lines": sum(n["kind"] == "line" for n in d["nodes"]),
               "lines_requiring_review": len(D.review_queue(d)),
               "schema_validated": bool(schemas), "certified_ground_truth": False,
               "retrieval": retrieval, "mets_package_integrity": integrity,
               "mods_version": "3.8", "premis_version": "3.0",
               "embedded_profile_validation": profile_validation}
    write_json(out/"package.json", summary)
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest="command", required=True)
    im = commands.add_parser("import", help="ALTO or PAGE → canonical graph")
    im.add_argument("xml"); im.add_argument("output")
    en = commands.add_parser("apply", help="apply a recorded ID-addressed model response")
    en.add_argument("document"); en.add_argument("response"); en.add_argument("output")
    en.add_argument("--model", required=True)
    en.add_argument("--request", help="trusted request JSON for a subset of lines")
    ex = commands.add_parser("export", help="graph → ALTO + METS + review queue")
    ex.add_argument("document"); ex.add_argument("directory")
    ex.add_argument("--schemas", help="directory containing offline ALTO/METS/XLink XSDs")
    ev = commands.add_parser("compare", help="score a saved hypothesis against a reference")
    ev.add_argument("reference"); ev.add_argument("hypothesis"); ev.add_argument("output")
    ev.add_argument("--mode", choices=["text", "words"], default="text")
    batch = commands.add_parser("prepare", help="prepare image crops and a blind or OCR-assisted request")
    batch.add_argument("document"); batch.add_argument("image"); batch.add_argument("page")
    batch.add_argument("directory"); batch.add_argument("--line-ids", nargs="+")
    batch.add_argument("--show-ocr", action="store_true")
    pero = commands.add_parser("pero-realign", help="native PERO alignment from a saved cache (optional dependency)")
    pero.add_argument("cache"); pero.add_argument("transcriptions"); pero.add_argument("output")
    search = commands.add_parser("search", help="lexical search with page/line/ALTO evidence")
    search.add_argument("index"); search.add_argument("query"); search.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    if args.command == "search":
        from .retrieval import search
        print(json.dumps(search(args.index, args.query, args.limit), ensure_ascii=False, indent=2))
    elif args.command == "import":
        D.save(import_xml(args.xml), args.output)
    elif args.command == "apply":
        proposal = json.loads(Path(args.response).read_text(encoding="utf-8"))
        requested = None
        if args.request:
            requested = json.loads(Path(args.request).read_text(encoding="utf-8"))["requested_line_ids"]
        D.save(D.apply_proposal(D.load(args.document), proposal, args.model, requested), args.output)
    elif args.command == "export":
        print(json.dumps(export_package(D.load(args.document), args.directory, args.schemas)))
    elif args.command == "prepare":
        from .vlm import prepare_batch
        d = D.load(args.document)
        ids = args.line_ids or [n["id"] for n in d["nodes"] if n["kind"] == "line" and n["page"] == args.page]
        request = prepare_batch(d, args.image, args.page, ids, args.directory, show_ocr=args.show_ocr)
        print(request["request_sha256"])
    elif args.command == "pero-realign":
        from .pero import load_cache, realign
        layout, meta = load_cache(args.cache)
        text = json.loads(Path(args.transcriptions).read_text(encoding="utf-8"))
        xml, report = realign(layout, text)
        Path(args.output).write_bytes(xml)
        write_json(str(args.output)+".json", dict(report, model_id=meta["model_id"]))
    else:
        if args.mode == "words":
            result = word_scores(D.load(args.reference), D.load(args.hypothesis))
        else:
            reference = json.loads(Path(args.reference).read_text(encoding="utf-8"))
            hypothesis = json.loads(Path(args.hypothesis).read_text(encoding="utf-8"))
            result = text_scores(reference, hypothesis["lines"] if isinstance(hypothesis, dict) else hypothesis)
        write_json(args.output, result)
        print(json.dumps({k: v for k, v in result.items() if k != "per_line"}))


if __name__ == "__main__":
    main()
