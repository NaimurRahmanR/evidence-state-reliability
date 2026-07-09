# Pilot 05AU Title, Abstract, and Keywords Draft

## Candidate title options

1. Evidence-State Reliability in Multi-Stage LLM Decision Pipelines
2. When Parser Validity Improves While Evidence Reliability Degrades: A Study of Reliability Cascades in LLM Decision Systems
3. Evidence-State Degradation and Reliability Cascades in Sanitized CFPB-Backed LLM Pipeline Experiments
4. Beyond Output Parsability: Measuring Evidence-State Reliability in Multi-Stage LLM Decision Workflows

## Preferred working title

**Evidence-State Reliability in Multi-Stage LLM Decision Pipelines**

## Structured abstract draft

### Background

LLM evaluation commonly emphasizes final-output validity, parser compliance, or answer-level correctness. In multi-stage decision pipelines, however, downstream outputs may remain parser-valid even when the evidence state reaching the downstream stage has been degraded. This creates a reliability layer that is not fully captured by final-output parsability alone.

### Objective

This study introduces and operationalizes Evidence-State Reliability as a layer of reliability concerned with whether intermediate evidence states remain sufficiently complete, grounded, and usable across a multi-stage LLM decision pipeline.

### Method

Using committed Pilot 05 outputs only, the study analyzes a sanitized, CFPB-backed, scaled GLM-5.2 pipeline experiment with controlled evidence-state degradation. The pipeline separates decision, audit, and escalation stages and compares parser-validity behavior against evidence-state and stage-success metrics. All manuscript artifacts in this package are derived from committed 05AR, 05AS, and 05AT outputs only.

### Results

The committed run is organized around 720 planned/ledgered pipeline calls. The sanitized execution layer contains 713 retained rows after parser and execution accounting. The stage-success degradation range is reported as -0.517241 to -0.40678. The parser-validity delta range is reported as 0.067797 to 0.368421. The all-sequence cascade-failure rate is reported as 0.929167. The degraded audit detection mean is reported as 1.0. The degraded escalation recovery mean is reported as 0.0. The central pattern is that parser-validity behavior and evidence-state reliability move in opposite directions under degradation: parser validity improves while stage/evidence success deteriorates. This supports the paper's core claim that parser validity is not a sufficient proxy for evidence-state reliability.

### Contribution

The contribution is a reproducible empirical framing for reliability cascades in multi-stage LLM decision systems. The study distinguishes output parsability from evidence-state reliability, provides paper-ready tables and figures, and supplies explicit claim boundaries for responsible interpretation.

### Limitations

The results are bounded to the committed Pilot 05 GLM-5.2 setup, the sanitized CFPB-backed evidence packets, the specific pipeline stages, and the implemented evidence-state degradation conditions. The study does not claim broad LLM reliability, model/provider superiority, deployment safety, regulatory validity, or real-world consumer harm prevalence.

## Keywords

Evidence-State Reliability; Reliability Cascades; LLM Evaluation; Multi-Stage Decision Pipelines; Parser Validity; Auditability; Escalation; CFPB; Reproducibility; GLM-5.2
