# Pilot 01 and Pilot 02 Results Summary

## Evidence-State Reliability in Multi-Stage LLM Pipelines

This report summarises the first two simulation pilots for the project:

**Evidence-State Reliability in Multi-Stage LLM Pipelines**

The central research idea is:

> A downstream LLM can be strong and still fail if the evidence reaching it has already been degraded by an upstream component.

At this stage, the project is simulation-first. The results reported here should be treated as **observed simulation results under current pilot assumptions only**. They do not yet claim real LLM behaviour.

---

## 1. Research motivation

Most reliability evaluation focuses on individual model performance. However, real AI decision systems increasingly use multi-stage pipelines.

A typical pipeline may include:

```text
original evidence
-> retrieved evidence
-> compressed or summarised evidence
-> decision evidence
-> audit evidence
-> escalation evidence
-> final output
```

This creates a reliability problem that is not fully captured by model-level evaluation.

A downstream model may be capable, but if the evidence reaching it has already lost important information, gained contradictions, or become contaminated with unsupported claims, the final output may still fail.

This project studies that problem as **evidence-state reliability**.

---

## 2. Working definition

The current working definition is:

> Evidence-State Reliability is the extent to which the evidence available to a downstream LLM component preserves the task-relevant information required for correct, calibrated, and auditable output generation.

This definition separates two things:

```text
model reliability
evidence-state reliability
```

The project tests whether downstream failure can be explained not only by weak models, but also by degraded evidence states.

---

## 3. Metrics used in the pilots

The current simulation framework measures the following outcomes.

### Evidence-State Reliability

Measures how much required task-relevant evidence is still preserved when it reaches the downstream stage.

Higher is better.

### Evidence-State Degradation

Measures how much the evidence state has been damaged through fact loss, mutation, contradiction, uncertainty removal, or unsupported addition.

Lower is better.

### Final Failure

Measures whether the final decision output is wrong.

Lower is better.

### Undetected Failure

Measures whether a wrong final output was accepted rather than caught.

Lower is better.

### Audit False Assurance

Measures whether the audit stage incorrectly accepts a faulty answer.

Lower is better.

### Escalation Contamination

Measures whether escalation receives degraded or contaminated evidence.

Lower is better.

### Cost per Governable Output

Measures the simulated operational cost required to produce outputs that remain governable.

Lower is better, but only if reliability is not lost.

---

## 4. Pilot 01: Pipeline-condition reliability study

Pilot 01 tested whether different pipeline structures produce different reliability and failure profiles.

### Pilot 01 conditions

```text
direct_answer
evidence_preserving
summary_only
visible_audit
blind_audit
```

### Pilot 01 design

```text
50 synthetic tasks
5 pipeline conditions
3 repeated runs
750 rows total
```

### Pilot 01 purpose

Pilot 01 asked:

> Can the framework measure reliability degradation, downstream failure, undetected failure, audit false assurance, escalation contamination, and governability cost across different pipeline conditions?

The answer under the current simulation setup was yes.

---

## 5. Pilot 01 condition-level results

| Condition           | Evidence Reliability | Evidence Degradation | Final Failure | Undetected Failure | Audit False Assurance | Escalation Contamination | Cost per Governable Output |
| ------------------- | -------------------: | -------------------: | ------------: | -----------------: | --------------------: | -----------------------: | -------------------------: |
| direct_answer       |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     1.2000 |
| evidence_preserving |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     2.7000 |
| summary_only        |               0.5000 |               1.5000 |        0.2267 |             0.2267 |                0.2267 |                   0.9067 |                     1.2931 |
| visible_audit       |               0.6778 |               0.9667 |        0.1600 |             0.0067 |                0.0067 |                   0.6733 |                     1.7857 |
| blind_audit         |               0.7044 |               1.8867 |        0.2067 |             0.1467 |                0.1467 |                   1.0000 |                     1.8908 |

### Pilot 01 interpretation

The direct and evidence-preserving conditions kept evidence reliability at 1.0000 and produced no final failure in the current simulation.

The summary-only condition had the lowest evidence reliability at 0.5000 and the highest final failure at 0.2267.

Visible audit reduced undetected failure strongly compared with summary-only and blind-audit conditions.

Blind audit had high escalation contamination at 1.0000, suggesting that escalation can become unreliable when the audit or escalation stage does not have sufficient evidence visibility.

