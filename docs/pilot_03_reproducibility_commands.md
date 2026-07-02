# Pilot 03 Reproducibility Commands

Reliability wording:

- GLM: observed result under current Pilot 03 real LLM experimental conditions
- Claude: observed comparison subset under current Pilot 03 real LLM experimental conditions

Do not claim general model reliability, real-world deployment proof, or universal validity.

## Commit-safe reproduction

Expected real API calls: 0

Run:
cd C:\Users\naimu\evidence-state-reliability
python -m py_compile experiments\pilot_03_generate_glm_claude_comparison_report.py
python -m py_compile experiments\pilot_03_generate_paper_figures.py
python -m experiments.pilot_03_generate_glm_claude_comparison_report
python -m experiments.pilot_03_generate_paper_figures

## Guarded Anthropic no-call test

Expected real API calls: 0

Run Anthropic provider without --confirm-real-llm-call. Expected skip:
SKIPPED: --confirm-real-llm-call was not provided.
No real LLM call was made.

## Real Claude calls

Only run after explicit confirmation.

- Claude smoke test: P03-T0001, all 3 conditions, expected real Claude calls = 9.
- Claude comparison subset: P03-T0001 to P03-T0005, all 3 conditions, expected real Claude calls = 45.

## Current Pilot 03 checkpoints

GLM 20-task checkpoint:
- 20 tasks
- 60 complete chains
- 180 real GLM calls/responses
- 180/180 valid JSON
- 180/180 valid schema
- valid_chain_rate = 1.0

GLM observed condition-level result:
- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.5, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.5, escalation_correct_rate = 0.5

Claude 5-task comparison subset:
- 5 tasks
- 15 complete chains
- 45 real Claude calls/responses
- 45/45 valid JSON
- 45/45 valid schema

Claude observed condition-level result:
- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.4, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.4, escalation_correct_rate = 0.4

## Safe interpretation

Under current Pilot 03 real LLM experimental conditions, both the GLM-5.2 20-task checkpoint and the Claude Opus 4.8 five-task comparison subset show preserved structured-output validity while decision and escalation correctness vary by evidence condition.

This is an observed local result only.
