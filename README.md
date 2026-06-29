# Evidence-State Reliability in Multi-Stage LLM Pipelines

This repository contains code and documentation for a doctoral-level research project on **Evidence-State Reliability in Multi-Stage LLM Pipelines**.

The core idea is:

> A downstream LLM can be strong and still fail if the evidence reaching it has already been degraded by an upstream component.

This project is currently **simulation-first**, with a local **Pilot 03 dry-run scaffold** added for real LLM readiness.

It does **not** claim real LLM behaviour yet.

The purpose of the current pilots is to test whether the experimental design can measure evidence-state degradation, final failure, undetected failure, audit false assurance, escalation contamination, and cost per governable output.

---

## Research concept

In a multi-stage LLM pipeline, evidence may pass through several stages:

```text
original evidence
-> retrieved evidence
-> compressed/summarised evidence
-> decision evidence
-> audit evidence
-> escalation evidence
-> final output
```

The project studies what happens when evidence is degraded before it reaches downstream model components.

The working definition is:

> **Evidence-State Reliability** is the extent to which the evidence available to a downstream LLM component preserves the task-relevant information required for correct, calibrated, and auditable output generation.

---

## Key concepts

This repository currently implements simulation and dry-run support for the following concepts:

```text
Evidence State
Evidence-State Reliability
Evidence-State Degradation
Decision-Critical Distortion
Escalation Contamination
Audit False Assurance
Undetected Failure
Cost per Governable Output
```

---

## Core research claim being tested

The current pilots test the following idea:

> If upstream evidence is degraded, then downstream failure can increase even when the downstream decision model is treated as strong.

This is not yet a claim about real deployed LLM systems.

The correct wording for Pilot 01 and Pilot 02 results is:

```text
observed simulation result under current pilot assumptions
```

The correct wording for the current Pilot 03 dry-run result is:

```text
observed local dry-run result under current Pilot 03 experimental conditions
```

The project should not be described as proving real LLM behaviour yet.

---

## Current project status

The repository currently contains three implemented pilot workflows.

```text
Pilot 01 = pipeline-condition reliability study
Pilot 02 = graded degradation severity study
Pilot 03 = local dry-run scaffold for real LLM readiness
```

Important:

```text
Pilot 03 has not run real LLM calls yet.
Pilot 03 currently uses deterministic local dry-run responses.
Pilot 03 results must not be described as real LLM behaviour.
```

All implemented pilots are reproducible from one-command Windows batch scripts.

To run everything currently implemented:

```bat
.\run_all_pilots.bat
```

The master workflow currently runs:

```text
Pilot 01 workflow
-> Pilot 02 workflow
-> Pilot 03 dry-run workflow
```

---

## Pilot 01: Pipeline-condition reliability study

Pilot 01 tests different multi-stage pipeline conditions:

```text
direct_answer
evidence_preserving
summary_only
visible_audit
blind_audit
```

Pilot 01 design:

```text
50 synthetic tasks
5 pipeline conditions
3 repeated runs
750 rows total
```

Run Pilot 01:

```bat
.\run_pilot_01.bat
```

Pilot 01 produces:

```text
data/outputs/pilot_results.csv

results/tables/pilot_01_condition_summary.csv
results/tables/pilot_01_reliability_failure_relationship.csv
results/tables/pilot_01_relationship_sensitivity.csv

results/plots/pilot_01_evidence_state_reliability.png
results/plots/pilot_01_final_failure.png
results/plots/pilot_01_undetected_failure.png
results/plots/pilot_01_cost_per_governable_output.png
```

### Pilot 01 condition-level result

| Condition           | Evidence Reliability | Evidence Degradation | Final Failure | Undetected Failure | Audit False Assurance | Escalation Contamination | Cost per Governable Output |
| ------------------- | -------------------: | -------------------: | ------------: | -----------------: | --------------------: | -----------------------: | -------------------------: |
| direct_answer       |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     1.2000 |
| evidence_preserving |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     2.7000 |
| summary_only        |               0.5000 |               1.5000 |        0.2267 |             0.2267 |                0.2267 |                   0.9067 |                     1.2931 |
| visible_audit       |               0.6778 |               0.9667 |        0.1600 |             0.0067 |                0.0067 |                   0.6733 |                     1.7857 |
| blind_audit         |               0.7044 |               1.8867 |        0.2067 |             0.1467 |                0.1467 |                   1.0000 |                     1.8908 |

### Pilot 01 relationship result

Under current Pilot 01 simulation assumptions:

