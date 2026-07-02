# Pilot 03 no-call evidence pipeline report

Generated at UTC: 2026-07-02T02:41:21+00:00

## Scope

No-call Pilot 03 evidence pipeline runner. This command rebuilds committed derived evidence tables and validates committed outputs without making real API calls.

Pipeline status: **PASS**

## Steps

| step_name | status | detail |
| --- | --- | --- |
| compile::experiments\pilot_03_generate_uncertainty_tables.py | PASS | py_compile passed |
| compile::experiments\pilot_03_generate_stage_cascade_tables.py | PASS | py_compile passed |
| compile::experiments\pilot_03_validate_committed_outputs.py | PASS | py_compile passed |
| compile::experiments\pilot_03_plan_real_runs.py | PASS | py_compile passed |
| compile::experiments\pilot_03_generate_paper_figures.py | PASS | py_compile passed |
| generate_uncertainty_tables | PASS | real_api_calls=0; row_counts={'glm_condition_uncertainty': 9, 'shared_provider_condition_uncertainty': 24, 'condition_difference_uncertainty': 22, 'provider_difference_uncertainty': 12} |
| generate_stage_cascade_tables | PASS | real_api_calls=0; raw_prompt_or_response_columns_exported=False; row_counts={'glm20_sanitized_chain_summary': 60, 'shared5_sanitized_chain_summary': 30, 'cascade_pattern_summary': 20, 'stage_transition_summary': 9} |
| validate_committed_outputs | PASS | status=PASS; n_checks=70; n_failed_checks=0; real_api_calls=0 |

## Manifest

```json
{
  "component_manifests": {
    "stage_cascade": {
      "raw_prompt_or_response_columns_exported": false,
      "real_api_calls": 0,
      "row_counts": {
        "cascade_pattern_summary": 20,
        "glm20_sanitized_chain_summary": 60,
        "shared5_sanitized_chain_summary": 30,
        "stage_transition_summary": 9
      },
      "status": "PASS"
    },
    "uncertainty": {
      "real_api_calls": 0,
      "row_counts": {
        "condition_difference_uncertainty": 22,
        "glm_condition_uncertainty": 9,
        "provider_difference_uncertainty": 12,
        "shared_provider_condition_uncertainty": 24
      },
      "status": "PASS"
    },
    "validation": {
      "n_checks": 70,
      "n_failed_checks": 0,
      "real_api_calls": 0,
      "status": "PASS"
    }
  },
  "created_at_utc": "2026-07-02T02:41:21+00:00",
  "n_failed_steps": 0,
  "n_skipped_steps": 0,
  "n_steps": 8,
  "outputs": {
    "manifest_json": "reports\\pilot_03_no_call_pipeline\\manifest.json",
    "pipeline_report_md": "reports\\pilot_03_no_call_pipeline\\no_call_evidence_pipeline_report.md",
    "pipeline_steps_csv": "reports\\pilot_03_no_call_pipeline\\pipeline_steps.csv"
  },
  "real_api_calls": 0,
  "safe_note": "No-call Pilot 03 evidence pipeline runner. This command rebuilds committed derived evidence tables and validates committed outputs without making real API calls.",
  "status": "PASS"
}
```
