# Pilot 05AT Repo-Wide Validation and Reproducibility Audit

## Status

PASS

## Purpose

Task 05AT records a repo-wide validation checkpoint after 05AR and 05AS were secured. It uses corrected operation-aware validation logic and allows only this task's approved expected untracked script/output files during local artifact generation.

## Scope

- No API/model calls.
- No .env reads.
- No raw prompt/response inspection.
- No raw CFPB access.
- No JSONL writing.
- No staging, commit, or push during artifact generation.

## Git checkpoint

- latest_commit: `b1c95da Add Pilot 05 paper figures and final tables`
- latest_hash: `b1c95da`
- latest_subject: `Add Pilot 05 paper figures and final tables`
- origin_main_alignment: `0 behind, 0 ahead`
- staged_count: `0`
- modified_tracked_count: `0`
- unexpected_untracked_count: `0`

## Corrected validator rule

Generated-task audits must not require a completely clean tree after the approved task script has been created. Instead, they must allow exactly the current task's expected untracked script/output files and fail on staged files, modified tracked files, Git divergence, or unexpected untracked files.

## Claim boundary

05AT is a reproducibility and safety audit artifact. It does not create new empirical evidence and does not expand the claim boundary.

Allowed bounded interpretation: Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting the claim that Evidence-State Reliability is distinct from parser validity.

Do not claim:

- broad GLM reliability
- general LLM reliability
- model/provider superiority
- real-world financial validity
- regulatory validity
- deployment safety
- consumer harm prevalence
- company misconduct
- parser validity equals answer correctness
- Q1 acceptance or paper completion

## Audit sections

### repo_checkpoint_audit

- rows: 7
- failed_rows: 0

| check | observed | status |
| --- | --- | --- |
| branch_is_main | main | PASS |
| latest_hash_is_05AS | b1c95da | PASS |
| latest_subject_is_05AS | Add Pilot 05 paper figures and final tables | PASS |
| origin_main_alignment | 0	0 | PASS |
| no_staged_files | NONE | PASS |
| no_modified_tracked_files | NONE | PASS |
| only_expected_untracked_05AT_files | untracked=1 unexpected=0 | PASS |


### committed_file_contract_audit

- rows: 40
- failed_rows: 0

| group | path | exists | tracked | size_bytes | status |
| --- | --- | --- | --- | --- | --- |
| pilot05_script | experiments/pilot_05_cfpb_glm52_scaled_real_execution.py | True | True | 44519 | PASS |
| pilot05_script | experiments/pilot_05_cfpb_glm52_scaled_real_execution_integrity.py | True | True | 21490 | PASS |
| pilot05_script | experiments/pilot_05_cfpb_glm52_scaled_metrics.py | True | True | 27376 | PASS |
| pilot05_script | experiments/pilot_05_cfpb_glm52_scaled_metrics_contract_patch.py | True | True | 30592 | PASS |
| pilot05_script | experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | True | True | 21025 | PASS |
| pilot05_script | experiments/pilot_05_cfpb_glm52_paper_figures_tables.py | True | True | 34470 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json | True | True | 2765 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_headline_empirical_findings.csv | True | True | 943 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv | True | True | 874 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_parser_vs_evidence_state_divergence.csv | True | True | 547 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_audit_escalation_interpretation.csv | True | True | 366 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_cascade_failure_interpretation.csv | True | True | 251 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_failure_family_interpretation.csv | True | True | 589 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_claim_boundary_table.csv | True | True | 1710 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_limitations_and_validity_threats.csv | True | True | 642 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_figure_specifications.csv | True | True | 551 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_metric_validation.csv | True | True | 3913 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_sanitized_input_file_index.csv | True | True | 6366 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_results_section_outline.md | True | True | 1489 | PASS |
| 05AR_output | reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_report.md | True | True | 3458 | PASS |


### manifest_safety_audit

- rows: 15
- failed_rows: 0

| manifest | field | value | status |
| --- | --- | --- | --- |
| 05AR | status | PASS | PASS |
| 05AR | no_api_calls | True | PASS |
| 05AR | no_model_calls | True | PASS |
| 05AR | no_env_read | True | PASS |
| 05AR | no_raw_prompt_response_access | True | PASS |
| 05AR | no_jsonl_written | True | PASS |
| 05AR | no_raw_cfpb_data_touched | True | PASS |
| 05AS | status | PASS | PASS |
| 05AS | no_api_calls | True | PASS |
| 05AS | no_model_calls | True | PASS |
| 05AS | no_env_read | True | PASS |
| 05AS | no_raw_prompt_response_access | True | PASS |
| 05AS | no_jsonl_written | True | PASS |
| 05AS | no_raw_cfpb_data_touched | True | PASS |
| 05AS | expected_output_count | 19 | PASS |


