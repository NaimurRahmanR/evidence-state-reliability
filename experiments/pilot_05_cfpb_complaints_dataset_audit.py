from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, TextIO


SCRIPT_VERSION = "pilot_05_cfpb_complaints_dataset_audit_v1"

DEFAULT_OUTPUT_DIR = Path("reports") / "pilot_05_cfpb_complaints_dataset_audit"
DEFAULT_RAW_ROOT = Path("data") / "raw" / "cfpb_complaints"

DEFAULT_SOURCE_ROUTE = "CFPB Consumer Complaint Database filtered local export"

REAL_API_CALLS = 0
MODEL_CALLS = 0
DATASET_DOWNLOADS = 0
RAW_RESPONSE_INSPECTION = False


TARGET_FIELD_CANDIDATES = [
    "timely response?",
    "timely_response",
    "company response to consumer",
    "company_response_to_consumer",
    "company public response",
    "company_public_response",
]

PREFERRED_TARGET_FIELD = "timely response?"

DATE_FIELD_CANDIDATES = {
    "date received",
    "date_received",
    "date sent to company",
    "date_sent_to_company",
}

NARRATIVE_FIELD_CANDIDATES = {
    "consumer complaint narrative",
    "consumer_complaint_narrative",
}

HIGH_RISK_FIELD_RULES = [
    {
        "keyword": "consumer complaint narrative",
        "risk_group": "raw_narrative",
        "risk_level": "HIGH",
        "reason": "Narratives can contain sensitive consumer-provided descriptions and must not be committed raw.",
        "default_handling": "Use presence/length aggregate only unless later explicitly approved.",
    },
    {
        "keyword": "complaint id",
        "risk_group": "direct_identifier",
        "risk_level": "HIGH",
        "reason": "Complaint ID is a record identifier and should not be used as a committed evidence-packet ID.",
        "default_handling": "Transform to synthetic internal case IDs only.",
    },
    {
        "keyword": "zip",
        "risk_group": "geography",
        "risk_level": "HIGH",
        "reason": "ZIP code can increase re-identification and proxy-risk concerns.",
        "default_handling": "Exclude from committed evidence packets; use missingness/count audit only.",
    },
    {
        "keyword": "state",
        "risk_group": "geography",
        "risk_level": "MEDIUM",
        "reason": "State is lower-risk than ZIP but still context-sensitive.",
        "default_handling": "Use carefully; avoid company/geography ranking claims.",
    },
    {
        "keyword": "company",
        "risk_group": "company_context",
        "risk_level": "MEDIUM_HIGH",
        "reason": "Company fields can invite ranking or misconduct claims.",
        "default_handling": "Do not publish company rankings; consider masking in evidence packets.",
    },
    {
        "keyword": "tags",
        "risk_group": "consumer_group_signal",
        "risk_level": "MEDIUM_HIGH",
        "reason": "Tags may indicate groups such as Older American or Servicemember.",
        "default_handling": "Use for claim-risk inventory only unless explicitly approved.",
    },
    {
        "keyword": "submitted via",
        "risk_group": "process_context",
        "risk_level": "LOW_MEDIUM",
        "reason": "Submission channel can affect process interpretation.",
        "default_handling": "Candidate structured evidence after audit.",
    },
    {
        "keyword": "consumer consent",
        "risk_group": "narrative_publication_context",
        "risk_level": "MEDIUM",
        "reason": "Consent status relates to narrative publication and must be handled carefully.",
        "default_handling": "Use as audit field; do not infer consumer intent beyond field meaning.",
    },
]

CANDIDATE_EVIDENCE_FIELDS = {
    "date received",
    "product",
    "sub-product",
    "issue",
    "sub-issue",
    "company public response",
    "state",
    "tags",
    "consumer consent provided?",
    "submitted via",
    "date sent to company",
    "company response to consumer",
    "timely response?",
}

LEAKAGE_RISK_RULES = [
    {
        "field_group": "target fields",
        "risk_level": "HIGH",
        "notes": "Target fields such as Timely response? or Company response to consumer must not be included as decision evidence.",
        "default_decision": "Use as target only, not input evidence.",
    },
    {
        "field_group": "consumer complaint narrative",
        "risk_level": "HIGH",
        "notes": "Raw narratives can contain sensitive consumer-submitted text and must not be committed.",
        "default_decision": "Use narrative presence/length aggregates first; raw text excluded from committed outputs.",
    },
    {
        "field_group": "company fields",
        "risk_level": "MEDIUM_HIGH",
        "notes": "Do not use company fields to support provider ranking or misconduct claims.",
        "default_decision": "Do not rank companies; consider masking company field in evidence packets.",
    },
    {
        "field_group": "geography fields",
        "risk_level": "MEDIUM_HIGH",
        "notes": "ZIP code and fine geography can raise proxy or re-identification concerns.",
        "default_decision": "Exclude ZIP from committed evidence packets; use only aggregate audit notes.",
    },
    {
        "field_group": "date fields",
        "risk_level": "MEDIUM",
        "notes": "Dates support temporal splits but can also enable reconstruction if combined with other fields.",
        "default_decision": "Use month/year buckets for committed evidence packets.",
    },
]


