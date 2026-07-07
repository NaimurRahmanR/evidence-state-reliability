#!/usr/bin/env python
"""
Pilot 05 CFPB sanitized evidence-packet construction.

This script constructs no-call, sanitized evidence packets from the locally stored
CFPB Consumer Complaint Database browser-export CSV that has already passed the
Pilot 05 dataset audit.

Safety boundaries:
- No API calls.
- No model calls.
- No dataset downloads.
- Does not write raw complaint narratives.
- Does not write company names.
- Does not write complaint IDs.
- Does not write ZIP codes.
- Does not write raw rows.
- Does not place the target label in evidence text.
- Writes target labels only in a separate labels file for later evaluation.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_COLUMNS = [
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Consumer complaint narrative",
    "Company public response",
    "Company",
    "State",
    "ZIP code",
    "Tags",
    "Submitted via",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Complaint ID",
]

ALLOWED_PRODUCTS = {"Credit card", "Prepaid card"}
ALLOWED_TARGETS = {"Yes", "No"}

FORBIDDEN_EVIDENCE_FIELD_NAMES = {
    # Task 05U recovery: generic company taxonomy wording allowed.
    # Company names and company-response fields remain excluded, but the generic
    # word "company" may appear in official CFPB issue/sub-issue taxonomy.
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

RAW_LIKE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bconsumer complaint narrative\b",
        r"\bcomplaint id\b",
        r"\bzip code\b",
        r"\btimely response\b",
        r"\bcompany response to consumer\b",
        r"\bcompany public response\b",
        r"\bclosed with\b",
        r"\bin progress\b",
        r"\buntimely response\b",
        r"XX/XX/XXXX",
        r"XXXX XXXX",
        r"\{\$",
        r"\bI received\b",
        r"\bI contacted\b",
        r"\bdeath certificate\b",
        r"\bfingerprint\b",
        r"\bBest Buy\b",
    ]
]


@dataclass(frozen=True)
class ConstructionStats:
    total_csv_records_seen_after_header: int
    packets_written: int
    labels_written: int
    rejected_rows: int
    rejection_counts: dict[str, int]
    target_counts: dict[str, int]
    product_counts: dict[str, int]
    narrative_availability_counts: dict[str, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct sanitized no-call CFPB evidence packets for Pilot 05."
    )
    parser.add_argument("--input-file", required=True, type=Path)
    parser.add_argument("--audit-manifest", required=True, type=Path)
    parser.add_argument("--strict-row-quality-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--max-packets", type=int, default=0)
    return parser.parse_args()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 8)


def date_like(value: str) -> bool:
    value = normalize_space(value)
    if not value:
        return False

    iso_prefix_like = (
        len(value) >= 10
        and value[4] == "-"
        and value[7] == "-"
        and value[:4].isdigit()
        and value[5:7].isdigit()
        and value[8:10].isdigit()
    )
    if iso_prefix_like:
        if len(value) == 10:
            return True
        if value[10] in {"T", " "}:
            return True

    slash_parts = value.split("/")
    slash_like = (
        len(slash_parts) == 3
        and all(part.isdigit() for part in slash_parts)
        and len(slash_parts[2]) in {2, 4}
    )
    return slash_like


def date_prefix(value: str) -> str:
    value = normalize_space(value)
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        return value[:10]
    return ""


def received_month(value: str) -> str:
    prefix = date_prefix(value)
    if prefix:
        return prefix[:7]
    return "__UNKNOWN_MONTH__"


def narrative_length_bucket(value: str) -> str:
    length = len(str(value or ""))
    if length <= 0:
        return "missing"
    if length < 250:
        return "1-249"
    if length < 1000:
        return "250-999"
    if length < 3000:
        return "1000-2999"
    return "3000_plus"


def presence(value: str) -> str:
    return "present" if normalize_space(value) else "absent"


def safe_category(value: str, *, max_length: int = 180) -> str:
    cleaned = normalize_space(value)
    if not cleaned:
        return "__MISSING__"

    if len(cleaned) > max_length:
        return "__CATEGORY_LENGTH_REDACTED__"

    for pattern in RAW_LIKE_PATTERNS:
        if pattern.search(cleaned):
            return "__CATEGORY_PATTERN_REDACTED__"

    return cleaned


def strict_clean_row(row: dict[Any, Any]) -> tuple[dict[str, str] | None, str | None]:
    extra_field_count = 0
    cleaned: dict[str, str] = {}

    for key, value in row.items():
        if key is None:
            extra_field_count += 1
            continue

        cleaned_key = normalize_space(str(key))
        if not cleaned_key:
            extra_field_count += 1
            continue

        cleaned[cleaned_key] = normalize_space("" if value is None else str(value))

    if extra_field_count:
        return None, "extra_csv_fields"

    for required in EXPECTED_COLUMNS:
        if required not in cleaned:
            return None, f"missing_required_column:{required}"

    product_value = cleaned.get("Product", "")
    target_value = cleaned.get("Timely response?", "")
    date_received_value = cleaned.get("Date received", "")
    date_sent_value = cleaned.get("Date sent to company", "")
    complaint_id_value = cleaned.get("Complaint ID", "")

    if product_value not in ALLOWED_PRODUCTS:
        return None, "invalid_product"

    if target_value not in ALLOWED_TARGETS:
        return None, "invalid_target"

    if not date_like(date_received_value):
        return None, "invalid_date_received"

    if not date_like(date_sent_value):
        return None, "invalid_date_sent_to_company"

    if complaint_id_value and not complaint_id_value.isdigit():
        return None, "invalid_complaint_id"

    received = date_prefix(date_received_value)
    if received and not ("2026-01-01" <= received <= "2026-03-31"):
        return None, "outside_approved_received_date_window"

    return cleaned, None


def build_evidence_text(packet: dict[str, str]) -> str:
    parts = [
        f"product_family={packet['product_family']}",
        f"sub_product_bucket={packet['sub_product_bucket']}",
        f"issue_category={packet['issue_category']}",
        f"sub_issue_category={packet['sub_issue_category']}",
        f"submitted_via={packet['submitted_via']}",
        f"received_month={packet['received_month']}",
        f"narrative_available={packet['narrative_available']}",
        f"narrative_length_bucket={packet['narrative_length_bucket']}",
        f"consumer_tag_presence={packet['consumer_tag_presence']}",
        f"state_presence={packet['state_presence']}",
    ]
    return "Evidence packet: " + "; ".join(parts) + "."


def assert_no_forbidden_evidence_text(packet: dict[str, str]) -> None:
    text = packet.get("evidence_text", "")

    for pattern in RAW_LIKE_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"Forbidden raw-like or target-like fragment in evidence_text: {pattern.pattern}")

    for forbidden in FORBIDDEN_EVIDENCE_FIELD_NAMES:
        if forbidden.lower() in text.lower():
            raise ValueError(f"Forbidden field name leaked into evidence_text: {forbidden}")


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


def construct_packets(
    *,
    input_file: Path,
    audit_manifest_path: Path,
    strict_row_quality_manifest_path: Path,
    output_dir: Path,
    max_packets: int,
) -> ConstructionStats:
    audit_manifest = load_json(audit_manifest_path)
    strict_manifest = load_json(strict_row_quality_manifest_path)

    expected_audited_rows = int(audit_manifest["row_counts"]["rows_audited"])
    expected_strict_rows = int(strict_manifest["accepted_rows"])

    if expected_audited_rows != expected_strict_rows:
        raise ValueError("Audit manifest row count and strict row-quality count do not match.")

    output_dir.mkdir(parents=True, exist_ok=True)

    packet_rows: list[dict[str, str]] = []
    label_rows: list[dict[str, str]] = []

    rejection_counts: Counter[str] = Counter()
    target_counts: Counter[str] = Counter()
    product_counts: Counter[str] = Counter()
    narrative_availability_counts: Counter[str] = Counter()

    total_seen = 0
    rejected_rows = 0

    with input_file.open("r", encoding="utf-8-sig", newline="") as file_obj:
        reader = csv.DictReader(file_obj, dialect=csv.excel)

        header = [normalize_space(name) for name in (reader.fieldnames or [])]
        if header != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected CFPB header. Got {header!r}")

        for row in reader:
            total_seen += 1

            cleaned, reason = strict_clean_row(row)
            if cleaned is None:
                rejected_rows += 1
                rejection_counts[str(reason)] += 1
                continue

            next_index = len(packet_rows) + 1
            if max_packets > 0 and next_index > max_packets:
                break

            packet_id = f"P05_CFPB_PKT_{next_index:06d}"

            narrative_value = cleaned.get("Consumer complaint narrative", "")
            narrative_is_present = presence(narrative_value)

            packet = {
                "packet_id": packet_id,
                "product_family": safe_category(cleaned.get("Product", "")),
                "sub_product_bucket": safe_category(cleaned.get("Sub-product", "")),
                "issue_category": safe_category(cleaned.get("Issue", "")),
                "sub_issue_category": safe_category(cleaned.get("Sub-issue", "")),
                "submitted_via": safe_category(cleaned.get("Submitted via", "")),
                "received_month": received_month(cleaned.get("Date received", "")),
                "consumer_tag_presence": presence(cleaned.get("Tags", "")),
                "state_presence": presence(cleaned.get("State", "")),
                "narrative_available": narrative_is_present,
                "narrative_length_bucket": narrative_length_bucket(narrative_value),
            }
            packet["evidence_text"] = build_evidence_text(packet)

            assert_no_forbidden_evidence_text(packet)

            label = {
                "packet_id": packet_id,
                "target_timely_response": cleaned.get("Timely response?", ""),
            }

            packet_rows.append(packet)
            label_rows.append(label)

            target_counts[label["target_timely_response"]] += 1
            product_counts[packet["product_family"]] += 1
            narrative_availability_counts[narrative_is_present] += 1

    packet_count = len(packet_rows)
    label_count = len(label_rows)

    if packet_count != label_count:
        raise ValueError("Packet count and label count do not match.")

    if max_packets == 0 and packet_count != expected_audited_rows:
        raise ValueError(
            f"Packet count {packet_count} does not match audited row count {expected_audited_rows}."
        )

    packet_path = output_dir / "pilot_05_cfpb_sanitized_evidence_packets.csv"
    label_path = output_dir / "pilot_05_cfpb_packet_labels.csv"

    packet_fieldnames = [
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

    label_fieldnames = [
        "packet_id",
        "target_timely_response",
    ]

    write_csv(packet_path, packet_fieldnames, packet_rows)
    write_csv(label_path, label_fieldnames, label_rows)

    target_distribution_rows = [
        {
            "target_timely_response": key,
            "count": count,
            "share": safe_ratio(count, packet_count),
        }
        for key, count in sorted(target_counts.items())
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_packet_label_distribution.csv",
        ["target_timely_response", "count", "share"],
        target_distribution_rows,
    )

    product_distribution_rows = [
        {
            "product_family": key,
            "count": count,
            "share": safe_ratio(count, packet_count),
        }
        for key, count in sorted(product_counts.items())
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_packet_product_distribution.csv",
        ["product_family", "count", "share"],
        product_distribution_rows,
    )

    narrative_distribution_rows = [
        {
            "narrative_available": key,
            "count": count,
            "share": safe_ratio(count, packet_count),
        }
        for key, count in sorted(narrative_availability_counts.items())
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_packet_narrative_availability_distribution.csv",
        ["narrative_available", "count", "share"],
        narrative_distribution_rows,
    )

    field_policy_rows = [
        {
            "source_field": "Date received",
            "decision": "derived_month_only",
            "output_field": "received_month",
            "rationale": "Temporal context kept at month granularity; raw timestamp excluded.",
        },
        {
            "source_field": "Product",
            "decision": "include_category",
            "output_field": "product_family",
            "rationale": "Official CFPB category; not raw narrative or identifier.",
        },
        {
            "source_field": "Sub-product",
            "decision": "include_category",
            "output_field": "sub_product_bucket",
            "rationale": "Official CFPB category; not raw narrative or identifier.",
        },
        {
            "source_field": "Issue",
            "decision": "include_category",
            "output_field": "issue_category",
            "rationale": "Official CFPB category; not raw narrative or identifier.",
        },
        {
            "source_field": "Sub-issue",
            "decision": "include_category",
            "output_field": "sub_issue_category",
            "rationale": "Official CFPB category; not raw narrative or identifier.",
        },
        {
            "source_field": "Consumer complaint narrative",
            "decision": "exclude_raw_text",
            "output_field": "narrative_available,narrative_length_bucket",
            "rationale": "Raw consumer-submitted text is not written; only availability and length bucket are retained.",
        },
        {
            "source_field": "Company public response",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Potentially outcome/process-related; excluded from evidence text.",
        },
        {
            "source_field": "Company",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Company names excluded to avoid provider ranking or company-specific claims.",
        },
        {
            "source_field": "State",
            "decision": "presence_only",
            "output_field": "state_presence",
            "rationale": "State value excluded; only presence flag retained.",
        },
        {
            "source_field": "ZIP code",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Geographic identifier excluded.",
        },
        {
            "source_field": "Tags",
            "decision": "presence_only",
            "output_field": "consumer_tag_presence",
            "rationale": "Sensitive tag values excluded; only presence flag retained.",
        },
        {
            "source_field": "Submitted via",
            "decision": "include_category",
            "output_field": "submitted_via",
            "rationale": "Submission channel is retained as a non-outcome categorical feature.",
        },
        {
            "source_field": "Date sent to company",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Process timing after receipt is excluded from evidence text.",
        },
        {
            "source_field": "Company response to consumer",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Outcome-adjacent company-response field excluded from evidence text.",
        },
        {
            "source_field": "Timely response?",
            "decision": "label_only",
            "output_field": "pilot_05_cfpb_packet_labels.csv",
            "rationale": "Target label is stored separately and is not included in evidence text.",
        },
        {
            "source_field": "Complaint ID",
            "decision": "exclude",
            "output_field": "",
            "rationale": "Raw record identifier excluded; synthetic packet_id generated instead.",
        },
    ]
    write_csv(
        output_dir / "pilot_05_cfpb_packet_field_policy.csv",
        ["source_field", "decision", "output_field", "rationale"],
        field_policy_rows,
    )

    summary_rows = [
        {"metric": "status", "value": "PASS"},
        {"metric": "total_csv_records_seen_after_header", "value": total_seen},
        {"metric": "audited_rows_expected", "value": expected_audited_rows},
        {"metric": "strict_rows_expected", "value": expected_strict_rows},
        {"metric": "packets_written", "value": packet_count},
        {"metric": "labels_written", "value": label_count},
        {"metric": "rejected_rows", "value": rejected_rows},
        {"metric": "real_api_calls", "value": 0},
        {"metric": "model_calls", "value": 0},
        {"metric": "dataset_downloads", "value": 0},
        {"metric": "raw_rows_written", "value": False},
        {"metric": "raw_narratives_written", "value": False},
        {"metric": "company_names_written", "value": False},
        {"metric": "complaint_ids_written", "value": False},
        {"metric": "zip_codes_written", "value": False},
        {"metric": "target_label_in_evidence_text", "value": False},
        {"metric": "labels_written_separately", "value": True},
    ]
    write_csv(output_dir / "pilot_05_cfpb_packet_summary.csv", ["metric", "value"], summary_rows)

    manifest = {
        "status": "PASS",
        "scope": "Pilot 05 CFPB sanitized evidence-packet construction",
        "source": "CFPB Consumer Complaint Database browser-export CSV audited in Pilot 05",
        "source_raw_filename_only": input_file.name,
        "source_audit_manifest": str(audit_manifest_path),
        "source_strict_row_quality_manifest": str(strict_row_quality_manifest_path),
        "outputs": {
            "evidence_packets_csv": str(packet_path),
            "labels_csv": str(label_path),
            "label_distribution_csv": str(output_dir / "pilot_05_cfpb_packet_label_distribution.csv"),
            "product_distribution_csv": str(output_dir / "pilot_05_cfpb_packet_product_distribution.csv"),
            "narrative_availability_distribution_csv": str(output_dir / "pilot_05_cfpb_packet_narrative_availability_distribution.csv"),
            "field_policy_csv": str(output_dir / "pilot_05_cfpb_packet_field_policy.csv"),
            "summary_csv": str(output_dir / "pilot_05_cfpb_packet_summary.csv"),
            "report_md": str(output_dir / "pilot_05_cfpb_evidence_packet_report.md"),
        },
        "row_counts": {
            "total_csv_records_seen_after_header": total_seen,
            "audited_rows_expected": expected_audited_rows,
            "strict_rows_expected": expected_strict_rows,
            "packets_written": packet_count,
            "labels_written": label_count,
            "rejected_rows": rejected_rows,
        },
        "label_counts": dict(sorted(target_counts.items())),
        "product_counts": dict(sorted(product_counts.items())),
        "narrative_availability_counts": dict(sorted(narrative_availability_counts.items())),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "safety": {
            "real_api_calls": 0,
            "model_calls": 0,
            "dataset_downloads": 0,
            "raw_rows_written": False,
            "raw_narratives_written": False,
            "company_names_written": False,
            "complaint_ids_written": False,
            "zip_codes_written": False,
            "company_response_fields_written": False,
            "target_label_in_evidence_text": False,
            "labels_written_separately": True,
            "raw_prompt_or_response_written": False,
        },
        "claim_boundary": "No-call sanitized evidence-packet construction for later controlled evidence-state reliability experiments; not a model result and not a real-world deployment claim.",
    }
    write_json(output_dir / "pilot_05_cfpb_evidence_packet_manifest.json", manifest)

    report = f"""# Pilot 05 CFPB Sanitized Evidence-Packet Construction

