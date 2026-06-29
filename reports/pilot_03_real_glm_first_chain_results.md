# Pilot 03 First Real GLM Chain Results

## Purpose

This report records the first completed real GLM-5.2 Pilot 03 chain results.

These results are real LLM outputs from Z.ai / GLM-5.2.

They are small-scale results and must not be generalised beyond the current Pilot 03 setup.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Runner: `experiments/pilot_03_zai_small_chain_run.py`
- Runner version: `pilot_03_zai_small_chain_run_v2`
- Task count: 1 synthetic administrative approval task
- Evidence conditions: 3
- Pipeline stages: decision -> audit -> escalation
- Total completed real GLM calls: 9
- Raw outputs: saved locally under `results/pilot_03_real_llm_analysis/`

## Saved run folders

```text
pilot_03_zai_small_chain_n1_20260629T191925Z
pilot_03_zai_small_chain_n1_20260629T192826Z
pilot_03_zai_small_chain_n1_20260629T194154Z
```

## Result summary

| Condition | Gold | Decision stage | Audit passed | Escalation stage | Final correct | Valid schemas | Total tokens |
|---|---|---|---|---|---|---|---:|
| original_evidence | approve | approve | True | approve | True | 3/3 | 2399 |
| missing_policy_rule | approve | approve | False | reject | False | 3/3 | 9606 |
| missing_one_required_unit | approve | reject | True | reject | False | 3/3 | 3386 |

## Parser and schema validity

Across the three completed real-chain runs:

- completed chain results: 3
- completed real GLM calls: 9
- decision-stage responses: 3
- audit-stage responses: 3
- escalation-stage responses: 3
- valid JSON responses: 9/9
- valid schema responses: 9/9
- invalid JSON responses: 0
- invalid schema responses: 0

## Early observed cascade signals

These are early observations only, based on one task per condition.

### Complete evidence

Under `original_evidence`, the decision, audit, and escalation stages stayed aligned with the gold decision.

```text
gold=approve -> decision=approve -> audit_passed=True -> escalation=approve
```

### Missing policy rule

Under `missing_policy_rule`, the initial decision stayed correct, but the audit failed the decision and escalation changed the final answer to reject.

```text
gold=approve -> decision=approve -> audit_passed=False -> escalation=reject
```

This is an early example of possible escalation-stage contamination or overcorrection after degraded evidence.

### Missing one required evidence unit

Under `missing_one_required_unit`, the decision stage rejected the applicant, the audit passed that decision, and escalation kept the rejection.

```text
gold=approve -> decision=reject -> audit_passed=True -> escalation=reject
```

This is an early example of possible audit false assurance under degraded evidence.

## Safe wording

```text
observed result under current Pilot 03 real LLM experimental conditions
```

## Reliability limitation

These results do not establish general GLM-5.2 reliability.

They do not establish final Pilot 03 results.

They show that the real GLM chain runner can execute and log complete decision-audit-escalation chains, and that the first one-task three-condition run produced schema-valid outputs with early evidence of reliability cascades under degraded evidence.

The next planned step is a larger controlled run, starting with 2 tasks across all 3 conditions.
