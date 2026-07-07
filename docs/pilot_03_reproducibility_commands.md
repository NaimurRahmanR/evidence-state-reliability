# Pilot 03 Reproducibility Commands

This document records the current commit-safe Pilot 03 reproduction and validation commands.

## Reliability wording

Use only cautious local wording:

- GLM: observed result under current Pilot 03 real LLM experimental conditions
- Claude: observed comparison subset under current Pilot 03 real LLM experimental conditions
- Robustness/sensitivity: descriptive checks over committed sanitized Pilot 03 outputs

Do not claim broad model reliability, broad deployment behavior, provider ordering, or validity outside the controlled Pilot 03 task design.

## Current commit-safe reproduction path

Expected real API calls: 0

Run from the repository root:

```powershell
cd C:\Users\naimu\evidence-state-reliability
python -m experiments.pilot_03_run_no_call_evidence_pipeline
python -m experiments.pilot_03_validate_all_committed_outputs
python -m experiments.pilot_03_validate_comparison_outputs
python -m experiments.pilot_03_generate_robustness_sensitivity_checks
```

Expected current results:

```text
no-call pipeline: PASS, 14 steps, 0 failed steps, 0 skipped steps
master committed-output validation: PASS, 3 validation commands, 0 failed validation commands
comparison-output validation: PASS, 171 checks, 0 failed checks
validated CSV outputs: 20
validated manifests: 6
robustness/sensitivity generation: PASS
real_api_calls in the no-call path: 0
raw_response_inspection in comparison validation: False
```

## Current committed Pilot 03 checkpoints

GLM 20-task checkpoint:

- 20 tasks
- 60 complete chains
- 180 real GLM calls/responses were used earlier to create the committed sanitized checkpoint
- 180/180 valid JSON
- 180/180 valid schema
- valid_chain_rate = 1.0

Claude comparison subset:

- 5 shared tasks
- 15 complete chains
- 45 real Claude calls/responses were used earlier to create the committed sanitized comparison subset
- 45/45 valid JSON
- 45/45 valid schema

The commit-safe commands above do not repeat those real API calls.

## Current committed output layers

The current Pilot 03 evidence package includes:

- full shared-task GLM-vs-Claude comparison
- paired uncertainty analysis
- paired task-level analysis
- reliability cascade metrics
- final figures
- robustness/sensitivity checks
- comparison-output validation
- no-call evidence pipeline

Main committed locations:

```text
reports/pilot_03_glm_vs_claude_t0020_full/
reports/pilot_03_glm_vs_claude_t0020_uncertainty/
reports/pilot_03_glm_vs_claude_t0020_paired_task_analysis/
reports/pilot_03_reliability_cascade_metrics/
reports/pilot_03_final_figures/
reports/pilot_03_robustness_sensitivity/
reports/pilot_03_comparison_validation/
reports/pilot_03_no_call_pipeline/
docs/pilot_03_master_status_checkpoint.md
```

## Robustness/sensitivity row counts

```text
cascade_threshold_sensitivity: 30
condition_order_sensitivity: 12
high_signal_case_profile: 7
leave_one_task_out_sensitivity: 18
paired_delta_interval_sensitivity: 15
```

## Real-call boundary

Real LLM calls are not part of the commit-safe reproduction path.

Only run real LLM commands after explicit confirmation and after checking the expected call count. Any new real-call output must be parsed, validated, sanitized, documented, and checked before being treated as a completed Pilot 03 result.

## Safe interpretation

Under current Pilot 03 real LLM experimental conditions, evidence-state degradation can be measured in a multi-stage decision-audit-escalation chain while structured-output validity remains separately trackable.

This is an observed local result under the current controlled setup.
