# Cross-Pilot Final Status Checkpoint

## Scope

This checkpoint records the current committed state of the Evidence-State Reliability work after Pilot 04 and cross-pilot integration.

The repository now contains:

- Pilot 03: locked synthetic administrative approval evidence package.
- Pilot 04: deterministic no-call synthetic loan-risk decision-support evidence package.
- Cross-pilot outputs: framework summary, validation summary, condition alignment, metric inventory, figures, and tables.

## Validation status

| Component | Status | Steps | Failed steps | Checks | Failed checks | API calls | Raw response inspection |
|---|---:|---:|---:|---:|---:|---:|---:|
| Pilot 03 no-call pipeline | PASS | 14 | 0 |  |  | 0 | False |
| Pilot 03 comparison validation | PASS |  |  | 171 | 0 | 0 | False |
| Pilot 04 no-call pipeline | PASS | 13 | 0 |  |  | 0 | False |
| Pilot 04 committed-output validation | PASS |  |  | 124 | 0 | 0 | False |
| Cross-pilot report | PASS |  |  |  |  | 0 | False |
| Cross-pilot validation | PASS |  |  | 28 | 0 | 0 | False |
| Cross-pilot figures/tables | PASS |  |  |  |  | 0 | False |

## Cross-pilot figure/table status

- Tables: 7
- Figures: 6

## Safe interpretation

The current repo supports a conservative controlled-experiment claim:

- evidence-state degradation is measurable;
- structural validity and reliability-layer behaviour are separate measurements;
- decision, audit, and escalation metrics can be compared across evidence conditions;
- the same measurement framing is implemented across two controlled synthetic domains.

The current repo does not establish operational deployment validity, overall model superiority, or safety for regulated use cases.

## Reproducibility boundary

This final checkpoint was generated from committed sanitized outputs and no-call validation scripts.

- real_api_calls: 0
- raw_response_inspection: False