```text
lower evidence-state reliability was associated with higher final failure
lower evidence-state reliability was associated with higher undetected failure
higher evidence-state degradation was associated with higher final failure
higher evidence-state degradation was associated with higher audit false assurance
```

Pilot 01 also includes a sensitivity analysis.

The sensitivity check showed that the relationship is visible at the full-design level and remains directionally visible after removing perfect/control conditions, but it does not hold consistently inside the degraded-evidence-only subset.

That limitation motivates Pilot 02.

---

## Pilot 02: Graded degradation severity study

Pilot 02 tests whether downstream failures increase as evidence degradation severity increases.

Pilot 02 severity levels:

```text
none
low
medium
high
severe
```

Pilot 02 design:

```text
50 synthetic tasks
5 degradation severity levels
3 repeated runs
750 rows total
```

Run Pilot 02:

```bat
.\run_pilot_02.bat
```

Pilot 02 produces:

```text
data/outputs/pilot_02_results.csv

results/tables/pilot_02_severity_summary.csv
results/tables/pilot_02_severity_relationships.csv

results/plots/pilot_02_evidence_state_reliability.png
results/plots/pilot_02_evidence_state_degradation.png
results/plots/pilot_02_final_failure.png
results/plots/pilot_02_undetected_failure.png
results/plots/pilot_02_audit_false_assurance.png
results/plots/pilot_02_escalation_contamination.png
results/plots/pilot_02_cost_per_governable_output.png
```

### Pilot 02 severity-level result

| Degradation Severity | Severity Index | Evidence Reliability | Evidence Degradation | Final Failure | Undetected Failure | Audit False Assurance | Escalation Contamination | Cost per Governable Output |
| -------------------- | -------------: | -------------------: | -------------------: | ------------: | -----------------: | --------------------: | -----------------------: | -------------------------: |
| none                 |              0 |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     1.5000 |
| low                  |              1 |               0.8600 |               0.4200 |        0.0933 |             0.0533 |                0.0533 |                   0.3667 |                     1.6544 |
| medium               |              2 |               0.6733 |               0.9800 |        0.1867 |             0.1467 |                0.1467 |                   0.7067 |                     1.8443 |
| high                 |              3 |               0.4311 |               2.7067 |        0.3667 |             0.2600 |                0.2600 |                   1.0000 |                     2.3684 |
| severe               |              4 |               0.2600 |               4.2200 |        0.4467 |             0.3467 |                0.3467 |                   1.0000 |                     2.7108 |

### Pilot 02 relationship result

Under current Pilot 02 simulation assumptions:

```text
6/6 relationship tests matched the expected direction
6/6 severity means were monotonic
```

The observed simulation pattern was:

```text
increasing degradation severity
-> lower evidence-state reliability
-> higher evidence-state degradation
-> higher final failure
-> higher undetected failure
-> higher audit false assurance
-> higher escalation contamination
```

This is currently the strongest simulation result in the repository.

---

## Pilot 03: Local dry-run scaffold for real LLM readiness

Pilot 03 is the first step toward real LLM readiness, but the current implementation is still a local dry-run scaffold.

It does not make real LLM API calls.

Pilot 03 currently tests three evidence conditions:

```text
original_evidence
missing_policy_rule
missing_one_required_unit
```

Pilot 03 uses three pipeline stages:

```text
decision
audit
escalation
```

Pilot 03 task design:

```text
50 synthetic administrative approval tasks
25 approve
25 reject
6 evidence units per task
```

Run Pilot 03 dry-run:

```bat
.\run_pilot_03.bat
```

Pilot 03 dry-run produces outputs under:

```text
results/pilot_03_dry_run_analysis/pilot_03_dry_run_analysis_latest/
```

This includes:

```text
analysis_records.csv
condition_summary.csv
analysis_summary.json

plots/audit_metrics_by_condition.png
plots/evidence_state_metrics_by_condition.png
plots/failure_metrics_by_condition.png
```

### Pilot 03 dry-run parser checkpoint

The current Pilot 03 dry-run parser checkpoint is:

```text
450 dry-run responses parsed
0 invalid JSON
0 invalid schema
```

This means the current local dry-run response format is parseable and schema-valid under the implemented parser.

It does not mean real LLM responses will behave the same way.

### Pilot 03 dry-run observed pattern

The current observed local dry-run pattern is:

```text
original evidence:
evidence-state reliability = 1.0
final failure = 0.0

missing evidence:
evidence-state reliability = 0.833333
final failure = 0.5
escalation contamination = 0.5
```

