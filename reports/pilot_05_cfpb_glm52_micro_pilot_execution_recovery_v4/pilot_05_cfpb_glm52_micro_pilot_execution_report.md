# Pilot 05 CFPB GLM-5.2 Micro-Pilot Execution

## Status

- Status: PASS_WITH_PRIOR_UNPERSISTED_CALLS
- Runner mode: REAL_EXECUTION_RECOVERY_SANITIZED_ONLY
- Model provider: Z.ai
- Model: GLM-5.2 / `glm-5.2`
- Configured call count: 36
- API/model calls: 33
- Successful API calls: 33
- Parsed JSON valid count: 17
- Estimated cost GBP: 0.081357

## Storage and safety

- Raw prompts written: False
- Raw responses written: False
- JSONL written: False
- API key source: local environment or local `.env`; key was not printed or written.
- Outputs are sanitized categorical CSV/JSON/MD artifacts only.

## Evidence source

- Sanitized evidence packet table: `reports\pilot_05_cfpb_evidence_packets\pilot_05_cfpb_sanitized_evidence_packets.csv`

## Stage summary

- decision: calls=11, parsed_valid=4, high_uncertainty=11, insufficient_or_more_info=4
- audit: calls=11, parsed_valid=5, high_uncertainty=8, insufficient_or_more_info=0
- escalation: calls=11, parsed_valid=8, high_uncertainty=8, insufficient_or_more_info=0

## Claim boundary

This is a controlled real-LLM micro-pilot on sanitized real-data-backed evidence packets. It is not a deployment study, not a regulated decision system, and not evidence of provider superiority.
