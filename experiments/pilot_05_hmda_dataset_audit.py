from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, TextIO


SCRIPT_VERSION = "pilot_05_hmda_dataset_audit_v1"

DEFAULT_OUTPUT_DIR = Path("reports") / "pilot_05_hmda_dataset_audit"
DEFAULT_RAW_ROOT = Path("data") / "raw" / "hmda"

DEFAULT_SOURCE_YEAR = "2025"
DEFAULT_SOURCE_ROUTE = "FFIEC HMDA Data Browser filtered 2025 sample"

REAL_API_CALLS = 0
RAW_RESPONSE_INSPECTION = False
MODEL_CALLS = 0
DATASET_DOWNLOADS = 0


ACTION_TAKEN_LABELS = {
    "1": "loan_originated",
    "2": "application_approved_but_not_accepted",
    "3": "application_denied",
    "4": "application_withdrawn_by_applicant",
    "5": "file_closed_for_incompleteness",
    "6": "purchased_loan",
    "7": "preapproval_request_denied",
    "8": "preapproval_request_approved_but_not_accepted",
}


SENSITIVE_FIELD_KEYWORDS = {
    "ethnicity": "Applicant/co-applicant ethnicity is sensitive and claim-risk relevant.",
    "race": "Applicant/co-applicant race is sensitive and claim-risk relevant.",
    "sex": "Applicant/co-applicant sex is sensitive and claim-risk relevant.",
    "age": "Applicant/co-applicant age is sensitive and claim-risk relevant.",
    "tract": "Census tract/geography can create proxy or re-identification risk.",
    "county": "County/geography can create proxy or re-identification risk.",
    "state": "State/geography is lower-risk than tract but still context-sensitive.",
    "msa": "MSA/geography can create proxy or context risk.",
    "lei": "Institution identifier can create lender-specific interpretation risk.",
    "denial_reason": "Denial reason can create false legal/compliance interpretations.",
    "credit_score": "Credit-score-related fields are sensitive and high-claim-risk.",
    "debt_to_income": "Debt-to-income is financial evidence and must not be overinterpreted.",
    "income": "Income is financial evidence and must not be overinterpreted.",
}


CANDIDATE_NON_SENSITIVE_FIELDS = {
    "activity_year",
    "loan_type",
    "loan_purpose",
    "loan_amount",
    "loan_amount_000s",
    "lien_status",
    "occupancy_type",
    "construction_method",
    "property_value",
    "total_units",
    "loan_term",
    "interest_rate",
    "rate_spread",
    "loan_to_value_ratio",
    "combined_loan_to_value_ratio",
    "income",
    "debt_to_income_ratio",
    "action_taken",
}


TEMPORAL_FIELD_CANDIDATES = {
    "activity_year",
    "year",
    "calendar_year",
    "submission_year",
}


TARGET_FIELD_CANDIDATES = [
    "action_taken",
    "action_taken_type",
    "action_taken_code",
    "action",
    "loan_action",
]


LEAKAGE_RISK_RULES = [
    {
        "field_group": "action_taken / recorded outcome",
        "risk_level": "HIGH",
        "notes": (
            "This is the candidate target/recorded outcome. It must not be included "
            "inside decision evidence packets when predicting or reconstructing the target."
        ),
        "default_decision": "Use as target only, not as input evidence.",
    },
    {
        "field_group": "denial_reason fields",
        "risk_level": "HIGH",
        "notes": (
            "Denial reasons can directly explain denied outcomes and may leak outcome "
            "information or create false legal/compliance interpretations."
        ),
        "default_decision": "Exclude from first decision evidence packet; audit separately.",
    },
    {
        "field_group": "applicant demographic fields",
        "risk_level": "HIGH",
        "notes": (
            "Race, ethnicity, sex, and age are sensitive or claim-risk fields. Including "
            "them in prompts could create ethical and claim-boundary risk."
        ),
        "default_decision": "Use for sensitive-field inventory only unless explicitly approved.",
    },
    {
        "field_group": "fine geography fields",
        "risk_level": "MEDIUM_HIGH",
        "notes": (
            "Census tract and detailed geography may act as proxies and may increase "
            "re-identification or fairness-risk concerns."
        ),
        "default_decision": "Prefer coarse audit notes; avoid raw geography in committed packets.",
    },
    {
        "field_group": "institution identifiers",
        "risk_level": "MEDIUM",
        "notes": (
            "Institution identifiers can create institution-specific interpretation and "
            "sampling-bias risk."
        ),
        "default_decision": "Do not use for public provider/lender ranking or superiority claims.",
    },
]


