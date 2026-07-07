from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


OUTPUT_DIR = Path("reports/cross_pilot_evidence_state_reliability")
REPORT_MD = OUTPUT_DIR / "cross_pilot_report.md"
FRAMEWORK_SUMMARY_CSV = OUTPUT_DIR / "cross_pilot_framework_summary.csv"
VALIDATION_SUMMARY_CSV = OUTPUT_DIR / "pipeline_validation_summary.csv"
CONDITION_ALIGNMENT_CSV = OUTPUT_DIR / "condition_metric_alignment.csv"
METRIC_INVENTORY_CSV = OUTPUT_DIR / "metric_inventory.csv"
MANIFEST_JSON = OUTPUT_DIR / "manifest.json"

PILOT_03_NO_CALL_MANIFEST = Path("reports/pilot_03_no_call_pipeline/manifest.json")
PILOT_03_COMPARISON_VALIDATION_MANIFEST = Path("reports/pilot_03_comparison_validation/manifest.json")
PILOT_03_MASTER_VALIDATION_SCRIPT = Path("experiments/pilot_03_validate_all_committed_outputs.py")
PILOT_03_CONDITION_METRICS = Path("reports/pilot_03_reliability_cascade_metrics/model_condition_cascade_metrics.csv")
PILOT_03_DELTA_METRICS = Path("reports/pilot_03_reliability_cascade_metrics/evidence_condition_delta_metrics.csv")
PILOT_03_ROBUSTNESS_MANIFEST = Path("reports/pilot_03_robustness_sensitivity/manifest.json")

PILOT_04_NO_CALL_MANIFEST = Path("reports/pilot_04_no_call_pipeline/manifest.json")
PILOT_04_VALIDATION_MANIFEST = Path("reports/pilot_04_validation/manifest.json")
PILOT_04_CONDITION_METRICS = Path("reports/pilot_04_reliability_cascade_metrics/condition_reliability_cascade_metrics.csv")
PILOT_04_DELTA_METRICS = Path("reports/pilot_04_reliability_cascade_metrics/evidence_condition_delta_metrics.csv")
PILOT_04_ROBUSTNESS_MANIFEST = Path("reports/pilot_04_robustness_sensitivity/manifest.json")

