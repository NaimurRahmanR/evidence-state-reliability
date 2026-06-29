# Pilot 03 Real LLM Design

## Evidence-State Reliability in Multi-Stage LLM Pipelines

This document defines the design for **Pilot 03**, the first real LLM experiment in the Evidence-State Reliability project.

Pilot 01 and Pilot 02 were simulation-only. They showed that the framework can measure evidence-state degradation, final failure, undetected failure, audit false assurance, escalation contamination, and cost per governable output under controlled assumptions.

Pilot 03 is the first step toward testing whether similar evidence-state reliability patterns appear when real LLM components are used inside a multi-stage pipeline.

---

## 1. Purpose of Pilot 03

The purpose of Pilot 03 is to test a small real LLM pipeline where evidence passes through multiple stages before a final decision is produced.

The core question is:

> When evidence reaching a downstream LLM is incomplete, distorted, contradicted, or contaminated, does the final decision become less reliable even when the downstream model itself is capable?

Pilot 03 is not intended to prove a general claim about all LLM systems.

It is intended to test whether the simulation framework can be connected to real LLM behaviour in a controlled, auditable, and reproducible way.

---

## 2. Claim boundary

Pilot 03 must preserve a strict claim boundary.

Allowed claim:

> Under the specific Pilot 03 task design, prompts, model settings, and evidence conditions, real LLM pipeline outputs showed measurable evidence-state reliability patterns.

Not allowed:

```text
This proves all LLM pipelines behave this way.
This proves model X is unreliable.
This proves evidence-state degradation always causes failure.
This proves audit stages are ineffective in general.
This proves real-world governance failure.
```

The safe wording should remain:

```text
observed result under current Pilot 03 experimental conditions
```

---

## 3. Pilot 03 research question

Pilot 03 will test:

> Do real LLM components show increased downstream failure, undetected failure, audit false assurance, and escalation contamination when the evidence state is degraded before decision and audit stages?

---

## 4. Pilot 03 hypotheses

### H1: Evidence reliability degradation

As evidence degradation severity increases, measured evidence-state reliability should decrease.

### H2: Final failure

As evidence degradation severity increases, final decision failure should increase.

### H3: Undetected failure

As evidence degradation severity increases, the rate of wrong answers accepted by the audit stage should increase.

### H4: Audit visibility

Visible-audit conditions should reduce undetected failure compared with blind-audit conditions.

### H5: Escalation contamination

Escalation packages built from degraded evidence should show higher contamination than escalation packages built from preserved evidence.

---

## 5. Pipeline structure

Pilot 03 will use the following real LLM pipeline structure:

```text
original evidence
-> evidence condition stage
-> decision model stage
-> audit model stage
-> escalation package stage
-> final output record
```

The important point is that the model does not always receive the original evidence.

Instead, different conditions control what evidence is passed forward.

---

## 6. Evidence conditions

Pilot 03 should begin with a small number of controlled evidence conditions.

Recommended first conditions:

```text
original_evidence
compressed_evidence
fact_loss_evidence
mutated_evidence
contradicted_evidence
unsupported_addition_evidence
blind_audit
visible_audit
```

### original_evidence

The decision model receives all required evidence units.

Purpose: control condition.

### compressed_evidence

The decision model receives a shorter summary that may preserve or lose important details.

Purpose: test summarisation as a source of evidence-state degradation.

### fact_loss_evidence

The decision model receives evidence where one or more decision-critical facts are missing.

Purpose: test missing evidence.

### mutated_evidence

The decision model receives evidence where one or more facts are changed.

Purpose: test distorted evidence.

### contradicted_evidence

The decision model receives evidence containing internal contradictions.

Purpose: test conflict inside evidence state.

### unsupported_addition_evidence

The decision model receives an extra unsupported claim.

Purpose: test contamination.

### visible_audit

The audit model receives the answer and the relevant evidence.

Purpose: test whether evidence visibility improves audit quality.

