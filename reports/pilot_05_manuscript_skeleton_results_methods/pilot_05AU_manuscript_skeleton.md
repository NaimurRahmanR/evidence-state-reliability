# Pilot 05AU Manuscript Skeleton

## Working title

Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

## Core thesis

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

## 1. Introduction

### Problem

Multi-stage LLM decision systems do not only fail at the final answer layer. They can also fail when the evidence state passed from one stage to another becomes degraded, incomplete, or misleading while the downstream output remains structurally parser-valid.

### Gap

Existing evaluation practice often checks whether final outputs are valid, parseable, or apparently complete. That is not enough for decision systems where upstream evidence degradation can propagate downstream and produce reliability cascades.

### Research question

How can Evidence-State Reliability be measured separately from final parser validity in a multi-stage LLM decision pipeline?

### Paper claim

The paper claims that parser-valid output is not sufficient evidence of reliable pipeline behavior. Evidence-state degradation can produce measurable reliability-layer changes even when parser validity improves.

## 2. Conceptual framing

### Evidence-State Reliability

Evidence-State Reliability is the reliability of the intermediate evidence state used by downstream stages in a decision pipeline. It is separate from final-output validity.

### Reliability cascade

A reliability cascade occurs when degradation at one stage changes downstream behavior across decision, audit, or escalation stages.

### Parser validity boundary

Parser validity means the output fits a required schema or parser contract. It does not imply that the evidence used by the pipeline was sufficient, grounded, complete, or decision-reliable.

## 3. Study design

### Pipeline stages

The study separates decision, audit, and escalation stages.

### Conditions

The committed Pilot 05 experiment compares controlled evidence-state degradation against non-degraded evidence-state conditions.

### Data boundary

The experiment uses sanitized CFPB-backed evidence packets and committed derived outputs only. 05AU does not inspect raw CFPB data and does not create new empirical evidence.

### Model boundary

The empirical results are bounded to the committed GLM-5.2 Pilot 05 run.

## 4. Measures

### Parser-validity measures

Parser-validity metrics track whether model outputs satisfy the required parser/schema contract.

### Evidence-state and stage-success measures

Evidence-state and stage-success metrics track whether the pipeline retains useful evidence across stages.

### Cascade measures

Cascade measures track whether degradation propagates across decision, audit, and escalation stages.

## 5. Results

### Main result

The committed run is organized around 720 planned/ledgered pipeline calls. The sanitized execution layer contains 713 retained rows after parser and execution accounting. The stage-success degradation range is reported as -0.517241 to -0.40678. The parser-validity delta range is reported as 0.067797 to 0.368421. The all-sequence cascade-failure rate is reported as 0.929167. The degraded audit detection mean is reported as 1.0. The degraded escalation recovery mean is reported as 0.0.

### Interpretation

The main result is a divergence between parser validity and evidence-state reliability under degradation. This is the head-turning empirical pattern: the system can look more parser-valid while becoming less reliable at the evidence-state level.

### Figure structure

- Figure 1: Parser validity versus evidence-state divergence.
- Figure 2: Audit and escalation interpretation.
- Figure 3: Cascade failure rate.
- Figure 4: Failure-family interpretation.

## 6. Discussion

### Why this matters

The results show why parser validity alone is unsafe as a reliability signal in multi-stage LLM decision systems. A system can satisfy output-format requirements while losing reliability in the evidence passed through the pipeline.

### Contribution

The paper contributes a concrete reliability layer, a reproducible empirical pipeline, paper-ready figures/tables, and explicit claim boundaries.

## 7. Limitations

The study is bounded to the committed Pilot 05 design and does not claim broad generalization beyond this setup.

## 8. Reproducibility

The committed repository contains the scaled results interpretation, paper figure/table assets, and repo-wide validation audit. 05AU is a synthesis artifact built only from those committed outputs.

## 9. Conclusion

Evidence-State Reliability should be evaluated separately from parser validity in multi-stage LLM decision systems. The Pilot 05 evidence supports this distinction and motivates reliability audits that track evidence-state degradation across pipeline stages.
