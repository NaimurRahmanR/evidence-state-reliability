# Pilot 03 stage-cascade tables

Generated at UTC: 2026-07-02T02:33:43+00:00

## Scope

Stage-cascade tables are descriptive outputs from the controlled Pilot 03 setup. They use sanitized chain-level fields only and should not be interpreted as broad provider rankings, deployment evidence, or general model reliability claims.

The GLM chain-level table is a sanitized export from an ignored local aggregate JSON.
The Claude chain-level table is read from the committed comparison-subset CSV.
No raw prompts, raw responses, API keys, or raw result folders are committed by this script.

## Cascade pattern summary

| scope | provider | model_name | condition | cascade_pattern_code | cascade_pattern_label | n | condition_n | condition_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_one_required_unit | D0_A1_E0 | decision_correct=False; audit_passed=True; escalation_correct=False | 3 | 5 | 0.600000 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_one_required_unit | D1_A1_E1 | decision_correct=True; audit_passed=True; escalation_correct=True | 2 | 5 | 0.400000 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_policy_rule | D0_A0_E1 | decision_correct=False; audit_passed=False; escalation_correct=True | 3 | 5 | 0.600000 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_policy_rule | D1_A0_E1 | decision_correct=True; audit_passed=False; escalation_correct=True | 2 | 5 | 0.400000 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | original_evidence | D1_A1_E1 | decision_correct=True; audit_passed=True; escalation_correct=True | 5 | 5 | 1.000000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | D0_A0_E0 | decision_correct=False; audit_passed=False; escalation_correct=False | 1 | 20 | 0.050000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | D0_A1_E0 | decision_correct=False; audit_passed=True; escalation_correct=False | 9 | 20 | 0.450000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | D1_A0_E1 | decision_correct=True; audit_passed=False; escalation_correct=True | 8 | 20 | 0.400000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | D1_A1_E1 | decision_correct=True; audit_passed=True; escalation_correct=True | 2 | 20 | 0.100000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_policy_rule | D0_A0_E1 | decision_correct=False; audit_passed=False; escalation_correct=True | 8 | 20 | 0.400000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_policy_rule | D0_A1_E1 | decision_correct=False; audit_passed=True; escalation_correct=True | 2 | 20 | 0.100000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_policy_rule | D1_A0_E1 | decision_correct=True; audit_passed=False; escalation_correct=True | 10 | 20 | 0.500000 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | D1_A1_E1 | decision_correct=True; audit_passed=True; escalation_correct=True | 20 | 20 | 1.000000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_one_required_unit | D0_A0_E0 | decision_correct=False; audit_passed=False; escalation_correct=False | 1 | 5 | 0.200000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_one_required_unit | D0_A1_E0 | decision_correct=False; audit_passed=True; escalation_correct=False | 2 | 5 | 0.400000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_one_required_unit | D1_A0_E1 | decision_correct=True; audit_passed=False; escalation_correct=True | 2 | 5 | 0.400000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_policy_rule | D0_A0_E1 | decision_correct=False; audit_passed=False; escalation_correct=True | 2 | 5 | 0.400000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_policy_rule | D0_A1_E1 | decision_correct=False; audit_passed=True; escalation_correct=True | 1 | 5 | 0.200000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_policy_rule | D1_A0_E1 | decision_correct=True; audit_passed=False; escalation_correct=True | 2 | 5 | 0.400000 |
| GLM shared 5-task subset | zai | glm-5.2 | original_evidence | D1_A1_E1 | decision_correct=True; audit_passed=True; escalation_correct=True | 5 | 5 | 1.000000 |

## Stage transition summary