@dataclass(frozen=True)
class OpenedHmdaFile:
    input_file: Path
    input_filename: str
    input_suffix: str
    source_inside_zip: str | None
    handle: TextIO


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_column_name(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


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
            "Input file must be under data/raw/hmda/ by default. "
            "Move the local HMDA raw file there, or rerun with "
            "--allow-external-local-path after explicit approval."
        )

    suffix = input_file.suffix.lower()
    allowed_suffixes = {".csv", ".zip", ".txt"}
    if suffix not in allowed_suffixes:
        raise ValueError(
            f"Unsupported input suffix '{suffix}'. Supported local formats: "
            ".csv, .txt, .zip containing one CSV/TXT file."
        )


def open_hmda_file(input_file: Path) -> OpenedHmdaFile:
    suffix = input_file.suffix.lower()

    if suffix in {".csv", ".txt"}:
        handle = input_file.open("r", encoding="utf-8-sig", newline="")
        return OpenedHmdaFile(
            input_file=input_file,
            input_filename=input_file.name,
            input_suffix=suffix,
            source_inside_zip=None,
            handle=handle,
        )

    if suffix == ".zip":
        archive = zipfile.ZipFile(input_file)
        candidates = [
            name for name in archive.namelist()
            if not name.endswith("/") and Path(name).suffix.lower() in {".csv", ".txt"}
        ]

        if len(candidates) != 1:
            archive.close()
            raise ValueError(
                "ZIP input must contain exactly one CSV/TXT file. "
                f"Found {len(candidates)} candidates."
            )

        inner_name = candidates[0]
        binary_handle = archive.open(inner_name, "r")
        text_handle = TextIOWrapperWithClose(binary_handle, archive)

        return OpenedHmdaFile(
            input_file=input_file,
            input_filename=input_file.name,
            input_suffix=suffix,
            source_inside_zip=inner_name,
            handle=text_handle,
        )

    raise ValueError(f"Unsupported input file type: {suffix}")


class TextIOWrapperWithClose:
    """
    Minimal UTF-8 text wrapper for a ZIP member that also closes the archive.

    This avoids adding external dependencies and keeps the audit local-only.
    """

    def __init__(self, binary_handle, archive: zipfile.ZipFile):
        import io

        self._binary_handle = binary_handle
        self._archive = archive
        self._wrapper = io.TextIOWrapper(binary_handle, encoding="utf-8-sig", newline="")

    def __iter__(self):
        return iter(self._wrapper)

    def read(self, *args, **kwargs):
        return self._wrapper.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._wrapper.readline(*args, **kwargs)

    def close(self) -> None:
        self._wrapper.close()
        self._archive.close()


def dialect_for_sample(handle: TextIO) -> csv.Dialect:
    sample = handle.read(8192)
    if hasattr(handle, "seek"):
        handle.seek(0)

    if not sample:
        raise ValueError("Input file is empty.")

    try:
        return csv.Sniffer().sniff(sample, delimiters=",|\t;")
    except csv.Error:
        return csv.excel


def detect_target_column(columns: list[str]) -> str | None:
    normalized = {normalize_column_name(column): column for column in columns}
    for candidate in TARGET_FIELD_CANDIDATES:
        if candidate in normalized:
            return normalized[candidate]
    return None


def infer_field_group(column_name: str) -> str:
    normalized = normalize_column_name(column_name)

    if "denial_reason" in normalized:
        return "denial_reason"
    if any(token in normalized for token in ["ethnicity", "race", "sex", "age"]):
        return "sensitive_demographic"
    if any(token in normalized for token in ["tract", "county", "state", "msa"]):
        return "geography"
    if any(token in normalized for token in ["income", "debt_to_income", "credit_score"]):
        return "financial_or_credit_context"
    if normalized in TARGET_FIELD_CANDIDATES:
        return "target_or_outcome"
    if normalized in CANDIDATE_NON_SENSITIVE_FIELDS:
        return "candidate_non_sensitive_evidence"
    if normalized in TEMPORAL_FIELD_CANDIDATES:
        return "temporal"
    return "other"


