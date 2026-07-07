#!/usr/bin/env python
"""
Pilot 05 CFPB no-call evidence-state condition construction.

This script constructs a controlled balanced subset and four evidence-state
condition variants from already sanitized CFPB evidence packets.

Inputs:
- Sanitized evidence packets from Task 05U.
- Separate packet labels from Task 05U.

Safety boundaries:
- No API calls.
- No model calls.
- No dataset downloads.
- Does not read raw CFPB export.
- Does not write raw complaint narratives.
- Does not write company names.
- Does not write complaint IDs.
- Does not write ZIP codes.
- Does not place target labels in evidence-state text.
- Writes target labels only in separate label files.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_RANDOM_SEED = 20260707
DEFAULT_N_PER_LABEL = 30

CONDITIONS = [
    "clean",
    "compressed",
    "partial_dropout",
    "noisy_conflicting",
]

EXPECTED_PACKET_HEADER = [
    "packet_id",
    "product_family",
    "sub_product_bucket",
    "issue_category",
    "sub_issue_category",
    "submitted_via",
    "received_month",
    "consumer_tag_presence",
    "state_presence",
    "narrative_available",
    "narrative_length_bucket",
    "evidence_text",
]

EXPECTED_LABEL_HEADER = [
    "packet_id",
    "target_timely_response",
]

ALLOWED_LABELS = {"Yes", "No"}

FORBIDDEN_EVIDENCE_TEXT_FRAGMENTS = [
    "Consumer complaint narrative",
    "Complaint ID",
    "ZIP code",
    "Timely response",
    "target_timely_response",
    "Company response to consumer",
    "Company public response",
    "Date sent to company",
    "Closed with",
    "In progress",
    "Untimely response",
    "XX/XX/XXXX",
    "XXXX XXXX",
    "{$",
    "I received",
    "I contacted",
    "death certificate",
    "fingerprint",
    "Best Buy",
    "raw_prompt",
    "raw_response",
    "api_response",
    "model_response",
    "llm_response",
]

FORBIDDEN_OUTPUT_FIELD_NAMES = {
    # Task 05X recovery: generic company taxonomy wording allowed.
    # Company names and company-response fields remain excluded, but the generic
    # word "company" may appear in official CFPB issue/sub-issue taxonomy.
    "target_timely_response",
    "Consumer complaint narrative",
    "Company public response",
    "company_name",
    "company=",
    "ZIP code",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Complaint ID",
}


@dataclass(frozen=True)
class ConstructionStats:
    base_packets_selected: int
    evidence_state_rows_written: int
    evidence_state_labels_written: int
    subset_labels_written: int
    condition_counts: dict[str, int]
    subset_label_counts: dict[str, int]
    evidence_state_label_counts: dict[str, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct no-call evidence-state condition variants for Pilot 05 CFPB."
    )
    parser.add_argument("--packets-file", required=True, type=Path)
    parser.add_argument("--labels-file", required=True, type=Path)
    parser.add_argument("--packet-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--n-per-label", type=int, default=DEFAULT_N_PER_LABEL)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    return parser.parse_args()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 8)


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj, dialect=csv.excel)
        header = list(reader.fieldnames or [])
        rows = [
            {
                str(key): normalize_space("" if value is None else str(value))
                for key, value in row.items()
                if key is not None
            }
            for row in reader
        ]
    return header, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def assert_no_forbidden_condition_text(text: str) -> None:
    text_lower = text.lower()

    for fragment in FORBIDDEN_EVIDENCE_TEXT_FRAGMENTS:
        if fragment.lower() in text_lower:
            raise ValueError(f"Forbidden fragment leaked into evidence-state text: {fragment}")

    for field_name in FORBIDDEN_OUTPUT_FIELD_NAMES:
        if field_name.lower() in text_lower:
            raise ValueError(f"Forbidden field name leaked into evidence-state text: {field_name}")


def assert_condition_row_schema(row: dict[str, str]) -> None:
    forbidden_fields_present = sorted(set(row.keys()) & FORBIDDEN_OUTPUT_FIELD_NAMES)
    if forbidden_fields_present:
        raise ValueError(f"Forbidden fields present in condition row: {forbidden_fields_present}")

    text = row.get("evidence_state_text", "")
    assert_no_forbidden_condition_text(text)


def select_balanced_subset(
    *,
    packets_by_id: dict[str, dict[str, str]],
    labels_by_id: dict[str, str],
    n_per_label: int,
    random_seed: int,
) -> list[dict[str, str]]:
    ids_by_label: dict[str, list[str]] = {
        "Yes": [],
        "No": [],
    }

    for packet_id, label in labels_by_id.items():
        if label not in ALLOWED_LABELS:
            raise ValueError(f"Invalid label for packet {packet_id}: {label}")

        if packet_id not in packets_by_id:
            raise ValueError(f"Label packet_id has no matching packet: {packet_id}")

        ids_by_label[label].append(packet_id)

    for label in ids_by_label:
        ids_by_label[label] = sorted(ids_by_label[label])

    for label in ("Yes", "No"):
        if len(ids_by_label[label]) < n_per_label:
            raise ValueError(
                f"Not enough {label} labels for balanced subset: "
                f"required {n_per_label}, found {len(ids_by_label[label])}"
            )

    rng = random.Random(random_seed)
    selected_yes = sorted(rng.sample(ids_by_label["Yes"], n_per_label))
    selected_no = sorted(rng.sample(ids_by_label["No"], n_per_label))

    interleaved: list[str] = []
    for idx in range(n_per_label):
        interleaved.append(selected_no[idx])
        interleaved.append(selected_yes[idx])

    selected_rows: list[dict[str, str]] = []
    for rank, packet_id in enumerate(interleaved, start=1):
        packet = packets_by_id[packet_id]
        label = labels_by_id[packet_id]

        selected_rows.append(
            {
                "subset_rank": str(rank),
                "packet_id": packet_id,
                "selection_group": label,
                "selection_method": "deterministic_seeded_balanced_sample",
                "random_seed": str(random_seed),
            }
        )

    return selected_rows


def alt_product(product_family: str) -> str:
    if product_family == "Credit card":
        return "Prepaid card"
    if product_family == "Prepaid card":
        return "Credit card"
    return "__ALTERNATIVE_PRODUCT_SIGNAL__"


def alt_submission_channel(submitted_via: str) -> str:
    if submitted_via == "Web":
        return "Referral"
    if submitted_via == "Referral":
        return "Web"
    if submitted_via == "Phone":
        return "Postal mail"
    return "Web"


def build_condition_text(packet: dict[str, str], condition: str) -> str:
    product = packet["product_family"]
    sub_product = packet["sub_product_bucket"]
    issue = packet["issue_category"]
    sub_issue = packet["sub_issue_category"]
    submitted_via = packet["submitted_via"]
    month = packet["received_month"]
    tag_presence = packet["consumer_tag_presence"]
    state_presence = packet["state_presence"]
    narrative_available = packet["narrative_available"]
    narrative_length_bucket = packet["narrative_length_bucket"]

    if condition == "clean":
        text = packet["evidence_text"]

    elif condition == "compressed":
        text = (
            "Evidence packet compressed: "
            f"product_family={product}; "
            f"issue_category={issue}; "
            f"received_month={month}; "
            f"narrative_available={narrative_available}."
        )

    elif condition == "partial_dropout":
        text = (
            "Evidence packet partial_dropout: "
            f"product_family={product}; "
            "sub_product_bucket=__DROPPED__; "
            f"issue_category={issue}; "
            "sub_issue_category=__DROPPED__; "
            "submitted_via=__DROPPED__; "
            f"received_month={month}; "
            f"consumer_tag_presence={tag_presence}; "
            "state_presence=__DROPPED__; "
            f"narrative_available={narrative_available}; "
            "narrative_length_bucket=__DROPPED__."
        )

    elif condition == "noisy_conflicting":
        text = (
            "Evidence packet noisy_conflicting: "
            f"product_family={product}; "
            f"alternative_product_signal={alt_product(product)}; "
            f"sub_product_bucket={sub_product}; "
            f"issue_category={issue}; "
            f"sub_issue_category={sub_issue}; "
            f"submitted_via={submitted_via}; "
            f"alternative_submission_signal={alt_submission_channel(submitted_via)}; "
            f"received_month={month}; "
            f"consumer_tag_presence={tag_presence}; "
            f"state_presence={state_presence}; "
            f"narrative_available={narrative_available}; "
            f"narrative_length_bucket={narrative_length_bucket}; "
            "evidence_quality_warning=simulated_non_outcome_conflict."
        )

    else:
        raise ValueError(f"Unknown condition: {condition}")

    assert_no_forbidden_condition_text(text)
    return text


def construct_conditions(
    *,
    packets_file: Path,
    labels_file: Path,
    packet_manifest_path: Path,
    output_dir: Path,
    n_per_label: int,
    random_seed: int,
) -> ConstructionStats:
    packet_manifest = load_json(packet_manifest_path)

    if packet_manifest.get("status") != "PASS":
        raise ValueError("Input packet manifest status is not PASS.")

    safety = packet_manifest.get("safety", {})
    if safety.get("target_label_in_evidence_text") is not False:
        raise ValueError("Input packet manifest does not confirm target labels excluded from evidence text.")
    if safety.get("raw_narratives_written") is not False:
        raise ValueError("Input packet manifest does not confirm raw narratives excluded.")
    if safety.get("company_names_written") is not False:
        raise ValueError("Input packet manifest does not confirm company names excluded.")
    if safety.get("complaint_ids_written") is not False:
        raise ValueError("Input packet manifest does not confirm complaint IDs excluded.")
    if safety.get("zip_codes_written") is not False:
        raise ValueError("Input packet manifest does not confirm ZIP codes excluded.")

    packet_header, packet_rows = read_csv_rows(packets_file)
    label_header, label_rows = read_csv_rows(labels_file)

    if packet_header != EXPECTED_PACKET_HEADER:
        raise ValueError(f"Unexpected packet header: {packet_header!r}")

    if label_header != EXPECTED_LABEL_HEADER:
        raise ValueError(f"Unexpected label header: {label_header!r}")

    packets_by_id = {row["packet_id"]: row for row in packet_rows}
    labels_by_id = {row["packet_id"]: row["target_timely_response"] for row in label_rows}

    if len(packets_by_id) != len(packet_rows):
        raise ValueError("Duplicate packet IDs found in packet file.")

    if len(labels_by_id) != len(label_rows):
        raise ValueError("Duplicate packet IDs found in label file.")

    if len(packets_by_id) != len(labels_by_id):
        raise ValueError("Packet and label counts do not match.")

    expected_packet_count = int(packet_manifest["row_counts"]["packets_written"])
    expected_label_count = int(packet_manifest["row_counts"]["labels_written"])

    if len(packet_rows) != expected_packet_count:
        raise ValueError("Packet row count does not match packet manifest.")

    if len(label_rows) != expected_label_count:
        raise ValueError("Label row count does not match packet manifest.")

    selected_rows = select_balanced_subset(
        packets_by_id=packets_by_id,
        labels_by_id=labels_by_id,
        n_per_label=n_per_label,
        random_seed=random_seed,
    )

    subset_label_rows: list[dict[str, str]] = []
    condition_rows: list[dict[str, str]] = []
    condition_label_rows: list[dict[str, str]] = []

    subset_label_counts: Counter[str] = Counter()
    evidence_state_label_counts: Counter[str] = Counter()
    condition_counts: Counter[str] = Counter()

    for selected in selected_rows:
        packet_id = selected["packet_id"]
        subset_rank = int(selected["subset_rank"])
        label = labels_by_id[packet_id]
        packet = packets_by_id[packet_id]

        subset_label_rows.append(
            {
                "packet_id": packet_id,
                "target_timely_response": label,
            }
        )
        subset_label_counts[label] += 1

        for condition_index, condition in enumerate(CONDITIONS, start=1):
            evidence_state_id = f"P05_CFPB_ES_{subset_rank:03d}_{condition_index:02d}_{condition}"

            condition_text = build_condition_text(packet, condition)

            condition_row = {
                "evidence_state_id": evidence_state_id,
                "packet_id": packet_id,
                "subset_rank": str(subset_rank),
                "condition_name": condition,
                "condition_order": str(condition_index),
                "evidence_state_text": condition_text,
                "degradation_profile": {
                    "clean": "original_sanitized_packet_text",
                    "compressed": "category_compression_and_detail_reduction",
                    "partial_dropout": "structured_field_dropout_without_target",
                    "noisy_conflicting": "simulated_non_outcome_conflicting_signals",
                }[condition],
            }

            assert_condition_row_schema(condition_row)

            condition_rows.append(condition_row)
            condition_label_rows.append(
                {
                    "evidence_state_id": evidence_state_id,
                    "packet_id": packet_id,
                    "target_timely_response": label,
                }
            )

            condition_counts[condition] += 1
            evidence_state_label_counts[label] += 1

    expected_base_count = n_per_label * 2
    expected_condition_count = expected_base_count * len(CONDITIONS)

    if len(selected_rows) != expected_base_count:
        raise ValueError("Unexpected balanced subset size.")

    if len(subset_label_rows) != expected_base_count:
        raise ValueError("Unexpected subset label row count.")

    if len(condition_rows) != expected_condition_count:
        raise ValueError("Unexpected evidence-state condition row count.")

    if len(condition_label_rows) != expected_condition_count:
        raise ValueError("Unexpected evidence-state label row count.")

    if subset_label_counts["Yes"] != n_per_label or subset_label_counts["No"] != n_per_label:
        raise ValueError("Balanced subset label counts are not correct.")

    if evidence_state_label_counts["Yes"] != n_per_label * len(CONDITIONS):
        raise ValueError("Evidence-state Yes label count is not correct.")

    if evidence_state_label_counts["No"] != n_per_label * len(CONDITIONS):
        raise ValueError("Evidence-state No label count is not correct.")

    for condition in CONDITIONS:
        if condition_counts[condition] != expected_base_count:
            raise ValueError(f"Condition {condition} does not have {expected_base_count} rows.")

    output_dir.mkdir(parents=True, exist_ok=True)

    subset_packet_path = output_dir / "pilot_05_cfpb_balanced_subset_packets.csv"
    subset_label_path = output_dir / "pilot_05_cfpb_balanced_subset_labels.csv"
    condition_path = output_dir / "pilot_05_cfpb_evidence_state_conditions.csv"
    condition_label_path = output_dir / "pilot_05_cfpb_evidence_state_labels.csv"

    write_csv(
        subset_packet_path,
        ["subset_rank", "packet_id", "selection_group", "selection_method", "random_seed"],
        selected_rows,
    )

    write_csv(
        subset_label_path,
        ["packet_id", "target_timely_response"],
        subset_label_rows,
    )

    write_csv(
        condition_path,
        [
            "evidence_state_id",
            "packet_id",
            "subset_rank",
            "condition_name",
            "condition_order",
            "evidence_state_text",
            "degradation_profile",
        ],
        condition_rows,
    )

    write_csv(
        condition_label_path,
        ["evidence_state_id", "packet_id", "target_timely_response"],
        condition_label_rows,
    )

    condition_distribution_rows = [
        {
            "condition_name": condition,
            "count": condition_counts[condition],
            "share": safe_ratio(condition_counts[condition], len(condition_rows)),
        }
        for condition in CONDITIONS
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_condition_distribution.csv",
        ["condition_name", "count", "share"],
        condition_distribution_rows,
    )

    subset_label_distribution_rows = [
        {
            "target_timely_response": label,
            "count": subset_label_counts[label],
            "share": safe_ratio(subset_label_counts[label], len(selected_rows)),
        }
        for label in ["No", "Yes"]
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_balanced_subset_label_distribution.csv",
        ["target_timely_response", "count", "share"],
        subset_label_distribution_rows,
    )

    evidence_state_label_distribution_rows = [
        {
            "target_timely_response": label,
            "count": evidence_state_label_counts[label],
            "share": safe_ratio(evidence_state_label_counts[label], len(condition_rows)),
        }
        for label in ["No", "Yes"]
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_evidence_state_label_distribution.csv",
        ["target_timely_response", "count", "share"],
        evidence_state_label_distribution_rows,
    )

    condition_policy_rows = [
        {
            "condition_name": "clean",
            "construction": "Uses original sanitized evidence_text from Task 05U.",
            "intended_reliability_role": "Baseline evidence state.",
            "target_label_used_in_evidence": "False",
        },
        {
            "condition_name": "compressed",
            "construction": "Keeps product, issue, month, and narrative-availability only.",
            "intended_reliability_role": "Tests compression-driven evidence-state degradation.",
            "target_label_used_in_evidence": "False",
        },
        {
            "condition_name": "partial_dropout",
            "construction": "Drops selected non-target categorical fields.",
            "intended_reliability_role": "Tests missing-evidence / partial-evidence degradation.",
            "target_label_used_in_evidence": "False",
        },
        {
            "condition_name": "noisy_conflicting",
            "construction": "Adds simulated non-outcome conflicting categorical signals.",
            "intended_reliability_role": "Tests noisy/conflicting evidence-state degradation.",
            "target_label_used_in_evidence": "False",
        },
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_condition_policy.csv",
        ["condition_name", "construction", "intended_reliability_role", "target_label_used_in_evidence"],
        condition_policy_rows,
    )

    summary_rows = [
        {"metric": "status", "value": "PASS"},
        {"metric": "input_packets", "value": len(packet_rows)},
        {"metric": "input_labels", "value": len(label_rows)},
        {"metric": "base_packets_selected", "value": len(selected_rows)},
        {"metric": "n_per_label", "value": n_per_label},
        {"metric": "random_seed", "value": random_seed},
        {"metric": "conditions_per_packet", "value": len(CONDITIONS)},
        {"metric": "evidence_state_rows_written", "value": len(condition_rows)},
        {"metric": "subset_labels_written", "value": len(subset_label_rows)},
        {"metric": "evidence_state_labels_written", "value": len(condition_label_rows)},
        {"metric": "real_api_calls", "value": 0},
        {"metric": "model_calls", "value": 0},
        {"metric": "dataset_downloads", "value": 0},
        {"metric": "raw_rows_written", "value": False},
        {"metric": "raw_narratives_written", "value": False},
        {"metric": "company_names_written", "value": False},
        {"metric": "complaint_ids_written", "value": False},
        {"metric": "zip_codes_written", "value": False},
        {"metric": "target_label_in_evidence_state_text", "value": False},
        {"metric": "labels_written_separately", "value": True},
    ]
    write_csv(output_dir / "pilot_05_cfpb_evidence_state_summary.csv", ["metric", "value"], summary_rows)

    manifest = {
        "status": "PASS",
        "scope": "Pilot 05 CFPB no-call evidence-state condition construction",
        "source_packets": str(packets_file),
        "source_labels": str(labels_file),
        "source_packet_manifest": str(packet_manifest_path),
        "selection": {
            "method": "deterministic_seeded_balanced_sample",
            "random_seed": random_seed,
            "n_per_label": n_per_label,
            "labels": ["No", "Yes"],
            "base_packets_selected": len(selected_rows),
        },
        "conditions": CONDITIONS,
        "outputs": {
            "balanced_subset_packets_csv": str(subset_packet_path),
            "balanced_subset_labels_csv": str(subset_label_path),
            "evidence_state_conditions_csv": str(condition_path),
            "evidence_state_labels_csv": str(condition_label_path),
            "condition_distribution_csv": str(output_dir / "pilot_05_cfpb_condition_distribution.csv"),
            "balanced_subset_label_distribution_csv": str(output_dir / "pilot_05_cfpb_balanced_subset_label_distribution.csv"),
            "evidence_state_label_distribution_csv": str(output_dir / "pilot_05_cfpb_evidence_state_label_distribution.csv"),
            "condition_policy_csv": str(output_dir / "pilot_05_cfpb_condition_policy.csv"),
            "summary_csv": str(output_dir / "pilot_05_cfpb_evidence_state_summary.csv"),
            "report_md": str(output_dir / "pilot_05_cfpb_evidence_state_condition_report.md"),
        },
        "row_counts": {
            "input_packets": len(packet_rows),
            "input_labels": len(label_rows),
            "base_packets_selected": len(selected_rows),
            "conditions_per_packet": len(CONDITIONS),
            "evidence_state_rows_written": len(condition_rows),
            "subset_labels_written": len(subset_label_rows),
            "evidence_state_labels_written": len(condition_label_rows),
        },
        "subset_label_counts": dict(sorted(subset_label_counts.items())),
        "evidence_state_label_counts": dict(sorted(evidence_state_label_counts.items())),
        "condition_counts": dict((condition, condition_counts[condition]) for condition in CONDITIONS),
        "safety": {
            "real_api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
            "raw_rows_written": False,
            "raw_narratives_written": False,
            "company_names_written": False,
            "complaint_ids_written": False,
            "zip_codes_written": False,
            "target_label_in_evidence_state_text": False,
            "labels_written_separately": True,
            "raw_prompt_or_response_written": False,
        },
        "claim_boundary": "No-call evidence-state condition construction for later approved controlled cascade experiments; not a model result and not a real-world deployment claim.",
    }
    write_json(output_dir / "pilot_05_cfpb_evidence_state_manifest.json", manifest)

    report = f"""# Pilot 05 CFPB Evidence-State Condition Construction