### operation_aware_script_safety_scan

- rows: 10
- failed_rows: 0

| script | line_number | classification | is_actual_risk | line_excerpt | status |
| --- | --- | --- | --- | --- | --- |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 3 | BENIGN_NO_RISK_OPERATION | False | No API/model calls. No .env reads. No raw prompt/response inspection. No JSONL writing. | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 20 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | FORBIDDEN_EXTENSIONS = {".jsonl", ".env"} | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 21 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | FORBIDDEN_NAME_FRAGMENTS = ["raw_prompt", "raw_response", "api_key", "secret"] | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 314 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_env_read": True, | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 315 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_raw_prompt_response_access": True, | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 316 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_jsonl_written": True, | PASS |
| experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py | 430 | BENIGN_NO_RISK_OPERATION | False | raw responses, .env contents, or API/model calls were read, made, or written as part | PASS |
| experiments/pilot_05_cfpb_glm52_paper_figures_tables.py | 64 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_env_read": True, | PASS |
| experiments/pilot_05_cfpb_glm52_paper_figures_tables.py | 65 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_raw_prompt_response_access": True, | PASS |
| experiments/pilot_05_cfpb_glm52_paper_figures_tables.py | 66 | BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT | False | "no_jsonl_written": True, | PASS |


### forbidden_file_audit

- rows: 10
- failed_rows: 0

| kind | path | safe_special_exception | forbidden | status |
| --- | --- | --- | --- | --- |
| tracked | .env.example | True | False | PASS |
| tracked | data/raw/cfpb_complaints/.gitignore | True | False | PASS |
| tracked | data/raw/cfpb_complaints/README.md | True | False | PASS |
| tracked | data/raw/hmda/.gitignore | True | False | PASS |
| tracked | data/raw/hmda/README.md | True | False | PASS |
| untracked | experiments/pilot_05_repo_validation_reproducibility_audit.py | True | False | PASS |
| untracked | reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_committed_file_contract_audit.csv | True | False | PASS |
| untracked | reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_manifest_safety_audit.csv | True | False | PASS |
| untracked | reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_operation_aware_script_safety_scan.csv | True | False | PASS |
| untracked | reports/pilot_05_repo_validation_reproducibility_audit/pilot_05AT_repo_checkpoint_audit.csv | True | False | PASS |


### figure_integrity_audit

- rows: 4
- failed_rows: 0

| figure | exists | tracked | size_bytes | is_png | status |
| --- | --- | --- | --- | --- | --- |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png | True | True | 105492 | True | PASS |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png | True | True | 72640 | True | PASS |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png | True | True | 67915 | True | PASS |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png | True | True | 87865 | True | PASS |


### input_index_validation

- rows: 14
- failed_rows: 0

| input_file | declared_exists | actual_exists | tracked | status |
| --- | --- | --- | --- | --- |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_headline_empirical_findings.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_parser_vs_evidence_state_divergence.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_audit_escalation_interpretation.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_cascade_failure_interpretation.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_failure_family_interpretation.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_claim_boundary_table.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_limitations_and_validity_threats.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_figure_specifications.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_metric_validation.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_sanitized_input_file_index.csv | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_results_section_outline.md | True | True | True | PASS |
| reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_report.md | True | True | True | PASS |


### reproducibility_claim_boundary_audit

- rows: 9
- failed_rows: 0

| claim_boundary_check | observed | status |
| --- | --- | --- |
| parser_validity_language_present | True | PASS |
| evidence_state_language_present | True | PASS |
| cascade_language_present | True | PASS |
| bounded_claim_language_present | True | PASS |
| do_not_claim_broad_glm_reliability_present | True | PASS |
| do_not_claim_general_llm_reliability_present | True | PASS |
| do_not_claim_provider_superiority_present | True | PASS |
| do_not_claim_real_world_financial_validity_present | True | PASS |
| do_not_claim_deployment_safety_present | True | PASS |