The important point is not that these exact numbers represent real LLM behaviour. The important point is that the framework can distinguish pipeline-level reliability behaviour across different evidence-flow conditions.

---

## 6. Pilot 01 relationship tests

Pilot 01 tested four reliability-failure relationships.

Under current Pilot 01 simulation assumptions:

```text
lower evidence-state reliability was associated with higher final failure
lower evidence-state reliability was associated with higher undetected failure
higher evidence-state degradation was associated with higher final failure
higher evidence-state degradation was associated with higher audit false assurance
```

The relationship results were:

| X Metric                   | Y Metric              | Expected Direction | Pearson | Spearman | Matched Expected Direction |
| -------------------------- | --------------------- | -----------------: | ------: | -------: | -------------------------- |
| evidence_state_reliability | final_failure         |           negative | -0.2513 |  -0.2770 | True                       |
| evidence_state_reliability | undetected_failure    |           negative | -0.2058 |  -0.2174 | True                       |
| evidence_state_degradation | final_failure         |           positive |  0.2727 |   0.3104 | True                       |
| evidence_state_degradation | audit_false_assurance |           positive |  0.2320 |   0.2536 | True                       |

### Pilot 01 sensitivity result

Pilot 01 also included a sensitivity analysis.

The relationship remained directionally visible at the full-design level and after removing perfect/control conditions.

However, the relationship did not hold consistently inside the degraded-evidence-only subset.

This is an important limitation.

It means Pilot 01 supports a between-condition reliability signal, but not yet a strong within-degraded-condition monotonic signal.

That limitation motivated Pilot 02.

---

## 7. Pilot 02: Graded degradation severity study

Pilot 02 tested whether downstream failures increase as evidence degradation severity increases.

### Pilot 02 severity levels

```text
none
low
medium
high
severe
```

### Pilot 02 design

```text
50 synthetic tasks
5 degradation severity levels
3 repeated runs
750 rows total
```

### Pilot 02 purpose

Pilot 02 asked:

> If evidence degradation becomes more severe, do evidence-state degradation, final failure, undetected failure, audit false assurance, and escalation contamination increase in a graded way?

Under the current simulation assumptions, the answer was yes.

---

## 8. Pilot 02 severity-level results

| Degradation Severity | Severity Index | Evidence Reliability | Evidence Degradation | Final Failure | Undetected Failure | Audit False Assurance | Escalation Contamination | Cost per Governable Output |
| -------------------- | -------------: | -------------------: | -------------------: | ------------: | -----------------: | --------------------: | -----------------------: | -------------------------: |
| none                 |              0 |               1.0000 |               0.0000 |        0.0000 |             0.0000 |                0.0000 |                   0.0000 |                     1.5000 |
| low                  |              1 |               0.8600 |               0.4200 |        0.0933 |             0.0533 |                0.0533 |                   0.3667 |                     1.6544 |
| medium               |              2 |               0.6733 |               0.9800 |        0.1867 |             0.1467 |                0.1467 |                   0.7067 |                     1.8443 |
| high                 |              3 |               0.4311 |               2.7067 |        0.3667 |             0.2600 |                0.2600 |                   1.0000 |                     2.3684 |
| severe               |              4 |               0.2600 |               4.2200 |        0.4467 |             0.3467 |                0.3467 |                   1.0000 |                     2.7108 |

### Pilot 02 interpretation

Pilot 02 produced the clearest result so far.

As degradation severity increased:

```text
evidence-state reliability decreased
evidence-state degradation increased
final failure increased
undetected failure increased
audit false assurance increased
escalation contamination increased
cost per governable output increased
```

This directly addresses the limitation found in Pilot 01.

Pilot 01 showed that pipeline conditions matter.

Pilot 02 showed that degradation severity can produce a monotonic downstream reliability pattern under the current simulation assumptions.

---

## 9. Pilot 02 relationship tests

Pilot 02 tested six severity relationships.