def sensitive_reason(column_name: str) -> str | None:
    normalized = normalize_column_name(column_name)
    reasons = []

    for keyword, reason in SENSITIVE_FIELD_KEYWORDS.items():
        if keyword in normalized:
            reasons.append(reason)

    if not reasons:
        return None

    return " ".join(reasons)


def action_label(value: str) -> str:
    stripped = value.strip()
    return ACTION_TAKEN_LABELS.get(stripped, "unmapped_or_nonstandard")


def update_unique_limited(
    unique_values: dict[str, set[str]],
    column_name: str,
    value: str,
    limit: int = 1000,
) -> None:
    if column_name not in unique_values:
        unique_values[column_name] = set()

    if len(unique_values[column_name]) < limit:
        unique_values[column_name].add(value)


def iter_rows(opened: OpenedHmdaFile) -> tuple[list[str], Iterator[dict[str, str]]]:
    dialect = dialect_for_sample(opened.handle)
    reader = csv.DictReader(opened.handle, dialect=dialect)

    if not reader.fieldnames:
        raise ValueError("Input file has no header row.")

    columns = [column.strip() for column in reader.fieldnames]

    def row_iterator() -> Iterator[dict[str, str]]:
        for row in reader:
            yield {key.strip(): "" if value is None else str(value).strip() for key, value in row.items()}

    return columns, row_iterator()


