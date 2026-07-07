# Pilot 05 HMDA Design Audit

Project: Reliability Cascades in AI Decision Systems / Evidence-State Reliability in Multi-Stage LLM Pipelines

Status: design-audit checkpoint only.

Date: 2026-07-07

Approved scope for this file:
- HMDA may be evaluated as the proposed Pilot 05 dataset path.
- No HMDA data has been downloaded.
- No external dataset has been committed.
- No API calls have been made.
- No real LLM/model API calls have been made.
- No raw prompts or raw model responses are introduced by this document.

## 1. Purpose

Pilot 05 is intended to repair the current empirical weakness in the project by adding a real-data-backed reliability cascade pilot.

The current repo already has:
- Pilot 03: real-LLM controlled evidence package in a synthetic administrative decision domain.
- Pilot 04: deterministic/no-call synthetic second-domain scaffold.
- Cross-pilot outputs: framework-level evidence across controlled synthetic settings.
- Final no-call validation checkpoint.

The current safe limitation is that the repo does not yet contain a real-data-backed empirical pilot.

Pilot 05 should therefore move the project from:

"controlled framework evidence only"

toward:

"framework plus real-data-backed simulation evidence that evidence-state degradation can matter in decision-support settings."

Pilot 05 must not be framed as real-world deployment proof.

## 2. Candidate dataset

Proposed dataset path:

Home Mortgage Disclosure Act (HMDA) public modified Loan/Application Register data, accessed through CFPB / FFIEC HMDA resources.

Primary official sources checked:
- CFPB HMDA data page: https://www.consumerfinance.gov/data-research/hmda/
- CFPB 2025 HMDA data release page: https://www.consumerfinance.gov/about-us/newsroom/2025-hmda-data-on-mortgage-lending-now-available/
- FFIEC HMDA Modified LAR page: https://ffiec.cfpb.gov/data-publication/modified-lar
- FFIEC HMDA Data Browser: https://ffiec.cfpb.gov/data-browser/
- CFPB historic HMDA data page: https://www.consumerfinance.gov/data-research/hmda/historic-data/
- CFPB Summary of 2023 HMDA Data: https://www.consumerfinance.gov/data-research/hmda/summary-of-2023-data-on-mortgage-lending/
- CFPB Public Data Inventory: https://www.consumerfinance.gov/data-research/public-data-inventory/
- Regulation C disclosure/reporting page: https://www.consumerfinance.gov/rules-policy/regulations/1003/5

## 3. Source and public availability audit

Current source assessment:

- HMDA is an official public mortgage data resource associated with CFPB and FFIEC.
- CFPB states that recent HMDA data can be accessed through the FFIEC HMDA Platform.
- The FFIEC Modified LAR page provides institution-level modified Loan/Application Register files by year.
- The FFIEC HMDA Data Browser allows filtering, aggregation, downloading, and visualization of HMDA datasets.
- CFPB describes HMDA data as public data, with privacy modifications applied to protect applicants and borrowers.

Level 1 reliability status:

PASS for public-source candidacy.

Caveat:
- Before any download or script-based acquisition step, the exact download method and any platform usage constraints must be confirmed and documented.
- This design audit does not decide whether to download national data, state-filtered data, institution-level LAR data, or API-filtered data.

## 4. License / terms audit

Current status:

- HMDA public data is available through official CFPB/FFIEC resources.
- CFPB public-data materials indicate that HMDA public data is modified from restricted data to protect privacy.
- A precise license label is not yet documented in this repo.

Level 1 reliability status:

PARTIAL.

Required before download:
- Confirm the exact source endpoint.
- Record the applicable terms, disclosure notes, or public-use conditions.
- Avoid committing raw HMDA data unless a later audit clearly justifies a small, safe, sanitized sample.

Default policy:
- Do not commit raw HMDA data.
- Prefer script-based acquisition instructions and local-only data paths.
- Commit only sanitized derived outputs, manifests, validation summaries, and documentation.

## 5. Sensitive attribute and ethics audit

HMDA is high-value but claim-sensitive.

Potentially sensitive or ethically relevant fields may include:
- applicant ethnicity
- applicant race
- applicant sex
- applicant age
- co-applicant demographic fields
- income
- debt-to-income ratio
- credit score related fields or credit score model fields where available
- geography/census tract fields
- denial reason fields where available
- action taken / recorded application outcome

The exact fields used must be verified against the official HMDA data dictionary / filing instructions for the selected data year.

Level 1 reliability status:

HIGH ETHICAL/CLAIM RISK, but manageable with strict framing.

