# Pilot 05 HMDA Option B Acquisition Design

Project: Reliability Cascades in AI Decision Systems / Evidence-State Reliability in Multi-Stage LLM Pipelines

Status: approved acquisition-design checkpoint only.

Date: 2026-07-07

Approved user decision:

"I approve Pilot 05 HMDA acquisition design using Option B — FFIEC HMDA Data Browser filtered 2025 sample, no raw data commit, no model API calls."

This document implements the design/planning layer only.

No HMDA data is downloaded by this document.
No raw HMDA file is committed by this document.
No model API call is made by this document.
No prompt or model-response artifact is created by this document.

## 1. Purpose

Pilot 05 is intended to add a real-data-backed empirical pilot to the project.

The current project already has:
- Pilot 03: real-LLM controlled synthetic administrative decision-pipeline domain.
- Pilot 04: deterministic/no-call synthetic second-domain scaffold.
- Cross-pilot framework outputs across controlled synthetic settings.
- Final no-call validation checkpoint.

The current empirical weakness is that the repo does not yet contain a real-data-backed pilot.

This acquisition design is the next safe step toward Pilot 05.

It improves the research path by preparing controlled access to real public HMDA data, but it does not yet provide empirical results.

## 2. Approved acquisition route

Approved route:

Option B — FFIEC HMDA Data Browser filtered 2025 sample.

Official source route:
- FFIEC HMDA Data Browser: https://ffiec.cfpb.gov/data-browser/
- CFPB HMDA data page: https://www.consumerfinance.gov/data-research/hmda/
- CFPB 2025 HMDA data release: https://www.consumerfinance.gov/about-us/newsroom/2025-hmda-data-on-mortgage-lending-now-available/
- FFIEC Modified LAR fallback route: https://ffiec.cfpb.gov/data-publication/modified-lar

Interpretation:
- The Data Browser route is preferred because it supports a filtered sample instead of a full national raw file.
- The Modified LAR route remains a fallback if the browser route cannot produce a usable local sample.

## 3. Source basis

Current official-source assessment:

- CFPB states HMDA public data are modified to protect applicant and borrower privacy.
- CFPB states 2025 HMDA Loan Application Register data are available on the FFIEC HMDA Platform.
- The FFIEC HMDA Data Browser provides filtering, summarizing, and downloading tools for HMDA datasets.
- The FFIEC Modified LAR page provides downloadable modified LAR files for institutions that completed HMDA data submission in a selected year.

Level 1 reliability status:

PASS for public-source/data-availability basis.

Remaining caveat:
- The exact browser-export format and selected filters must be confirmed during the local acquisition step.
- This document does not itself download, inspect, or validate the data.

## 4. Local-only raw data policy

Raw HMDA data must remain local-only.

Local raw-data folder:

data/raw/hmda/

Guardrail:
- data/raw/hmda/.gitignore ignores every file in that folder except README.md and .gitignore.

Do not commit:
- raw HMDA CSV files
- raw HMDA ZIP files
- raw HMDA parquet files
- raw HMDA JSON/JSONL files
- browser-export raw files
- unredacted row-level samples
- API/download cache files
- secrets or .env files

Allowed to commit later, after validation:
- dataset audit summaries
- schema summaries
- row count summaries
- missingness summaries
- target distribution summaries
- selected-field inventory
- sensitive-field inventory
- leakage-risk notes
- derived sanitized evidence packet templates
- derived sanitized condition metadata
- validation manifests

## 5. Expected manual acquisition workflow

This workflow is documented but not executed by this task.

Step 1:
Open the FFIEC HMDA Data Browser.

Step 2:
Select a 2025 HMDA dataset/filtering workflow.

Step 3:
Choose a filtered sample small enough for local audit and reproducible documentation.

Step 4:
Download the filtered export manually.

Step 5:
Place the downloaded raw file locally under:

data/raw/hmda/

Recommended local filename pattern:

hmda_2025_option_b_filtered_raw.<extension>

Examples:
- hmda_2025_option_b_filtered_raw.csv
- hmda_2025_option_b_filtered_raw.zip

Step 6:
Do not stage or commit that raw file.

Step 7:
Run a local audit script that reads the raw file from the local path and writes only sanitized aggregate outputs.

## 6. Exact filter decision still open

The route is approved, but the exact filter choices are not finalized in this document.

Open filter decisions:
- geography filter, such as state or metro area
- loan purpose
- occupancy type
- property type
- action/outcome categories to retain
- sample-size cap
- whether to include or exclude demographic fields from the evidence packet
- whether demographic fields are used only for sensitive-field audit notes

Default recommendation for the first local acquisition:
- Use one recent year only: 2025.
- Use a filtered sample, not national full-file data.
- Keep the first audit sample small enough for fast reproducibility.
- Do not include demographic fields in decision evidence packets at first.
- Keep demographic fields only for sensitive-field inventory and claim-boundary audit unless explicitly approved later.

Important:
The next implementation step may create a local audit script, but the exact raw data file must still come from the approved local HMDA download route.

## 7. Safe task framing

Pilot 05 should not ask a model to approve or deny a mortgage.

Safe framing:

"Recorded outcome review simulation."

Possible task wording:

