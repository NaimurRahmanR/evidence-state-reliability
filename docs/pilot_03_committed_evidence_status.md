# Pilot 03 committed evidence status

This document records the current committed Pilot 03 evidence state after the Anthropic/Claude 20-task validity-aware checkpoint.

## Current checkpoint

Latest committed checkpoint:

- `55ef916` — Add Pilot 03 master committed-output validator
- `6411b9b` — Add Pilot 03 Anthropic T0020 report validator
- `4d8783b` — Add Pilot 03 Anthropic T0020 valid report
- `9d06c87` — Add Pilot 03 Anthropic validity-aware selector

## Validation command

The committed evidence can be checked with:

```powershell
python -m experiments.pilot_03_validate_all_committed_outputs
```

Expected result:

```text
status: PASS
n_validation_commands: 2
n_failed_validation_commands: 0
real_api_calls: 0
raw_response_inspection: False
```

## Anthropic/Claude committed checkpoint

Scope:

- provider: `anthropic`
- model: `claude-opus-4-8`
- tasks: 20
- evidence conditions per task: 3
- selected completed chains: 60
- parsed stage responses: 180

Validity-aware final report:

- JSON-valid responses: 180/180
- schema-valid responses: 180/180
- invalid JSON responses: 0
- invalid schema responses: 0
- selected unique task-condition keys: 60/60

Condition-level summary:

| Condition | Chains | Decision correct | Escalation correct | Audit passed | Valid JSON chains | Valid schema chains |
|---|---:|---:|---:|---:|---:|---:|
| original_evidence | 20 | 20/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| missing_policy_rule | 20 | 10/20 | 17/20 | 0/20 | 20/20 | 20/20 |
| missing_one_required_unit | 20 | 10/20 | 10/20 | 14/20 | 20/20 | 20/20 |

## Validity-aware selector

The Anthropic/Claude result uses a committed selector to avoid duplicate or invalid local run contamination.

Selector status:

- candidate run directories found: 48
- selected valid run directories: 46
- selected unique task-condition keys: 60/60
- missing selected valid keys: 0
- duplicate selected keys: 0
- invalid selected rows: 0

## Targeted repair note

A targeted repair run was performed for:

- task: `P03-T0015`
- condition: `missing_one_required_unit`
- expected real Anthropic calls: 3
- result: completed
- parser result for repair: 3/3 JSON valid and 3/3 schema valid

The old invalid local chain was not deleted. It is excluded from the final committed Anthropic/Claude report by the validity-aware selector.

## Scope limits

These are observed results under the current controlled Pilot 03 real LLM experimental conditions.

They should not be interpreted as:

- broad deployment evidence
- general model reliability claims
- broad cross-provider conclusions
- confirmation of real-world performance

Raw responses, prompts, API keys, raw aggregate JSON files, and ignored local result folders are not committed.
