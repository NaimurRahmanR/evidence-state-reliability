# Pilot 05AU Methods Section Draft

## Study design

This study evaluates Evidence-State Reliability in a multi-stage LLM decision pipeline. The pipeline is organized around decision, audit, and escalation stages. The empirical design compares pipeline behavior under controlled evidence-state degradation against behavior under non-degraded evidence-state conditions.

## Data and evidence-state boundary

The study uses sanitized CFPB-backed evidence packets and committed derived outputs only. The manuscript synthesis does not read raw CFPB data, raw model prompts, raw model responses, JSONL model-output files, or environment/API-key material.

## Model and execution boundary

The empirical execution summarized here is bounded to the committed GLM-5.2 Pilot 05 run. The synthesis does not make API calls or model calls.

## Pipeline stages

1. **Decision stage**: produces an initial downstream decision/assessment from the evidence state.
2. **Audit stage**: evaluates whether the evidence and decision state should trigger detection or concern.
3. **Escalation stage**: evaluates whether downstream recovery or escalation behavior succeeds under degraded evidence conditions.

## Metrics

The study separates parser-validity metrics from evidence-state and stage-success metrics.

### Parser-validity metrics

Parser-validity metrics measure whether outputs satisfy the expected parser/schema contract. These metrics are useful for execution accounting but are not treated as evidence of substantive decision reliability.

### Evidence-state and stage-success metrics

Evidence-state and stage-success metrics measure whether evidence remains usable across the pipeline stages.

### Cascade metrics

Cascade metrics measure whether reliability degradation propagates across decision, audit, and escalation layers.

## Committed main table used by this synthesis

| metric | value | unit_or_type | paper_ready |
| --- | --- | --- | --- |
| call_plan_rows | 720 | count | yes |
| ledger_rows | 720 | count | yes |
| sanitized_execution_rows | 713 | count | yes |
| parser_invalid_summary_rows | 243 | count | yes |
| ledger_parser_valid_true | 470 | count | yes |
| ledger_parser_valid_false | 250 | count | yes |
| persisted_parser_valid_true | 470 | count | yes |
| persisted_parser_valid_false | 243 | count | yes |
| ledger_only_missing_sanitized_rows | 7 | count | yes, disclosed as limitation |
| max_cumulative_estimated_cost_usd | 2.2731216 | USD | yes |
| stage_success_delta_min | -0.517241 | proportion_delta | yes |
| stage_success_delta_max | -0.40678 | proportion_delta | yes |


## Metric validation table used by this synthesis

| metric | source | validation_note |
| --- | --- | --- |
| call_plan_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| sanitized_execution_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| parser_invalid_summary_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_parser_valid_true | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_parser_valid_false | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| persisted_parser_valid_true | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| persisted_parser_valid_false | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| ledger_only_missing_sanitized_rows | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| max_cumulative_estimated_cost_usd | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| stage_success_delta_min | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |
| stage_success_delta_max | 05AN/05AO/05AP/05AP-B committed contract value | Recorded as previously verified scaled-output contract value; not recomputed from raw data in this task per approved 05AR scope. |


## Reproducibility controls

The committed 05AT audit verifies the repo checkpoint, committed file contracts, manifest safety flags, operation-aware script safety scan, forbidden-file audit, figure integrity, input-index validation, and claim-boundary audit. 05AU uses these committed artifacts as its source boundary.

## No-new-evidence rule

05AU is a manuscript synthesis task. It does not create new empirical results. All methodological and results-language in this package must trace back to committed 05AR, 05AS, or 05AT artifacts.