### blind_audit

The audit model receives the answer but not the full evidence needed to verify it.

Purpose: test audit false assurance under evidence restriction.

---

## 7. Task design

Pilot 03 should use synthetic tasks first.

This is safer than starting with real user data or high-stakes datasets.

Each task should contain:

```text
task_id
question
gold_answer
original_evidence_units
required_evidence_unit_ids
decision_rule
```

Each evidence unit should contain:

```text
unit_id
text
is_required
source_type
```

The first Pilot 03 task set should be small:

```text
30 to 50 synthetic tasks
```

The tasks should be simple enough that correctness can be judged automatically.

Recommended first task types:

```text
eligibility decisions
policy-rule decisions
financial-style rule decisions
medical-style triage only if fully synthetic and non-clinical
administrative approval decisions
```

A good first version should use low-risk synthetic administrative or policy-rule tasks.

Example task shape:

```text
Question:
Should the applicant be approved?

Evidence:
- Applicant income is above the required threshold.
- Applicant has submitted identity documents.
- Applicant has not completed the address verification step.
- The policy requires income, identity, and address verification.

Gold answer:
No

Reason:
Address verification is missing.
```

This type of task allows us to know exactly which evidence units are decision-critical.

---

## 8. Model stages

Pilot 03 should separate the model stages clearly.

### Decision model stage

Input:

```text
question
conditioned evidence
decision instruction
```

Output:

```text
answer
reasoning_summary
confidence
```

The model should not be asked to produce hidden chain-of-thought.

It should provide a short explanation or reasoning summary only.

### Audit model stage

Input depends on audit condition.

Visible audit input:

```text
question
model answer
reasoning_summary
conditioned evidence
audit instruction
```

Blind audit input:

```text
question
model answer
reasoning_summary
audit instruction
```

Output:

```text
audit_decision
audit_reason
detected_error
accepted_answer
```

### Escalation stage

If the audit rejects the answer or uncertainty is high, create an escalation package.

Escalation package should include:

```text
question
answer
audit_decision
available_evidence
missing_evidence_flags
contradiction_flags
unsupported_claim_flags
```

The escalation package itself should be measured for contamination.

---

## 9. Prompt design principles

Pilot 03 prompts must be simple and stable.

They should avoid:

```text
overly complex instructions
ambiguous judgement criteria
requests for long reasoning
requests for hidden reasoning
uncontrolled creativity
```

They should include:

```text
clear task instruction
clear output JSON schema
strict answer options
short explanation field
confidence field
```

The output format should be JSON where possible.

Example decision output:

```json
{
  "answer": "approve_or_reject",
  "decision": "reject",
  "confidence": 0.74,
  "reasoning_summary": "The applicant meets income and identity requirements but address verification is missing."
}
```

Example audit output:

```json
{
  "audit_decision": "reject_answer",
  "detected_error": true,
  "accepted_answer": false,
  "audit_reason": "The answer incorrectly approves the applicant even though address verification is missing."
}
```

---

## 10. Logging requirements

Pilot 03 must log every stage.

Required output file:

```text
data/outputs/pilot_03_real_llm_results.csv
```

Each row should include:

```text
run_id
task_id
condition
model_name
decision_prompt_id
audit_prompt_id
question
gold_answer
model_answer
decision_correct
decision_confidence
audit_decision
audit_detected_error
audit_false_assurance
final_failure
undetected_failure
evidence_state_reliability
evidence_state_degradation
escalation_triggered
escalation_contamination
input_token_estimate
output_token_estimate
estimated_cost
raw_decision_response_path
raw_audit_response_path
```

Raw model outputs should be saved separately to avoid losing detail.

Recommended raw output folder:

```text
data/outputs/raw_pilot_03/
```

---

## 11. Metrics

Pilot 03 should reuse the existing metric names where possible.

Required metrics:

