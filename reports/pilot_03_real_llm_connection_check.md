# Pilot 03 Real LLM Connection Check

## Purpose

This report records the first successful guarded real LLM connection check for Pilot 03.

This is not a Pilot 03 real LLM experiment.
This is not evidence of real pipeline reliability behaviour.
This is only a provider/model connectivity checkpoint.

## Confirmed connection-check setup

- Date: 2026-06-29
- Provider: Z.ai
- Model: GLM-5.2
- Endpoint: Z.ai chat completions endpoint
- Script: `experiments/pilot_03_zai_connection_check.py`
- Safety flag used locally: `PILOT03_REAL_LLM_ENABLED=true`
- Explicit confirmation flag used: `--confirm-real-llm-call`

## Observed result

The guarded connection check successfully reached Z.ai and received the expected response token.

Observed response:

```text
pilot03_connection_ok
```

Observed usage:

```text
completion_tokens: 32
reasoning_tokens: 25
prompt_tokens: 20
total_tokens: 52
```

## Safety checks

The connection-check script confirmed that:

- API key values were not printed.
- The real LLM call required both the local safety flag and the explicit command-line confirmation flag.
- The repository working tree remained clean after the call.
- Real calls were turned off again after the check by setting `PILOT03_REAL_LLM_ENABLED=false`.

## Reliability wording

The safe wording for this result is:

```text
observed result under current Pilot 03 real LLM connection-check conditions
```

## Scope limitation

This result only confirms that the local Pilot 03 code can make one guarded API call to Z.ai / GLM-5.2.

It does not show:

- real Pilot 03 task performance
- evidence-state reliability under real LLM conditions
- decision failure rates under real LLM conditions
- audit false assurance under real LLM conditions
- escalation contamination under real LLM conditions
- general GLM-5.2 reliability

The Pilot 03 real LLM experiment has not been run yet.
