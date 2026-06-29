from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.pilot_03_llm_client import Pilot03LLMCallRecord, llm_call_record_to_dict


PILOT_03_LOG_SCHEMA_VERSION = "pilot_03_log_schema_v1"


def make_pilot_03_run_id(prefix: str = "pilot_03_dry_run") -> str:
    """Create a stable run id for Pilot 03 output folders."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}"


def _json_text(value: Any) -> str:
    """Serialise nested values for CSV-safe storage."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalise_call_record_for_csv(record: Pilot03LLMCallRecord) -> dict[str, Any]:
    """
    Convert one call record into a flat CSV row.

    Full prompt and raw response are preserved. Nested parsed response and metadata
    are stored as JSON strings.
    """
    raw = llm_call_record_to_dict(record)

    raw["parsed_response"] = _json_text(raw["parsed_response"])
    raw["metadata"] = _json_text(raw["metadata"])

    return raw


def _normalise_call_record_for_jsonl(record: Pilot03LLMCallRecord) -> dict[str, Any]:
    """Convert one call record into a JSONL-safe dictionary."""
    return llm_call_record_to_dict(record)


def summarise_raw_response_logs(records: list[Pilot03LLMCallRecord]) -> dict[str, Any]:
    """Return a compact summary of raw response logs."""
    stage_counts = Counter(record.stage for record in records)
    mode_counts = Counter(record.client_mode for record in records)
    provider_counts = Counter(record.provider for record in records)
    model_counts = Counter(record.model_name for record in records)
    dry_run_counts = Counter(str(record.dry_run) for record in records)

    error_records = [record for record in records if record.error]
    raw_response_lengths = [len(record.raw_response_text) for record in records]
    prompt_lengths = [len(record.prompt_text) for record in records]

    return {
        "schema_version": PILOT_03_LOG_SCHEMA_VERSION,
        "n_call_records": len(records),
        "stage_counts": dict(stage_counts),
        "mode_counts": dict(mode_counts),
        "provider_counts": dict(provider_counts),
        "model_counts": dict(model_counts),
        "dry_run_counts": dict(dry_run_counts),
        "error_count": len(error_records),
        "prompt_length_min": min(prompt_lengths) if prompt_lengths else 0,
        "prompt_length_max": max(prompt_lengths) if prompt_lengths else 0,
        "raw_response_length_min": min(raw_response_lengths) if raw_response_lengths else 0,
        "raw_response_length_max": max(raw_response_lengths) if raw_response_lengths else 0,
    }


def write_call_records_csv(records: list[Pilot03LLMCallRecord], output_path: str | Path) -> Path:
    """Write Pilot 03 call records to CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [_normalise_call_record_for_csv(record) for record in records]
    fieldnames = list(rows[0].keys()) if rows else [
        "call_id",
        "task_id",
        "task_type",
        "stage",
        "client_mode",
        "provider",
        "model_name",
        "dry_run",
        "prompt_version",
        "prompt_text",
        "raw_response_text",
        "parsed_response",
        "error",
        "metadata",
        "created_at_utc",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def write_call_records_jsonl(records: list[Pilot03LLMCallRecord], output_path: str | Path) -> Path:
    """Write Pilot 03 call records to JSONL."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(_json_text(_normalise_call_record_for_jsonl(record)) + "\n")

    return output_path


def write_summary_json(summary: dict[str, Any], output_path: str | Path) -> Path:
    """Write a summary dictionary to JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return output_path


def write_pilot_03_raw_response_logs(
    records: list[Pilot03LLMCallRecord],
    output_dir: str | Path = "results/pilot_03_dry_run",
    run_id: str | None = None,
    extra_summary: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """
    Write Pilot 03 raw response logs.

    This saves:
    - CSV call records for quick inspection
    - JSONL call records for faithful raw logging
    - JSON summary for reproducibility
    """
    run_id = make_pilot_03_run_id() if run_id is None else run_id
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    call_records_csv = write_call_records_csv(records, run_dir / "call_records.csv")
    raw_responses_jsonl = write_call_records_jsonl(records, run_dir / "raw_responses.jsonl")

    summary = summarise_raw_response_logs(records)
    summary["run_id"] = run_id
    summary["output_dir"] = str(run_dir)
    if extra_summary is not None:
        summary["extra_summary"] = extra_summary

    summary_json = write_summary_json(summary, run_dir / "summary.json")

    return {
        "run_dir": run_dir,
        "call_records_csv": call_records_csv,
        "raw_responses_jsonl": raw_responses_jsonl,
        "summary_json": summary_json,
    }


def read_jsonl_records(input_path: str | Path) -> list[dict[str, Any]]:
    """Read JSONL records back from disk for validation."""
    input_path = Path(input_path)
    records: list[dict[str, Any]] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected JSON object in {input_path}, got {type(parsed)}")
            records.append(parsed)

    return records


if __name__ == "__main__":
    from experiments.pilot_03_dry_run_runner import flatten_call_records, run_pilot_03_dry_run, summarise_runner_results

    results = run_pilot_03_dry_run(n_tasks=2)
    call_records = flatten_call_records(results)
    runner_summary = summarise_runner_results(results)

    paths = write_pilot_03_raw_response_logs(
        records=call_records,
        run_id="pilot_03_logging_smoke_test",
        extra_summary=runner_summary,
    )

    print("Pilot 03 logging smoke test")
    print("===========================")
    print(summarise_raw_response_logs(call_records))
    for key, path in paths.items():
        print(f"{key}: {path}")

    loaded_records = read_jsonl_records(paths["raw_responses_jsonl"])
    print(f"loaded_jsonl_records: {len(loaded_records)}")