def audit_hmda_file(
    input_file: Path,
    output_dir: Path,
    source_year: str,
    source_route: str,
    max_rows: int,
    allow_external_local_path: bool,
    compute_sha256: bool,
) -> dict[str, object]:
    validate_input_file_policy(input_file, allow_external_local_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    opened = open_hmda_file(input_file)
    try:
        columns, rows = iter_rows(opened)

        row_count = 0
        column_count = len(columns)
        missing_counts: Counter[str] = Counter()
        non_missing_counts: Counter[str] = Counter()
        target_counts: Counter[str] = Counter()
        temporal_unique_values: dict[str, set[str]] = {}
        target_column = detect_target_column(columns)

        temporal_columns = [
            column for column in columns
            if normalize_column_name(column) in TEMPORAL_FIELD_CANDIDATES
        ]

        for row in rows:
            row_count += 1

            for column in columns:
                value = row.get(column, "").strip()
                if value == "":
                    missing_counts[column] += 1
                else:
                    non_missing_counts[column] += 1

                if column in temporal_columns and value != "":
                    update_unique_limited(temporal_unique_values, column, value)

            if target_column:
                target_value = row.get(target_column, "").strip()
                if target_value == "":
                    target_value = "__MISSING__"
                target_counts[target_value] += 1

            if max_rows > 0 and row_count >= max_rows:
                break

        input_sha256 = None
        if compute_sha256:
            input_sha256 = sha256_file(input_file)

        write_outputs(
            output_dir=output_dir,
            input_file=input_file,
            input_filename=opened.input_filename,
            input_suffix=opened.input_suffix,
            source_inside_zip=opened.source_inside_zip,
            source_year=source_year,
            source_route=source_route,
            row_count=row_count,
            column_count=column_count,
            columns=columns,
            missing_counts=missing_counts,
            non_missing_counts=non_missing_counts,
            target_column=target_column,
            target_counts=target_counts,
            temporal_columns=temporal_columns,
            temporal_unique_values=temporal_unique_values,
            max_rows=max_rows,
            allow_external_local_path=allow_external_local_path,
            input_sha256=input_sha256,
        )

        manifest = build_manifest(
            output_dir=output_dir,
            input_file=input_file,
            input_filename=opened.input_filename,
            input_suffix=opened.input_suffix,
            source_inside_zip=opened.source_inside_zip,
            source_year=source_year,
            source_route=source_route,
            row_count=row_count,
            column_count=column_count,
            target_column=target_column,
            max_rows=max_rows,
            allow_external_local_path=allow_external_local_path,
            compute_sha256=compute_sha256,
            input_sha256=input_sha256,
        )

        return manifest

    finally:
        opened.handle.close()


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


def write_outputs(
    output_dir: Path,
    input_file: Path,
    input_filename: str,
    input_suffix: str,
    source_inside_zip: str | None,
    source_year: str,
    source_route: str,
    row_count: int,
    column_count: int,
    columns: list[str],
    missing_counts: Counter[str],
    non_missing_counts: Counter[str],
    target_column: str | None,
    target_counts: Counter[str],
    temporal_columns: list[str],
    temporal_unique_values: dict[str, set[str]],
    max_rows: int,
    allow_external_local_path: bool,
    input_sha256: str | None,
) -> None:
    write_dataset_audit_summary(
        output_dir / "dataset_audit_summary.csv",
        input_file=input_file,
        input_filename=input_filename,
        input_suffix=input_suffix,
        source_inside_zip=source_inside_zip,
        source_year=source_year,
        source_route=source_route,
        row_count=row_count,
        column_count=column_count,
        target_column=target_column,
        max_rows=max_rows,
        allow_external_local_path=allow_external_local_path,
        input_sha256=input_sha256,
    )

    write_column_inventory(output_dir / "column_inventory.csv", columns)
    write_missingness_summary(output_dir / "missingness_summary.csv", columns, row_count, missing_counts, non_missing_counts)
    write_target_distribution(output_dir / "target_distribution.csv", target_column, target_counts, row_count)
    write_sensitive_field_inventory(output_dir / "sensitive_field_inventory.csv", columns)
    write_temporal_field_audit(output_dir / "temporal_field_audit.csv", columns, temporal_columns, temporal_unique_values)
    write_leakage_risk_notes(output_dir / "leakage_risk_notes.csv")
    write_report(
        output_dir / "pilot_05_hmda_dataset_audit_report.md",
        input_filename=input_filename,
        source_year=source_year,
        source_route=source_route,
        row_count=row_count,
        column_count=column_count,
        target_column=target_column,
        max_rows=max_rows,
        temporal_columns=temporal_columns,
    )


def write_dataset_audit_summary(
    path: Path,
    input_file: Path,
    input_filename: str,
    input_suffix: str,
    source_inside_zip: str | None,
    source_year: str,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    max_rows: int,
    allow_external_local_path: bool,
    input_sha256: str | None,
) -> None:
    rows = [
        {"metric": "script_version", "value": SCRIPT_VERSION},
        {"metric": "created_at_utc", "value": utc_now_iso()},
        {"metric": "source_year", "value": source_year},
        {"metric": "source_route", "value": source_route},
        {"metric": "input_filename_only", "value": input_filename},
        {"metric": "input_suffix", "value": input_suffix},
        {"metric": "source_inside_zip", "value": source_inside_zip or ""},
        {"metric": "input_path_is_under_data_raw_hmda", "value": str(is_under_path(input_file, DEFAULT_RAW_ROOT))},
        {"metric": "allow_external_local_path", "value": str(allow_external_local_path)},
        {"metric": "input_sha256", "value": input_sha256 or "not_computed"},
        {"metric": "row_count_audited", "value": str(row_count)},
        {"metric": "column_count", "value": str(column_count)},
        {"metric": "target_column_detected", "value": target_column or ""},
        {"metric": "max_rows", "value": str(max_rows)},
        {"metric": "real_api_calls", "value": str(REAL_API_CALLS)},
        {"metric": "model_calls", "value": str(MODEL_CALLS)},
        {"metric": "dataset_downloads", "value": str(DATASET_DOWNLOADS)},
        {"metric": "raw_response_inspection", "value": str(RAW_RESPONSE_INSPECTION)},
        {"metric": "raw_data_committed", "value": "False"},
        {"metric": "raw_rows_written_to_reports", "value": "False"},
        {"metric": "claim_boundary", "value": "recorded outcome review simulation only"},
    ]

    write_csv(path, ["metric", "value"], rows)


def write_column_inventory(path: Path, columns: list[str]) -> None:
    rows = []
    for index, column in enumerate(columns, start=1):
        normalized = normalize_column_name(column)
        reason = sensitive_reason(column)
        rows.append(
            {
                "ordinal": index,
                "column_name": column,
                "normalized_column_name": normalized,
                "inferred_group": infer_field_group(column),
                "is_sensitive_or_claim_risk": str(reason is not None),
                "sensitive_or_claim_risk_reason": reason or "",
                "candidate_non_sensitive_evidence": str(normalized in CANDIDATE_NON_SENSITIVE_FIELDS and reason is None),
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
            "sensitive_or_claim_risk_reason",
            "candidate_non_sensitive_evidence",
            "default_handling",
        ],
        rows,
    )


def default_handling_for_column(column: str) -> str:
    normalized = normalize_column_name(column)

    if normalized in TARGET_FIELD_CANDIDATES:
        return "target_only_exclude_from_decision_evidence"
    if "denial_reason" in normalized:
        return "exclude_from_first_decision_packet_audit_separately"
    if sensitive_reason(column):
        return "sensitive_inventory_only_unless_explicitly_approved"
    if normalized in CANDIDATE_NON_SENSITIVE_FIELDS:
        return "candidate_for_sanitized_evidence_packet"
    return "review_before_use"


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
                "mapped_label": "",
                "count": 0,
                "share": 0.0,
                "note": "No HMDA action/outcome target column detected.",
            }
        )
    else:
        for value, count in target_counts.most_common():
            rows.append(
                {
                    "target_column": target_column,
                    "target_value": value,
                    "mapped_label": action_label(value),
                    "count": int(count),
                    "share": safe_ratio(int(count), row_count),
                    "note": "Recorded HMDA outcome distribution; not a real-world correctness label.",
                }
            )

    write_csv(path, ["target_column", "target_value", "mapped_label", "count", "share", "note"], rows)


