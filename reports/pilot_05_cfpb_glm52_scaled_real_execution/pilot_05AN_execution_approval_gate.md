# TASK 05AN Approval Gate

Current package status: **preflight only**.

This preflight created no API/model calls and read no API key.

## Proposed real execution

- Model: `glm-5.2`
- Option: A
- Base cases: 60
- Evidence conditions: 4 (clean, compressed_lossy, partial_dropout, noisy_conflicting)
- Stages: 3 (decision, audit, escalation)
- Planned calls: 720
- Output contract: sanitized categorical CSV/JSON only
- Forbidden outputs: raw prompts, raw responses, JSONL, `.env`, raw CFPB data
- Default pricing assumption: $1.4/M input tokens and $4.4/M output tokens
- Exact spend: depends on actual token usage and must be bounded by user-approved cost cap

## To run real execution later

Only run after explicitly approving the model, call count, cost cap, storage contract, and abort rules.

Example:

```powershell
python experiments/pilot_05_cfpb_glm52_scaled_real_execution.py --mode execute --approve-real-api-calls --model glm-5.2 --base-url "https://api.z.ai/api/paas/v4" --api-key-env-var ZAI_API_KEY --cost-cap-usd 8 --expected-call-count 720
```

Replace `25` with the cost cap you actually approve.