"Given a structured evidence packet derived from public HMDA records, classify or review the recorded application outcome category under controlled evidence-state degradation."

Unsafe framing:
- Do not frame the task as a real lending approval/rejection decision.
- Do not claim the model determines whether a real applicant should receive a mortgage.
- Do not claim agreement with HMDA labels proves lending correctness.
- Do not claim disagreement with HMDA labels proves lender error.
- Do not claim financial safety.
- Do not claim legal safety.
- Do not claim lending regulation compliance.
- Do not claim fair-lending compliance.
- Do not claim real lending decision validity.
- Do not claim real-world deployment proof.

## 8. Candidate target

Candidate target:

HMDA recorded action/outcome category.

Examples may include:
- originated
- denied
- withdrawn
- incomplete
- approved but not accepted
- purchased loan
- other schema-defined action categories

The exact labels and numeric codes must be verified from the selected 2025 data export and official data dictionary.

Safe interpretation:
- The target is a recorded public outcome field for research simulation.
- The target is not a truth label for real-world lending correctness.

## 9. Candidate field groups

Candidate non-sensitive evidence fields:
- loan type
- loan purpose
- loan amount
- lien status
- occupancy type
- property type
- loan term where available
- interest rate where available and safe
- income where available
- debt-to-income ratio where available
- loan-to-value ratio where available
- property value where available
- action taken / recorded outcome
- denial reason fields where available, depending on final task design

Sensitive or claim-risk fields:
- applicant ethnicity
- applicant race
- applicant sex
- applicant age
- co-applicant demographic fields
- geography fields with re-identification or proxy-risk concerns
- census tract fields
- credit-score related fields where present
- denial reason fields, because they may create false legal/compliance interpretations

Default handling:
- Use sensitive fields for dataset audit inventory only.
- Do not include sensitive demographic fields in decision evidence packets without explicit approval.
- Treat geography carefully and prefer coarse documentation in committed outputs.

## 10. Evidence-state construction plan

For each selected HMDA row, construct a sanitized evidence packet.

Original evidence state:
- selected non-sensitive fields
- normalized categorical labels
- mapped action/outcome category
- no direct raw identifiers
- no raw institution-specific identifier in committed evidence packets unless justified and sanitized

Derived degraded evidence states:
1. complete
   Selected non-sensitive evidence fields are present.

2. partial_missing_affordability
   Affordability-related fields are masked or removed.

3. partial_missing_property_context
   Property/context fields are masked or removed.

4. conflicted_noisy
   A controlled contradiction or perturbation is introduced in non-sensitive fields.

5. compressed_lossy
   Structured evidence is reduced into a lossy summary.

All degraded evidence states must include metadata stating:
- source condition
- degradation type
- fields affected
- whether values are original, masked, transformed, or simulated

## 11. Dataset audit outputs planned

The local dataset audit script should produce only sanitized outputs such as:

reports/pilot_05_hmda_dataset_audit/
- selected_source_manifest.json
- dataset_audit_summary.csv
- column_inventory.csv
- target_distribution.csv
- missingness_summary.csv
- sensitive_field_inventory.csv
- temporal_field_audit.csv
- leakage_risk_notes.csv
- pilot_05_hmda_dataset_audit_report.md

No raw data should be copied into reports.

## 12. Required validators

Before any commit involving Pilot 05 generated outputs, validators must check:

- no raw HMDA file staged
- no .env staged
- no JSONL raw dump staged
- no raw prompts staged
- no raw responses staged
- no secrets staged
- row counts match manifest
- column counts match manifest
- target distribution generated
- missingness summary generated
- sensitive-field inventory generated
- leakage-risk notes generated
- temporal-field audit generated
- claim-boundary scan passes
- real_api_calls is 0 unless explicitly approved
- raw_response_inspection is False unless explicitly justified and approved

## 13. Model/API status

No model API calls are approved in this checkpoint.

Before any real LLM run, user must explicitly approve:
- provider
- model
- temperature/settings
- sample size
- estimated cost
- exact prompt family
- raw prompt/response storage policy
- sanitized output schema
- validator plan

Current status:
- real_api_calls: 0
- raw_response_inspection: False
- dataset_download: 0 in this task
- raw_data_committed: False

## 14. Research-strength note

This step improves infrastructure and research credibility preparation.

It does not yet prove evidence-state reliability cascades in HMDA.

The research-strength upgrade happens only after:
- a real HMDA filtered sample is locally acquired,
- dataset audit passes,
- evidence packets are constructed,
- degradation conditions are generated,
- validators pass,
- and later, if approved, real LLM chains are run with sanitized outputs only.

## 15. Next step after this document

Recommended next task:

Create a local-only HMDA dataset audit script that accepts a local file path, reads the filtered 2025 HMDA export, and writes sanitized aggregate audit outputs.

That script must:
- make no internet downloads,
- make no model API calls,
- not print raw rows,
- not copy raw data into reports,
- write only aggregate/sanitized audit outputs,
- validate that the local raw file is under data/raw/hmda/ or a user-supplied local path,
- track real_api_calls = 0,
- track raw_response_inspection = False,
- track raw_data_committed = False.

User approval needed before running any script against an actual HMDA raw file:
"I approve running the Pilot 05 local HMDA dataset audit on my local filtered HMDA file."