Required safeguards:
- Treat the task as research simulation only.
- Do not ask a model to make real lending decisions.
- Do not claim any real lending decision is correct or incorrect.
- Do not claim financial safety, legal safety, lending compliance, or fair-lending validity.
- Do not publish raw row-level evidence packets if they risk re-identification or sensitive reconstruction.
- Prefer aggregate/sanitized derived outputs.

## 6. Target variable suitability

Candidate target/outcome:

Recorded HMDA action/outcome category, such as originated, denied, incomplete, withdrawn, approved-not-accepted, purchased loan, or other HMDA action categories depending on selected year/schema.

Safe interpretation:

- The target is a recorded outcome label for research simulation.
- The task may be framed as "recorded outcome review" or "outcome-category reconstruction under evidence degradation."
- The task is not a real lending approval/rejection task.

Unsafe interpretation:

- Do not frame the model as deciding whether a mortgage should be approved.
- Do not frame model error as proof that a real lender was wrong.
- Do not frame agreement with HMDA outcome as evidence of lending correctness.
- Do not use HMDA alone to infer fair-lending compliance.

Level 1 reliability status:

SUITABLE if framed as recorded-outcome simulation, not real lending decision-making.

## 7. Temporal split possibility

HMDA supports multi-year data availability.

Possible temporal designs:
- Train/design on one year and test simulation cases on a later year.
- Compare evidence-state reliability metrics across two years.
- Use year as a domain-shift axis.
- Start with a single-year sample for design audit, then expand only if needed.

Caveats:
- HMDA definitions, reporting thresholds, geography, and field meanings may change across years.
- Cross-year comparisons must document schema differences and avoid overclaiming temporal generalization.
- CFPB notes that comparisons across multiple years can be limited by definition/value/threshold changes.

Level 1 reliability status:

POSSIBLE, but requires schema-year caution.

Recommended first Pilot 05 design:
- Use one recent data year for initial dataset audit and evidence packet construction.
- Add temporal comparison only after schema consistency is confirmed.

## 8. Evidence-state construction plan

Pilot 05 should convert selected real HMDA rows into structured evidence packets.

Candidate original evidence packet sections:
- case metadata: synthetic case_id, source_year, selected sampling notes
- loan/request evidence: loan type, loan purpose, loan amount, lien status, occupancy type
- applicant financial evidence: income, debt-to-income ratio if available, affordability-related fields
- property evidence: property value, property type, tract/MSA/state/county fields where safe
- process/outcome evidence: action taken, denial reason fields where available
- demographic fields: either excluded from decision packets or included only in explicit audit/fairness-risk packets depending on final design approval

Important design choice still needed:

Should sensitive demographic fields be:
A. excluded from the decision evidence packet and used only for audit-risk documentation,
B. included in a separate fairness-risk/audit-only evidence packet,
C. included in degraded evidence experiments only after explicit ethics approval?

Default recommendation:
- Start with A or B.
- Do not include sensitive demographic fields in the model decision prompt without explicit approval.

## 9. Evidence degradation conditions

Minimum Pilot 05 evidence conditions:

1. complete
   All selected non-sensitive evidence fields available.

2. partial_missing_affordability
   Remove or mask affordability-related fields such as income, debt-to-income ratio, or loan-to-value proxy fields where available.

3. partial_missing_outcome_context
   Remove or mask denial reason fields or selected process/outcome context fields where available.

4. conflicted_noisy
   Introduce controlled contradictions or perturbations in non-sensitive evidence fields, clearly marked in derived condition metadata.

5. compressed_lossy
   Replace structured evidence with a lossy natural-language summary or compressed structured summary.

Condition safety rules:
- Do not create fake values that look like real raw HMDA records without marking them as transformed/simulated condition evidence.
- Keep original record identifiers out of committed outputs.
- Preserve an explicit link between condition and degradation operation in sanitized manifests.
- Do not commit raw prompts or raw responses.

## 10. Decision/audit/escalation chain plan

Pilot 05 should preserve the existing project logic:

Decision stage:
- Given evidence packet, provide a controlled outcome-review classification or risk-coded assessment.
- Must not be phrased as "approve/deny this real applicant."

Audit stage:
- Check whether the decision-stage output is supported by the available evidence state.
- Track structural validity and reliability-layer behaviour separately.

Escalation stage:
- Decide whether the case should be escalated because evidence is incomplete, conflicted, or insufficient.
- Track escalation contamination or missed escalation under degraded evidence.

No real model API calls are approved at this stage.

Before any real LLM chain:
- user must approve provider/model,
- user must approve cost/rate-limit risk,
- user must approve exact sample size,
- user must approve prompt family,
- raw prompt/response handling must be validated,
- only sanitized parsed outputs may be committed.

## 11. Sanitization and storage rules

