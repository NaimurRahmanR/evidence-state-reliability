# Pilot 03 uncertainty tables

Generated at UTC: 2026-07-02T02:27:21+00:00

## Scope

Descriptive uncertainty intervals only. These tables are computed from committed Pilot 03 summary CSV files and should not be read as general model-performance claims, deployment evidence, or provider rankings.

The intervals are descriptive summaries of the committed Pilot 03 count tables.
No p-values, provider rankings, deployment claims, or broad generalisation claims are made here.

## GLM 20-task condition intervals

| condition | metric | successes | n | estimate | ci_method | ci_lower | ci_upper |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original_evidence | decision_correct | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |
| original_evidence | escalation_correct | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |
| original_evidence | valid_chain | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |
| missing_policy_rule | decision_correct | 10 | 20 | 0.500000 | wilson_score_95 | 0.299298 | 0.700702 |
| missing_policy_rule | escalation_correct | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |
| missing_policy_rule | valid_chain | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |
| missing_one_required_unit | decision_correct | 10 | 20 | 0.500000 | wilson_score_95 | 0.299298 | 0.700702 |
| missing_one_required_unit | escalation_correct | 10 | 20 | 0.500000 | wilson_score_95 | 0.299298 | 0.700702 |
| missing_one_required_unit | valid_chain | 20 | 20 | 1.000000 | wilson_score_95 | 0.838875 | 1.000000 |

## Shared 5-task provider-condition intervals

| provider | model | condition | metric | successes | n | estimate | ci_method | ci_lower | ci_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| zai | glm-5.2 | missing_one_required_unit | decision_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| zai | glm-5.2 | missing_one_required_unit | escalation_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| zai | glm-5.2 | missing_one_required_unit | audit_passed_true | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| zai | glm-5.2 | missing_one_required_unit | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | missing_policy_rule | decision_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| zai | glm-5.2 | missing_policy_rule | escalation_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | missing_policy_rule | audit_passed_true | 1 | 5 | 0.200000 | wilson_score_95 | 0.036224 | 0.624465 |
| zai | glm-5.2 | missing_policy_rule | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | original_evidence | decision_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | original_evidence | escalation_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | original_evidence | audit_passed_true | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| zai | glm-5.2 | original_evidence | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | missing_one_required_unit | decision_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| anthropic | claude-opus-4-8 | missing_one_required_unit | escalation_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| anthropic | claude-opus-4-8 | missing_one_required_unit | audit_passed_true | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | missing_one_required_unit | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | missing_policy_rule | decision_correct | 2 | 5 | 0.400000 | wilson_score_95 | 0.117621 | 0.769276 |
| anthropic | claude-opus-4-8 | missing_policy_rule | escalation_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | missing_policy_rule | audit_passed_true | 0 | 5 | 0.000000 | wilson_score_95 | 0.000000 | 0.434482 |
| anthropic | claude-opus-4-8 | missing_policy_rule | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | original_evidence | decision_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | original_evidence | escalation_correct | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | original_evidence | audit_passed_true | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |
| anthropic | claude-opus-4-8 | original_evidence | valid_chain | 5 | 5 | 1.000000 | wilson_score_95 | 0.565518 | 1.000000 |

## Condition differences from original evidence

| scope | provider | model | baseline_condition | comparison_condition | metric | difference_comparison_minus_baseline | difference_interval_method | difference_ci_lower | difference_ci_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_one_required_unit | decision_correct | -0.500000 | wilson_interval_difference_descriptive_95 | -0.700702 | -0.138173 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_one_required_unit | escalation_correct | -0.500000 | wilson_interval_difference_descriptive_95 | -0.700702 | -0.138173 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_one_required_unit | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.161125 | 0.161125 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_policy_rule | decision_correct | -0.500000 | wilson_interval_difference_descriptive_95 | -0.700702 | -0.138173 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_policy_rule | escalation_correct | 0.000000 | wilson_interval_difference_descriptive_95 | -0.161125 | 0.161125 |
| GLM 20-task checkpoint | zai | glm-5.2 | original_evidence | missing_policy_rule | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.161125 | 0.161125 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_one_required_unit | audit_passed_true | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_one_required_unit | decision_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_one_required_unit | escalation_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_one_required_unit | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_policy_rule | audit_passed_true | -0.800000 | wilson_interval_difference_descriptive_95 | -0.963776 | 0.058948 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_policy_rule | decision_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_policy_rule | escalation_correct | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | zai | glm-5.2 | original_evidence | missing_policy_rule | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_one_required_unit | audit_passed_true | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_one_required_unit | decision_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_one_required_unit | escalation_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_one_required_unit | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_policy_rule | audit_passed_true | -1.000000 | wilson_interval_difference_descriptive_95 | -1.000000 | -0.131035 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_policy_rule | decision_correct | -0.600000 | wilson_interval_difference_descriptive_95 | -0.882379 | 0.203758 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_policy_rule | escalation_correct | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| Shared 5-task comparison | anthropic | claude-opus-4-8 | original_evidence | missing_policy_rule | valid_chain | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |

## Shared 5-task provider differences

| condition | metric | provider_a | model_a | successes_a | n_a | provider_b | model_b | successes_b | n_b | difference_a_minus_b | difference_interval_method | difference_ci_lower | difference_ci_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| missing_one_required_unit | decision_correct | anthropic | claude-opus-4-8 | 2 | 5 | zai | glm-5.2 | 2 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.651655 | 0.651655 |
| missing_one_required_unit | escalation_correct | anthropic | claude-opus-4-8 | 2 | 5 | zai | glm-5.2 | 2 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.651655 | 0.651655 |
| missing_one_required_unit | audit_passed_true | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 2 | 5 | 0.600000 | wilson_interval_difference_descriptive_95 | -0.203758 | 0.882379 |
| missing_one_required_unit | valid_chain | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| missing_policy_rule | decision_correct | anthropic | claude-opus-4-8 | 2 | 5 | zai | glm-5.2 | 2 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.651655 | 0.651655 |
| missing_policy_rule | escalation_correct | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| missing_policy_rule | audit_passed_true | anthropic | claude-opus-4-8 | 0 | 5 | zai | glm-5.2 | 1 | 5 | -0.200000 | wilson_interval_difference_descriptive_95 | -0.624465 | 0.398258 |
| missing_policy_rule | valid_chain | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| original_evidence | decision_correct | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| original_evidence | escalation_correct | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| original_evidence | audit_passed_true | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |
| original_evidence | valid_chain | anthropic | claude-opus-4-8 | 5 | 5 | zai | glm-5.2 | 5 | 5 | 0.000000 | wilson_interval_difference_descriptive_95 | -0.434482 | 0.434482 |

## Manifest

```json
{
  "confidence_level": 0.95,
  "created_at_utc": "2026-07-02T02:27:21+00:00",
  "difference_interval_method": "wilson_interval_difference_descriptive_95",
  "interval_method": "wilson_score_95",
  "outputs": {
    "condition_difference_uncertainty_csv": "reports\\pilot_03_uncertainty\\condition_difference_uncertainty.csv",
    "glm_condition_uncertainty_csv": "reports\\pilot_03_uncertainty\\glm20_condition_uncertainty.csv",
    "manifest_json": "reports\\pilot_03_uncertainty\\manifest.json",
    "provider_difference_uncertainty_csv": "reports\\pilot_03_uncertainty\\shared5_provider_difference_uncertainty.csv",
    "report_md": "reports\\pilot_03_uncertainty\\uncertainty_tables_report.md",
    "shared_provider_condition_uncertainty_csv": "reports\\pilot_03_uncertainty\\shared5_provider_condition_uncertainty.csv"
  },
  "real_api_calls": 0,
  "row_counts": {
    "condition_difference_uncertainty": 22,
    "glm_condition_uncertainty": 9,
    "provider_difference_uncertainty": 12,
    "shared_provider_condition_uncertainty": 24
  },
  "safe_note": "Descriptive uncertainty intervals only. These tables are computed from committed Pilot 03 summary CSV files and should not be read as general model-performance claims, deployment evidence, or provider rankings.",
  "source_files": {
    "glm_condition_csv": "reports\\pilot_03_real_glm_t0020_condition_summary.csv",
    "shared_comparison_csv": "reports\\pilot_03_glm_vs_claude_comparison\\shared_5_task_condition_comparison.csv"
  }
}
```