Safe wording:

> Under current Pilot 03 experimental conditions, the local dry-run scaffold produced an observed pattern where missing evidence reduced evidence-state reliability and increased final failure and escalation contamination.

This should only be described as:

```text
observed local dry-run result under current Pilot 03 experimental conditions
```

It should not be described as real LLM behaviour.

---

## Planned real LLM setup

The planned real LLM setup is:

```text
Main model:
GLM-5.2

Comparison model:
Claude Fable 5

Fallback comparison model:
Claude Opus 4.8
```

This setup is planned for future real LLM readiness only.

It has not been run yet.

The intended role of each model is:

```text
GLM-5.2:
main real LLM model for controlled Pilot 03 testing

Claude Fable 5:
frontier comparison model, if accessible

Claude Opus 4.8:
fallback comparison model if Claude Fable 5 is not accessible
```

The first real LLM run should not be a full experiment.

The correct sequence is:

```text
1. GLM-5.2 one-task smoke test
2. Parse and validate the raw response
3. Manually inspect the result
4. GLM-5.2 small controlled run
5. GLM-5.2 full Pilot 03 run only if the small run is stable
6. Claude Fable 5 comparison subset only after GLM is stable
7. Claude Opus 4.8 comparison subset only if Fable 5 is not accessible
```

The comparison model should initially run on a subset, not the full Pilot 03 design.

This keeps the project cost-controlled while still allowing a stronger model comparison later.

---

## Future real LLM safety rules

Future real LLM work must follow these rules:

```text
No API key from any provider should ever be committed.
Use environment variables only.
Default mode must remain dry-run.
Real LLM mode must require explicit command-line opt-in.
Real smoke test should use only one task and one condition.
Raw real responses must be saved separately from dry-run responses.
One smoke test must not be generalised into a broad empirical claim.
```

Expected future environment variables:

```text
ZAI_API_KEY
ANTHROPIC_API_KEY
```

Expected future model/config variables:

```text
PILOT03_LLM_PROVIDER
PILOT03_LLM_MODEL
PILOT03_REAL_LLM_ENABLED
```

Expected future real LLM result wording:

```text
observed result under current Pilot 03 real LLM experimental conditions
```

No real LLM experiment should be treated as complete until real LLM calls have actually been made, parsed, analysed, and checked.

---

## Reproduce all current pilots

Run all implemented pilot workflows:

```bat
.\run_all_pilots.bat
```

This runs:

```text
Pilot 01 workflow
-> Pilot 02 workflow
-> Pilot 03 dry-run workflow
```

The master workflow regenerates the current simulation outputs, dry-run outputs, analysis tables, relationship checks, parser checks, and plots.

---

## Repository structure

```text
evidence-state-reliability/
|
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- run_pilot_01.bat
|-- run_pilot_02.bat
|-- run_pilot_03.bat
|-- run_all_pilots.bat
|
|-- data/
|   |-- synthetic/
|   |-- outputs/
|
|-- docs/
|   |-- pilot_03_real_llm_design.md
|
|-- reports/
|   |-- pilot_01_02_results_summary.md
|
|-- experiments/
|   |-- __init__.py
|   |-- sanity_check_evidence_state.py
|   |-- sanity_check_task_generator.py
|   |-- sanity_check_degradation.py
|   |-- sanity_check_graded_degradation.py
|   |-- sanity_check_pipeline_conditions.py
|   |-- sanity_check_metrics.py
|   |-- sanity_check_simulated_models.py
|   |-- run_pilot_01.py
|   |-- analyse_pilot_01.py
|   |-- analyse_reliability_failure_relationship.py
|   |-- analyse_relationship_sensitivity.py
|   |-- plot_pilot_01.py
|   |-- run_pilot_02.py
|   |-- analyse_pilot_02.py
|   |-- plot_pilot_02.py
|   |-- pilot_03_dry_run_runner.py
|   |-- pilot_03_dry_run_analysis.py
|   |-- pilot_03_dry_run_plots.py
|
|-- results/
|   |-- tables/
|   |-- plots/
|   |-- pilot_03_dry_run_analysis/
|
|-- notebooks/
|
|-- src/
    |-- __init__.py
    |-- evidence_state.py
    |-- task_generator.py
    |-- degradation.py
    |-- pipeline_conditions.py
    |-- metrics.py
    |-- simulated_models.py
    |-- pilot_runner.py
    |-- pilot_02_runner.py
    |-- pilot_03_tasks.py
    |-- pilot_03_prompts.py
    |-- pilot_03_dry_run.py
    |-- pilot_03_llm_client.py
    |-- pilot_03_logging.py
    |-- pilot_03_parser.py
```

