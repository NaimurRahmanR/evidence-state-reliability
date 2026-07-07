# Pilot 05 CFPB Consumer Complaint Database Design Audit

Project: Reliability Cascades in AI Decision Systems / Evidence-State Reliability in Multi-Stage LLM Pipelines

Status: design-audit checkpoint only.

Date: 2026-07-07

Approved active dataset path:

CFPB Consumer Complaint Database.

No CFPB complaint data is downloaded by this document.
No CFPB complaint API call is made by this document.
No raw CFPB complaint file is committed by this document.
No model API call is made by this document.
No raw prompts or raw model responses are introduced by this document.

## 1. Purpose

Pilot 05 is intended to repair the current empirical weakness by adding a real-data-backed pilot.

The active dataset path is now CFPB Consumer Complaint Database, replacing HMDA as the immediate Pilot 05 empirical route because the FFIEC HMDA platform was temporarily unavailable.

The goal is not to build a consumer-protection claim engine.

The goal is to study evidence-state reliability cascades in a real public complaint-resolution setting.

## 2. Source and public availability audit

Official source pages:
- CFPB Consumer Complaint Database: https://www.consumerfinance.gov/data-research/consumer-complaints/
- CFPB complaint data sharing explanation: https://www.consumerfinance.gov/complaint/data-use/
- CFPB Consumer Complaint Database API field reference: https://cfpb.github.io/api/ccdb/fields.html
- CFPB Consumer Complaint Database API documentation: https://cfpb.github.io/api/ccdb/

Current source assessment:

- CFPB publishes complaint data in a public database.
- CFPB states that published complaint data are freely available for use, analysis, and building on.
- CFPB provides complaint data download and API routes.
- CFPB publishes complaints after company response or after 15 days, whichever comes first.
- CFPB publishes complaint narratives only if the consumer opts in and after steps to remove personal information.

Level 1 reliability status:

PASS for public-source candidacy.

Caveat:
- This document does not itself download or inspect the data.
- The exact filtered sample route must be documented before any local audit output is committed.

## 3. Dataset limitation audit

Important CFPB limitations that affect claim boundaries:

- Complaint data are not a statistical sample.
- Complaint data are not necessarily representative of all consumer experiences.
- Complaint narratives are consumer descriptions.
- CFPB does not verify that complaint narratives are accurate or unbiased.
- Recent complaint data may not include all complaints eligible for publication because companies have response time.
- Complaint volume must be interpreted with care because company size, market share, geography, and population context matter.

Level 1 reliability status:

SUITABLE only for controlled research simulation.

Do not use this dataset to claim consumer harm prevalence, company wrongdoing, legal compliance, or provider ranking.

## 4. Candidate fields

Candidate evidence fields include:
- Date received
- Product
- Sub-product
- Issue
- Sub-issue
- Consumer complaint narrative
- Company public response
- Company
- State
- ZIP code
- Tags
- Consumer consent provided?
- Submitted via
- Date sent to company
- Company response to consumer
- Timely response?
- Complaint ID

The exact field names must be verified against the downloaded/exported file.

## 5. Sensitive and claim-risk fields

Sensitive or claim-risk fields may include:
- complaint narrative text
- ZIP code
- State
- Tags such as Older American or Servicemember
- Company name
- Company public response
- Complaint ID
- dates that allow temporal reconstruction
- any text that may contain residual personal information despite scrubbing

Default handling:
- Do not commit raw complaint narratives.
- Do not commit raw row-level complaint records.
- Do not include Complaint ID in committed evidence packets unless transformed into a synthetic internal case ID.
- Use company names carefully.
- Do not rank companies.
- Prefer aggregate outputs and sanitized evidence packets.
- Treat narratives as consumer-submitted descriptions, not verified truth.

## 6. Target variable suitability

Candidate targets:
- Company response to consumer
- Timely response?
- Company public response availability/category
- selected complaint-resolution outcome categories

Recommended first target:

Timely response?

Reason:
- binary or near-binary target,
- clean decision-support simulation target,
- avoids stronger legal/monetary-relief interpretations,
- directly supports evidence sufficiency and escalation logic.

Alternative target:

Company response to consumer.

Reason:
- richer multi-class target,
- strong fit for outcome-review simulation,
- but more class imbalance and interpretation risk.

Unsafe target framing:
- Do not predict whether a company acted wrongly.
- Do not predict whether a consumer claim is true.
- Do not predict legal merit.
- Do not predict consumer harm prevalence.
- Do not claim company compliance.

Safe target framing:

Recorded complaint-resolution outcome review simulation.

## 7. Temporal split possibility

The database includes date fields such as Date received and Date sent to company.

Temporal design options:
- use one recent bounded window for the first audit,
- split earlier complaints and later complaints by Date received,
- compare evidence-state reliability across months or years,
- keep recent incomplete-publication caveats in mind.

Recommended first Pilot 05 dataset audit:
- use a recent but not too recent fixed date window,
- avoid newest records if response/publication completeness is uncertain,
- document date range exactly.

## 8. Evidence-state construction plan

For each selected complaint record, construct a sanitized evidence packet.

Original evidence state:
- product
- sub-product
- issue
- sub-issue
- submitted via
- date received bucket or month
- state or coarse geography if approved
- narrative presence flag
- sanitized narrative excerpt or derived summary only if approved
- target field held out from decision evidence

