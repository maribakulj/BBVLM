"""Normalize one frozen Spiritualist development page without laundering defects."""
from pathlib import Path
import hashlib
import json
import sys

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bbvlm import document as D
from bbvlm.formats import export_alto, export_mets, import_xml, validate_xml, ALTO, METS

PAGE = "0009"  # fixed development member; never an independent validation page
XML = ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled/0009_p009.xml"
IMAGE = ROOT / "corpora/spiritualist/companion/Spiritualist_Images/0009.png"
OUT = ROOT / "experiments/loop/spiritualist-v1/import-0009"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = import_xml(XML, "spiritualist-0009")
    original_word_nodes = [n for n in d["nodes"] if n["kind"] == "word"]
    for line in [n for n in d["nodes"] if n["kind"] == "line"]:
        line["needs_alignment"] = True
        line.setdefault("issues", []).append("distributed_word_geometry_quarantined")
    d["nodes"] = [n for n in d["nodes"] if n["kind"] != "word"]

    page = next(n for n in d["nodes"] if n["kind"] == "page")
    source_image_name = page["image"]
    page["image"] = "Spiritualist_Images/0009.png"
    image_sha = hashlib.sha256(IMAGE.read_bytes()).hexdigest()
    d["events"].append({
        "action": "resolve_source_image",
        "source_alto_filename": source_image_name,
        "resolved_file": page["image"],
        "rule": "ALTO page_id prefix 0009_p009 -> companion image basename 0009.png",
        "sha256": image_sha,
        "dimensions_verified": [int(page["bbox"][2]), int(page["bbox"][3])],
        "status": "automatic",
    })
    d["events"].append({
        "action": "quarantine_geometry",
        "scope": "distributed word boxes",
        "count": len(original_word_nodes),
        "reason": "corpus-wide audit found 87.7% adjacent overlaps >=25% and 11.7% outside line boxes",
        "source_preserved": str(XML),
    })
    D.validate(d)
    D.save(d, OUT / "document.json")
    alto = export_alto(d, "P0001")
    mets = export_mets(d, {"P0001": "P0001.alto.xml"}, graph_file="document.json")
    validate_xml(alto, ROOT / "schemas/alto-4-4.xsd")
    validate_xml(mets, ROOT / "schemas/mets.xsd")
    (OUT / "P0001.alto.xml").write_bytes(alto)
    (OUT / "mets.xml").write_bytes(mets)

    alto_root, mets_root = E.fromstring(alto), E.fromstring(mets)
    alto_ids = set(alto_root.xpath("//@ID"))
    area_refs = mets_root.xpath("//m:area/@BEGIN", namespaces={"m": METS})
    report = {
        "schema": "bbvlm.spiritualist-import-evaluation/1",
        "page": PAGE,
        "split_role": "development",
        "source_alto_sha256": hashlib.sha256(XML.read_bytes()).hexdigest(),
        "source_image_sha256": image_sha,
        "quarantined_word_boxes": len(original_word_nodes),
        "lines_exported_unaligned": len(alto_root.findall(f".//{{{ALTO}}}TextLine")),
        "semantic_units": len(d["semantic_units"]),
        "articles_invented": len(d["articles"]),
        "reading_order_edges": len(d["reading_order"]),
        "alto44_valid": True,
        "mets1121_valid": True,
        "mets_area_refs": len(area_refs),
        "mets_area_refs_resolve_to_alto": all(ref in alto_ids for ref in area_refs),
        "pass_count": 0,
        "decision": "SSU/order can enter the evidence graph; word geometry must be regenerated and independently validated.",
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
