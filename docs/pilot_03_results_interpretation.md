# Pilot 03 Results Interpretation

This document records the conservative interpretation of the current Pilot 03 results.

All wording must remain Level 1 reliability wording.

## Safe wording

Use:

- observed result under current Pilot 03 real LLM experimental conditions
- observed comparison subset under current Pilot 03 real LLM experimental conditions

Do not use:

- established
- GLM reliability beyond the controlled checkpoint
- Claude reliability beyond the controlled subset
- live deployment evidence
- broadly valid
- complete evidence already available
- no one has ever done this

## Evidence levels in the project

Pilot 01 and Pilot 02 are simulation results.
Pilot 03 dry-run is a scaffold and parser/reproducibility check.
Pilot 03 GLM-5.2 is the current main real LLM evidence track.
Pilot 03 Claude Opus 4.8 is a small comparison subset.

These categories must not be mixed.

## Main GLM-5.2 checkpoint

Scope:

- 20 tasks
- 3 evidence conditions per task
- 60 complete decision-audit-escalation chains
- 180 real GLM-5.2 calls/responses
- 180/180 valid JSON
- 180/180 valid schema
- valid_chain_rate = 1.0

Observed condition-level result:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.5, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.5, escalation_correct_rate = 0.5

Conservative interpretation:

Under the current Pilot 03 real LLM experimental conditions, the GLM-5.2 checkpoint shows preserved structured-output validity across all completed chains, while decision and escalation correctness vary by evidence condition.

## Claude Opus 4.8 comparison subset

Scope:

- 5 tasks
- 3 evidence conditions per task
- 15 complete decision-audit-escalation chains
- 45 real Claude calls/responses
- 45/45 valid JSON
- 45/45 valid schema

Observed condition-level comparison subset:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.4, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.4, escalation_correct_rate = 0.4

Conservative interpretation:

Under the shared five-task Pilot 03 comparison subset, Claude Opus 4.8 shows the same broad local pattern as GLM-5.2: structured-output validity remains intact, while decision and escalation correctness vary by evidence condition.

This is not a general claim about Claude or Anthropic models.

## GLM-vs-Claude comparison

The safer comparison is the shared five-task comparison because both providers are evaluated on the same task IDs.

Do not compare the full 20-task GLM checkpoint against the 5-task Claude subset as if they had equal scope.

The 20-task GLM result may be used as the stronger main evidence track.
The 5-task Claude result may be used as a comparison subset showing that the Pilot 03 method can be applied to another strong LLM provider under the same controlled task structure.

## What the results currently support

The current Pilot 03 results support the following cautious claim:

Under current Pilot 03 real LLM experimental conditions, downstream decision-audit-escalation chains can remain structurally valid while their correctness changes when required evidence is removed.

The results also support the claim that evidence-state degradation can be measured using task-level evidence conditions, chained LLM stages, parser validation, and condition-level correctness summaries.

## What the results do not support

The current results do not support:

- a general ranking between GLM-5.2 and Claude Opus 4.8
- a claim that either provider is generally reliable or unreliable
- a claim that the observed pattern will hold in all domains
- a claim that the benchmark already represents real deployment conditions
- a claim that publication readiness is complete

## Paper-use guidance

In the paper, present Pilot 03 as a controlled empirical pilot.

The strongest paper framing is:

1. The project proposes an evidence-state reliability framing for multi-stage LLM decision pipelines.
2. Pilot 01 and Pilot 02 motivate the measurement design through simulation.
3. Pilot 03 demonstrates that the design can be executed with real LLM calls under controlled tasks, evidence conditions, chained stages, and parser validation.
4. The observed real LLM results show condition-sensitive correctness changes while schema validity remains high.
5. A small Claude comparison subset shows that the same measurement procedure can be applied to another strong LLM provider.

## Current next step

The next project step should be a validity-threats and limitations document before paper drafting.

That document should cover:

- small task count
- synthetic task construction
- provider/model/version specificity
- prompt specificity
- parser/schema dependence
- no human-subject or real-world deployment validation
- Claude subset smaller than GLM checkpoint
- possible sampling/API/version changes over time
- limited domain coverage
- distinction between structured validity and decision correctness

## Bottom-line interpretation

Pilot 03 currently provides credible early real LLM evidence for the local research thesis: a downstream LLM chain can remain structurally valid while final correctness changes when upstream evidence is degraded.

This must remain framed as an observed local result under current Pilot 03 conditions.