RISKY_PUBLIC_WORDING = [
    "Q1",
    "journal-level",
    "groundbreaking",
    "proven",
    "universal",
    "real-world deployment proof",
    "provider ranking",
    "general Claude reliability",
    "general GLM reliability",
    "live deployment validity",
    "broad LLM reliability",
    "general model superiority",
    "financial safety",
    "legal safety",
    "medical safety",
    "lending regulation",
    "compliance with lending regulation",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_existing_created_at(path: Path) -> str:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            existing_created_at = existing.get("created_at_utc")
            if existing_created_at:
                return str(existing_created_at)
        except Exception:
            pass

    return datetime.now(UTC).isoformat(timespec="seconds")


def _safe_get(mapping: dict[str, Any], key: str, default: Any = "") -> Any:
    return mapping.get(key, default)


def _safe_bool_default_false(mapping: dict[str, Any], key: str) -> bool:
    value = mapping.get(key, False)
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _to_float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean_available(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return round(mean(clean), 6)


def _find_first_column(columns: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _summarise_numeric_columns(rows: list[dict[str, str]], source_name: str) -> list[dict[str, Any]]:
    if not rows:
        return []

    columns = list(rows[0].keys())
    inventory_rows: list[dict[str, Any]] = []

    for column in columns:
        numeric_values = [_to_float_or_none(row.get(column)) for row in rows]
        numeric_values_clean = [value for value in numeric_values if value is not None]

        if numeric_values_clean:
            inventory_rows.append(
                {
                    "source": source_name,
                    "column_name": column,
                    "n_rows": len(rows),
                    "n_numeric_values": len(numeric_values_clean),
                    "mean_numeric_value": round(mean(numeric_values_clean), 6),
                    "min_numeric_value": round(min(numeric_values_clean), 6),
                    "max_numeric_value": round(max(numeric_values_clean), 6),
                    "metric_inventory_only": True,
                    "real_api_calls": 0,
                }
            )
        else:
            inventory_rows.append(
                {
                    "source": source_name,
                    "column_name": column,
                    "n_rows": len(rows),
                    "n_numeric_values": 0,
                    "mean_numeric_value": "",
                    "min_numeric_value": "",
                    "max_numeric_value": "",
                    "metric_inventory_only": True,
                    "real_api_calls": 0,
                }
            )

    return inventory_rows


def _summarise_pilot_03_metrics() -> dict[str, Any]:
    rows = _read_csv(PILOT_03_CONDITION_METRICS)
    columns = set(rows[0].keys()) if rows else set()

    condition_col = _find_first_column(
        columns,
        ["condition", "evidence_condition", "evidence_state", "evidence_condition_name"],
    )
    structural_col = _find_first_column(
        columns,
        ["schema_valid_rate", "parse_success_rate", "parser_valid_rate", "structural_validity_rate"],
    )
    reliability_col = _find_first_column(
        columns,
        [
            "reliability_cascade_index",
            "decision_match_rate",
            "final_correct_rate",
            "decision_accuracy",
            "final_accuracy",
        ],
    )
    audit_col = _find_first_column(columns, ["audit_pass_rate", "audit_agreement_rate", "audit_valid_rate"])
    escalation_col = _find_first_column(columns, ["escalation_rate", "requires_human_review_rate"])

    condition_values = sorted({row.get(condition_col, "not_detected") for row in rows}) if condition_col else []

    return {
        "pilot_id": "pilot_03",
        "domain": "synthetic administrative approval",
        "evidence_package_role": "locked first real-LLM evidence package",
        "condition_metric_rows": len(rows),
        "condition_column_detected": condition_col or "",
        "condition_values_detected": condition_values,
        "structural_metric_column": structural_col or "",
        "reliability_metric_column": reliability_col or "",
        "audit_metric_column": audit_col or "",
        "escalation_metric_column": escalation_col or "",
        "mean_structural_metric": _mean_available([_to_float_or_none(row.get(structural_col)) for row in rows])
        if structural_col
        else "",
        "mean_reliability_metric": _mean_available([_to_float_or_none(row.get(reliability_col)) for row in rows])
        if reliability_col
        else "",
        "mean_audit_metric": _mean_available([_to_float_or_none(row.get(audit_col)) for row in rows])
        if audit_col
        else "",
        "mean_escalation_metric": _mean_available([_to_float_or_none(row.get(escalation_col)) for row in rows])
        if escalation_col
        else "",
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }


def _summarise_pilot_04_metrics() -> dict[str, Any]:
    rows = _read_csv(PILOT_04_CONDITION_METRICS)
    condition_values = sorted({row["condition"] for row in rows})

    return {
        "pilot_id": "pilot_04",
        "domain": "synthetic loan-risk decision support",
        "evidence_package_role": "second controlled deterministic no-call domain",
        "condition_metric_rows": len(rows),
        "condition_column_detected": "condition",
        "condition_values_detected": condition_values,
        "structural_metric_column": "structural_validity_rate",
        "reliability_metric_column": "reliability_cascade_index",
        "audit_metric_column": "audit_pass_rate",
        "escalation_metric_column": "escalation_rate",
        "mean_structural_metric": _mean_available([_to_float_or_none(row["structural_validity_rate"]) for row in rows]),
        "mean_reliability_metric": _mean_available([_to_float_or_none(row["reliability_cascade_index"]) for row in rows]),
        "mean_audit_metric": _mean_available([_to_float_or_none(row["audit_pass_rate"]) for row in rows]),
        "mean_escalation_metric": _mean_available([_to_float_or_none(row["escalation_rate"]) for row in rows]),
        "real_api_calls": 0,
        "raw_response_inspection": False,
    }


def _framework_summary_rows(p03: dict[str, Any], p04: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "pilot_id": "pilot_03",
            "domain": p03["domain"],
            "evidence_package_role": p03["evidence_package_role"],
            "pipeline_type": "real-LLM evidence package with no-call committed-output validation",
            "domain_status": "locked",
            "condition_metric_rows": p03["condition_metric_rows"],
            "condition_values_detected": json.dumps(p03["condition_values_detected"], ensure_ascii=False),
            "framework_comparison_level": "evidence-state measurement layer",
            "claim_boundary": "controlled synthetic domain only",
            "real_api_calls_in_cross_pilot_generation": 0,
            "raw_response_inspection": False,
        },
        {
            "pilot_id": "pilot_04",
            "domain": p04["domain"],
            "evidence_package_role": p04["evidence_package_role"],
            "pipeline_type": "deterministic no-call synthetic evidence package",
            "domain_status": "new second domain",
            "condition_metric_rows": p04["condition_metric_rows"],
            "condition_values_detected": json.dumps(p04["condition_values_detected"], ensure_ascii=False),
            "framework_comparison_level": "evidence-state measurement layer",
            "claim_boundary": "controlled synthetic domain only",
            "real_api_calls_in_cross_pilot_generation": 0,
            "raw_response_inspection": False,
        },
    ]


def _validation_summary_rows() -> list[dict[str, Any]]:
    p03_no_call = _load_json(PILOT_03_NO_CALL_MANIFEST)
    p03_comparison = _load_json(PILOT_03_COMPARISON_VALIDATION_MANIFEST)
    p04_no_call = _load_json(PILOT_04_NO_CALL_MANIFEST)
    p04_validation = _load_json(PILOT_04_VALIDATION_MANIFEST)

    return [
        {
            "pilot_id": "pilot_03",
            "validation_source": str(PILOT_03_NO_CALL_MANIFEST),
            "status": _safe_get(p03_no_call, "status"),
            "n_steps": _safe_get(p03_no_call, "n_steps"),
            "n_failed_steps": _safe_get(p03_no_call, "n_failed_steps"),
            "n_checks": "",
            "n_failed_checks": "",
            "real_api_calls": _safe_get(p03_no_call, "real_api_calls"),
            "raw_response_inspection": _safe_bool_default_false(p03_no_call, "raw_response_inspection"),
        },
        {
            "pilot_id": "pilot_03",
            "validation_source": str(PILOT_03_COMPARISON_VALIDATION_MANIFEST),
            "status": _safe_get(p03_comparison, "status"),
            "n_steps": "",
            "n_failed_steps": "",
            "n_checks": _safe_get(p03_comparison, "n_checks"),
            "n_failed_checks": _safe_get(p03_comparison, "n_failed_checks"),
            "real_api_calls": _safe_get(p03_comparison, "real_api_calls"),
            "raw_response_inspection": _safe_bool_default_false(p03_comparison, "raw_response_inspection"),
        },
        {
            "pilot_id": "pilot_04",
            "validation_source": str(PILOT_04_NO_CALL_MANIFEST),
            "status": _safe_get(p04_no_call, "status"),
            "n_steps": _safe_get(p04_no_call, "n_steps"),
            "n_failed_steps": _safe_get(p04_no_call, "n_failed_steps"),
            "n_checks": "",
            "n_failed_checks": "",
            "real_api_calls": _safe_get(p04_no_call, "real_api_calls"),
            "raw_response_inspection": _safe_bool_default_false(p04_no_call, "raw_response_inspection"),
        },
        {
            "pilot_id": "pilot_04",
            "validation_source": str(PILOT_04_VALIDATION_MANIFEST),
            "status": _safe_get(p04_validation, "status"),
            "n_steps": "",
            "n_failed_steps": "",
            "n_checks": _safe_get(p04_validation, "n_checks"),
            "n_failed_checks": _safe_get(p04_validation, "n_failed_checks"),
            "real_api_calls": _safe_get(p04_validation, "real_api_calls"),
            "raw_response_inspection": _safe_bool_default_false(p04_validation, "raw_response_inspection"),
        },
    ]


def _condition_alignment_rows(p03: dict[str, Any], p04: dict[str, Any]) -> list[dict[str, Any]]:
    p04_rows = _read_csv(PILOT_04_CONDITION_METRICS)
    p03_condition_available = bool(p03["condition_column_detected"])

    rows: list[dict[str, Any]] = []

    rows.append(
        {
            "pilot_id": "pilot_03",
            "domain": p03["domain"],
            "condition": "detected_from_committed_metrics" if p03_condition_available else "not_detected",
            "structural_metric_column": p03["structural_metric_column"],
            "reliability_metric_column": p03["reliability_metric_column"],
            "audit_metric_column": p03["audit_metric_column"],
            "escalation_metric_column": p03["escalation_metric_column"],
            "structural_metric_value": p03["mean_structural_metric"],
            "reliability_metric_value": p03["mean_reliability_metric"],
            "audit_metric_value": p03["mean_audit_metric"],
            "escalation_metric_value": p03["mean_escalation_metric"],
            "metric_scope_note": "Pilot 03 metric names are preserved from its locked output schema.",
            "real_api_calls": 0,
        }
    )

    for row in p04_rows:
        rows.append(
            {
                "pilot_id": "pilot_04",
                "domain": p04["domain"],
                "condition": row["condition"],
                "structural_metric_column": "structural_validity_rate",
                "reliability_metric_column": "reliability_cascade_index",
                "audit_metric_column": "audit_pass_rate",
                "escalation_metric_column": "escalation_rate",
                "structural_metric_value": row["structural_validity_rate"],
                "reliability_metric_value": row["reliability_cascade_index"],
                "audit_metric_value": row["audit_pass_rate"],
                "escalation_metric_value": row["escalation_rate"],
                "metric_scope_note": "Pilot 04 metrics are deterministic no-call derived outputs.",
                "real_api_calls": 0,
            }
        )

    return rows


def _metric_inventory_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    rows.extend(_summarise_numeric_columns(_read_csv(PILOT_03_CONDITION_METRICS), "pilot_03_condition_metrics"))
    rows.extend(_summarise_numeric_columns(_read_csv(PILOT_03_DELTA_METRICS), "pilot_03_delta_metrics"))
    rows.extend(_summarise_numeric_columns(_read_csv(PILOT_04_CONDITION_METRICS), "pilot_04_condition_metrics"))
    rows.extend(_summarise_numeric_columns(_read_csv(PILOT_04_DELTA_METRICS), "pilot_04_delta_metrics"))

    return rows


def _report_text(
    *,
    p03: dict[str, Any],
    p04: dict[str, Any],
    validation_rows: list[dict[str, Any]],
    condition_rows: list[dict[str, Any]],
) -> str:
    p03_no_call = next(row for row in validation_rows if row["pilot_id"] == "pilot_03" and "no_call_pipeline" in row["validation_source"])
    p04_no_call = next(row for row in validation_rows if row["pilot_id"] == "pilot_04" and "no_call_pipeline" in row["validation_source"])
    p04_validation = next(row for row in validation_rows if row["pilot_id"] == "pilot_04" and "validation" in row["validation_source"])

    p04_condition_lines = []
    for row in condition_rows:
        if row["pilot_id"] != "pilot_04":
            continue
        p04_condition_lines.append(
            f"- {row['condition']}: structural={row['structural_metric_value']}, "
            f"reliability_index={row['reliability_metric_value']}, "
            f"audit_pass={row['audit_metric_value']}, escalation={row['escalation_metric_value']}"
        )

    p04_condition_block = "\n".join(p04_condition_lines)

    return f"""# Cross-Pilot Evidence-State Reliability Report

## Scope

This report links two controlled synthetic evidence-state reliability pilots without changing either pilot's committed outputs.

- Pilot 03: synthetic administrative approval.
- Pilot 04: synthetic loan-risk decision support.
- Cross-pilot level: framework-level evidence-state measurement, not a claim about live systems.

Pilot 03 remains the locked first real-LLM evidence package. Pilot 04 is a deterministic no-call second-domain implementation. The comparison below is limited to whether the same reliability-layer framing can be represented across two controlled domains.

## Current validation state

| Pilot | Validation source | Status | Steps | Failed steps | Checks | Failed checks | API calls |
|---|---|---:|---:|---:|---:|---:|---:|
| Pilot 03 | no-call pipeline | {p03_no_call['status']} | {p03_no_call['n_steps']} | {p03_no_call['n_failed_steps']} |  |  | {p03_no_call['real_api_calls']} |
| Pilot 04 | no-call pipeline | {p04_no_call['status']} | {p04_no_call['n_steps']} | {p04_no_call['n_failed_steps']} |  |  | {p04_no_call['real_api_calls']} |
| Pilot 04 | committed-output validator | {p04_validation['status']} |  |  | {p04_validation['n_checks']} | {p04_validation['n_failed_checks']} | {p04_validation['real_api_calls']} |

## What the cross-pilot layer adds

The important addition is not a larger task count by itself. The useful contribution is that evidence-state degradation is now represented in two separate synthetic settings:

1. a locked administrative approval pipeline;
2. a separate synthetic loan-risk decision-support pipeline.

This supports a conservative framework claim: structural validity and evidence-state reliability can be measured as different layers in controlled multi-stage LLM decision-pipeline experiments.

## Pilot 04 condition-level pattern

Pilot 04 is deterministic no-call evidence, so these rows should be read as a validated pipeline test, not as real model behaviour.

{p04_condition_block}

The key pattern is that structural validity remains available as a separate metric while decision, audit, and escalation measures vary by evidence condition.

## Pilot 03 metric preservation

Pilot 03 is intentionally not rewritten for this report. Its locked output schema is preserved. The cross-pilot generator records detected Pilot 03 metric columns and keeps them separate from Pilot 04 deterministic metrics.

Detected Pilot 03 condition metric columns:

- condition column: `{p03['condition_column_detected']}`
- structural metric column: `{p03['structural_metric_column']}`
- reliability metric column: `{p03['reliability_metric_column']}`
- audit metric column: `{p03['audit_metric_column']}`
- escalation metric column: `{p03['escalation_metric_column']}`

## Safe interpretation

The current repo can support these claims:

- controlled evidence-state degradation can be measured;
- decision, audit, and escalation behaviour can be compared across evidence conditions;
- structured validity and reliability-layer behaviour are different measurements;
- the framework can be implemented across two controlled synthetic domains.

The current repo does not establish operational deployment validity, overall model superiority, or safety for regulated use cases.

## Reproducibility note

This cross-pilot report was generated locally from committed sanitized outputs. It does not inspect raw responses, export prompt text, or make API calls.

- real_api_calls: 0
- raw_response_inspection: False
"""


def _public_wording_check(text: str) -> list[str]:
    return [phrase for phrase in RISKY_PUBLIC_WORDING if phrase in text]


def generate_cross_pilot_report(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    required_paths = [
        PILOT_03_NO_CALL_MANIFEST,
        PILOT_03_COMPARISON_VALIDATION_MANIFEST,
        PILOT_03_MASTER_VALIDATION_SCRIPT,
        PILOT_03_CONDITION_METRICS,
        PILOT_03_DELTA_METRICS,
        PILOT_03_ROBUSTNESS_MANIFEST,
        PILOT_04_NO_CALL_MANIFEST,
        PILOT_04_VALIDATION_MANIFEST,
        PILOT_04_CONDITION_METRICS,
        PILOT_04_DELTA_METRICS,
        PILOT_04_ROBUSTNESS_MANIFEST,
    ]

    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required cross-pilot inputs: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)

    p03 = _summarise_pilot_03_metrics()
    p04 = _summarise_pilot_04_metrics()

    framework_rows = _framework_summary_rows(p03, p04)
    validation_rows = _validation_summary_rows()
    condition_rows = _condition_alignment_rows(p03, p04)
    metric_inventory_rows = _metric_inventory_rows()

    report_text = _report_text(
        p03=p03,
        p04=p04,
        validation_rows=validation_rows,
        condition_rows=condition_rows,
    )

    wording_hits = _public_wording_check(report_text)
    if wording_hits:
        raise RuntimeError(f"Public wording safety check failed: {wording_hits}")

    _write_csv(FRAMEWORK_SUMMARY_CSV, framework_rows)
    _write_csv(VALIDATION_SUMMARY_CSV, validation_rows)
    _write_csv(CONDITION_ALIGNMENT_CSV, condition_rows)
    _write_csv(METRIC_INVENTORY_CSV, metric_inventory_rows)
    REPORT_MD.write_text(report_text, encoding="utf-8")

    manifest = {
        "artifact": "cross_pilot_evidence_state_reliability_report",
        "status": "PASS",
        "created_at_utc": _load_existing_created_at(MANIFEST_JSON),
        "generator": "experiments.generate_cross_pilot_evidence_state_report",
        "pilots": ["pilot_03", "pilot_04"],
        "report_scope": "controlled synthetic cross-pilot evidence-state reliability measurement",
        "row_counts": {
            "cross_pilot_framework_summary": len(framework_rows),
            "pipeline_validation_summary": len(validation_rows),
            "condition_metric_alignment": len(condition_rows),
            "metric_inventory": len(metric_inventory_rows),
        },
        "public_wording_safety_check": "PASS",
        "public_wording_hits": wording_hits,
        "output_files": [
            str(FRAMEWORK_SUMMARY_CSV),
            str(VALIDATION_SUMMARY_CSV),
            str(CONDITION_ALIGNMENT_CSV),
            str(METRIC_INVENTORY_CSV),
            str(REPORT_MD),
            str(MANIFEST_JSON),
        ],
        "raw_prompts_exported": False,
        "raw_responses_exported": False,
        "raw_response_inspection": False,
        "real_api_calls": 0,
    }

    _write_json(MANIFEST_JSON, manifest)
    return manifest


def main() -> None:
    manifest = generate_cross_pilot_report()
    print("Cross-pilot evidence-state reliability report generated.")
    print(f"output_dir: {OUTPUT_DIR}")
    print(f"status: {manifest['status']}")
    print(f"row_counts: {manifest['row_counts']}")
    print(f"public_wording_safety_check: {manifest['public_wording_safety_check']}")
    print(f"real_api_calls: {manifest['real_api_calls']}")
    print(f"raw_response_inspection: {manifest['raw_response_inspection']}")


if __name__ == "__main__":
    main()
