# Pilot 03 Real GLM 10-Task Results

## Purpose

This report documents the 10-task controlled real GLM-5.2 checkpoint for Pilot 03.
Use only conservative Level 1 wording: observed result under current Pilot 03 real LLM experimental conditions.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Pipeline: decision -> audit -> escalation
- Evidence conditions: original_evidence, missing_policy_rule, missing_one_required_unit
- Aggregate source: `results\pilot_03_real_llm_analysis\pilot_03_real_glm_t0010_aggregate.json`
- Completed chains: 30
- Parsed responses: 90
- Stage counts: {'decision': 30, 'audit': 30, 'escalation': 30}
- Valid JSON counts: {'True': 90}
- Valid schema counts: {'True': 90}

## Overall Summary

- Decision correct: 20/30 (0.666667)
- Escalation correct: 25/30 (0.833333)
- Valid chain: 30/30 (1.0)

## Condition-Level Summary

| condition | n | gold_decisions | decision_correct_rate | escalation_correct_rate | audit_passed | valid_chain_rate |
| --- | --- | --- | --- | --- | --- | --- |
| original_evidence | 10 | approve:5, reject:5 | 1.0 | 1.0 | True:10 | 1.0 |
| missing_policy_rule | 10 | approve:5, reject:5 | 0.5 | 1.0 | False:9, True:1 | 1.0 |
| missing_one_required_unit | 10 | approve:5, reject:5 | 0.5 | 0.5 | False:6, True:4 | 1.0 |

## Failure and Recovery Taxonomy

| failure_or_pattern | n | rate | conditions | gold_decisions | task_ids |
| --- | --- | --- | --- | --- | --- |
| decision_error | 10 | 0.333333 | missing_one_required_unit:5, missing_policy_rule:5 | approve:10 | P03-T0001, P03-T0001, P03-T0003, P03-T0003, P03-T0005, P03-T0005, P03-T0007, P03-T0007, P03-T0009, P03-T0009 |
| escalation_recovery_after_decision_error | 5 | 0.166667 | missing_policy_rule:5 | approve:5 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009 |
| unrecovered_final_error | 5 | 0.166667 | missing_one_required_unit:5 | approve:5 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009 |
| audit_pass_on_incorrect_decision | 5 | 0.166667 | missing_one_required_unit:4, missing_policy_rule:1 | approve:5 | P03-T0003, P03-T0005, P03-T0005, P03-T0007, P03-T0009 |
| audit_block_on_incorrect_decision | 5 | 0.166667 | missing_one_required_unit:1, missing_policy_rule:4 | approve:5 | P03-T0001, P03-T0001, P03-T0003, P03-T0007, P03-T0009 |
| escalation_override | 5 | 0.166667 | missing_policy_rule:5 | approve:5 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009 |
| correct_complete_chain | 10 | 0.333333 | original_evidence:10 | approve:5, reject:5 | P03-T0001, P03-T0002, P03-T0003, P03-T0004, P03-T0005, P03-T0006, P03-T0007, P03-T0008, P03-T0009, P03-T0010 |

## Chain-Level Results

| task_id | condition | gold_decision | decision | decision_correct | audit_passed | audit_supported_decision | escalation | escalation_correct | overrode | valid_chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
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
| P03-T0005 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0005 | missing_policy_rule | approve | reject | False | True | reject | approve | True | True | True |
| P03-T0005 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0006 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0006 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0006 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0007 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0007 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0007 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0008 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0008 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0008 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0009 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0009 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0009 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0010 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0010 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0010 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |

## Generated Tables

- Condition CSV: `reports\pilot_03_real_glm_t0010_condition_summary.csv`
- Failure taxonomy CSV: `reports\pilot_03_real_glm_t0010_failure_taxonomy.csv`

## Safe Wording

> observed result under current Pilot 03 real LLM experimental conditions

Do not claim general GLM reliability, real-world deployment validity, or complete evidence from this checkpoint alone.

## Raw Combined Summary

```json
{
  "audit_passed": {
    "False": 15,
    "True": 15
  },
  "condition_counts": {
    "missing_one_required_unit": 10,
    "missing_policy_rule": 10,
    "original_evidence": 10
  },
  "decision_correct": {
    "False": 10,
    "True": 20
  },
  "decision_correct_rate": 0.666667,
  "escalation_correct": {
    "False": 5,
    "True": 25
  },
  "escalation_correct_rate": 0.833333,
  "gold_decisions": {
    "approve": 15,
    "reject": 15
  },
  "n_chain_rows": 30,
  "source_runs": {
    "pilot_03_zai_small_chain_n2_20260629T195801Z": 4,
    "pilot_03_zai_small_chain_p03_t0002_20260629T205234Z": 2,
    "pilot_03_zai_small_chain_p03_t0003_20260629T212651Z": 1,
    "pilot_03_zai_small_chain_p03_t0003_20260629T213210Z": 1,
    "pilot_03_zai_small_chain_p03_t0003_20260629T213750Z": 1,
    "pilot_03_zai_small_chain_p03_t0004_20260629T230442Z": 1,
    "pilot_03_zai_small_chain_p03_t0004_20260629T230732Z": 1,
    "pilot_03_zai_small_chain_p03_t0004_20260629T231233Z": 1,
    "pilot_03_zai_small_chain_p03_t0005_20260630T001835Z": 3,
    "pilot_03_zai_small_chain_p03_t0006_20260630T002428Z": 3,
    "pilot_03_zai_small_chain_selected4_20260630T005018Z": 12
  },
  "valid_chain": {
    "True": 30
  },
  "valid_chain_rate": 1.0
}
```