Do not include:
- raw Complaint ID
- raw ZIP code in committed evidence packets
- raw full narrative in committed evidence packets
- company ranking fields for public comparison
- direct target field as input evidence

## 9. Evidence degradation conditions

Minimum evidence conditions:

1. complete_structured
   Selected non-target structured fields are available.

2. missing_issue_context
   Product/sub-product/issue/sub-issue context is partially masked.

3. missing_narrative_context
   Complaint narrative or narrative-derived summary is removed or replaced with a narrative-missing flag.

4. conflicted_noisy_context
   A controlled contradiction is introduced between product and issue or between issue and sub-issue.

5. compressed_lossy_summary
   Evidence is reduced into a lossy structured or textual summary.

Optional later condition:
- missing_company_context
  Company field is masked to test whether outcome-review behaviour depends heavily on company-specific patterns.

## 10. Decision/audit/escalation chain plan

Decision stage:
- Given a sanitized evidence packet, perform recorded outcome-review classification.
- Recommended first task: classify whether the recorded company response was timely, using only allowed evidence.
- Do not ask a model to determine whether a complaint is true or whether the company acted wrongly.

Audit stage:
- Check whether the decision-stage output is supported by the available evidence state.
- Track structural validity separately from reliability-layer behaviour.

Escalation stage:
- Decide whether missing, conflicted, or insufficient complaint evidence should be escalated.
- Track missed escalation and over-escalation under degraded evidence.

No real LLM/model API calls are approved by this document.

## 11. Sanitization and storage rules

Do not commit:
- raw CFPB complaint CSV files
- raw CFPB complaint JSON files
- raw CFPB complaint XLS/XLSX files
- raw full complaint narratives
- raw row-level complaint records
- raw prompts
- raw model responses
- JSONL raw dumps
- .env
- API keys
- secrets

Allowed to commit after validation:
- dataset audit summaries
- column inventories
- target distribution summaries
- missingness summaries
- sensitive/claim-risk field inventories
- temporal field audits
- leakage-risk notes
- sanitized evidence packet templates
- sanitized condition metadata
- validation manifests
- claim-boundary safety reports

## 12. Validators required

Pilot 05 CFPB complaint validators must check:
- no raw CFPB complaint file staged
- no raw row-level records staged
- no raw narratives staged
- no raw prompts staged
- no raw responses staged
- no JSONL raw dumps staged
- no .env staged
- no secrets staged
- row counts match manifest
- column counts match manifest
- target distribution is generated
- missingness summary is generated
- sensitive/claim-risk inventory is generated
- temporal field audit is generated
- leakage-risk notes are generated
- claim-boundary scan passes
- real_api_calls is 0 unless explicitly approved
- model_calls is 0 unless explicitly approved
- raw_response_inspection is False unless explicitly approved

## 13. Claim boundary

Safe Pilot 05 claim:

Pilot 05 uses public CFPB complaint records to construct a real-data-backed research simulation of evidence-state degradation in recorded complaint-resolution outcome review. It studies whether structural validity and reliability-layer behaviour can diverge under controlled evidence degradation across decision, audit, and escalation stages.

Unsafe claims forbidden:
- Do not claim company misconduct.
- Do not claim consumer harm prevalence.
- Do not claim complaint records are representative of all consumers.
- Do not claim complaint narratives are verified as accurate or unbiased.
- Do not claim financial safety.
- Do not claim legal safety.
- Do not claim real-world deployment proof.
- Do not claim provider ranking.
- Do not claim general model superiority.
- Do not claim broad LLM reliability.
- Do not claim Q1 as a public result.
- Do not claim journal-level as a public result.
- Do not claim ground-breaking as a proven result.

Safe wording:
- real-data-backed complaint-resolution simulation
- public-data-backed evidence packet construction
- controlled evidence degradation
- reliability cascade measurement
- structural validity and reliability-layer behaviour can diverge
- decision, audit, and escalation behaviour can be tracked across evidence conditions

## 14. Research-strength assessment

CFPB Consumer Complaint Database improves the project because it adds:
- real public data,
- current consumer-finance complaint records,
- structured evidence fields,
- narrative availability when consented and scrubbed,
- outcome fields suitable for recorded outcome-review simulation,
- temporal fields,
- clear safety/claim-boundary limitations.

The main risks are:
- non-representative complaint data,
- consumer narratives are not verified,
- residual sensitivity in narratives and geography,
- company names can invite unsafe ranking claims,
- complaint outcomes do not prove truth, fault, harm, or compliance.

Level 1 assessment:

This is a strong active Pilot 05 path if and only if:
- raw complaint data is not committed,
- raw narratives are not committed,
- claims remain conservative,
- the task is recorded outcome-review simulation,
- validators are strict,
- real LLM calls happen only after explicit approval.

## 15. Next approval gate

Before any dataset audit run, the user must approve one exact acquisition route.

Recommended route:
- download a filtered CFPB complaint CSV manually from the official CFPB page,
- use a bounded date range,
- preferably use a manageable product category,
- save locally under data/raw/cfpb_complaints/,
- commit only sanitized audit outputs.

No download is performed by this document.
