# Pilot 03 Real GLM Three-Task Results

## Purpose

This report records the first completed three-task controlled real GLM-5.2 Pilot 03 aggregate result.

These are real LLM outputs from Z.ai / GLM-5.2.

They remain small-scale controlled results and must not be generalised beyond the current Pilot 03 setup, model, prompts, parser, tasks, and evidence conditions.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Parser: `pilot_03_parser_v2`
- Runner: `experiments/pilot_03_zai_small_chain_run.py`
- Aggregation utility: `experiments/pilot_03_aggregate_real_runs.py`
- Tasks: 3 synthetic administrative approval tasks
- Evidence conditions: 3
- Pipeline stages: decision -> audit -> escalation
- Combined completed chains: 9
- Combined completed real GLM calls: 27

## Source run folders

```text
pilot_03_zai_small_chain_n2_20260629T195801Z
pilot_03_zai_small_chain_p03_t0002_20260629T205234Z
pilot_03_zai_small_chain_p03_t0003_20260629T212651Z
pilot_03_zai_small_chain_p03_t0003_20260629T213210Z
pilot_03_zai_small_chain_p03_t0003_20260629T213750Z
```

## Parser validity

Across the combined three-task result:

```text
real GLM responses: 27
decision-stage responses: 9
audit-stage responses: 9
escalation-stage responses: 9

valid JSON responses under parser v2: 27/27
valid schema responses under parser v2: 27/27
invalid JSON responses: 0
invalid schema responses: 0

complete chains: 9
valid chains: 9
valid_chain_rate: 1.0
```

## Combined chain summary

```text
condition_counts:
  original_evidence: 3
  missing_policy_rule: 3
  missing_one_required_unit: 3

gold_decisions:
  approve: 6
  reject: 3

decision_correct:
  True: 5
  False: 4

escalation_correct:
  True: 7
  False: 2

audit_passed:
  True: 4
  False: 5

decision_correct_rate: 0.555556
escalation_correct_rate: 0.777778
valid_chain_rate: 1.0
```

## Condition-level result summary

| Condition | Chains | Decision correct rate | Final correct rate | Audit passed | Valid chain rate |
|---|---:|---:|---:|---|---:|
| original_evidence | 3 | 1.000000 | 1.000000 | True: 3 | 1.000000 |
| missing_policy_rule | 3 | 0.333333 | 1.000000 | False: 3 | 1.000000 |
| missing_one_required_unit | 3 | 0.333333 | 0.333333 | False: 2, True: 1 | 1.000000 |

## Combined chain-level table

| Task | Condition | Gold | Decision | Decision correct | Audit passed | Audit supported decision | Escalation | Final correct | Escalation overrode | Valid chain |
|---|---|---|---|---|---|---|---|---|---|---|
| P03-T0001 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0001 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0001 | missing_one_required_unit | approve | reject | False | False | reject | reject | False | False | True |
| P03-T0002 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0002 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0002 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0003 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0003 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0003 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |

## Early observed patterns

These are early observations only, based on three synthetic tasks.

### 1. Complete evidence stayed correct

Under `original_evidence`, all three chains stayed aligned with the gold decision.

```text
decision_correct_rate: 1.0
final_correct_rate: 1.0
audit_passed: 3/3
```

### 2. Missing policy rule produced decision-stage errors but escalation recovered them

Under `missing_policy_rule`, the decision stage was correct in only 1/3 chains, but the escalation stage was correct in 3/3 chains.

```text
decision_correct_rate: 0.333333
final_correct_rate: 1.0
audit_passed: 0/3
```

This is an early example of audit/escalation recovery under degraded evidence.

### 3. Missing one required evidence unit produced final failure in approve cases

Under `missing_one_required_unit`, the decision stage was correct in only 1/3 chains and the final escalation stage was also correct in only 1/3 chains.

```text
decision_correct_rate: 0.333333
final_correct_rate: 0.333333
```

This is the strongest early cascade signal in the current real GLM run.

### 4. Audit false assurance appeared in one degraded chain

For `P03-T0003` under `missing_one_required_unit`, the model rejected an approve case, the audit passed the rejection, and escalation kept reject.

```text
gold=approve -> decision=reject -> audit_passed=True -> escalation=reject
```

This is an early example of audit false assurance under degraded evidence.

## Reproducible aggregate command

The three-task aggregate can be regenerated from saved raw real-response logs using:

~~~powershell
python -m experiments.pilot_03_aggregate_real_runs `
  --run-dirs `
  .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_n2_20260629T195801Z `
  .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0002_20260629T205234Z `
  .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T212651Z `
  .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T213210Z `
  .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T213750Z `
  --output-json .\results\pilot_03_real_llm_analysis\pilot_03_real_glm_three_task_aggregate.json
~~~

The generated aggregate JSON is saved locally under:

~~~text
results\pilot_03_real_llm_analysis\pilot_03_real_glm_three_task_aggregate.json
~~~

This JSON file is a local result artifact and is not committed because real LLM result folders are intentionally ignored.

## Safe wording

```text
observed result under current Pilot 03 real LLM experimental conditions
```

## Reliability limitation

These results do not establish general GLM-5.2 reliability.

They do not establish final Pilot 03 results.

They show that, under the current Pilot 03 setup, GLM-5.2 produced schema-valid decision-audit-escalation outputs across 27 real calls, and the small three-task run showed both recovery and final failure behaviours under degraded evidence.

The next step is to scale cautiously to more tasks or add comparison-model checks.