| Metric                     | Expected Direction | Pearson | Spearman | Matched Expected Direction | Monotonic by Severity Mean | Severe Minus None |
| -------------------------- | -----------------: | ------: | -------: | -------------------------- | -------------------------- | ----------------: |
| evidence_state_reliability |           negative | -0.7699 |  -0.7889 | True                       | True                       |           -0.7400 |
| evidence_state_degradation |           positive |  0.8867 |   0.8969 | True                       | True                       |            4.2200 |
| final_failure              |           positive |  0.3992 |   0.3992 | True                       | True                       |            0.4467 |
| undetected_failure         |           positive |  0.3460 |   0.3460 | True                       | True                       |            0.3467 |
| audit_false_assurance      |           positive |  0.3460 |   0.3460 | True                       | True                       |            0.3467 |
| escalation_contamination   |           positive |  0.7652 |   0.7652 | True                       | True                       |            1.0000 |

The strongest current statement is:

> Under current Pilot 02 simulation assumptions, increasing evidence degradation severity is associated with lower evidence-state reliability, higher evidence-state degradation, higher final failure, higher undetected failure, higher audit false assurance, and higher escalation contamination.

---

## 10. What the first two pilots show

The first two pilots show that the framework can measure evidence-state reliability as a pipeline-level reliability problem.

The strongest current findings are:

```text
Pilot 01 shows that different pipeline conditions create different reliability and failure profiles.

Pilot 01 shows that audit design matters, especially whether the audit stage has sufficient evidence visibility.

Pilot 01 shows that escalation can become contaminated when degraded evidence is passed forward.

Pilot 02 shows that increasing evidence degradation severity creates monotonic reliability and failure patterns under the current simulation assumptions.

Pilot 02 gives the strongest current support for the evidence-state reliability framing.
```

---

## 11. What the first two pilots do not show yet

The current pilots do not show that real LLM systems behave the same way.

They also do not yet show:

```text
real retrieval behaviour
real summarisation behaviour
real LLM decision behaviour
real LLM audit behaviour
real human escalation behaviour
model-family differences
provider-level differences
prompt-sensitivity effects
domain-specific effects
```

These are future research steps.

The correct limitation statement is:

> These are simulation-only findings. They demonstrate that the framework can express and measure evidence-state reliability phenomena, but they do not yet prove that the same relationships occur in real LLM pipelines.

---

## 12. Why this matters for the research direction

The first two pilots make the project more than a conceptual idea.

They show that evidence-state reliability can be operationalised using:

```text
synthetic tasks
evidence units
degradation operations
pipeline conditions
severity levels
decision simulation
audit simulation
escalation tracking
governability cost
relationship analysis
sensitivity analysis
plots
reproducible workflows
```

This creates a foundation for moving from simulation to real LLM experiments.

The important research move is:

> Reliability should be measured not only at the model level, but also at the evidence-state level across the pipeline.

This creates a way to study failure cascades in AI decision systems.

---

## 13. Recommended next stage

The recommended next stage is Pilot 03.

Pilot 03 should be the first real LLM pipeline experiment.

However, before coding Pilot 03, the project should first create a design document.

Recommended next file:

```text
docs/pilot_03_real_llm_design.md
```

This design document should specify:

```text
which LLM stages will be tested
which models will be used
what prompts will be used
what evidence will be passed between stages
what outputs will be logged
how final failure will be judged
how audit false assurance will be measured
how escalation contamination will be measured
how cost will be controlled
what claims are allowed
what claims are not allowed
```

Pilot 03 should not overclaim. Its purpose should be to test whether the evidence-state reliability patterns observed in simulation also appear in a small real LLM pipeline.

---

## 14. Reproducibility

All current pilots can be run with:

```bat
.\run_all_pilots.bat
```

Pilot 01 can be run with:

```bat
.\run_pilot_01.bat
```

Pilot 02 can be run with:

```bat
.\run_pilot_02.bat
```

The current repository therefore supports end-to-end reproduction of the simulation outputs, analysis tables, relationship tests, and plots.

---

## 15. Current conclusion

The current project has reached a stable simulation milestone.

Pilot 01 established that different multi-stage evidence-flow conditions produce different reliability and failure profiles.

Pilot 02 strengthened the project by showing a monotonic relationship between degradation severity and downstream failure metrics under current simulation assumptions.

The project is now ready for a carefully designed real LLM pilot, provided the next stage preserves the current reliability discipline:

```text
simulation claims stay labelled as simulation claims
real LLM claims must be tested separately
pipeline-level reliability must remain separate from model-level reliability
evidence-state degradation must be logged explicitly
audit and escalation must be evaluated as part of the pipeline, not as afterthoughts
```
