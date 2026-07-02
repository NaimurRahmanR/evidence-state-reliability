# Pilot 03 Real GLM 20-Task Results

## Purpose

This report documents the 20-task controlled real GLM-5.2 checkpoint for Pilot 03.
Use only conservative Level 1 wording: observed result under current Pilot 03 real LLM experimental conditions.

## Scope

- Provider: Z.ai
- Model: GLM-5.2
- Pipeline: decision -> audit -> escalation
- Evidence conditions: original_evidence, missing_policy_rule, missing_one_required_unit
- Aggregate source: `results\pilot_03_real_llm_analysis\pilot_03_real_glm_t0020_aggregate.json`
- Completed chains: 60
- Parsed responses: 180
- Stage counts: {'decision': 60, 'audit': 60, 'escalation': 60}
- Valid JSON counts: {'True': 180}
- Valid schema counts: {'True': 180}

## Overall Summary

- Decision correct: 40/60 (0.666667)
- Escalation correct: 50/60 (0.833333)
- Valid chain: 60/60 (1.0)

## Condition-Level Summary

| condition | n | gold_decisions | decision_correct_rate | escalation_correct_rate | audit_passed | valid_chain_rate |
| --- | --- | --- | --- | --- | --- | --- |
| original_evidence | 20 | approve:10, reject:10 | 1.0 | 1.0 | True:20 | 1.0 |
| missing_policy_rule | 20 | approve:10, reject:10 | 0.5 | 1.0 | False:18, True:2 | 1.0 |
| missing_one_required_unit | 20 | approve:10, reject:10 | 0.5 | 0.5 | False:9, True:11 | 1.0 |

## Failure and Recovery Taxonomy

| failure_or_pattern | n | rate | conditions | gold_decisions | task_ids |
| --- | --- | --- | --- | --- | --- |
| decision_error | 20 | 0.333333 | missing_one_required_unit:10, missing_policy_rule:10 | approve:20 | P03-T0001, P03-T0001, P03-T0003, P03-T0003, P03-T0005, P03-T0005, P03-T0007, P03-T0007, P03-T0009, P03-T0009, P03-T0011, P03-T0011, P03-T0013, P03-T0013, P03-T0015, P03-T0015, P03-T0017, P03-T0017, P03-T0019, P03-T0019 |
| escalation_recovery_after_decision_error | 10 | 0.166667 | missing_policy_rule:10 | approve:10 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009, P03-T0011, P03-T0013, P03-T0015, P03-T0017, P03-T0019 |
| unrecovered_final_error | 10 | 0.166667 | missing_one_required_unit:10 | approve:10 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009, P03-T0011, P03-T0013, P03-T0015, P03-T0017, P03-T0019 |
| audit_pass_on_incorrect_decision | 11 | 0.183333 | missing_one_required_unit:9, missing_policy_rule:2 | approve:11 | P03-T0003, P03-T0005, P03-T0005, P03-T0007, P03-T0009, P03-T0011, P03-T0013, P03-T0015, P03-T0015, P03-T0017, P03-T0019 |
| audit_block_on_incorrect_decision | 9 | 0.15 | missing_one_required_unit:1, missing_policy_rule:8 | approve:9 | P03-T0001, P03-T0001, P03-T0003, P03-T0007, P03-T0009, P03-T0011, P03-T0013, P03-T0017, P03-T0019 |
| escalation_override | 10 | 0.166667 | missing_policy_rule:10 | approve:10 | P03-T0001, P03-T0003, P03-T0005, P03-T0007, P03-T0009, P03-T0011, P03-T0013, P03-T0015, P03-T0017, P03-T0019 |
| correct_complete_chain | 22 | 0.366667 | missing_one_required_unit:2, original_evidence:20 | approve:10, reject:12 | P03-T0001, P03-T0002, P03-T0003, P03-T0004, P03-T0005, P03-T0006, P03-T0007, P03-T0008, P03-T0009, P03-T0010, P03-T0011, P03-T0012, P03-T0013, P03-T0014, P03-T0014, P03-T0015, P03-T0016, P03-T0017, P03-T0018, P03-T0019, P03-T0020, P03-T0020 |

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
| P03-T0011 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0011 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0011 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0012 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0012 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0012 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0013 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0013 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0013 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0014 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0014 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0014 | missing_one_required_unit | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0015 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0015 | missing_policy_rule | approve | reject | False | True | reject | approve | True | True | True |
| P03-T0015 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0016 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0016 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0016 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0017 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0017 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0017 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0018 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0018 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0018 | missing_one_required_unit | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0019 | original_evidence | approve | approve | True | True | approve | approve | True | False | True |
| P03-T0019 | missing_policy_rule | approve | reject | False | False | approve | approve | True | True | True |
| P03-T0019 | missing_one_required_unit | approve | reject | False | True | reject | reject | False | False | True |
| P03-T0020 | original_evidence | reject | reject | True | True | reject | reject | True | False | True |
| P03-T0020 | missing_policy_rule | reject | reject | True | False | reject | reject | True | False | True |
| P03-T0020 | missing_one_required_unit | reject | reject | True | True | reject | reject | True | False | True |

## Generated Tables

- Condition CSV: `reports\pilot_03_real_glm_t0020_condition_summary.csv`
- Failure taxonomy CSV: `reports\pilot_03_real_glm_t0020_failure_taxonomy.csv`

## Safe Wording

> observed result under current Pilot 03 real LLM experimental conditions

Do not claim general GLM reliability, real-world deployment validity, or complete evidence from this checkpoint alone.

## Raw Combined Summary

```json
{
  "audit_passed": {
    "False": 27,
    "True": 33
  },
  "condition_counts": {
    "missing_one_required_unit": 20,
    "missing_policy_rule": 20,
    "original_evidence": 20
  },
  "decision_correct": {
    "False": 20,
    "True": 40
  },
  "decision_correct_rate": 0.666667,
  "escalation_correct": {
    "False": 10,
    "True": 50
  },
  "escalation_correct_rate": 0.833333,
  "gold_decisions": {
    "approve": 30,
    "reject": 30
  },
  "n_chain_rows": 60,
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
    "pilot_03_zai_small_chain_p03_t0012_20260630T015814Z": 1,
    "pilot_03_zai_small_chain_selected3_20260630T020000Z": 9,
    "pilot_03_zai_small_chain_selected4_20260630T005018Z": 12,
    "pilot_03_zai_small_chain_selected5_20260630T013957Z": 5,
    "pilot_03_zai_small_chain_selected5_20260630T021837Z": 15
  },
  "valid_chain": {
    "True": 60
  },
  "valid_chain_rate": 1.0
}
```
