# Pilot 04 Second-Domain Design: Synthetic Loan-Risk Decision Support

## Purpose

Pilot 04 extends the evidence-state reliability framework into a second controlled synthetic domain.

Pilot 03 remains locked as the first real-LLM evidence package for the synthetic administrative approval domain. Pilot 04 must not modify, reinterpret, or replace Pilot 03. Its purpose is to test whether the same measurement framework can be implemented in a separate synthetic decision-support setting with different task semantics.

The central question for Pilot 04 is:

> Can a multi-stage LLM decision pipeline remain structurally valid while its decision reliability, evidence use, audit behaviour, and escalation behaviour change under controlled degradation of the evidence state?

Pilot 04 is designed as a local, deterministic, no-call implementation first. Real model execution is outside this immediate task unless explicitly approved later.

## Domain boundary

Pilot 04 uses a synthetic loan-risk decision-support setting.

The domain is intentionally simplified. It does not represent live lending, regulated underwriting, credit scoring, affordability assessment, or legal compliance. The tasks are synthetic cases created only for evaluating evidence-state reliability behaviour in a controlled research pipeline.

Safe domain description:

- synthetic applicant profile
- synthetic income and expenditure signals
- synthetic debt and repayment signals
- synthetic employment and stability signals
- synthetic risk notes
- controlled evidence degradation
- structured decision, audit, and escalation outputs

Unsafe interpretation to avoid:

- treating outputs as lending advice
- claiming regulatory compliance
- claiming borrower-level fairness
- claiming production credit-risk validity
- claiming safety for finance use cases

## Relationship to Pilot 03

Pilot 03 and Pilot 04 should stay separate.

| Pilot | Domain | Role in project |
|---|---|---|
| Pilot 03 | Synthetic administrative approval | First locked real-LLM evidence package |
| Pilot 04 | Synthetic loan-risk decision support | Second controlled synthetic domain |
| Cross-pilot analysis | Two controlled domains | Tests whether the framework can be applied beyond one task setting |

Pilot 04 should reuse the conceptual measurement structure from Pilot 03 where appropriate, but it should not copy Pilot 03 task content.

## Pipeline structure

Pilot 04 should keep the same high-level reliability cascade logic:

1. Evidence state is constructed.
2. A decision stage produces a structured decision.
3. An audit stage evaluates the decision against the available evidence.
4. An escalation stage decides whether the case should be escalated.
5. Derived metrics compare behaviour across evidence conditions.

The pipeline should support deterministic local execution before any real model call is considered.

## Evidence conditions

Pilot 04 should use controlled evidence conditions. The exact names can be implemented in code, but the design should preserve this logic:

| Condition | Description | Intended reliability stress |
|---|---|---|
| `complete` | All task-relevant synthetic evidence is available and internally consistent. | Baseline evidence state |
| `partial` | Some relevant evidence is removed or weakened. | Tests sensitivity to missing evidence |
| `conflicted` | Evidence contains controlled tension between risk and support signals. | Tests handling of ambiguity and contradiction |

Each condition must keep the output schema valid. The research focus is not whether the parser breaks. The focus is whether valid structured outputs can still show measurable reliability changes.

## Synthetic task design

Each task should describe a synthetic applicant case using controlled fields.

Recommended task fields:

- `task_id`
- `case_summary`
- `income_signal`
- `employment_signal`
- `debt_signal`
- `repayment_signal`
- `stability_signal`
- `risk_flags`
- `supporting_factors`
- `ground_truth_label`
- `expected_primary_evidence`
- `condition_payloads`

The `ground_truth_label` should be deterministic and synthetic. It should support metric generation, not real financial judgement.

Recommended labels:

- `approve`
- `review`
- `decline`

The expected evidence should make clear which facts are decision-relevant so that evidence-use metrics can be calculated locally.

## Prompt and parser design

Pilot 04 prompt builders should produce structured stage prompts for:

- decision
- audit
- escalation

The parser should accept only the expected sanitized structured output format. It should not store raw prompts or raw model responses in committed outputs.

For deterministic no-call execution, the dry-run simulator should produce parser-valid synthetic outputs locally.

The expected parsed fields should include:

Decision stage:

- `task_id`
- `condition`
- `decision_label`
- `confidence`
- `primary_evidence_used`
- `missing_evidence_acknowledged`
- `risk_flags_identified`
- `decision_rationale_summary`

Audit stage:

- `task_id`
- `condition`
- `audit_pass`
- `evidence_alignment_score`
- `unsupported_claim_count`
- `missed_key_evidence_count`
- `audit_notes_summary`

Escalation stage:

- `task_id`
- `condition`
- `escalation_label`
- `escalation_reason`
- `requires_human_review`
- `escalation_confidence`

## Deterministic no-call simulation

