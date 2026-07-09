# Pilot 05AU Contribution and Novelty Framing

## One-sentence contribution

This paper introduces Evidence-State Reliability as a reliability layer separate from parser validity and demonstrates, using a committed sanitized CFPB-backed GLM-5.2 pipeline experiment, that evidence-state degradation can worsen stage reliability even when parser validity improves.

## Main novelty

The novelty is not that LLMs can make mistakes. The novelty is that a multi-stage LLM decision pipeline can become more parser-valid while becoming less reliable at the evidence-state layer. This creates a reliability cascade that final-output parser checks can miss.

## Why this is stronger than a normal LLM evaluation paper

A normal evaluation paper often asks whether the final answer is correct, valid, or parseable. This work asks whether the evidence state passed through the system remains reliable enough for downstream decision, audit, and escalation behavior.

## What the paper contributes

1. **Conceptual layer**: Evidence-State Reliability as distinct from final-output validity.
2. **Empirical pattern**: Parser validity improves under degraded evidence while stage/evidence success deteriorates.
3. **Pipeline framing**: Reliability is measured across decision, audit, and escalation stages.
4. **Cascade framing**: Degradation is treated as a propagated pipeline phenomenon, not only a final-answer problem.
5. **Reproducibility package**: Committed 05AR, 05AS, and 05AT artifacts provide tables, figures, audit outputs, and claim boundaries.

## Strong but safe claim

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

## What makes the work potentially head-turning

The result challenges a comfortable assumption: a cleaner, parser-valid output is not necessarily a more reliable decision-system output. In this experiment, parser validity can improve precisely when evidence-state reliability gets worse. That is the paper's strongest empirical and conceptual hook.

## Claim boundary

The contribution is a bounded empirical and methodological contribution. It should not be framed as a universal claim about GLM-5.2, all LLMs, all financial decision systems, or deployment safety.