Status: PASS

This no-call step constructs evidence-state condition variants from the committed sanitized CFPB evidence packets.

## Balanced subset

- Base packets selected: {len(selected_rows)}
- No labels selected: {subset_label_counts["No"]}
- Yes labels selected: {subset_label_counts["Yes"]}
- Selection method: deterministic seeded balanced sample
- Random seed: {random_seed}

## Evidence-state conditions

- clean
- compressed
- partial_dropout
- noisy_conflicting

Each base packet is represented under all four conditions.

## Counts

- Evidence-state rows written: {len(condition_rows)}
- Evidence-state labels written separately: {len(condition_label_rows)}
- Conditions per packet: {len(CONDITIONS)}

## Safety boundary

No raw CFPB export is read by this script. The construction uses only the committed sanitized evidence packets and separate labels.

Evidence-state text does not include raw complaint narratives, company names, complaint IDs, ZIP codes, company-response fields, raw prompts, raw responses, API outputs, model outputs, or target labels.

## Claim boundary

This output is a no-call evidence-construction layer for later controlled evidence-state reliability experiments. It does not claim model reliability, provider ranking, financial safety, legal safety, consumer harm prevalence, real-world deployment validity, or regulated lending validity.
"""
    (output_dir / "pilot_05_cfpb_evidence_state_condition_report.md").write_text(report, encoding="utf-8")

    return ConstructionStats(
        base_packets_selected=len(selected_rows),
        evidence_state_rows_written=len(condition_rows),
        evidence_state_labels_written=len(condition_label_rows),
        subset_labels_written=len(subset_label_rows),
        condition_counts=dict((condition, condition_counts[condition]) for condition in CONDITIONS),
        subset_label_counts=dict(sorted(subset_label_counts.items())),
        evidence_state_label_counts=dict(sorted(evidence_state_label_counts.items())),
    )


def main() -> None:
    args = parse_args()

    for path in [args.packets_file, args.labels_file, args.packet_manifest]:
        if not path.exists():
            raise FileNotFoundError(path)

    stats = construct_conditions(
        packets_file=args.packets_file,
        labels_file=args.labels_file,
        packet_manifest_path=args.packet_manifest,
        output_dir=args.output_dir,
        n_per_label=args.n_per_label,
        random_seed=args.random_seed,
    )

    print("Pilot 05 CFPB evidence-state conditions generated.")
    print(f"output_dir: {args.output_dir}")
    print("status: PASS")
    print(f"base_packets_selected: {stats.base_packets_selected}")
    print(f"evidence_state_rows_written: {stats.evidence_state_rows_written}")
    print(f"subset_labels_written: {stats.subset_labels_written}")
    print(f"evidence_state_labels_written: {stats.evidence_state_labels_written}")
    print(f"condition_counts: {stats.condition_counts}")
    print(f"subset_label_counts: {stats.subset_label_counts}")
    print(f"evidence_state_label_counts: {stats.evidence_state_label_counts}")
    print("real_api_calls: 0")
    print("model_calls: 0")
    print("dataset_downloads: 0")
    print("raw_rows_written: False")
    print("raw_narratives_written: False")
    print("company_names_written: False")
    print("complaint_ids_written: False")
    print("zip_codes_written: False")
    print("target_label_in_evidence_state_text: False")


if __name__ == "__main__":
    main()
