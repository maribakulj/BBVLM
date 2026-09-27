"""Measure role, eligibility and SSU conventions on development pages only."""
from collections import Counter, defaultdict
from pathlib import Path
import json

from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments/loop/spiritualist-v1/semantic-v1"
PAGES = ("0009", "0038", "0041", "0043")
NS = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}


def main():
    role_counts = Counter()
    role_eligible = Counter()
    page_reports = []
    group_sizes = Counter()
    group_role_mixes = Counter()
    groups_with_header_and_text = 0
    cross_column_groups = 0
    total_groups = 0
    violations = []
    for page in PAGES:
        xml = next((ROOT / "corpora/spiritualist/alto_xml/ocr_gt_labelled").glob(f"{page}_*.xml"))
        blocks = E.parse(str(xml)).findall(".//a:TextBlock", NS)
        groups = defaultdict(list)
        for block in blocks:
            role = block.get("BLOCK_TYPE")
            order = int(block.get("READING_ORDER"))
            eligible = order >= 0
            role_counts[role] += 1
            role_eligible[role] += int(eligible)
            groups[block.get("SSU_ID")].append(block)
            if role in {"MASTHEAD", "OTHER"} and eligible:
                violations.append(f"{page}:{block.get('ID')} {role} unexpectedly eligible")
            if role in {"HEADER", "TEXT", "ADVERT"} and not eligible:
                violations.append(f"{page}:{block.get('ID')} {role} unexpectedly excluded")
        page_groups = []
        for gid, members in sorted(groups.items()):
            total_groups += 1
            roles = sorted({m.get("BLOCK_TYPE") for m in members})
            columns = sorted({m.get("COLUMN_ID") for m in members if m.get("COLUMN_ID")})
            group_sizes[len(members)] += 1
            group_role_mixes["+".join(roles)] += 1
            groups_with_header_and_text += int("HEADER" in roles and "TEXT" in roles)
            cross_column_groups += int(len(columns) > 1)
            page_groups.append({
                "source_semantic_unit": gid,
                "members": len(members),
                "roles": roles,
                "columns": columns,
                "eligible_members": sum(int(m.get("READING_ORDER")) >= 0 for m in members),
            })
        page_reports.append({"page": page, "regions": len(blocks), "semantic_units": len(groups), "groups": page_groups})
    role_table = {
        role: {"regions": role_counts[role], "eligible": role_eligible[role],
               "eligibility_rate": role_eligible[role] / role_counts[role]}
        for role in sorted(role_counts)
    }
    result = {
        "schema": "bbvlm.spiritualist-semantic-conventions/1",
        "split": "development_only",
        "pages": list(PAGES),
        "role_eligibility": role_table,
        "semantic_units": total_groups,
        "group_size_histogram": {str(k): v for k, v in sorted(group_sizes.items())},
        "group_role_mix_histogram": dict(sorted(group_role_mixes.items())),
        "groups_with_header_and_text": groups_with_header_and_text,
        "cross_column_groups": cross_column_groups,
        "observed_invariants": {
            "masthead_and_other_excluded_from_reading_stream": not any(
                v["eligible"] for k, v in role_table.items() if k in {"MASTHEAD", "OTHER"}
            ),
            "header_text_and_advert_included_when_present": not violations,
            "semantic_units_may_span_columns": cross_column_groups > 0,
            "headers_may_share_a_unit_with_text": groups_with_header_and_text > 0,
        },
        "violations": violations,
        "page_details": page_reports,
        "warning": "These are corpus conventions inferred from provisional enriched labels, not independently adjudicated truth.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "development-conventions.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