Do not commit:
- raw HMDA full dataset
- raw row-level data extracts unless explicitly approved and privacy-audited
- raw prompts
- raw model responses
- JSONL raw dumps
- secrets
- API keys
- .env
- provider logs

Allowed to commit after validation:
- dataset audit summaries
- schema summaries
- row-count summaries
- missingness summaries
- target distribution summaries
- sensitive-field notes
- sanitized evidence packet templates
- transformed/degraded condition metadata
- sanitized parsed model outputs, if real LLM runs are later approved
- validation manifests
- claim-boundary safety reports

## 12. Validators required

Pilot 05 must include validators for:

Dataset audit:
- row count
- column count
- target distribution
- missingness profile
- selected-field inventory
- sensitive-field inventory
- temporal field availability
- leakage-risk notes

Evidence-state outputs:
- condition row counts
- one row per selected case per condition
- no raw applicant identifiers
- no raw prompts/responses
- no secrets
- no JSONL raw dumps
- no unapproved raw data files
- degradation condition labels valid
- target labels mapped and documented

Model-output outputs, only if later approved:
- schema validity
- parser success rate
- no raw response leakage
- no raw prompt leakage
- real_api_calls tracked
- raw_response_inspection tracked
- provider/model metadata sanitized
- claim-boundary safety scan

Repo-wide final validation:
- no untracked raw data
- no .env staged
- no secrets
- no forbidden claims
- all manifests present
- all row counts match expected values
- all generated outputs reproducible from committed scripts and local approved data path

## 13. Claim boundary

Safe Pilot 05 claim:

"Pilot 05 uses public HMDA records to construct a real-data-backed research simulation of evidence-state degradation in recorded mortgage-application outcome review. It studies whether structural validity and reliability-layer behaviour can diverge under controlled evidence degradation across decision, audit, and escalation stages."

Unsafe claims forbidden:

- Do not claim real lending decision validity.
- Do not claim financial safety.
- Do not claim legal safety.
- Do not claim lending regulation compliance.
- Do not claim fair-lending compliance.
- Do not claim real-world deployment proof.
- Do not claim universal LLM reliability.
- Do not claim broad model reliability.
- Do not claim provider ranking.
- Do not claim model superiority.
- Do not claim proof that a lender decision was correct or incorrect.
- Do not claim proof that an LLM can make mortgage decisions.
- Do not use Q1 as a public claim.
- Do not use journal-level as a public claim.
- Do not claim ground-breaking as a proven result.

Safe wording:
- real-data-backed simulation evidence
- public-data-backed evidence packet construction
- controlled evidence degradation
- reliability cascade measurement
- structural validity and reliability-layer behaviour can diverge
- decision, audit, and escalation behaviour can be tracked across evidence conditions

## 14. Research-strength assessment

HMDA improves the project because it adds:
- real public data,
- a decision-system-adjacent domain,
- meaningful evidence fields,
- recorded application outcome labels,
- possible multi-year structure,
- clear sensitive-attribute and claim-boundary audit requirements.

HMDA also increases risk because:
- the domain is financially and legally sensitive,
- HMDA fields include demographic and geography signals,
- HMDA is not enough on its own to evaluate lender compliance,
- the project must avoid any implication of real lending advice or decision validity.

Level 1 assessment:

HMDA is the strongest current Pilot 05 candidate if and only if:
- raw data is not committed,
- claims remain conservative,
- the task is recorded-outcome review simulation,
- sensitive fields are handled carefully,
- validators are strict,
- real LLM calls happen only after explicit approval.

## 15. Next approval gate

Before any coding or dataset acquisition, the user must approve the exact Pilot 05 acquisition/design route.

Open decision:

Preferred first implementation route:

Option A: Institution-level HMDA Modified LAR sample
- Use one or a few selected institutions.
- Smaller and easier to audit.
- But institution selection may introduce sampling bias.

Option B: Filtered HMDA Data Browser/API sample
- Use filters such as year/state/loan purpose.
- More controlled for sample construction.
- Requires careful endpoint/terms documentation.

Option C: Historic CFPB downloadable data sample
- Easier stable download documentation for 2007-2017.
- Older data and schema may be less aligned with current HMDA fields.

Recommendation:
- Start with Option B if the Data Browser/API path can produce a small documented sample without committing raw data.
- Use Option A as fallback if Browser/API filtering is too slow or unstable.
- Avoid national full-file download for the first Pilot 05 iteration.

Required user approval before next step:
"I approve Pilot 05 HMDA acquisition design using Option B, no raw data commit."

or choose another option.

## 16. Current checkpoint statement

This document is a design audit only.

No data was downloaded.
No dataset was selected for acquisition.
No model calls were made.
No raw prompts or responses were generated.
No files were staged.
No files were committed.