```text
evidence_state_reliability
evidence_state_degradation
final_failure
undetected_failure
audit_false_assurance
escalation_contamination
cost_per_governable_output
```

This keeps Pilot 03 comparable with Pilot 01 and Pilot 02.

---

## 12. Reliability discipline

Pilot 03 must keep the same reliability discipline as the simulation pilots.

Each result must be labelled as:

```text
observed result under current Pilot 03 experimental conditions
```

The analysis should separate:

```text
model error
evidence-state error
audit error
escalation contamination
```

This is important because the project is not only asking whether an LLM gets an answer wrong.

The project is asking whether failure can be traced through the evidence state across the pipeline.

---

## 13. Recommended Pilot 03 minimum viable experiment

The first version should be small and controlled.

Recommended minimum:

```text
30 synthetic tasks
5 evidence conditions
2 audit conditions
1 model family
1 decision prompt
1 audit prompt
3 repeated runs
```

Expected rows:

```text
30 tasks x 5 evidence conditions x 2 audit conditions x 3 runs = 900 rows
```

This is enough to test the pipeline without making cost or debugging too heavy.

---

## 14. Recommended file plan

Pilot 03 should add the following files.

```text
src/llm_client.py
src/pilot_03_runner.py

experiments/run_pilot_03.py
experiments/analyse_pilot_03.py
experiments/plot_pilot_03.py

run_pilot_03.bat
```

Optional later files:

```text
experiments/sanity_check_pilot_03_prompts.py
experiments/compare_pilot_02_pilot_03.py
reports/pilot_03_results_summary.md
```

---

## 15. Implementation order

Pilot 03 should be implemented in this order:

```text
1. Add task export support for real LLM tasks
2. Add prompt templates
3. Add local dry-run mode without API calls
4. Add LLM client wrapper
5. Add Pilot 03 runner
6. Add raw response logging
7. Add parser and validation
8. Add analysis script
9. Add plotting script
10. Add run_pilot_03.bat
```

The dry-run mode is important.

It allows testing the pipeline structure before spending API calls.

---

## 16. Cost control

Pilot 03 should include cost control from the start.

Recommended controls:

```text
small task count first
short prompts
short JSON outputs
temperature fixed at 0 or low value
max output tokens limited
raw outputs saved
reruns avoided unless needed
```

The first live test should use only a very small sample:

```text
5 tasks
2 evidence conditions
1 audit condition
1 run
```

Only after this works should the full Pilot 03 run be executed.

---

## 17. Success criteria

Pilot 03 is successful if it can:

```text
run a real LLM multi-stage pipeline
pass evidence through controlled conditions
produce structured decision outputs
produce structured audit outputs
log raw responses
calculate existing reliability metrics
produce a condition-level summary
identify whether evidence degradation affects downstream outcomes
preserve claim boundaries
```

Pilot 03 does not need to prove the full thesis.

It only needs to show that the simulation framework can be connected to real LLM pipeline behaviour.

---

## 18. Risk checklist

Before running Pilot 03, check:

```text
Are all tasks synthetic?
Are all gold answers known?
Are prompts versioned?
Are raw outputs saved?
Are model settings recorded?
Are failure metrics computed consistently?
Are simulation claims separated from real LLM claims?
Is cost controlled?
Is the run reproducible?
```

---

## 19. Current recommended next action

The next practical step is not to call an LLM yet.

The next practical step is:

```text
create a dry-run Pilot 03 scaffold
```

The dry-run scaffold should use fake LLM responses so that the full pipeline can be tested without API cost.

After the dry-run works, the real LLM client can be added safely.

---

## 20. Summary

Pilot 03 is the bridge between simulation and real LLM evidence-state reliability testing.

Its role is to test whether evidence-state degradation can be measured in a real LLM pipeline while keeping the experiment small, controlled, auditable, and honest.

The guiding rule is:

> Do not claim more than the experiment actually tests.

This keeps the project reliable, defensible, and ready for later expansion.
