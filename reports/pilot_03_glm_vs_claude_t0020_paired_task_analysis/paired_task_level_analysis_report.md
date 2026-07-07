# Pilot 03 full GLM-5.2 vs Anthropic/Claude paired task-level analysis

Generated at UTC: 2026-07-07T09:49:31+00:00

## Scope

Paired task-level analysis for the controlled Pilot 03 20-task GLM-5.2 and Anthropic/Claude comparison. This analysis uses committed sanitized paired-chain outputs only and should not be interpreted as broad deployment evidence or broad cross-provider conclusions.

This report focuses on task-condition paired behavior: agreement, disagreement, shared errors, audit differences, and escalation recovery patterns.

## Condition-level paired profile

| Condition | n | Decision both correct | Decision both wrong | Escalation both correct | Escalation both wrong | Audit both passed | Audit disagreement | GLM recoveries | Claude recoveries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| original_evidence | 20 | 20 (1.0) | 0 (0.0) | 20 (1.0) | 0 (0.0) | 20 (1.0) | 0 | 0 | 0 |
| missing_policy_rule | 20 | 10 (0.5) | 10 (0.5) | 17 (0.85) | 0 (0.0) | 0 (0.0) | 2 | 10 | 7 |
| missing_one_required_unit | 20 | 10 (0.5) | 10 (0.5) | 10 (0.5) | 10 (0.5) | 10 (0.5) | 5 | 0 | 0 |

## Task-pattern counts

| Task pattern | n tasks |
| --- | ---: |
| audit_disagreement_only | 4 |
| paired_outcomes_aligned | 6 |
| shared_escalation_error_present | 10 |

## High-signal task-condition cases

| Task | Condition | Reasons | GLM transition | Claude transition |
| --- | --- | --- | --- | --- |
| P03-T0001 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0001 | missing_one_required_unit | audit_disagreement,both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0002 | missing_one_required_unit | audit_disagreement | decision_correct_preserved | decision_correct_preserved |
| P03-T0003 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0003 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0004 | missing_one_required_unit | audit_disagreement | decision_correct_preserved | decision_correct_preserved |
| P03-T0005 | missing_policy_rule | audit_disagreement,both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0005 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0007 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0007 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0009 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0009 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0011 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0011 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0012 | missing_one_required_unit | audit_disagreement | decision_correct_preserved | decision_correct_preserved |
| P03-T0013 | missing_policy_rule | escalation_disagreement,both_decision_wrong,glm_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_not_recovered |
| P03-T0013 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0014 | missing_one_required_unit | audit_disagreement | decision_correct_preserved | decision_correct_preserved |
| P03-T0015 | missing_policy_rule | escalation_disagreement,audit_disagreement,both_decision_wrong,glm_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_not_recovered |
| P03-T0015 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0017 | missing_policy_rule | escalation_disagreement,both_decision_wrong,glm_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_not_recovered |
| P03-T0017 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |
| P03-T0019 | missing_policy_rule | both_decision_wrong,glm_recovered_by_escalation,claude_recovered_by_escalation | decision_wrong_recovered_by_escalation | decision_wrong_recovered_by_escalation |
| P03-T0019 | missing_one_required_unit | both_decision_wrong,both_escalation_wrong | decision_wrong_not_recovered | decision_wrong_not_recovered |

## Manifest

```json
{
  "created_at_utc": "2026-07-07T09:49:31+00:00",
  "methods": {
    "pairing": "same task_id and same evidence condition across GLM-5.2 and Anthropic/Claude",
    "transition_categories": [
      "decision_correct_preserved",
      "decision_wrong_recovered_by_escalation",
      "decision_wrong_not_recovered",
      "decision_correct_lost_at_escalation"
    ]
  },
  "outputs": {
    "condition_pair_profile_csv": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\condition_pair_profile.csv",
    "high_signal_cases_csv": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\high_signal_cases.csv",
    "manifest_json": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\manifest.json",
    "report_md": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\paired_task_level_analysis_report.md",
    "task_condition_paired_outcomes_csv": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\task_condition_paired_outcomes.csv",
    "task_level_summary_csv": "reports\\pilot_03_glm_vs_claude_t0020_paired_task_analysis\\task_level_summary.csv"
  },
  "raw_response_inspection": false,
  "real_api_calls": 0,
  "row_counts": {
    "condition_pair_profile": 3,
    "high_signal_cases": 24,
    "paired_chain_rows": 60,
    "task_condition_paired_outcomes": 60,
    "task_level_summary": 20
  },
  "safe_note": "Paired task-level analysis for the controlled Pilot 03 20-task GLM-5.2 and Anthropic/Claude comparison. This analysis uses committed sanitized paired-chain outputs only and should not be interpreted as broad deployment evidence or broad cross-provider conclusions.",
  "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude paired task-level analysis",
  "source_files": {
    "paired_chain_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\paired_chain_comparison.csv"
  },
  "source_policy": "committed sanitized paired-chain comparison CSV only",
  "status": "PASS"
}
```