| scope | provider | model_name | condition | n | decision_correct_rate | audit_passed_rate | escalation_correct_rate | audit_passed_when_decision_wrong_count | audit_passed_when_decision_wrong_rate_among_wrong_decisions | audit_failed_when_decision_correct_count | audit_failed_when_decision_correct_rate_among_correct_decisions | escalation_correct_when_decision_wrong_count | escalation_correct_when_decision_wrong_rate_among_wrong_decisions | escalation_wrong_after_audit_passed_count | escalation_wrong_after_audit_passed_rate_among_audit_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_one_required_unit | 5 | 0.400000 | 1.000000 | 0.400000 | 3 | 1.000000 | 0 | 0.000000 | 0 | 0.000000 | 3 | 0.600000 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_policy_rule | 5 | 0.400000 | 0.000000 | 1.000000 | 0 | 0.000000 | 2 | 1.000000 | 3 | 1.000000 | 0 |  |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | original_evidence | 5 | 1.000000 | 1.000000 | 1.000000 | 0 |  | 0 | 0.000000 | 0 |  | 0 | 0.000000 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | 20 | 0.500000 | 0.550000 | 0.500000 | 9 | 0.900000 | 8 | 0.800000 | 0 | 0.000000 | 9 | 0.818182 |
| GLM 20-task checkpoint | zai | glm-5.2 | missing_policy_rule | 20 | 0.500000 | 0.100000 | 1.000000 | 2 | 0.200000 | 10 | 1.000000 | 10 | 1.000000 | 0 | 0.000000 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | 20 | 1.000000 | 1.000000 | 1.000000 | 0 |  | 0 | 0.000000 | 0 |  | 0 | 0.000000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_one_required_unit | 5 | 0.400000 | 0.400000 | 0.400000 | 2 | 0.666667 | 2 | 1.000000 | 0 | 0.000000 | 2 | 1.000000 |
| GLM shared 5-task subset | zai | glm-5.2 | missing_policy_rule | 5 | 0.400000 | 0.200000 | 1.000000 | 1 | 0.333333 | 2 | 1.000000 | 3 | 1.000000 | 0 | 0.000000 |
| GLM shared 5-task subset | zai | glm-5.2 | original_evidence | 5 | 1.000000 | 1.000000 | 1.000000 | 0 |  | 0 | 0.000000 | 0 |  | 0 | 0.000000 |

## Manifest

```json
{
  "created_at_utc": "2026-07-02T02:33:43+00:00",
  "outputs": {
    "cascade_pattern_summary_csv": "reports\\pilot_03_stage_cascade\\cascade_pattern_summary.csv",
    "glm20_sanitized_chain_summary_csv": "reports\\pilot_03_stage_cascade\\glm20_sanitized_chain_summary.csv",
    "manifest_json": "reports\\pilot_03_stage_cascade\\manifest.json",
    "report_md": "reports\\pilot_03_stage_cascade\\stage_cascade_report.md",
    "shared5_sanitized_chain_summary_csv": "reports\\pilot_03_stage_cascade\\shared5_sanitized_chain_summary.csv",
    "stage_transition_summary_csv": "reports\\pilot_03_stage_cascade\\stage_transition_summary.csv"
  },
  "raw_prompt_or_response_columns_exported": false,
  "real_api_calls": 0,
  "row_counts": {
    "cascade_pattern_summary": 20,
    "glm20_sanitized_chain_summary": 60,
    "shared5_sanitized_chain_summary": 30,
    "stage_transition_summary": 9
  },
  "safe_note": "Stage-cascade tables are descriptive outputs from the controlled Pilot 03 setup. They use sanitized chain-level fields only and should not be interpreted as broad provider rankings, deployment evidence, or general model reliability claims.",
  "shared_task_ids": [
    "P03-T0001",
    "P03-T0002",
    "P03-T0003",
    "P03-T0004",
    "P03-T0005"
  ],
  "source_file_policy": {
    "claude_chain_csv": "committed comparison-subset chain summary",
    "glm_aggregate_json": "ignored local aggregate used only for sanitized chain-level export"
  },
  "source_files": {
    "claude_chain_csv": "reports\\pilot_03_claude_comparison_subset\\claude_subset_chain_summary.csv",
    "glm_aggregate_json": "results\\pilot_03_real_llm_analysis\\pilot_03_real_glm_t0020_aggregate.json"
  }
}
```