def write_sensitive_field_inventory(path: Path, columns: list[str]) -> None:
    rows = []

    for column in columns:
        reason = sensitive_reason(column)
        if reason:
            rows.append(
                {
                    "column_name": column,
                    "normalized_column_name": normalize_column_name(column),
                    "reason": reason,
                    "default_handling": default_handling_for_column(column),
                }
            )

    if not rows:
        rows.append(
            {
                "column_name": "",
                "normalized_column_name": "",
                "reason": "No sensitive/claim-risk fields detected by keyword scan.",
                "default_handling": "manual_review_still_required",
            }
        )

    write_csv(path, ["column_name", "normalized_column_name", "reason", "default_handling"], rows)


def write_temporal_field_audit(
    path: Path,
    columns: list[str],
    temporal_columns: list[str],
    temporal_unique_values: dict[str, set[str]],
) -> None:
    rows = []

    detected = set(temporal_columns)
    for column in columns:
        normalized = normalize_column_name(column)
        if normalized in TEMPORAL_FIELD_CANDIDATES:
            values = sorted(temporal_unique_values.get(column, set()))
            rows.append(
                {
                    "column_name": column,
                    "normalized_column_name": normalized,
                    "detected": "True",
                    "unique_values_count_limited": len(values),
                    "min_value": values[0] if values else "",
                    "max_value": values[-1] if values else "",
                    "note": "Temporal suitability requires schema-year caution and manual review.",
                }
            )

    if not detected:
        rows.append(
            {
                "column_name": "",
                "normalized_column_name": "",
                "detected": "False",
                "unique_values_count_limited": 0,
                "min_value": "",
                "max_value": "",
                "note": "No temporal field detected by candidate-name scan.",
            }
        )

    write_csv(
        path,
        [
            "column_name",
            "normalized_column_name",
            "detected",
            "unique_values_count_limited",
            "min_value",
            "max_value",
            "note",
        ],
        rows,
    )


def write_leakage_risk_notes(path: Path) -> None:
    write_csv(
        path,
        ["field_group", "risk_level", "notes", "default_decision"],
        LEAKAGE_RISK_RULES,
    )