---

## Main source files

```text
src/evidence_state.py
    Defines EvidenceUnit and EvidenceState.

src/task_generator.py
    Generates synthetic tasks with original evidence, required units, and gold answers.

src/degradation.py
    Simulates fact loss, fact mutation, contradiction, uncertainty removal,
    unsupported addition, and graded degradation severity.

src/pipeline_conditions.py
    Defines the Pilot 01 pipeline conditions.

src/metrics.py
    Calculates Evidence-State Reliability, Evidence-State Degradation,
    Final Failure, Undetected Failure, Audit False Assurance,
    Escalation Contamination, and Cost per Governable Output.

src/simulated_models.py
    Simulates decision and audit models without real LLM API calls.
    Includes Pilot 01 baseline model logic and Pilot 02 severity-sensitive model logic.

src/pilot_runner.py
    Runs Pilot 01 by connecting tasks, pipeline conditions, simulated models,
    metrics, and CSV output.

src/pilot_02_runner.py
    Runs Pilot 02 by connecting tasks, graded degradation severity,
    severity-sensitive simulated models, metrics, and CSV output.

src/pilot_03_tasks.py
    Generates Pilot 03 synthetic administrative approval tasks.

src/pilot_03_prompts.py
    Builds Pilot 03 decision, audit, and escalation prompts.

src/pilot_03_dry_run.py
    Generates deterministic local dry-run responses for Pilot 03.

src/pilot_03_llm_client.py
    Contains the placeholder/client boundary for future real LLM calls.
    Real LLM calls are not part of the current dry-run result claim.

src/pilot_03_logging.py
    Supports Pilot 03 response and result logging.

src/pilot_03_parser.py
    Parses and validates Pilot 03 structured responses.
```

---

## Environment

The project has been developed and tested on:

```text
Windows
VS Code
Python 3.12.2
pip 24.0
Git 2.53.0
virtual environment: .venv
```

Required Python packages:

```text
pandas
numpy
matplotlib
pytest
```

Install requirements:

```bat
pip install -r requirements.txt
```

---

## Reproducibility commands

Run everything:

```bat
.\run_all_pilots.bat
```

Run Pilot 01 only:

```bat
.\run_pilot_01.bat
```

Run Pilot 02 only:

```bat
.\run_pilot_02.bat
```

Run Pilot 03 dry-run only:

```bat
.\run_pilot_03.bat
```

Run individual Pilot 02 steps:

```bat
python -m experiments.sanity_check_graded_degradation
python -m experiments.run_pilot_02
python -m experiments.analyse_pilot_02
python -m experiments.plot_pilot_02
```

Run individual Pilot 03 dry-run steps:

```bat
python -m experiments.pilot_03_dry_run_runner
python -m experiments.pilot_03_dry_run_analysis
python -m experiments.pilot_03_dry_run_plots
```

---

## Important limitation

This repository currently contains:

```text
Pilot 01 simulation results
Pilot 02 simulation results
Pilot 03 local dry-run results
```

The results should be described as:

```text
observed simulation results under current pilot assumptions
```

or, for Pilot 03 dry-run:

```text
observed local dry-run result under current Pilot 03 experimental conditions
```

They should not be described as proof that real LLM pipelines behave this way.

Real LLM experiments are planned only after the dry-run scaffold, parser, logging, guardrails, and one-task smoke test are stable.

---

## Planned next steps

The next planned stages are:

```text
1. Document the completed Pilot 03 dry-run checkpoint.
2. Add real LLM readiness guardrails.
3. Add safe config examples.
4. Add API-key protection.
5. Add real LLM client implementation behind explicit opt-in.
6. Add one-task real LLM smoke test only.
7. Log raw real responses separately.
8. Parse and validate real responses.
9. Manually inspect the one-task result.
10. Only then consider a small controlled real LLM Pilot 03 run.
```

No real LLM experiment should be treated as complete until real LLM calls have actually been made, parsed, analysed, and checked.

---

## Research positioning

This project focuses on reliability in **multi-stage AI decision systems**, not only individual model reliability.

The central research direction is:

> Reliability should be measured not only at the model level, but also at the evidence-state level across the pipeline.

This means a pipeline can fail because the model is weak, but it can also fail because the evidence reaching the model has already become incomplete, distorted, contradicted, or contaminated.

