# Evidence-State Reliability in Multi-Stage LLM Pipelines

This repository contains simulation code for a doctoral-level research project on **Evidence-State Reliability in Multi-Stage LLM Pipelines**.

The core idea is:

> A downstream LLM can be strong and still fail if the evidence reaching it has already been degraded by an upstream component.

This project is currently **simulation-first**. It does **not** claim real LLM behaviour yet. The purpose of the current pilots is to test whether the experimental design can measure evidence-state degradation, final failure, undetected failure, audit false assurance, escalation contamination, and cost per governable output.

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

This repository currently implements simulation support for the following concepts:

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

The current simulation pilots test the following idea:

> If upstream evidence is degraded, then downstream failure can increase even when the downstream decision model is treated as strong.

This is not yet a claim about real deployed LLM systems. The correct wording for current results is:

```text
observed simulation result under current pilot assumptions
```

The project should not be described as proving real LLM behaviour yet.

---

## Current project status

The repository currently contains two working simulation pilots.

```text
Pilot 01 = pipeline-condition reliability study
Pilot 02 = graded degradation severity study
```

Both pilots are reproducible from one-command Windows batch scripts.

To run everything currently implemented:

```bat
.\run_all_pilots.bat
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

Pilot 01 also includes a sensitivity analysis. The sensitivity check showed that the relationship is visible at the full-design level and remains directionally visible after removing perfect/control conditions, but it does not hold consistently inside the degraded-evidence-only subset.

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

This is currently the strongest result in the repository.

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
```

The master workflow regenerates the current simulation outputs, analysis tables, relationship tests, and plots.

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
|-- run_all_pilots.bat
|
|-- data/
|   |-- synthetic/
|   |-- outputs/
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
|
|-- results/
|   |-- tables/
|   |-- plots/
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

Run individual Pilot 02 steps:

```bat
python -m experiments.sanity_check_graded_degradation
python -m experiments.run_pilot_02
python -m experiments.analyse_pilot_02
python -m experiments.plot_pilot_02
```

---

## Important limitation

This repository currently contains simulation experiments only.

The results should be described as:

```text
observed simulation results under current pilot assumptions
```

They should not be described as proof that real LLM pipelines behave this way.

Real LLM experiments are planned for a later pilot after the simulation framework is stable.

---

## Planned next steps

The next planned stages are:

```text
Pilot 03 = first real LLM pipeline experiment
Pilot 04 = model comparison and benchmark expansion
Paper writing = after simulation and real LLM results are stable
```

Pilot 03 will test whether real LLM pipeline components show similar evidence-state reliability patterns when evidence is retrieved, compressed, audited, escalated, and used for final decisions.

---

## Research positioning

This project focuses on reliability in **multi-stage AI decision systems**, not only individual model reliability.

The central research direction is:

> Reliability should be measured not only at the model level, but also at the evidence-state level across the pipeline.

This means a pipeline can fail because the model is weak, but it can also fail because the evidence reaching the model has already become incomplete, distorted, contradicted, or contaminated.
