# Pilot 05BA Manuscript Integrity and Submission-Readiness Audit

## Audit boundary

- Manuscript: `reports/pilot_05_verified_citation_integration/pilot_05AY_citation_integrated_manuscript.md`
- Manuscript SHA-256: `5D79D5DC4518B413CD270FA2002ADA69F10BCDC45FEBE52013103D8BF3B22C6B`
- Secured repository commit: `c3cecc13539f47d6e5af7bbb39d12d13590f756f`
- Reads: committed sanitized manuscript-supporting artifacts only
- Manuscript edits: none
- Experiments/model/API calls: none
- Raw data, `.env`, raw prompts/responses, JSONL: not accessed

## Overall verdict

`NOT_SUBMISSION_READY_MAJOR_REPAIR`

- BLOCKER issues: 0
- MAJOR issues: 19
- MODERATE issues: 10
- MINOR issues: 1
- Required structural sections detected: YES
- Protected numerical checks all passed: YES
- Citation checks all passed: YES
- Internal scaffold matches detected: 21

## Answers to the ten submission-readiness questions

### 1. Is the current manuscript structurally a complete paper?

It contains the expected core academic sections, but it is not yet a clean journal-form paper because internal assembly/scaffold sections remain.

### 2. Is it internally numerically consistent?

Yes for every protected check implemented in this audit.

### 3. Is its novelty claim defensible?

Yes, only within the verified bounded verdict: Bounded combination-and-operationalization differentiation supported; global priority or first-ever novelty not established.

### 4. Are citations complete and correctly bounded?

The automated citation-integrity checks passed; final human citation-placement review is still required.

### 5. Does it still contain internal scaffold/report language?

Yes. 21 scaffold-pattern checks failed.

### 6. Is the single-model Pilot 05 scope an acceptance blocker or a disclosed limitation?

It is not automatically an acceptance blocker for a bounded single-model study. It is a major external-validity limitation that must be explicit in the abstract, discussion, limitations, and conclusion.

### 7. Is another scaled model run scientifically necessary before submission?

No for the current bounded within-experiment claim. It becomes necessary only if the paper claims cross-model or provider-general reliability effects, or if a chosen venue explicitly requires broader empirical generalisation.

### 8. What exact work remains before journal targeting?

Resolve every BLOCKER and MAJOR issue; remove internal task/scaffold language; consolidate section hierarchy; convert source packs into numbered tables and figures; repair any failed numerical, citation, notation, and alignment checks; then conduct a final human claim-to-evidence review and select a target journal.

### 9. Is Word/PDF conversion justified now?

No. Substantive manuscript repair should occur before Word/PDF conversion.

### 10. What is the shortest evidence-grounded route to a submission-ready paper?

Perform one bounded manuscript-repair task using this issue register, without new experiments; rerun 05BA against the repaired manuscript; obtain a clean integrity verdict; then format the paper for the selected journal. Add another scaled model only if the intended claim or venue requires cross-model generalisation.

## Interpretation boundary

Audit execution `PASS` means the audit completed and validated its output contract. It does not mean the manuscript is submission-ready. Submission readiness is reported separately by the verdict above.
