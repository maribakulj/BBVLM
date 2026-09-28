#!/usr/bin/env python3
"""Score the targeted blind A47 readers without mutating the BnL reference."""
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bbvlm.metrics import edit_distance
from bbvlm.text_views import lexical_alnum, retrieval_fold_v1


ROOT = Path(__file__).resolve().parents[1]
A45 = ROOT / "experiments/loop/bnl-independent-a45/source"
A46 = ROOT / "experiments/loop/bnl-independent-a46/output/predictions.json"
A47 = ROOT / "experiments/loop/bnl-vlm-a47"
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
TARGETS = {
    "Q01": ("0464", None), "Q02": ("1523", None),
    "Q03": ("1155", 2), "Q04": ("1155", 7), "Q05": ("1155", 42),
    "Q06": ("1155", 66), "Q07": ("1155", 74),
}
VIEWS = {"lexical_alnum": lexical_alnum, "retrieval_fold_v1": retrieval_fold_v1}


def references(identifier: str) -> list[str]:
    root = ET.parse(A45 / f"{identifier}.xml").getroot()
    return [" ".join(word.attrib.get("CONTENT", "") for word in line.findall("a:String", NS))
            for line in root.findall(".//a:TextLine", NS)]


def score(left: str, right: str) -> dict:
    result = {}
    for name, transform in VIEWS.items():
        ref, hyp = transform(left), transform(right)
        edits = edit_distance(ref, hyp)
        result[name] = {"characters": len(ref), "edits": edits,
                        "cer": edits / len(ref) if ref else None, "exact": ref == hyp}
    return result


def main() -> None:
    prediction = json.loads(A46.read_text())
    predicted = {block["id"]: [line["text"] for line in block["lines"]]
                 for block in prediction["blocks"]}
    readers = {}
    for name in ("luna", "sol"):
        payload = json.loads((A47 / f"{name}.json").read_text())
        readers[name] = {item["id"]: item["transcription"] for item in payload["items"]}
    rows = []
    for opaque_id, (source_id, line_index) in TARGETS.items():
        ref_lines = references(source_id)
        ref = "\n".join(ref_lines) if line_index is None else ref_lines[line_index]
        pero_lines = predicted[source_id]
        pero = "\n".join(pero_lines) if line_index is None else pero_lines[line_index]
        rows.append({
            "id": opaque_id,
            "source_mapping_opened_only_by_evaluator": {"block": source_id, "line_index": line_index},
            "scores_against_immutable_reference": {
                "pero": score(ref, pero), "luna": score(ref, readers["luna"][opaque_id]),
                "sol": score(ref, readers["sol"][opaque_id]),
            },
            "blind_reader_agreement": score(readers["luna"][opaque_id], readers["sol"][opaque_id]),
        })
    aggregate = {}
    for candidate in ("pero", "luna", "sol"):
        aggregate[candidate] = {}
        for view in VIEWS:
            chars = sum(row["scores_against_immutable_reference"][candidate][view]["characters"] for row in rows)
            edits = sum(row["scores_against_immutable_reference"][candidate][view]["edits"] for row in rows)
            aggregate[candidate][view] = {
                "characters": chars, "edits": edits, "cer": edits / chars,
                "exact_items": sum(row["scores_against_immutable_reference"][candidate][view]["exact"] for row in rows),
            }
    report = {
        "schema": "bbvlm.bnl-vlm-a47-report/1",
        "status": "targeted_post_score_blind_audit_complete",
        "selection_bias": "Known A46 lexical residuals only; never aggregate this CER into A46.",
        "passes": {"luna": 1, "sol_escalation": 1, "layout": 0, "recognizer": 0},
        "aggregate_against_immutable_reference": aggregate,
        "adjudication_triage": [
            {"id": "Q01", "reference": "sera", "visible_consensus": "fera", "disposition": "probable_reference_error"},
            {"id": "Q01", "pero": "ans le Journal de Gand", "visible_consensus": "— On lit dans le Journal de Gand", "disposition": "model_error"},
            {"id": "Q02", "reference": "impos.-", "visible_consensus": "impos-", "disposition": "probable_reference_error"},
            {"id": "Q02", "reference": "précisement", "visible_consensus": "précisément", "disposition": "probable_reference_error"},
            {"id": "Q02", "pero": "cerlains ... daction", "visible_consensus": "certains ... La rédaction", "disposition": "model_and_segmentation_error"},
            {"id": "Q03", "reference": "II", "visible_consensus": "Il", "disposition": "probable_reference_error"},
            {"id": "Q04", "reference": "II", "visible_consensus": "Il", "disposition": "probable_reference_error"},
            {"id": "Q04", "luna_reference_pero": "l’é", "sol": "l’e", "disposition": "isolated_sol_diacritic_error"},
            {"id": "Q05", "reference": "eile", "visible_consensus": "elle", "disposition": "probable_reference_error"},
            {"id": "Q06", "pero": "arriére", "visible_consensus": "arrière", "disposition": "model_diacritic_error"},
            {"id": "Q07", "reference": "a la", "visible_consensus": "à la", "disposition": "probable_reference_error"}
        ],
        "truth_policy": "Probable reference errors are flags for independent human adjudication; neither reader output nor consensus overwrites the original.",
        "rows": rows,
        "accepted_for_project_completion_gate": False,
    }
    (A47 / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    compact = dict(report); compact.pop("rows")
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
