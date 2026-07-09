# TASK 05AN approval prompt — scaled Pilot 05 GLM-5.2 real execution

Use this only after reviewing the 05AM outputs.

I approve **TASK 05AN: SCALED PILOT 05 GLM-5.2 REAL EXECUTION** with the following exact boundaries:

- Model provider/display: GLM-5.2
- API model name: `glm-5.2`
- Run option: A
- Base cases: 60
- Evidence conditions: 4 (`clean`, `compressed_lossy`, `partial_dropout`, `noisy_conflicting`)
- Stages: 3 (`decision`, `audit`, `escalation`)
- Models: 1
- Maximum approved real model calls: 720
- Hard cost cap: £____  **I will fill this before execution**
- Storage contract: sanitized CSV/JSON/MD outputs only
- Raw prompt storage: forbidden
- Raw response storage: forbidden
- JSONL storage: forbidden
- `.env` commit/read-print exposure: forbidden; API key may only be read by the approved execution runner if explicitly needed for 05AN and must never be printed
- Raw CFPB data access: forbidden
- Commit/push after execution: not approved until I separately approve after validation

Abort rules:

1. Stop before exceeding the approved call cap.
2. Stop before exceeding the approved cost cap.
3. Stop if raw prompts, raw responses, JSONL, `.env`, or raw CFPB data would be written or printed.
4. Stop if sanitization validation fails.
5. Stop if call accounting becomes ambiguous.
6. Pause if early parser-invalid rate is unexpectedly high and ask before spending the remaining cap.
7. Stop if the model/provider differs from approved GLM-5.2 / `glm-5.2`.

Required 05AN outputs:

- sanitized execution manifest
- sanitized call-accounting table
- sanitized parsed output table
- parser validity by stage, condition, and condition-stage
- decision/audit/escalation validity tables
- cascade sequence metrics
- paired clean-vs-degraded deltas
- bootstrap confidence intervals or equivalent uncertainty estimates
- claim-boundary update
- final validation summary

Exact pricing status from 05AM: `requires_user_confirmation`. If exact GLM-5.2 pricing is not available locally, do not run 05AN until I approve a hard cost cap.