Pilot 04 must first implement a deterministic no-call dry-run. This allows the repo to validate schema, task generation, metric logic, and cross-pilot reporting without API use.

The dry-run should intentionally simulate behaviour changes across evidence conditions while remaining conservative and transparent. It should not be presented as real model behaviour.

Expected deterministic patterns:

- complete evidence should generally produce stronger evidence alignment
- partial evidence should increase missing-evidence acknowledgement and uncertainty
- conflicted evidence should increase review/escalation behaviour
- parser validity should remain stable across conditions

These are simulation design expectations only. They should not be written as empirical findings until outputs are generated and validated.

## Derived outputs

Pilot 04 should generate sanitized derived outputs only.

Expected report folders:

- `reports/pilot_04_tasks`
- `reports/pilot_04_dry_run`
- `reports/pilot_04_stage_cascade`
- `reports/pilot_04_uncertainty`
- `reports/pilot_04_reliability_cascade_metrics`
- `reports/pilot_04_robustness_sensitivity`
- `reports/pilot_04_no_call_pipeline`
- `reports/pilot_04_validation`

Expected derived CSV outputs:

- task inventory
- condition inventory
- parsed decision outputs
- parsed audit outputs
- parsed escalation outputs
- task-level paired metrics
- condition-level cascade metrics
- uncertainty summary
- robustness and sensitivity tables
- validation summary

Expected manifest outputs:

- input file list
- output file list
- row counts
- checksum or file-size checks where practical
- `real_api_calls: 0`
- `raw_response_inspection: False`

## Metrics

Pilot 04 should support metrics that are comparable with Pilot 03 at the framework level, while preserving domain-specific details.

Core metric families:

1. Structural validity

   - parse success
   - schema completeness
   - expected field presence

2. Decision reliability

   - label agreement with synthetic expected label
   - condition-level decision shift
   - task-level paired decision delta

3. Evidence use

   - key evidence coverage
   - missed key evidence count
   - unsupported claim count
   - evidence alignment score

4. Audit behaviour

   - audit pass rate
   - audit sensitivity to missing or conflicted evidence
   - audit false assurance proxy

5. Escalation behaviour

   - escalation rate
   - human-review trigger rate
   - escalation sensitivity under degraded evidence

6. Reliability cascade

   - decision-to-audit change
   - audit-to-escalation change
   - condition-level cascade profile
   - paired task-level cascade delta

## Validation requirements

Pilot 04 must include a committed-output validator before its derived outputs are treated as complete.

The validator should check:

- required files exist
- required columns exist
- task IDs are unique where expected
- each task has all required evidence conditions
- row counts match expected task-condition-stage counts
- labels belong to allowed sets
- numeric scores are within valid ranges
- manifests declare no API calls
- committed outputs do not include raw prompts or raw responses
- generated outputs are deterministic across repeated runs where practical

## Safety and reproducibility rules

Pilot 04 must follow the same safety posture as Pilot 03:

- no API calls in no-call path
- no raw model outputs committed
- no raw prompts committed
- no `.env` files committed
- no `.jsonl` raw run files committed
- no unsafe aggregate raw files committed
- only sanitized derived outputs committed
- all committed outputs must be validator-backed
- public docs must avoid broad claims
- public docs must clearly state synthetic and controlled scope

## Cross-pilot role

Pilot 04 enables a cross-pilot report only after its own outputs and validator pass.

The cross-pilot report may compare framework-level behaviours such as:

- evidence-condition sensitivity
- decision shift under degraded evidence
- audit false assurance proxy
- escalation sensitivity
- parser validity versus reliability metrics

The cross-pilot report must not claim overall superiority of one model, validity for operational deployment, or behaviour outside the controlled tested setting.

Safe cross-pilot claim:

> Across two controlled synthetic domains, the framework can measure differences between structural validity and evidence-state reliability behaviour.

## Task sequence

Implementation should proceed in this order:

1. deterministic Pilot 04 task generator and export
2. Pilot 04 prompt builder and parser
3. Pilot 04 deterministic no-call dry-run simulation
4. Pilot 04 committed-output validator
5. Pilot 04 stage-cascade, uncertainty, reliability-cascade, and robustness outputs
6. Pilot 04 no-call evidence pipeline
7. cross-pilot evidence-state reliability report and validator
8. cross-pilot figures and tables
9. final repo-wide validation, safety scan, commit, and push

## Completion criterion for this design step

This design step is complete when:

- `docs/pilot_04_second_domain_design.md` exists
- the document preserves Pilot 03 as locked
- the Pilot 04 domain is clearly synthetic
- no broad reliability or deployment claims are made
- public wording safety checks pass
- git whitespace checks pass
- staged-file safety checks pass
- the document is committed cleanly
