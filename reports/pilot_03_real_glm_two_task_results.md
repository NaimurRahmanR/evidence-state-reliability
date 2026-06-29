# Pilot 03 Real GLM Two-Task Results

## Purpose

This report records the first completed two-task real GLM-5.2 Pilot 03 chain result.

The result combines one partial checkpoint run and one targeted completion run.

These are real LLM outputs from Z.ai / GLM-5.2.

They remain small-scale controlled results and must not be generalised beyond the current Pilot 03 setup.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Parser: `pilot_03_parser_v2`
- Runner: `experiments/pilot_03_zai_small_chain_run.py`
- Runner versions involved: `pilot_03_zai_small_chain_run_v2` and `pilot_03_zai_small_chain_run_v3`
- Re-parse utility: `experiments/pilot_03_reparse_real_run.py`
- Tasks: 2 synthetic administrative approval tasks
- Evidence conditions: 3
- Pipeline stages: decision -> audit -> escalation
- Combined completed chains: 6
- Combined completed real GLM calls: 18

## Source run folders

```text
pilot_03_zai_small_chain_n2_20260629T195801Z
pilot_03_zai_small_chain_p03_t0002_20260629T205234Z
```

## Combined chain-level result table

| Task | Condition | Gold | Decision | Decision correct | Audit passed | Audit supported decision | Escalation | Final correct | Escalation overrode | Valid chain |
|---|---|---|---|---|---|---|---|---|---|---|
| P03-T0001 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0001 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0001 | missing_one_required_unit | approve | reject | False | False | reject | reject | False | False | True |
| P03-T0002 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0002 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0002 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |

## Combined parser validity

Across the combined two-task result:

- real GLM responses: 18
- valid JSON responses under parser v2: 18/18
- valid schema responses under parser v2: 18/18
- invalid JSON responses under parser v2: 0
- invalid schema responses under parser v2: 0
- complete chains: 6/6
- valid chains: 6/6

Important parser note:

The earlier partial run originally showed two invalid JSON responses under parser v1 because GLM returned valid JSON inside markdown code fences. Parser v2 now handles fenced JSON while preserving the raw response text exactly in logs.

## Combined chain summary

```text
condition_counts:
  original_evidence: 2
  missing_policy_rule: 2
  missing_one_required_unit: 2

gold_decisions:
  approve: 3
  reject: 3

decision_correct:
  True: 4
  False: 2

escalation_correct:
  True: 5
  False: 1

audit_passed:
  True: 2
  False: 4
```

## Early observed patterns

These are early observations only, based on two synthetic tasks.

### 1. Complete evidence stayed correct

For both tasks under `original_evidence`, the full chain stayed aligned with the gold decision.

```text
P03-T0001: approve -> approve -> audit passed -> approve
P03-T0002: reject -> reject -> audit passed -> reject
```

### 2. Missing policy rule produced a recoverable decision error for P03-T0001

For `P03-T0001` under `missing_policy_rule`, the decision stage rejected incorrectly. The audit stage did not pass the decision, supported approve, and escalation overrode the earlier rejection back to approve.

```text
gold=approve -> decision=reject -> audit_supported_decision=approve -> escalation=approve
```

This is an early example of audit/escalation recovery after a decision-stage error.

### 3. Missing one required unit produced final failure for P03-T0001

For `P03-T0001` under `missing_one_required_unit`, the decision stage rejected incorrectly and escalation kept reject.

```text
gold=approve -> decision=reject -> audit_supported_decision=reject -> escalation=reject
```

This is an early example of final failure under degraded evidence.

### 4. Degraded evidence did not change the final decision for P03-T0002

For `P03-T0002`, the gold decision was reject. Under both degraded evidence conditions, the model still rejected and the final escalation decision stayed correct.

```text
gold=reject -> decision=reject -> escalation=reject
```

However, the audit stage did not pass the decision under the degraded conditions, which suggests the audit component treated the degraded evidence state as insufficient or problematic even when the final answer was correct.

## Safe wording

```text
observed result under current Pilot 03 real LLM experimental conditions
```

## Reliability limitation

These results do not establish general GLM-5.2 reliability.

They do not establish final Pilot 03 results.

They show that, under the current Pilot 03 setup, GLM-5.2 produced schema-valid decision-audit-escalation outputs across 18 real calls, and the small two-task run showed both recovery and failure behaviours under degraded evidence.

The next step is to scale cautiously to more tasks, using targeted runs and parser v2.
