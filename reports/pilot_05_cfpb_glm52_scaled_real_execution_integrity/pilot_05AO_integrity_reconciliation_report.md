# Pilot 05AN Integrity Reconciliation Report

## Status

05AO status: **PASS**  
Ready for 05AP metrics: **True**

This is a no-call reconciliation step over sanitized 05AN outputs only. It did not read API keys, did not read `.env`, did not write raw prompts, did not write raw responses, and did not create JSONL.

## Core accounting

| Item | Count |
|---|---:|
| Planned calls | 720 |
| Call plan rows | 720 |
| Call ledger rows | 720 |
| Persisted sanitized execution rows | 713 |
| Parser-invalid summary rows | 243 |
| Ledger parser-valid rows | 470 |
| Ledger parser-invalid/false rows | 250 |
| Persisted parser-valid rows | 470 |
| Persisted parser-invalid rows | 243 |
| Ledger-only rows missing from sanitized execution rows | 7 |
| Cumulative estimated cost USD | 2.2731216 |

## Interpretation boundary

This is now scaled real GLM-5.2 execution evidence, but not yet a paper-ready result. The correct claim is that the scaled run produced a complete call ledger and a large sanitized persisted execution set suitable for no-call analysis. The seven ledger-only/non-persisted rows must be explicitly accounted for in downstream metrics.

Do **not** claim broad GLM reliability, broad LLM reliability, real-world financial validity, regulated-decision validity, or deployment safety.

## Next recommended task

**TASK 05AP: Scaled Pilot 05 cascade metrics and paired uncertainty analysis**

05AP should use the 05AN ledger plus persisted sanitized execution rows, treat ledger-only rows as accountable failures/missing persisted outputs, and generate parser validity, stage reliability, evidence-condition deltas, audit false assurance, escalation recovery/loss, cascade sequence metrics, and bootstrap/paired confidence intervals.