def write_report(
    path: Path,
    input_filename: str,
    source_year: str,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    max_rows: int,
    temporal_columns: list[str],
) -> None:
    lines = [
        "# Pilot 05 HMDA dataset audit",
        "",
        f"Generated at UTC: {utc_now_iso()}",
        "",
        "## Scope",
        "",
        "This report is a sanitized aggregate audit of a local HMDA filtered export.",
        "It does not include raw rows, raw prompts, raw responses, secrets, or model/API outputs.",
        "",
        "## Source summary",
        "",
        f"- Source route: {source_route}",
        f"- Source year: {source_year}",
        f"- Input filename only: {input_filename}",
        f"- Rows audited: {row_count}",
        f"- Columns detected: {column_count}",
        f"- Max rows setting: {max_rows}",
        f"- Target column detected: {target_column or 'not detected'}",
        f"- Temporal columns detected: {', '.join(temporal_columns) if temporal_columns else 'none detected'}",
        "",
        "## Claim boundary",
        "",
        "This audit supports a recorded-outcome review simulation only.",
        "It does not claim real lending decision validity.",
        "It does not claim financial safety.",
        "It does not claim legal safety.",
        "It does not claim lending regulation compliance.",
        "It does not claim real-world deployment proof.",
        "",
        "## Safety status",
        "",
        f"- real_api_calls: {REAL_API_CALLS}",
        f"- model_calls: {MODEL_CALLS}",
        f"- dataset_downloads: {DATASET_DOWNLOADS}",
        f"- raw_response_inspection: {RAW_RESPONSE_INSPECTION}",
        "- raw_rows_written_to_reports: False",
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
        "- pilot_05_hmda_dataset_audit_report.md",
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
    source_year: str,
    source_route: str,
    row_count: int,
    column_count: int,
    target_column: str | None,
    max_rows: int,
    allow_external_local_path: bool,
    compute_sha256: bool,
    input_sha256: str | None,
) -> dict[str, object]:
    manifest = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "status": "PASS",
        "scope": "Pilot 05 HMDA local-only sanitized dataset audit",
        "source_policy": "local user-provided filtered HMDA export only; no internet download by this script",
        "source_year": source_year,
        "source_route": source_route,
        "input_filename_only": input_filename,
        "input_suffix": input_suffix,
        "source_inside_zip": source_inside_zip,
        "input_path_is_under_data_raw_hmda": is_under_path(input_file, DEFAULT_RAW_ROOT),
        "allow_external_local_path": allow_external_local_path,
        "compute_sha256": compute_sha256,
        "input_sha256": input_sha256,
        "row_counts": {
            "rows_audited": row_count,
            "columns_detected": column_count,
        },
        "target_column_detected": target_column,
        "max_rows": max_rows,
        "real_api_calls": REAL_API_CALLS,
        "model_calls": MODEL_CALLS,
        "dataset_downloads": DATASET_DOWNLOADS,
        "raw_response_inspection": RAW_RESPONSE_INSPECTION,
        "raw_data_committed": False,
        "raw_rows_written_to_reports": False,
        "outputs": {
            "selected_source_manifest_json": str(output_dir / "selected_source_manifest.json"),
            "dataset_audit_summary_csv": str(output_dir / "dataset_audit_summary.csv"),
            "column_inventory_csv": str(output_dir / "column_inventory.csv"),
            "target_distribution_csv": str(output_dir / "target_distribution.csv"),
            "missingness_summary_csv": str(output_dir / "missingness_summary.csv"),
            "sensitive_field_inventory_csv": str(output_dir / "sensitive_field_inventory.csv"),
            "temporal_field_audit_csv": str(output_dir / "temporal_field_audit.csv"),
            "leakage_risk_notes_csv": str(output_dir / "leakage_risk_notes.csv"),
            "report_md": str(output_dir / "pilot_05_hmda_dataset_audit_report.md"),
        },
        "safe_note": (
            "This is a sanitized local dataset audit only. "
            "It does not provide real-world deployment proof. "
            "It does not claim financial safety. "
            "It does not claim legal safety. "
            "It does not claim lending regulation compliance."
        ),
    }

    manifest_path = output_dir / "selected_source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def positive_int_or_zero(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Value must be >= 0.")
    return parsed


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a sanitized local-only dataset audit for a filtered HMDA export. "
            "This command makes no internet downloads and no model/API calls."
        )
    )

    parser.add_argument(
        "--input-file",
        type=Path,
        required=True,
        help=(
            "Local HMDA filtered export path. By default this must be under "
            "data/raw/hmda/."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for sanitized audit files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--source-year",
        default=DEFAULT_SOURCE_YEAR,
        help=f"HMDA source year label. Default: {DEFAULT_SOURCE_YEAR}",
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
        help=(
            "Allow a local input file outside data/raw/hmda/. Use only after explicit "
            "approval. No download is performed."
        ),
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

    manifest = audit_hmda_file(
        input_file=args.input_file,
        output_dir=args.output_dir,
        source_year=args.source_year,
        source_route=args.source_route,
        max_rows=args.max_rows,
        allow_external_local_path=args.allow_external_local_path,
        compute_sha256=args.compute_sha256,
    )

    print("Pilot 05 HMDA dataset audit generated.")
    print(f"output_dir: {args.output_dir}")
    print(f"status: {manifest['status']}")
    print(f"rows_audited: {manifest['row_counts']['rows_audited']}")
    print(f"columns_detected: {manifest['row_counts']['columns_detected']}")
    print(f"target_column_detected: {manifest['target_column_detected']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"model_calls: {manifest['model_calls']}")
    print(f"dataset_downloads: {manifest['dataset_downloads']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")
    print("raw_rows_written_to_reports: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

