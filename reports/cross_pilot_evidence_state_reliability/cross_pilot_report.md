# Cross-Pilot Evidence-State Reliability Report

## Scope

This report links two controlled synthetic evidence-state reliability pilots without changing either pilot's committed outputs.

- Pilot 03: synthetic administrative approval.
- Pilot 04: synthetic loan-risk decision support.
- Cross-pilot level: framework-level evidence-state measurement, not a claim about live systems.

Pilot 03 remains the locked first real-LLM evidence package. Pilot 04 is a deterministic no-call second-domain implementation. The comparison below is limited to whether the same reliability-layer framing can be represented across two controlled domains.

## Current validation state

| Pilot | Validation source | Status | Steps | Failed steps | Checks | Failed checks | API calls |
|---|---|---:|---:|---:|---:|---:|---:|
| Pilot 03 | no-call pipeline | PASS | 14 | 0 |  |  | 0 |
| Pilot 04 | no-call pipeline | PASS | 13 | 0 |  |  | 0 |
| Pilot 04 | committed-output validator | PASS |  |  | 124 | 0 | 0 |

## What the cross-pilot layer adds

The important addition is not a larger task count by itself. The useful contribution is that evidence-state degradation is now represented in two separate synthetic settings:

1. a locked administrative approval pipeline;
2. a separate synthetic loan-risk decision-support pipeline.

This supports a conservative framework claim: structural validity and evidence-state reliability can be measured as different layers in controlled multi-stage LLM decision-pipeline experiments.

## Pilot 04 condition-level pattern

Pilot 04 is deterministic no-call evidence, so these rows should be read as a validated pipeline test, not as real model behaviour.

- complete: structural=1.0, reliability_index=0.9825, audit_pass=1.0, escalation=0.0
- partial: structural=1.0, reliability_index=0.326666, audit_pass=0.333333, escalation=1.0
- conflicted: structural=1.0, reliability_index=0.510833, audit_pass=0.333333, escalation=0.666667

The key pattern is that structural validity remains available as a separate metric while decision, audit, and escalation measures vary by evidence condition.

## Pilot 03 metric preservation

Pilot 03 is intentionally not rewritten for this report. Its locked output schema is preserved. The cross-pilot generator records detected Pilot 03 metric columns and keeps them separate from Pilot 04 deterministic metrics.

Detected Pilot 03 condition metric columns:

- condition column: `condition`
- structural metric column: ``
- reliability metric column: ``
- audit metric column: `audit_pass_rate`
- escalation metric column: ``

## Safe interpretation

The current repo can support these claims:

- controlled evidence-state degradation can be measured;
- decision, audit, and escalation behaviour can be compared across evidence conditions;
- structured validity and reliability-layer behaviour are different measurements;
- the framework can be implemented across two controlled synthetic domains.

The current repo does not establish operational deployment validity, overall model superiority, or safety for regulated use cases.

## Reproducibility note

This cross-pilot report was generated locally from committed sanitized outputs. It does not inspect raw responses, export prompt text, or make API calls.

- real_api_calls: 0
- raw_response_inspection: False
