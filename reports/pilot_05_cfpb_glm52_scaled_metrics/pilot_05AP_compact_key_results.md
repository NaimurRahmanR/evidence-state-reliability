# Pilot 05AP-B Compact Key Results

Task: 05AP-B
Patch version: 05AP_B_OUTPUT_CONTRACT_PATCH_V1
Generated UTC: 2026-07-09T16:21:18.120018+00:00

## What is safely established

- The scaled 05AN GLM-5.2 run has 720 ledger rows and 713 sanitized persisted execution rows.
- The persisted sanitized rows include 470 parser-valid rows and 243 parser-invalid rows.
- The ledger accounts for 470 parser-valid rows and 250 parser-invalid rows.
- The 05AO reconciliation accounts for 7 ledger-only rows missing from sanitized persisted rows.
- The estimated cumulative cost is 2.2731216 USD, under the approved cap.

## Main empirical signal

The scaled metrics indicate that degraded evidence conditions produce consistently negative paired deltas for stage success, while parser-valid deltas are positive across the degraded paired comparisons. This supports a claim-bounded interpretation that parser validity and evidence-state reliability are separable measurement layers in this Pilot 05 setting.

- Stage-success degraded-minus-clean delta range: -0.517241 to -0.40678.
- Parser-valid degraded-minus-clean delta range: 0.067797 to 0.368421.
- Mean degraded audit detection rate among parser-valid degraded audit rows: 1.0.
- Mean degraded escalation recovery rate among parser-valid degraded escalation rows: 0.0.

## Claim boundary

These results are scaled, real-model, sanitized Pilot 05 evidence. They do not prove broad GLM-5.2 reliability, real-world financial/regulatory validity, or deployment readiness. They support paper development only after the outputs are committed, claim-boundary tables are updated, and figure/table validation passes.
