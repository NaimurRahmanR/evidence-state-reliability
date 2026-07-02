# Pilot 03 Anthropic/Claude 20-task validity-aware report

Generated at UTC: 2026-07-02T03:16:34+00:00

## Scope

Descriptive Anthropic/Claude 20-task outputs from the controlled Pilot 03 setup. These outputs use sanitized chain-level fields only and should not be interpreted as broad cross-provider conclusions, deployment evidence, or general reliability claims.

This report is generated from the validity-aware local aggregate and the committed Anthropic selector output. The raw aggregate and raw response files remain outside git.

## Parser summary

| Metric | Value |
| --- | --- |
| n_source_runs | 46 |
| n_raw_response_records | 180 |
| parser_version | pilot_03_parser_v2 |
| n_parsed_responses | 180 |
| stage_counts | {"audit": 60, "decision": 60, "escalation": 60} |
| valid_json_counts | {"True": 180} |
| valid_schema_counts | {"True": 180} |
| n_invalid_json | 0 |
| n_invalid_schema | 0 |
| error_counts | {} |

## Condition summary

| Condition | n | Decision correct | Escalation correct | Audit passed | Valid JSON chains | Valid schema chains |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original_evidence | 20 | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) |
| missing_policy_rule | 20 | 10 (0.5) | 17 (0.85) | 0 (0.0) | 20 (1.0) | 20 (1.0) |
| missing_one_required_unit | 20 | 10 (0.5) | 10 (0.5) | 14 (0.7) | 20 (1.0) | 20 (1.0) |

## Failure-pattern summary

| Condition | Pattern | n | Rate | Task IDs |
| --- | --- | ---: | ---: | --- |
| missing_one_required_unit | decision_correct=False; audit_passed=True; escalation_correct=False | 10 | 0.5 | P03-T0001,P03-T0003,P03-T0005,P03-T0007,P03-T0009,P03-T0011,P03-T0013,P03-T0015,P03-T0017,P03-T0019 |
| missing_one_required_unit | decision_correct=True; audit_passed=False; escalation_correct=True | 6 | 0.3 | P03-T0006,P03-T0008,P03-T0010,P03-T0014,P03-T0016,P03-T0018 |
| missing_one_required_unit | decision_correct=True; audit_passed=True; escalation_correct=True | 4 | 0.2 | P03-T0002,P03-T0004,P03-T0012,P03-T0020 |
| missing_policy_rule | decision_correct=False; audit_passed=False; escalation_correct=False | 3 | 0.15 | P03-T0013,P03-T0015,P03-T0017 |
| missing_policy_rule | decision_correct=False; audit_passed=False; escalation_correct=True | 7 | 0.35 | P03-T0001,P03-T0003,P03-T0005,P03-T0007,P03-T0009,P03-T0011,P03-T0019 |
| missing_policy_rule | decision_correct=True; audit_passed=False; escalation_correct=True | 10 | 0.5 | P03-T0002,P03-T0004,P03-T0006,P03-T0008,P03-T0010,P03-T0012,P03-T0014,P03-T0016,P03-T0018,P03-T0020 |
| original_evidence | decision_correct=True; audit_passed=True; escalation_correct=True | 20 | 1.0 | P03-T0001,P03-T0002,P03-T0003,P03-T0004,P03-T0005,P03-T0006,P03-T0007,P03-T0008,P03-T0009,P03-T0010,P03-T0011,P03-T0012,P03-T0013,P03-T0014,P03-T0015,P03-T0016,P03-T0017,P03-T0018,P03-T0019,P03-T0020 |

## Manifest

```json
{
  "created_at_utc": "2026-07-02T03:16:34+00:00",
  "model_name": "claude-opus-4-8",
  "outputs": {
    "chain_summary_csv": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_chain_summary.csv",
    "condition_summary_csv": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_condition_summary.csv",
    "failure_patterns_csv": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_failure_patterns.csv",
    "manifest_json": "reports\\pilot_03_anthropic_t0020_valid\\manifest.json",
    "parser_summary_csv": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_parser_summary.csv",
    "report_md": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_report.md"
  },
  "provider": "anthropic",
  "raw_prompt_or_response_columns_exported": false,
  "real_api_calls": 0,
  "row_counts": {
    "chain_summary": 60,
    "condition_summary": 3,
    "failure_patterns": 7,
    "parser_summary": 10
  },
  "safe_note": "Descriptive Anthropic/Claude 20-task outputs from the controlled Pilot 03 setup. These outputs use sanitized chain-level fields only and should not be interpreted as broad cross-provider conclusions, deployment evidence, or general reliability claims.",
  "scope": "Anthropic Claude 20-task validity-aware checkpoint",
  "selector_manifest": "reports\\pilot_03_anthropic_validity_selector\\manifest.json",
  "source_aggregate_json": "results\\pilot_03_real_llm_analysis\\pilot_03_anthropic_t0020_valid_aggregate.json",
  "source_aggregate_policy": "ignored local aggregate used only for sanitized export",
  "status": "PASS",
  "validity": {
    "n_chain_rows": 60,
    "n_invalid_json": 0,
    "n_invalid_schema": 0,
    "n_parsed_responses": 180,
    "n_raw_response_records": 180,
    "n_source_runs": 46,
    "valid_json_counts": {
      "True": 180
    },
    "valid_schema_counts": {
      "True": 180
    }
  }
}
```
