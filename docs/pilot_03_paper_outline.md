# Paper Outline: Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

This outline is for a conservative first paper draft based on the current Pilot 01, Pilot 02, and Pilot 03 evidence.

The paper must use Level 1 reliability wording only.

## Working title

Evidence-State Reliability in Multi-Stage LLM Decision Pipelines: A Controlled Pilot Study of Decision, Audit, and Escalation Chains

Alternative shorter title:

Evidence-State Reliability in Multi-Stage LLM Pipelines

## Core thesis

A downstream LLM can remain structurally capable and still produce incorrect decisions if the evidence reaching it has already been degraded upstream.

The paper studies this as an evidence-state reliability problem in multi-stage LLM decision pipelines.

## Safe central claim

Under current Pilot 03 real LLM experimental conditions, downstream decision-audit-escalation chains can remain structurally valid while their correctness changes when required evidence is removed.

This is an observed local result, not a general claim about all LLMs or real-world deployments.

## Contribution framing

The paper should frame contributions conservatively as:

1. An evidence-state reliability framing for multi-stage LLM decision pipelines.
2. A controlled task-and-condition design for measuring evidence degradation across decision, audit, and escalation stages.
3. A reproducible Pilot 03 real LLM implementation with parser validation, chain-level summaries, and condition-level metrics.
4. An observed GLM-5.2 20-task checkpoint showing condition-sensitive correctness changes under evidence degradation.
5. A small Claude Opus 4.8 comparison subset showing that the same measurement procedure can be applied to another strong LLM provider.

Do not claim that the paper proves a universal reliability law.

## Paper structure

### 1. Introduction

Purpose:

- Explain why multi-stage LLM systems are different from single-model evaluation.
- Introduce the evidence-state problem.
- State the core thesis.
- Motivate decision, audit, and escalation chains.
- Present the paper as a controlled empirical pilot.

Key wording:

Modern AI systems often operate as chains of components rather than isolated models. A downstream model may be strong in isolation, but its behaviour depends on the evidence state passed from upstream stages.

Avoid:

- saying existing work has never considered this
- claiming deployment proof
- claiming the benchmark is complete

### 2. Background and motivation

Purpose:

- Discuss reliability in LLM systems.
- Explain why per-model reliability is not enough for chained systems.
- Define evidence-state degradation.
- Position audit and escalation as downstream stages that may inherit degraded evidence.

Possible subsections:

2.1 Single-model reliability versus pipeline reliability
2.2 Evidence state as an intermediate reliability object
2.3 Decision, audit, and escalation chains

### 3. Problem formulation

Purpose:

- Define the pipeline stages.
- Define evidence conditions.
- Define chain correctness.
- Separate structured validity from decision correctness.

Core definitions:

- original evidence
- degraded evidence
- decision stage
- audit stage
- escalation stage
- valid JSON
- valid schema
- decision correctness
- escalation correctness
- valid chain

Important distinction:

Structured validity means the output is parseable and schema-compliant. It does not mean the decision is correct.

### 4. Experimental design

Purpose:

- Describe Pilot 01 and Pilot 02 as simulation-first design checks.
- Describe Pilot 03 as the controlled real LLM pilot.
- Explain task generation, evidence conditions, prompts, parser, and reporting.

Subsections:

4.1 Pilot 01 and Pilot 02 simulation role
4.2 Pilot 03 task design
4.3 Evidence conditions
4.4 Decision-audit-escalation chain
4.5 Parser and schema validation
4.6 Provider setup and guarded real-call procedure

### 5. Results

Purpose:

- Present exact observed counts and rates.
- Separate GLM main evidence track from Claude comparison subset.
- Use descriptive statistics only.

Subsections:

5.1 GLM-5.2 20-task checkpoint

Report:

- 20 tasks
- 60 complete chains
- 180 real GLM calls/responses
- 180/180 valid JSON
- 180/180 valid schema
- valid_chain_rate = 1.0

Condition-level result:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.5, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.5, escalation_correct_rate = 0.5

5.2 Claude Opus 4.8 five-task comparison subset

Report:

- 5 tasks
- 15 complete chains
- 45 real Claude calls/responses
- 45/45 valid JSON
- 45/45 valid schema

Condition-level result:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.4, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.4, escalation_correct_rate = 0.4

5.3 Shared five-task GLM-vs-Claude comparison

Use the shared five-task comparison only for direct provider comparison.

Do not compare the 20-task GLM result against the 5-task Claude subset as if they had equal scope.

### 6. Figures

Use the committed figures:

- Figure 1: GLM-5.2 20-task condition-level rates
- Figure 2: Shared five-task decision correctness by provider and condition
- Figure 3: Shared five-task escalation correctness by provider and condition

Figure captions must include conservative wording.

Example caption style:

Observed condition-level rates under current Pilot 03 real LLM experimental conditions. Rates are descriptive proportions from the controlled Pilot 03 setup and should not be interpreted as general model reliability estimates.

### 7. Discussion

Purpose:

- Explain what the observed pattern means.
- Emphasise evidence-state degradation.
- Explain why structured validity is not enough.
- Discuss why audit and escalation can recover or fail depending on evidence condition.

Safe interpretation:

The current Pilot 03 results suggest that evidence degradation can affect downstream correctness even when outputs remain valid under the parser and schema.

### 8. Validity threats and limitations

Use docs/pilot_03_validity_threats.md as the source.

Must include:

- small task count
- synthetic task construction
- provider and model specificity
- prompt specificity
- parser and schema dependence
- Claude subset smaller than GLM checkpoint
- limited domain coverage
- no real deployment validation
- no human-subject validation
- API and model-version instability
- descriptive statistics only

### 9. Reproducibility

Use docs/pilot_03_reproducibility_commands.md as the source.

Mention:

- committed scripts
- committed CSV summaries
- committed markdown reports
- committed figures
- ignored raw real LLM output folders
- explicit confirmation required for real API calls
- exact call counts for Claude smoke and subset runs

### 10. Conclusion

Conclusion should be cautious.

Possible conclusion:

This controlled pilot provides early real LLM evidence that evidence-state degradation can be measured in multi-stage LLM decision pipelines. Under current Pilot 03 real LLM experimental conditions, chain outputs remained structurally valid while decision and escalation correctness varied by evidence condition. These results motivate larger task sets, additional domains, and broader provider comparisons before any general deployment claim can be made.

## What not to write

Do not write:

- This proves the theory.
- GLM is reliable or unreliable.
- Claude is reliable or unreliable.
- This is a complete benchmark.
- This is deployment evidence.
- This is already Q1-ready.
- No one has ever studied this.

## Current paper-readiness status

Current status:

- Code evidence: strong enough for a controlled pilot paper draft.
- Real GLM evidence: good first main evidence track.
- Claude comparison: useful but small subset.
- Figures: available.
- Reproducibility docs: available.
- Interpretation docs: available.
- Validity-threats docs: available.

Remaining before full paper draft:

- final README update
- final repository status summary
- draft abstract
- draft introduction
- draft methods
- draft results section using exact tables and figures
- related work search and citation integration

Important: related work and citation integration must use up-to-date web/literature search before final paper writing.
