# Pilot 03 Master Status Checkpoint

Generated at UTC: 2026-07-07T11:43:09+00:00

Latest confirmed commit: `04eb92e`

## Scope

This document records the current committed Pilot 03 evidence checkpoint after the comparison-output validator, robustness/sensitivity checks, and no-call pipeline integration.

All values below are taken from committed sanitized outputs and manifests. The checkpoint is a controlled Pilot 03 evidence record, not a broad claim about deployed systems or model populations.

## Current reproducibility checkpoint

| item | value |
| --- | --- |
| no-call pipeline status | PASS |
| no-call pipeline steps | 14 |
| no-call failed steps | 0 |
| no-call skipped steps | 0 |
| comparison validation status | PASS |
| comparison validation checks | 171 |
| comparison validation failed checks | 0 |
| validated CSV outputs | 20 |
| validated manifests | 6 |
| robustness status | PASS |
| final figure count | 7 |
| final figure output files | 15 |
| real API calls in no-call validation path | 0 |
| raw response inspection in comparison validation | False |

## No-call pipeline components

| component |
| --- |
| comparison_validation |
| final_figures |
| robustness_sensitivity |
| stage_cascade |
| uncertainty |
| validation |

## Key committed output row counts

| output | rows |
| --- | --- |
| full_paired_chain_comparison | 60 |
| full_model_condition_summary | 6 |
| full_condition_delta_summary | 15 |
| full_paired_agreement_summary | 9 |
| full_failure_pattern_comparison | 15 |
| uncertainty_model_metric_uncertainty | 30 |
| uncertainty_paired_delta_uncertainty | 15 |
| paired_task_condition_outcomes | 60 |
| paired_task_level_summary | 20 |
| paired_condition_pair_profile | 3 |
| paired_high_signal_cases | 24 |
| cascade_model_condition_metrics | 6 |
| cascade_evidence_condition_delta_metrics | 48 |
| cascade_cross_model_comparison | 30 |
| cascade_metric_definitions | 12 |
| robustness_leave_one_task_out | 18 |
| robustness_condition_order | 12 |
| robustness_paired_delta_interval | 15 |
| robustness_cascade_threshold | 30 |
| robustness_high_signal_case_profile | 7 |
| comparison_validation_results | 171 |
| no_call_pipeline_steps | 14 |

## Robustness/sensitivity row counts

| output | rows |
| --- | --- |
| cascade_threshold_sensitivity | 30 |
| condition_order_sensitivity | 12 |
| high_signal_case_profile | 7 |
| leave_one_task_out_sensitivity | 18 |
| paired_delta_interval_sensitivity | 15 |

## Reproduction and validation commands

Run from the repository root:

```powershell
python -m experiments.pilot_03_run_no_call_evidence_pipeline
python -m experiments.pilot_03_validate_all_committed_outputs
python -m experiments.pilot_03_validate_comparison_outputs
python -m experiments.pilot_03_generate_robustness_sensitivity_checks
```

Expected current results:

- no-call pipeline: `PASS`, 14 steps, 0 failed steps, 0 skipped steps
- master committed-output validation: `PASS`, 3 validation commands, 0 failed validation commands
- comparison-output validation: `PASS`, 171 checks, 0 failed checks
- robustness/sensitivity generation: `PASS`, 5 generated CSV outputs plus report and manifest

## Current committed evidence base

- Full GLM-vs-Claude shared task comparison outputs are committed under `reports/pilot_03_glm_vs_claude_t0020_full/`.
- Paired uncertainty outputs are committed under `reports/pilot_03_glm_vs_claude_t0020_uncertainty/`.
- Paired task-level analysis outputs are committed under `reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/`.
- Reliability cascade metrics are committed under `reports/pilot_03_reliability_cascade_metrics/`.
- Final figures are committed under `reports/pilot_03_final_figures/`.
- Robustness/sensitivity checks are committed under `reports/pilot_03_robustness_sensitivity/`.
- Comparison validation outputs are committed under `reports/pilot_03_comparison_validation/`.
- No-call pipeline outputs are committed under `reports/pilot_03_no_call_pipeline/`.

## Claim boundary

Safe current wording:

> Under current Pilot 03 real LLM experimental conditions, evidence-state degradation can be measured in a multi-stage decision-audit-escalation chain while structured-output validity remains separately trackable.

Do not state that Pilot 03 establishes broad deployment behavior, population-level model rates, provider ordering, or results outside the controlled task design.

## Safety and data handling boundary

- The no-call pipeline reports `real_api_calls: 0`.
- The comparison validator reports `raw_response_inspection: False`.
- The committed validation path uses sanitized derived CSV/Markdown/JSON manifest outputs.
- Raw prompts, raw responses, API keys, JSONL API outputs, and ignored aggregate raw artifacts are not part of this checkpoint document.

## Latest local commit log at checkpoint

```text
04eb92e Integrate Pilot 03 robustness checks into no-call pipeline
797abe9 Add Pilot 03 robustness sensitivity checks
666d5f8 Add Pilot 03 comparison output validator
90382c3 Update Pilot 03 no-call pipeline with final figures
a34ad4f Add Pilot 03 final figures
8408241 Add Pilot 03 reliability cascade metrics
36c7a08 Add Pilot 03 paired task-level comparison analysis
570cb60 Add Pilot 03 full comparison uncertainty report
ff723d5 Add Pilot 03 full GLM Claude comparison report
feff39a Document Pilot 03 master validation command in README
```
