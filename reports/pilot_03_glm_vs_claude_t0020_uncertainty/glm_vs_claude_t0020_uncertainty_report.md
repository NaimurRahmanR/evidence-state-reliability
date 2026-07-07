# Pilot 03 full GLM-5.2 vs Anthropic/Claude uncertainty report

Generated at UTC: 2026-07-07T09:44:55+00:00

## Scope

Uncertainty estimates are descriptive for the controlled Pilot 03 20-task comparison and use committed sanitized paired-chain outputs only. They should not be interpreted as broad deployment evidence or broad cross-provider conclusions.

This report is based on the committed full 20-task paired comparison outputs. It makes no model calls and does not inspect ignored local source artifacts.

## Model-condition Wilson intervals

| Model | Condition | Metric | Successes / n | Estimate | 95% CI |
| --- | --- | --- | ---: | ---: | ---: |
| glm-5.2 | original_evidence | decision_correct | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | original_evidence | escalation_correct | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | original_evidence | audit_passed | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | original_evidence | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | original_evidence | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | original_evidence | decision_correct | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | original_evidence | escalation_correct | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | original_evidence | audit_passed | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | original_evidence | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | original_evidence | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | missing_policy_rule | decision_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| glm-5.2 | missing_policy_rule | escalation_correct | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | missing_policy_rule | audit_passed | 2 / 20 | 0.1 | [0.027866, 0.301034] |
| glm-5.2 | missing_policy_rule | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | missing_policy_rule | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | missing_policy_rule | decision_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| claude-opus-4-8 | missing_policy_rule | escalation_correct | 17 / 20 | 0.85 | [0.639581, 0.947631] |
| claude-opus-4-8 | missing_policy_rule | audit_passed | 0 / 20 | 0.0 | [0.0, 0.161125] |
| claude-opus-4-8 | missing_policy_rule | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | missing_policy_rule | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | missing_one_required_unit | decision_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| glm-5.2 | missing_one_required_unit | escalation_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| glm-5.2 | missing_one_required_unit | audit_passed | 11 / 20 | 0.55 | [0.342085, 0.741802] |
| glm-5.2 | missing_one_required_unit | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| glm-5.2 | missing_one_required_unit | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | missing_one_required_unit | decision_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| claude-opus-4-8 | missing_one_required_unit | escalation_correct | 10 / 20 | 0.5 | [0.299298, 0.700702] |
| claude-opus-4-8 | missing_one_required_unit | audit_passed | 14 / 20 | 0.7 | [0.481027, 0.854523] |
| claude-opus-4-8 | missing_one_required_unit | valid_json_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |
| claude-opus-4-8 | missing_one_required_unit | valid_schema_chain | 20 / 20 | 1.0 | [0.838875, 1.0] |

## Paired Claude-minus-GLM uncertainty

Positive differences mean the Anthropic/Claude rate is higher under the same task-condition pairs.

| Condition | Metric | GLM rate | Claude rate | Claude minus GLM | 95% paired bootstrap CI | Discordant pairs | Exact paired p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original_evidence | decision_correct | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| original_evidence | escalation_correct | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| original_evidence | audit_passed | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| original_evidence | valid_json_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| original_evidence | valid_schema_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_policy_rule | decision_correct | 0.5 | 0.5 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_policy_rule | escalation_correct | 1.0 | 0.85 | -0.15 | [-0.3, 0.0] | 3 | 0.25 |
| missing_policy_rule | audit_passed | 0.1 | 0.0 | -0.1 | [-0.25, 0.0] | 2 | 0.5 |
| missing_policy_rule | valid_json_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_policy_rule | valid_schema_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_one_required_unit | decision_correct | 0.5 | 0.5 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_one_required_unit | escalation_correct | 0.5 | 0.5 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_one_required_unit | audit_passed | 0.55 | 0.7 | 0.15 | [-0.05, 0.35] | 5 | 0.375 |
| missing_one_required_unit | valid_json_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |
| missing_one_required_unit | valid_schema_chain | 1.0 | 1.0 | 0.0 | [0.0, 0.0] | 0 | N/A |

## Manifest

```json
{
  "created_at_utc": "2026-07-07T09:44:55+00:00",
  "methods": {
    "n_bootstrap": 10000,
    "paired_difference_interval": "Deterministic paired bootstrap percentile 95% interval over task-condition pairs",
    "paired_disagreement_test": "Exact two-sided binomial form of McNemar discordant-pair test where discordant pairs exist",
    "seed": 20260707,
    "single_model_interval": "Wilson 95% confidence interval for binomial proportions"
  },
  "outputs": {
    "manifest_json": "reports\\pilot_03_glm_vs_claude_t0020_uncertainty\\manifest.json",
    "model_metric_uncertainty_csv": "reports\\pilot_03_glm_vs_claude_t0020_uncertainty\\model_metric_uncertainty.csv",
    "paired_delta_uncertainty_csv": "reports\\pilot_03_glm_vs_claude_t0020_uncertainty\\paired_delta_uncertainty.csv",
    "report_md": "reports\\pilot_03_glm_vs_claude_t0020_uncertainty\\glm_vs_claude_t0020_uncertainty_report.md"
  },
  "raw_response_inspection": false,
  "real_api_calls": 0,
  "row_counts": {
    "model_metric_uncertainty": 30,
    "paired_chain_rows": 60,
    "paired_delta_uncertainty": 15
  },
  "safe_note": "Uncertainty estimates are descriptive for the controlled Pilot 03 20-task comparison and use committed sanitized paired-chain outputs only. They should not be interpreted as broad deployment evidence or broad cross-provider conclusions.",
  "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude uncertainty analysis",
  "source_files": {
    "paired_chain_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\paired_chain_comparison.csv"
  },
  "source_policy": "committed sanitized paired-chain comparison CSV only",
  "status": "PASS"
}
```