@dataclass(frozen=True)
class OpenedDataset:
    input_file: Path
    input_filename: str
    input_suffix: str
    source_inside_zip: str | None
    records: list[dict[str, str]] | None
    handle: TextIO | None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_column_name(value: str) -> str:
    return value.strip().lower().replace("_", " ")


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def is_under_path(path: Path, root: Path) -> bool:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
        return True
    except ValueError:
        return False


def validate_input_file_policy(input_file: Path, allow_external_local_path: bool) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    if not input_file.is_file():
        raise ValueError(f"Input path is not a file: {input_file}")

    if not allow_external_local_path and not is_under_path(input_file, DEFAULT_RAW_ROOT):
        raise ValueError(
            "Input file must be under data/raw/cfpb_complaints/ by default. "
            "Move the local CFPB complaint export there, or rerun with "
            "--allow-external-local-path only after explicit approval."
        )

    allowed_suffixes = {".csv", ".json", ".zip"}
    suffix = input_file.suffix.lower()
    if suffix not in allowed_suffixes:
        raise ValueError(
            f"Unsupported input suffix '{suffix}'. Supported local formats: "
            ".csv, .json, .zip containing one CSV or JSON file."
        )


def read_json_records_from_text(text: str) -> list[dict[str, str]]:
    parsed = json.loads(text)

    if isinstance(parsed, list):
        raw_records = parsed
    elif isinstance(parsed, dict) and isinstance(parsed.get("hits"), dict):
        hits = parsed["hits"]
        if isinstance(hits.get("hits"), list):
            raw_records = [item.get("_source", item) for item in hits["hits"]]
        else:
            raw_records = []
    elif isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        raw_records = parsed["data"]
    else:
        raise ValueError(
            "Unsupported JSON structure. Expected a list of records, "
            "a {'data': [...]} object, or an Elasticsearch-style hits object."
        )

    records: list[dict[str, str]] = []
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        records.append({str(key): "" if value is None else str(value) for key, value in item.items()})

    return records


def open_dataset(input_file: Path) -> OpenedDataset:
    suffix = input_file.suffix.lower()

    if suffix == ".csv":
        handle = input_file.open("r", encoding="utf-8-sig", newline="")
        return OpenedDataset(
            input_file=input_file,
            input_filename=input_file.name,
            input_suffix=suffix,
            source_inside_zip=None,
            records=None,
            handle=handle,
        )

    if suffix == ".json":
        text = input_file.read_text(encoding="utf-8-sig")
        records = read_json_records_from_text(text)
        return OpenedDataset(
            input_file=input_file,
            input_filename=input_file.name,
            input_suffix=suffix,
            source_inside_zip=None,
            records=records,
            handle=None,
        )

    if suffix == ".zip":
        archive = zipfile.ZipFile(input_file)
        candidates = [
            name for name in archive.namelist()
            if not name.endswith("/") and Path(name).suffix.lower() in {".csv", ".json"}
        ]

        if len(candidates) != 1:
            archive.close()
            raise ValueError(
                "ZIP input must contain exactly one CSV or JSON file. "
                f"Found {len(candidates)} candidates."
            )

        inner_name = candidates[0]
        inner_suffix = Path(inner_name).suffix.lower()

        if inner_suffix == ".csv":
            binary_handle = archive.open(inner_name, "r")
            text_handle = io.TextIOWrapper(binary_handle, encoding="utf-8-sig", newline="")
            return OpenedDataset(
                input_file=input_file,
                input_filename=input_file.name,
                input_suffix=suffix,
                source_inside_zip=inner_name,
                records=None,
                handle=ZipTextHandle(text_handle, archive),
            )

        if inner_suffix == ".json":
            with archive.open(inner_name, "r") as binary:
                text = binary.read().decode("utf-8-sig")
            archive.close()
            records = read_json_records_from_text(text)
            return OpenedDataset(
                input_file=input_file,
                input_filename=input_file.name,
                input_suffix=suffix,
                source_inside_zip=inner_name,
                records=records,
                handle=None,
            )

    raise ValueError(f"Unsupported input file type: {suffix}")


