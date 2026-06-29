# Pilot 03 Real GLM Four-Task Results

## Purpose

This report records the first completed four-task controlled real GLM-5.2 Pilot 03 aggregate result.

These are real LLM outputs from Z.ai / GLM-5.2. They remain small-scale controlled results and must not be generalised beyond the current Pilot 03 setup, model, prompts, parser, tasks, and evidence conditions.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Parser: `pilot_03_parser_v2`
- Runner: `experiments/pilot_03_zai_small_chain_run.py`
- New P03-T0004 runner version: `pilot_03_zai_small_chain_run_v4`
- Aggregation utility: `experiments/pilot_03_aggregate_real_runs.py`
- Tasks: 4 synthetic administrative approval tasks
- Evidence conditions: 3
- Pipeline stages: decision -> audit -> escalation
- Combined completed chains: 12
- Combined completed real GLM calls: 36

## Source run folders

```text
pilot_03_zai_small_chain_n2_20260629T195801Z
pilot_03_zai_small_chain_p03_t0002_20260629T205234Z
pilot_03_zai_small_chain_p03_t0003_20260629T212651Z
pilot_03_zai_small_chain_p03_t0003_20260629T213210Z
pilot_03_zai_small_chain_p03_t0003_20260629T213750Z
pilot_03_zai_small_chain_p03_t0004_20260629T230442Z
pilot_03_zai_small_chain_p03_t0004_20260629T230732Z
pilot_03_zai_small_chain_p03_t0004_20260629T231233Z
```

## Parser validity

```text
real GLM responses: 36
decision-stage responses: 12
audit-stage responses: 12
escalation-stage responses: 12

valid JSON responses under parser v2: 36/36
valid schema responses under parser v2: 36/36
invalid JSON responses: 0
invalid schema responses: 0

complete chains: 12
valid chains: 12
valid_chain_rate: 1.0
```

## Combined chain summary

```text
condition_counts:
  original_evidence: 4
  missing_policy_rule: 4
  missing_one_required_unit: 4

gold_decisions:
  approve: 6
  reject: 6

decision_correct:
  True: 8
  False: 4

escalation_correct:
  True: 10
  False: 2

audit_passed:
  True: 5
  False: 7

decision_correct_rate: 0.666667
escalation_correct_rate: 0.833333
valid_chain_rate: 1.0
```

## Condition-level result summary

| Condition | Chains | Decision correct rate | Final correct rate | Audit passed | Valid chain rate |
|---|---:|---:|---:|---|---:|
| original_evidence | 4 | 1.000000 | 1.000000 | True: 4 | 1.000000 |
| missing_policy_rule | 4 | 0.500000 | 1.000000 | False: 4 | 1.000000 |
| missing_one_required_unit | 4 | 0.500000 | 0.500000 | False: 3, True: 1 | 1.000000 |

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
| P03-T0004 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0004 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0004 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |

## Early observed patterns

These are early observations only, based on four synthetic tasks.

1. Under `original_evidence`, all four chains stayed aligned with the gold decision.

2. Under `missing_policy_rule`, the decision stage was correct in 2/4 chains, but the escalation stage was correct in 4/4 chains. This is an early controlled observation of audit/escalation recovery under degraded evidence.

3. Under `missing_one_required_unit`, the decision stage was correct in 2/4 chains and the final escalation stage was also correct in 2/4 chains. In the current four-task set, the final failures occurred in approve cases where required evidence was missing.

4. For `P03-T0004`, all three conditions produced the correct final reject decision. However, audit passed under complete evidence and did not pass under the two degraded evidence conditions.

## Reproducible aggregate command

The four-task aggregate can be regenerated from saved raw real-response logs using:

~~~powershell
python -m experiments.pilot_03_aggregate_real_runs --run-dirs .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_n2_20260629T195801Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0002_20260629T205234Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T212651Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T213210Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0003_20260629T213750Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0004_20260629T230442Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0004_20260629T230732Z .\results\pilot_03_real_llm_analysis\pilot_03_zai_small_chain_p03_t0004_20260629T231233Z --output-json .\results\pilot_03_real_llm_analysis\pilot_03_real_glm_four_task_aggregate.json
~~~

## Local aggregate artifact

```text
results\pilot_03_real_llm_analysis\pilot_03_real_glm_four_task_aggregate.json
```

This JSON file is a local result artifact and is not committed because real LLM result folders are intentionally ignored.

## Safe wording

```text
observed result under current Pilot 03 real LLM experimental conditions
```

## Reliability limitation

These results do not establish general GLM-5.2 reliability.

They do not establish final Pilot 03 results.

They show that, under the current Pilot 03 setup, GLM-5.2 produced schema-valid decision-audit-escalation outputs across 36 real calls, and the small four-task run showed both recovery and final failure behaviours under degraded evidence.

The next step is to decide whether to scale cautiously to more tasks or add comparison-model checks later.
