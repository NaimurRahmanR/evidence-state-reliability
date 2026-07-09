# Pilot 05AP scaled GLM-5.2 metrics report

Status: PASS

## Scope

This no-call task computes metrics over the sanitized Pilot 05AN scaled GLM-5.2 execution outputs and the 05AO integrity reconciliation. It does not make API/model calls, read API keys or `.env`, write raw prompts/responses, create JSONL, stage, commit, or push.

## Row accounting

- Planned calls: 720
- Ledger rows: 720
- Sanitized persisted execution rows: 713
- Parser-invalid summary rows: 243
- Ledger parser-valid rows: 470
- Ledger parser-invalid rows: 250
- Persisted parser-valid rows: 470
- Persisted parser-invalid rows: 243
- Ledger-only missing sanitized rows: 7
- Cumulative estimated cost USD: 2.2731216

## Metrics generated

- Parser validity by condition and stage
- Stage validity proxy by condition and stage
- Condition-stage interaction table with deltas versus clean condition
- Clean-vs-degraded paired deltas by base case
- Bootstrap confidence intervals over paired base cases
- Audit detection and false-assurance metrics
- Escalation recovery/loss proxy metrics
- Cascade sequence patterns
- Failure-family/category distributions
- Metric definitions and claim boundaries

## Claim boundary

This is scaled, real GLM-5.2, CFPB-backed sanitized pipeline evidence. It supports metric generation for evidence-state reliability analysis. It does not yet prove the final paper claim, does not establish broad GLM-5.2 reliability, and does not establish real-world financial or regulatory validity.
