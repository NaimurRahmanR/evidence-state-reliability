# Pilot 05 Dataset Switch: HMDA to CFPB Consumer Complaint Database

Project: Reliability Cascades in AI Decision Systems / Evidence-State Reliability in Multi-Stage LLM Pipelines

Status: approved dataset-route switch checkpoint.

Date: 2026-07-07

## 1. Approved user decision

The user approved the following switch:

"I approve switching Pilot 05 to the CFPB Consumer Complaint Database as the real-data-backed empirical pilot."

## 2. Why the switch happened

The original Pilot 05 direction was HMDA through the FFIEC HMDA Data Browser filtered 2025 sample route.

During the workflow, the FFIEC HMDA platform showed a temporary unavailability page. Because the project priority is to build a real-data-backed empirical pilot efficiently without weakening reliability controls, the dataset path was reconsidered.

The CFPB Consumer Complaint Database was selected as the active Pilot 05 real-data-backed route because it is:
- official public CFPB data,
- downloadable/exportable,
- available through a public API,
- current enough for a near-term empirical pilot,
- structured enough for evidence-state construction,
- suitable for decision/audit/escalation simulation,
- safer than a mortgage approval/denial framing,
- still high-value for AI decision-system reliability research.

## 3. HMDA status after switch

HMDA work is not deleted.

Existing HMDA files remain as:
- a documented attempted path,
- an audited dataset-candidate path,
- a possible future backup if FFIEC availability returns,
- a record of why raw-data guardrails were created.

HMDA is not the active Pilot 05 empirical path after this switch unless explicitly re-approved later.

## 4. Active Pilot 05 dataset path

Active dataset:

CFPB Consumer Complaint Database.

Official source pages:
- Consumer Complaint Database: https://www.consumerfinance.gov/data-research/consumer-complaints/
- Complaint data sharing explanation: https://www.consumerfinance.gov/complaint/data-use/
- API field reference: https://cfpb.github.io/api/ccdb/fields.html
- API documentation: https://cfpb.github.io/api/ccdb/

## 5. Safe active claim

Safe claim:

Pilot 05 uses public CFPB complaint records to construct a real-data-backed research simulation of evidence-state degradation in complaint-resolution outcome review. It studies whether structural validity and reliability-layer behaviour can diverge under controlled evidence degradation across decision, audit, and escalation stages.

## 6. Unsafe claims forbidden

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

## 7. Current checkpoint

No CFPB complaint data has been downloaded by this checkpoint.
No CFPB complaint API call has been made by this checkpoint.
No raw CFPB complaint file has been committed.
No model API call has been made.
No raw prompts or raw model responses have been created.
No files are staged by this checkpoint.