class ZipTextHandle:
    def __init__(self, text_handle: TextIO, archive: zipfile.ZipFile):
        self._text_handle = text_handle
        self._archive = archive

    def read(self, *args, **kwargs):
        return self._text_handle.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._text_handle.readline(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._text_handle.seek(*args, **kwargs)

    def __iter__(self):
        return iter(self._text_handle)

    def close(self) -> None:
        self._text_handle.close()
        self._archive.close()


def dialect_for_sample(handle: TextIO) -> csv.Dialect:
    sample = handle.read(8192)
    handle.seek(0)

    if not sample:
        raise ValueError("Input CSV file is empty.")

    try:
        return csv.Sniffer().sniff(sample, delimiters=",|\t;")
    except csv.Error:
        return csv.excel


def records_from_opened_dataset(opened: OpenedDataset) -> tuple[list[str], Iterator[dict[str, str]]]:
    if opened.records is not None:
        if not opened.records:
            raise ValueError("JSON input produced no records.")
        columns = sorted({key for record in opened.records for key in record.keys()})

        def iterator() -> Iterator[dict[str, str]]:
            for record in opened.records or []:
                yield {column: str(record.get(column, "")).strip() for column in columns}

        return columns, iterator()

    if opened.handle is None:
        raise ValueError("Opened dataset has neither records nor file handle.")

    # Task 05R: deterministic standard CSV parsing for CFPB browser exports.
    # csv.Sniffer can infer an unsafe dialect on narrative-heavy browser exports,
    # causing rows to be skipped or misread. The CFPB browser export is standard
    # comma-separated CSV with quoted fields, so use csv.excel deterministically.
    opened.handle.seek(0)
    reader = csv.DictReader(opened.handle, dialect=csv.excel)

    if not reader.fieldnames:
        raise ValueError("Input CSV file has no header row.")

    columns = [column.strip() for column in reader.fieldnames]

    def iterator() -> Iterator[dict[str, str]]:
        for row in reader:
            # Task 05P: strict CFPB CSV row-quality gate for browser-export misalignment.
            cleaned_row = {}
            extra_field_count = 0
            for key, value in row.items():
                if key is None:
                    extra_field_count += 1
                    continue
                cleaned_key = str(key).strip()
                if not cleaned_key:
                    extra_field_count += 1
                    continue
                cleaned_row[cleaned_key] = "" if value is None else str(value).strip()
            
            def _task_05p_date_like(value: str) -> bool:
                # Task 05Q: accept CFPB browser-export datetime strings.
                value = str(value).strip()
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
            
            if extra_field_count:
                continue
            
            product_value = cleaned_row.get("Product", "").strip()
            target_value = cleaned_row.get("Timely response?", "").strip()
            date_received_value = cleaned_row.get("Date received", "").strip()
            date_sent_value = cleaned_row.get("Date sent to company", "").strip()
            complaint_id_value = cleaned_row.get("Complaint ID", "").strip()
            
            if product_value not in {"Credit card", "Prepaid card"}:
                continue
            if target_value not in {"Yes", "No", ""}:
                continue
            if not _task_05p_date_like(date_received_value):
                continue
            if not _task_05p_date_like(date_sent_value):
                continue
            if complaint_id_value and not complaint_id_value.isdigit():
                continue
            
            yield cleaned_row

    return columns, iterator()


def detect_target_column(columns: list[str]) -> str | None:
    normalized_to_original = {normalize_column_name(column): column for column in columns}

    preferred = normalize_column_name(PREFERRED_TARGET_FIELD)
    if preferred in normalized_to_original:
        return normalized_to_original[preferred]

    for candidate in TARGET_FIELD_CANDIDATES:
        normalized = normalize_column_name(candidate)
        if normalized in normalized_to_original:
            return normalized_to_original[normalized]

    return None


def detect_narrative_column(columns: list[str]) -> str | None:
    normalized_to_original = {normalize_column_name(column): column for column in columns}
    for candidate in NARRATIVE_FIELD_CANDIDATES:
        normalized = normalize_column_name(candidate)
        if normalized in normalized_to_original:
            return normalized_to_original[normalized]
    return None


def field_risk_matches(column_name: str) -> list[dict[str, str]]:
    normalized = normalize_column_name(column_name)
    matches = []
    for rule in HIGH_RISK_FIELD_RULES:
        if rule["keyword"] in normalized:
            matches.append(rule)
    return matches


def infer_field_group(column_name: str) -> str:
    normalized = normalize_column_name(column_name)

    if normalized in {normalize_column_name(value) for value in TARGET_FIELD_CANDIDATES}:
        return "candidate_target"
    if normalized in {normalize_column_name(value) for value in NARRATIVE_FIELD_CANDIDATES}:
        return "narrative"
    if "company" in normalized:
        return "company_context"
    if "zip" in normalized or normalized == "state":
        return "geography"
    if normalized in DATE_FIELD_CANDIDATES:
        return "temporal"
    if normalized in {normalize_column_name(value) for value in CANDIDATE_EVIDENCE_FIELDS}:
        return "candidate_structured_evidence"
    return "other"


def default_handling_for_column(column_name: str) -> str:
    normalized = normalize_column_name(column_name)

    if normalized in {normalize_column_name(value) for value in TARGET_FIELD_CANDIDATES}:
        return "target_only_exclude_from_decision_evidence"
    if normalized in {normalize_column_name(value) for value in NARRATIVE_FIELD_CANDIDATES}:
        return "do_not_commit_raw_text_use_presence_or_length_aggregate_first"
    if normalized == "complaint id":
        return "transform_to_synthetic_internal_case_id_only"
    if "zip" in normalized:
        return "exclude_from_committed_evidence_packets"
    if "company" in normalized:
        return "review_before_use_do_not_rank_companies"
    if normalized in {normalize_column_name(value) for value in CANDIDATE_EVIDENCE_FIELDS}:
        return "candidate_for_sanitized_structured_evidence_packet"
    return "manual_review_before_use"


def update_limited_counter(counter: Counter[str], value: str, limit: int = 100) -> None:
    if len(counter) < limit or value in counter:
        counter[value] += 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_dataset_audit_summary(
    path: Path,
    input_file: Path,
    input_filename: str,
    input_suffix: str,
    source_inside_zip: str | None,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    narrative_column: str | None,
    max_rows: int,
    allow_external_local_path: bool,
    input_sha256: str | None,
) -> None:
    rows = [
        {"metric": "script_version", "value": SCRIPT_VERSION},
        {"metric": "created_at_utc", "value": utc_now_iso()},
        {"metric": "source_route", "value": source_route},
        {"metric": "input_filename_only", "value": input_filename},
        {"metric": "input_suffix", "value": input_suffix},
        {"metric": "source_inside_zip", "value": source_inside_zip or ""},
        {"metric": "input_path_is_under_data_raw_cfpb_complaints", "value": str(is_under_path(input_file, DEFAULT_RAW_ROOT))},
        {"metric": "allow_external_local_path", "value": str(allow_external_local_path)},
        {"metric": "input_sha256", "value": input_sha256 or "not_computed"},
        {"metric": "row_count_audited", "value": str(row_count)},
        {"metric": "column_count", "value": str(column_count)},
        {"metric": "target_column_detected", "value": target_column or ""},
        {"metric": "narrative_column_detected", "value": narrative_column or ""},
        {"metric": "max_rows", "value": str(max_rows)},
        {"metric": "real_api_calls", "value": str(REAL_API_CALLS)},
        {"metric": "model_calls", "value": str(MODEL_CALLS)},
        {"metric": "dataset_downloads", "value": str(DATASET_DOWNLOADS)},
        {"metric": "raw_response_inspection", "value": str(RAW_RESPONSE_INSPECTION)},
        {"metric": "raw_data_committed", "value": "False"},
        {"metric": "raw_rows_written_to_reports", "value": "False"},
        {"metric": "raw_narratives_written_to_reports", "value": "False"},
        {"metric": "claim_boundary", "value": "recorded complaint-resolution outcome review simulation only"},
    ]
    write_csv(path, ["metric", "value"], rows)


def write_column_inventory(path: Path, columns: list[str]) -> None:
    rows = []
    for index, column in enumerate(columns, start=1):
        matches = field_risk_matches(column)
        rows.append(
            {
                "ordinal": index,
                "column_name": column,
                "normalized_column_name": normalize_column_name(column),
                "inferred_group": infer_field_group(column),
                "is_sensitive_or_claim_risk": str(bool(matches)),
                "risk_groups": "; ".join(match["risk_group"] for match in matches),
                "risk_reasons": " ".join(match["reason"] for match in matches),
                "default_handling": default_handling_for_column(column),
            }
        )

    write_csv(
        path,
        [
            "ordinal",
            "column_name",
            "normalized_column_name",
            "inferred_group",
            "is_sensitive_or_claim_risk",
            "risk_groups",
            "risk_reasons",
            "default_handling",
        ],
        rows,
    )


def write_missingness_summary(
    path: Path,
    columns: list[str],
    row_count: int,
    missing_counts: Counter[str],
    non_missing_counts: Counter[str],
) -> None:
    rows = []
    for column in columns:
        missing = int(missing_counts[column])
        non_missing = int(non_missing_counts[column])
        rows.append(
            {
                "column_name": column,
                "non_missing_count": non_missing,
                "missing_count": missing,
                "missing_rate": safe_ratio(missing, row_count),
            }
        )

    write_csv(path, ["column_name", "non_missing_count", "missing_count", "missing_rate"], rows)


def write_target_distribution(
    path: Path,
    target_column: str | None,
    target_counts: Counter[str],
    row_count: int,
) -> None:
    rows = []

    if target_column is None:
        rows.append(
            {
                "target_column": "",
                "target_value": "",
                "count": 0,
                "share": 0.0,
                "note": "No preferred CFPB complaint target column detected.",
            }
        )
    else:
        for value, count in target_counts.most_common():
            rows.append(
                {
                    "target_column": target_column,
                    "target_value": value,
                    "count": int(count),
                    "share": safe_ratio(int(count), row_count),
                    "note": "Recorded complaint-resolution field distribution; not a truth/fault/compliance label.",
                }
            )

    write_csv(path, ["target_column", "target_value", "count", "share", "note"], rows)


def write_sensitive_field_inventory(path: Path, columns: list[str]) -> None:
    rows = []

    for column in columns:
        matches = field_risk_matches(column)
        for match in matches:
            rows.append(
                {
                    "column_name": column,
                    "normalized_column_name": normalize_column_name(column),
                    "risk_group": match["risk_group"],
                    "risk_level": match["risk_level"],
                    "reason": match["reason"],
                    "default_handling": match["default_handling"],
                }
            )

    if not rows:
        rows.append(
            {
                "column_name": "",
                "normalized_column_name": "",
                "risk_group": "",
                "risk_level": "",
                "reason": "No sensitive/claim-risk fields detected by keyword scan.",
                "default_handling": "manual_review_still_required",
            }
        )

    write_csv(
        path,
        ["column_name", "normalized_column_name", "risk_group", "risk_level", "reason", "default_handling"],
        rows,
    )


def write_temporal_field_audit(
    path: Path,
    columns: list[str],
    date_minmax: dict[str, tuple[str, str]],
) -> None:
    rows = []

    for column in columns:
        normalized = normalize_column_name(column)
        if normalized in DATE_FIELD_CANDIDATES:
            min_value, max_value = date_minmax.get(column, ("", ""))
            rows.append(
                {
                    "column_name": column,
                    "normalized_column_name": normalized,
                    "detected": "True",
                    "min_value_observed": min_value,
                    "max_value_observed": max_value,
                    "note": "Temporal suitability requires fixed-window documentation and recent-publication caveats.",
                }
            )

    if not rows:
        rows.append(
            {
                "column_name": "",
                "normalized_column_name": "",
                "detected": "False",
                "min_value_observed": "",
                "max_value_observed": "",
                "note": "No CFPB complaint date field detected by candidate-name scan.",
            }
        )

    write_csv(
        path,
        ["column_name", "normalized_column_name", "detected", "min_value_observed", "max_value_observed", "note"],
        rows,
    )


def write_leakage_risk_notes(path: Path) -> None:
    write_csv(path, ["field_group", "risk_level", "notes", "default_decision"], LEAKAGE_RISK_RULES)


def write_narrative_audit(
    path: Path,
    narrative_column: str | None,
    narrative_present_count: int,
    narrative_missing_count: int,
    narrative_length_min: int,
    narrative_length_max: int,
    narrative_length_total: int,
    row_count: int,
) -> None:
    if narrative_column is None:
        rows = [
            {
                "narrative_column": "",
                "narrative_present_count": 0,
                "narrative_missing_count": 0,
                "narrative_present_rate": 0.0,
                "narrative_length_min": 0,
                "narrative_length_max": 0,
                "narrative_length_mean": 0.0,
                "raw_narratives_written": "False",
                "note": "No narrative column detected.",
            }
        ]
    else:
        mean_length = round(narrative_length_total / narrative_present_count, 3) if narrative_present_count else 0.0
        rows = [
            {
                "narrative_column": narrative_column,
                "narrative_present_count": narrative_present_count,
                "narrative_missing_count": narrative_missing_count,
                "narrative_present_rate": safe_ratio(narrative_present_count, row_count),
                "narrative_length_min": narrative_length_min if narrative_present_count else 0,
                "narrative_length_max": narrative_length_max if narrative_present_count else 0,
                "narrative_length_mean": mean_length,
                "raw_narratives_written": "False",
                "note": "Aggregate narrative availability only; no raw narrative text is written.",
            }
        ]

    write_csv(
        path,
        [
            "narrative_column",
            "narrative_present_count",
            "narrative_missing_count",
            "narrative_present_rate",
            "narrative_length_min",
            "narrative_length_max",
            "narrative_length_mean",
            "raw_narratives_written",
            "note",
        ],
        rows,
    )


def write_product_issue_summary(
    path: Path,
    product_counts: Counter[str],
    issue_counts: Counter[str],
    row_count: int,
) -> None:
    rows = []

    for product, count in product_counts.most_common(30):
        rows.append(
            {
                "summary_type": "product",
                "value": product,
                "count": count,
                "share": safe_ratio(count, row_count),
                "note": "Aggregate product distribution only.",
            }
        )

    for issue, count in issue_counts.most_common(30):
        rows.append(
            {
                "summary_type": "issue",
                "value": issue,
                "count": count,
                "share": safe_ratio(count, row_count),
                "note": "Aggregate issue distribution only.",
            }
        )

    if not rows:
        rows.append(
            {
                "summary_type": "",
                "value": "",
                "count": 0,
                "share": 0.0,
                "note": "No product or issue columns detected.",
            }
        )

    write_csv(path, ["summary_type", "value", "count", "share", "note"], rows)


def write_report(
    path: Path,
    input_filename: str,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    narrative_column: str | None,
    max_rows: int,
) -> None:
    lines = [
        "# Pilot 05 CFPB complaint dataset audit",
        "",
        f"Generated at UTC: {utc_now_iso()}",
        "",
        "## Scope",
        "",
        "This report is a sanitized aggregate audit of a local CFPB Consumer Complaint Database export.",
        "It does not include raw rows, raw complaint narratives, raw prompts, raw responses, secrets, or model/API outputs.",
        "",
        "## Source summary",
        "",
        f"- Source route: {source_route}",
        f"- Input filename only: {input_filename}",
        f"- Rows audited: {row_count}",
        f"- Columns detected: {column_count}",
        f"- Max rows setting: {max_rows}",
        f"- Target column detected: {target_column or 'not detected'}",
        f"- Narrative column detected: {narrative_column or 'not detected'}",
        "",
        "## Claim boundary",
        "",
        "This audit supports a recorded complaint-resolution outcome review simulation only.",
        "It does not claim company misconduct.",
        "It does not claim consumer harm prevalence.",
        "It does not claim financial safety.",
        "It does not claim legal safety.",
        "It does not claim real-world deployment proof.",
        "It does not claim provider ranking.",
        "",
        "## Safety status",
        "",
        f"- real_api_calls: {REAL_API_CALLS}",
        f"- model_calls: {MODEL_CALLS}",
        f"- dataset_downloads: {DATASET_DOWNLOADS}",
        f"- raw_response_inspection: {RAW_RESPONSE_INSPECTION}",
        "- raw_rows_written_to_reports: False",
        "- raw_narratives_written_to_reports: False",
        "- raw_data_committed: False",
        "",
        "## Output files",
        "",
        "- selected_source_manifest.json",
        "- dataset_audit_summary.csv",
        "- column_inventory.csv",
        "- target_distribution.csv",
        "- missingness_summary.csv",
        "- sensitive_field_inventory.csv",
        "- temporal_field_audit.csv",
        "- leakage_risk_notes.csv",
        "- narrative_availability_summary.csv",
        "- product_issue_summary.csv",
        "- pilot_05_cfpb_complaints_dataset_audit_report.md",
        "",
        "## Next step",
        "",
        "Use this audit to decide the exact sanitized evidence-packet construction.",
        "Do not run real LLM chains until provider/model/sample size/prompt family are explicitly approved.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def build_manifest(
    output_dir: Path,
    input_file: Path,
    input_filename: str,
    input_suffix: str,
    source_inside_zip: str | None,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    narrative_column: str | None,
    max_rows: int,
    allow_external_local_path: bool,
    compute_sha256: bool,
    input_sha256: str | None,
) -> dict[str, object]:
    manifest = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "status": "PASS",
        "scope": "Pilot 05 CFPB complaints local-only sanitized dataset audit",
        "source_policy": "local user-provided CFPB complaint export only; no internet download by this script",
        "source_route": source_route,
        "input_filename_only": input_filename,
        "input_suffix": input_suffix,
        "source_inside_zip": source_inside_zip,
        "input_path_is_under_data_raw_cfpb_complaints": is_under_path(input_file, DEFAULT_RAW_ROOT),
        "allow_external_local_path": allow_external_local_path,
        "compute_sha256": compute_sha256,
        "input_sha256": input_sha256,
        "row_counts": {
            "rows_audited": row_count,
            "columns_detected": column_count,
        },
        "target_column_detected": target_column,
        "narrative_column_detected": narrative_column,
        "max_rows": max_rows,
        "real_api_calls": REAL_API_CALLS,
        "model_calls": MODEL_CALLS,
        "dataset_downloads": DATASET_DOWNLOADS,
        "raw_response_inspection": RAW_RESPONSE_INSPECTION,
        "raw_data_committed": False,
        "raw_rows_written_to_reports": False,
        "raw_narratives_written_to_reports": False,
        "outputs": {
            "selected_source_manifest_json": str(output_dir / "selected_source_manifest.json"),
            "dataset_audit_summary_csv": str(output_dir / "dataset_audit_summary.csv"),
            "column_inventory_csv": str(output_dir / "column_inventory.csv"),
            "target_distribution_csv": str(output_dir / "target_distribution.csv"),
            "missingness_summary_csv": str(output_dir / "missingness_summary.csv"),
            "sensitive_field_inventory_csv": str(output_dir / "sensitive_field_inventory.csv"),
            "temporal_field_audit_csv": str(output_dir / "temporal_field_audit.csv"),
            "leakage_risk_notes_csv": str(output_dir / "leakage_risk_notes.csv"),
            "narrative_availability_summary_csv": str(output_dir / "narrative_availability_summary.csv"),
            "product_issue_summary_csv": str(output_dir / "product_issue_summary.csv"),
            "report_md": str(output_dir / "pilot_05_cfpb_complaints_dataset_audit_report.md"),
        },
        "safe_note": (
            "This is a sanitized local dataset audit only. "
            "It does not claim company misconduct. "
            "It does not claim consumer harm prevalence. "
            "It does not claim financial safety. "
            "It does not claim legal safety. "
            "It does not claim real-world deployment proof. "
            "It does not claim provider ranking."
        ),
    }

    manifest_path = output_dir / "selected_source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def audit_cfpb_complaints_file(
    input_file: Path,
    output_dir: Path,
    source_route: str,
    max_rows: int,
    allow_external_local_path: bool,
    compute_sha256: bool,
) -> dict[str, object]:
    validate_input_file_policy(input_file, allow_external_local_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    opened = open_dataset(input_file)
    try:
        columns, records = records_from_opened_dataset(opened)

        target_column = detect_target_column(columns)
        narrative_column = detect_narrative_column(columns)

        row_count = 0
        column_count = len(columns)

        missing_counts: Counter[str] = Counter()
        non_missing_counts: Counter[str] = Counter()
        target_counts: Counter[str] = Counter()
        product_counts: Counter[str] = Counter()
        issue_counts: Counter[str] = Counter()

        date_minmax: dict[str, tuple[str, str]] = {}

        narrative_present_count = 0
        narrative_missing_count = 0
        narrative_length_min = 0
        narrative_length_max = 0
        narrative_length_total = 0

        normalized_to_original = {normalize_column_name(column): column for column in columns}
        product_column = normalized_to_original.get("product")
        issue_column = normalized_to_original.get("issue")

        for record in records:
            row_count += 1

            for column in columns:
                value = record.get(column, "").strip()
                if value == "":
                    missing_counts[column] += 1
                else:
                    non_missing_counts[column] += 1

                normalized = normalize_column_name(column)
                if normalized in DATE_FIELD_CANDIDATES and value:
                    current_min, current_max = date_minmax.get(column, (value, value))
                    date_minmax[column] = (min(current_min, value), max(current_max, value))

            if target_column:
                value = record.get(target_column, "").strip() or "__MISSING__"
                target_counts[value] += 1

            if product_column:
                product_value = record.get(product_column, "").strip() or "__MISSING__"
                update_limited_counter(product_counts, product_value, limit=250)

            if issue_column:
                issue_value = record.get(issue_column, "").strip() or "__MISSING__"
                update_limited_counter(issue_counts, issue_value, limit=500)

            if narrative_column:
                narrative_value = record.get(narrative_column, "").strip()
                if narrative_value:
                    narrative_present_count += 1
                    length = len(narrative_value)
                    narrative_length_total += length
                    if narrative_length_min == 0 or length < narrative_length_min:
                        narrative_length_min = length
                    if length > narrative_length_max:
                        narrative_length_max = length
                else:
                    narrative_missing_count += 1

            if max_rows > 0 and row_count >= max_rows:
                break

        input_sha256 = sha256_file(input_file) if compute_sha256 else None

        write_dataset_audit_summary(
            output_dir / "dataset_audit_summary.csv",
            input_file=input_file,
            input_filename=opened.input_filename,
            input_suffix=opened.input_suffix,
            source_inside_zip=opened.source_inside_zip,
            source_route=source_route,
            row_count=row_count,
            column_count=column_count,
            target_column=target_column,
            narrative_column=narrative_column,
            max_rows=max_rows,
            allow_external_local_path=allow_external_local_path,
            input_sha256=input_sha256,
        )

        write_column_inventory(output_dir / "column_inventory.csv", columns)
        write_missingness_summary(output_dir / "missingness_summary.csv", columns, row_count, missing_counts, non_missing_counts)
        write_target_distribution(output_dir / "target_distribution.csv", target_column, target_counts, row_count)
        write_sensitive_field_inventory(output_dir / "sensitive_field_inventory.csv", columns)
        write_temporal_field_audit(output_dir / "temporal_field_audit.csv", columns, date_minmax)
        write_leakage_risk_notes(output_dir / "leakage_risk_notes.csv")
        write_narrative_audit(
            output_dir / "narrative_availability_summary.csv",
            narrative_column=narrative_column,
            narrative_present_count=narrative_present_count,
            narrative_missing_count=narrative_missing_count,
            narrative_length_min=narrative_length_min,
            narrative_length_max=narrative_length_max,
            narrative_length_total=narrative_length_total,
            row_count=row_count,
        )
        write_product_issue_summary(output_dir / "product_issue_summary.csv", product_counts, issue_counts, row_count)
        write_report(
            output_dir / "pilot_05_cfpb_complaints_dataset_audit_report.md",
            input_filename=opened.input_filename,
            source_route=source_route,
            row_count=row_count,
            column_count=column_count,
            target_column=target_column,
            narrative_column=narrative_column,
            max_rows=max_rows,
        )

        manifest = build_manifest(
            output_dir=output_dir,
            input_file=input_file,
            input_filename=opened.input_filename,
            input_suffix=opened.input_suffix,
            source_inside_zip=opened.source_inside_zip,
            source_route=source_route,
            row_count=row_count,
            column_count=column_count,
            target_column=target_column,
            narrative_column=narrative_column,
            max_rows=max_rows,
            allow_external_local_path=allow_external_local_path,
            compute_sha256=compute_sha256,
            input_sha256=input_sha256,
        )

        return manifest

    finally:
        if opened.handle is not None:
            opened.handle.close()


def positive_int_or_zero(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Value must be >= 0.")
    return parsed


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a sanitized local-only dataset audit for a CFPB Consumer Complaint Database export. "
            "This command makes no internet downloads and no model/API calls."
        )
    )

    parser.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help="Local CFPB complaint export path. By default this must be under data/raw/cfpb_complaints/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for sanitized audit files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--source-route",
        default=DEFAULT_SOURCE_ROUTE,
        help=f"Source route label. Default: {DEFAULT_SOURCE_ROUTE}",
    )
    parser.add_argument(
        "--max-rows",
        type=positive_int_or_zero,
        default=0,
        help="Maximum rows to audit. Use 0 for all rows. Default: 0.",
    )
    parser.add_argument(
        "--allow-external-local-path",
        action="store_true",
        help="Allow a local input file outside data/raw/cfpb_complaints/. Use only after explicit approval.",
    )
    parser.add_argument(
        "--compute-sha256",
        action="store_true",
        help="Compute SHA256 of the local input file. Can be slow for large files.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    manifest = audit_cfpb_complaints_file(
        input_file=args.input_file,
        output_dir=args.output_dir,
        source_route=args.source_route,
        max_rows=args.max_rows,
        allow_external_local_path=args.allow_external_local_path,
        compute_sha256=args.compute_sha256,
    )

    print("Pilot 05 CFPB complaint dataset audit generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"rows_audited: {manifest['row_counts']['rows_audited']}")
    print(f"columns_detected: {manifest['row_counts']['columns_detected']}")
    print(f"target_column_detected: {manifest['target_column_detected']}")
    print(f"narrative_column_detected: {manifest['narrative_column_detected']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"model_calls: {manifest['model_calls']}")
    print(f"dataset_downloads: {manifest['dataset_downloads']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    print("raw_rows_written_to_reports: False")
    print("raw_narratives_written_to_reports: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