Status: PASS

This no-call construction step converts the audited CFPB browser-export dataset into sanitized evidence packets for later controlled evidence-state reliability experiments.

## Counts

- Total CSV records seen after header: {total_seen}
- Audited rows expected: {expected_audited_rows}
- Strict rows expected: {expected_strict_rows}
- Evidence packets written: {packet_count}
- Labels written separately: {label_count}
- Rejected rows during packet construction: {rejected_rows}

## Safety boundary

The committed evidence packets do not include raw complaint narratives, company names, complaint IDs, ZIP codes, raw rows, company-response fields, raw prompts, raw responses, API outputs, or model outputs.

The target label is stored separately in `pilot_05_cfpb_packet_labels.csv` and is not included in the evidence text.

## Claim boundary

This output is a no-call sanitized data-construction layer. It does not claim model reliability, company ranking, financial safety, legal safety, consumer harm prevalence, deployment validity, or regulated lending validity.
"""
    (output_dir / "pilot_05_cfpb_evidence_packet_report.md").write_text(report, encoding="utf-8")

    return ConstructionStats(
        total_csv_records_seen_after_header=total_seen,
        packets_written=packet_count,
        labels_written=label_count,
        rejected_rows=rejected_rows,
        rejection_counts=dict(sorted(rejection_counts.items())),
        target_counts=dict(sorted(target_counts.items())),
        product_counts=dict(sorted(product_counts.items())),
        narrative_availability_counts=dict(sorted(narrative_availability_counts.items())),
    )


def main() -> None:
    args = parse_args()

    if not args.input_file.exists():
        raise FileNotFoundError(args.input_file)

    if not args.audit_manifest.exists():
        raise FileNotFoundError(args.audit_manifest)

    if not args.strict_row_quality_manifest.exists():
        raise FileNotFoundError(args.strict_row_quality_manifest)

    stats = construct_packets(
        input_file=args.input_file,
        audit_manifest_path=args.audit_manifest,
        strict_row_quality_manifest_path=args.strict_row_quality_manifest,
        output_dir=args.output_dir,
        max_packets=args.max_packets,
    )

    print("Pilot 05 CFPB sanitized evidence packets generated.")
    print(f"output_dir: {args.output_dir}")
    print("status: PASS")
    print(f"total_csv_records_seen_after_header: {stats.total_csv_records_seen_after_header}")
    print(f"packets_written: {stats.packets_written}")
    print(f"labels_written: {stats.labels_written}")
    print(f"rejected_rows: {stats.rejected_rows}")
    print("real_api_calls: 0")
    print("model_calls: 0")
    print("dataset_downloads: 0")
    print("raw_rows_written: False")
    print("raw_narratives_written: False")
    print("company_names_written: False")
    print("complaint_ids_written: False")
    print("zip_codes_written: False")
    print("target_label_in_evidence_text: False")


if __name__ == "__main__":
    main()
