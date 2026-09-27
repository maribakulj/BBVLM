"""Audit the Spiritualist enriched ALTO before using it as independent GT.

This script never repairs the distributed files.  In particular, word boxes are
audited as geometry rather than trusted because the dataset card says character
positions are inferred and visual inspection suggests some word positions are too.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import random
import sys

from lxml import etree as E


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bbvlm.formats import LocalSchemaResolver, import_xml

SOURCE = ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled"
OUT = ROOT / "experiments/loop/spiritualist-v1"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
SEED = 2026092702


def number(node, name):
    value = node.get(name)
    return float(value) if value not in (None, "") else None


def bbox(node):
    x, y = number(node, "HPOS"), number(node, "VPOS")
    w, h = number(node, "WIDTH"), number(node, "HEIGHT")
    if None in (x, y, w, h):
        return None
    return (x, y, x + w, y + h)


def outside(inner, outer):
    return (
        inner[0] < outer[0]
        or inner[1] < outer[1]
        or inner[2] > outer[2]
        or inner[3] > outer[3]
    )


def main():
    paths = sorted(SOURCE.glob("*.xml"))
    if not paths:
        raise SystemExit(f"no ALTO files under {SOURCE}")
    OUT.mkdir(parents=True, exist_ok=True)
    names_hash = hashlib.sha256("\n".join(p.name for p in paths).encode()).hexdigest()

    split_path = OUT / "split.json"
    if not split_path.exists():
        ids = [p.stem.split("_")[0] for p in paths]
        shuffled = ids[:]
        random.Random(SEED).shuffle(shuffled)
        split_path.write_text(
            json.dumps(
                {
                    "schema": "bbvlm.fixed-split/1",
                    "seed": SEED,
                    "population": len(ids),
                    "population_names_sha256": names_hash,
                    "development": sorted(shuffled[:4]),
                    "validation": sorted(shuffled[4:12]),
                    "unseen_remainder": sorted(shuffled[12:]),
                    "selection_inputs": "ALTO filenames only; no images, text, scores or geometry inspected",
                    "warning": "Do not move pages between sets after observing outcomes.",
                },
                indent=2,
            )
            + "\n"
        )
    split = json.loads(split_path.read_text())
    if split["population_names_sha256"] != names_hash:
        raise RuntimeError("Spiritualist population changed after split freeze")

    parser = E.XMLParser(resolve_entities=False, no_network=True)
    parser.resolvers.add(LocalSchemaResolver(ROOT / "schemas"))
    schema = E.XMLSchema(E.parse(str(ROOT / "schemas/alto-4-4.xsd"), parser))
    totals = Counter()
    block_types = Counter()
    xsd_errors = Counter()
    page_rows = []
    anomaly_samples = []
    source_names = []
    import_failures = []

    for path in paths:
        tree = E.parse(str(path))
        page = tree.find(".//a:Page", NS)
        width, height = number(page, "WIDTH"), number(page, "HEIGHT")
        page_box = (0.0, 0.0, width, height)
        source_name_node = tree.find(".//a:sourceImageInformation/a:fileName", NS)
        source_name = source_name_node.text if source_name_node is not None else None
        source_names.append(source_name)
        valid = schema.validate(tree)
        errors = [str(e.message) for e in schema.error_log]
        for e in errors:
            # Collapse numeric element locations while keeping the normative cause.
            xsd_errors[e.split(", line ")[0]] += 1

        ids = [n.get("ID") for n in tree.xpath("//*[@ID]")]
        duplicate_ids = len(ids) - len(set(ids))
        blocks = tree.findall(".//a:TextBlock", NS)
        lines = tree.findall(".//a:TextLine", NS)
        words = tree.findall(".//a:String", NS)
        ssu = {b.get("SSU_ID") for b in blocks if b.get("SSU_ID")}
        semantic = {b.get("SEMANTIC_ID") for b in blocks if b.get("SEMANTIC_ID")}
        orders = [int(b.get("READING_ORDER")) for b in blocks if b.get("READING_ORDER") not in (None, "")]
        nonnegative_orders = [v for v in orders if v >= 0]
        duplicate_orders = len(nonnegative_orders) - len(set(nonnegative_orders))
        unique_orders = sorted(set(nonnegative_orders))
        order_gaps = 0
        if unique_orders:
            order_gaps = len(set(range(unique_orders[0], unique_orders[-1] + 1)) - set(unique_orders))

        counters = Counter()
        for block in blocks:
            block_types[block.get("BLOCK_TYPE") or "<missing>"] += 1
            for attr in ("BLOCK_TYPE", "COLUMN_ID", "READING_ORDER", "SEMANTIC_ID", "SSU_ID"):
                counters[f"blocks_with_{attr.lower()}"] += block.get(attr) is not None
        for line in lines:
            line_box = bbox(line)
            line_words = line.findall("a:String", NS)
            counters["lines_without_baseline"] += line.get("BASELINE") is None
            counters["lines_without_words"] += not line_words
            previous = None
            for word in line_words:
                counters["words"] += 1
                wb = bbox(word)
                counters["words_empty_content"] += (word.get("CONTENT") or "") == ""
                counters["words_hyphen_parts"] += word.get("SUBS_TYPE") in {"HypPart1", "HypPart2"}
                if wb is None:
                    counters["words_without_box"] += 1
                    continue
                counters["words_outside_page"] += outside(wb, page_box)
                counters["words_outside_line_bbox"] += line_box is not None and outside(wb, line_box)
                if previous is not None:
                    overlap = max(0.0, min(previous[2], wb[2]) - max(previous[0], wb[0]))
                    if overlap > 0:
                        counters["adjacent_word_x_overlaps"] += 1
                        denom = max(1.0, min(previous[2] - previous[0], wb[2] - wb[0]))
                        counters["adjacent_overlap_ge_25pct"] += overlap / denom >= 0.25
                        if len(anomaly_samples) < 30:
                            anomaly_samples.append(
                                {
                                    "page": path.name,
                                    "line": line.get("ID"),
                                    "previous_box": previous,
                                    "word": word.get("CONTENT"),
                                    "word_box": wb,
                                    "overlap_over_smaller_width": overlap / denom,
                                }
                            )
                previous = wb

        row = {
            "file": path.name,
            "page_width": width,
            "page_height": height,
            "source_image_filename": source_name,
            "xsd_valid": valid,
            "xsd_error_count": len(errors),
            "duplicate_ids": duplicate_ids,
            "blocks": len(blocks),
            "lines": len(lines),
            "words": len(words),
            "distinct_ssu_ids": len(ssu),
            "distinct_semantic_ids": len(semantic),
            "negative_reading_orders": sum(v < 0 for v in orders),
            "duplicate_nonnegative_reading_orders": duplicate_orders,
            "reading_order_gaps": order_gaps,
            **counters,
        }
        page_rows.append(row)
        totals.update({k: v for k, v in row.items() if isinstance(v, int) and not isinstance(v, bool)})
        totals["xsd_valid_pages"] += valid
        try:
            imported = import_xml(path)
            totals["imported_semantic_units"] += len(imported.get("semantic_units", []))
            totals["imported_reading_order_edges"] += len(imported.get("reading_order", []))
            totals["imported_articles"] += len(imported.get("articles", []))
        except Exception as error:
            import_failures.append({"file": path.name, "error": f"{type(error).__name__}: {error}"})

    word_total = totals["words"]
    report = {
        "schema": "bbvlm.reference-audit/1",
        "dataset": "Jonnob/the-spiritualist-enriched",
        "revision": "0f3ddfda24ecde8897ee9c0f575c59d7b95cf995",
        "distributed_zip_sha256": "ef42670d7f45adf16bc9dbca0c021b56f33881d41e238d1b369098eae428e47b",
        "files": len(paths),
        "split": split,
        "totals": totals,
        "rates": {
            "words_outside_page": totals["words_outside_page"] / word_total,
            "words_outside_line_bbox": totals["words_outside_line_bbox"] / word_total,
            "adjacent_word_x_overlaps_per_word": totals["adjacent_word_x_overlaps"] / word_total,
            "adjacent_overlap_ge_25pct_per_word": totals["adjacent_overlap_ge_25pct"] / word_total,
        },
        "block_types": block_types,
        "source_image_filenames": {
            "unique": len(set(source_names)),
            "extensions": Counter(Path(v).suffix.lower() if v else "<missing>" for v in source_names),
            "companion_mapping": "XML prefix 0001..0050 and companion PNG paths can be joined only by an explicit manifest; ALTO sourceImageInformation contains unrelated numeric JPG names",
        },
        "xsd": {
            "schema": "local unmodified ALTO 4.4 XSD",
            "valid_pages": totals["xsd_valid_pages"],
            "top_errors": xsd_errors.most_common(20),
            "warning": "Invalid custom attributes may be preserved in a source layer but cannot be copied into normative ALTO unchanged.",
        },
        "normalized_import": {
            "successful_pages": len(paths) - len(import_failures),
            "failures": import_failures,
            "semantic_units": totals["imported_semantic_units"],
            "reading_order_edges": totals["imported_reading_order_edges"],
            "articles_invented": totals["imported_articles"],
            "warning": "Import success preserves evidence but does not certify distributed word geometry or labels.",
        },
        "anomaly_samples": anomaly_samples,
        "pages": page_rows,
        "decision": {
            "text": "candidate after independent spot adjudication",
            "word_geometry": "reject as independent GT until inferred-box provenance and overlap defects are resolved",
            "olr_articles": "usable as proposed labels only; audit order and SSU conventions before scoring",
            "alto_profile": "distributed XML is not assumed schema-valid; normalize through a provenance-preserving projection",
        },
    }
    (OUT / "reference-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(OUT / "reference-audit.json"), **report["rates"], "xsd_valid_pages": totals["xsd_valid_pages"], "words": word_total}, indent=2))


if __name__ == "__main__":
    main()
