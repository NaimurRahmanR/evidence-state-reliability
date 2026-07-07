# Pilot 03 full GLM-5.2 vs Anthropic/Claude 20-task comparison

Generated at UTC: 2026-07-07T09:39:47+00:00

## Scope

Descriptive full 20-task GLM-5.2 and Anthropic/Claude comparison under the controlled Pilot 03 setup. This report uses committed sanitized chain-level outputs only and should not be interpreted as broad deployment evidence, broad cross-provider conclusions, or general reliability claims.

This report compares committed sanitized chain-level outputs only. It does not inspect raw prompts, raw responses, API keys, or ignored local aggregate files.

## Model-condition summary

| Model | Condition | n | Decision correct | Escalation correct | Audit passed | Valid JSON chains | Valid schema chains |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| glm-5.2 | original_evidence | 20 | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) |
| glm-5.2 | missing_policy_rule | 20 | 10 (0.5) | 20 (1.0) | 2 (0.1) | 20 (1.0) | 20 (1.0) |
| glm-5.2 | missing_one_required_unit | 20 | 10 (0.5) | 10 (0.5) | 11 (0.55) | 20 (1.0) | 20 (1.0) |
| claude-opus-4-8 | original_evidence | 20 | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) | 20 (1.0) |
| claude-opus-4-8 | missing_policy_rule | 20 | 10 (0.5) | 17 (0.85) | 0 (0.0) | 20 (1.0) | 20 (1.0) |
| claude-opus-4-8 | missing_one_required_unit | 20 | 10 (0.5) | 10 (0.5) | 14 (0.7) | 20 (1.0) | 20 (1.0) |

## Descriptive rate differences

Positive values mean the Anthropic/Claude rate is higher than the GLM-5.2 rate under the same condition.

| Condition | Metric | GLM-5.2 | Claude Opus 4.8 | Claude minus GLM |
| --- | --- | ---: | ---: | ---: |
| original_evidence | decision_correct_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | escalation_correct_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | audit_passed_true_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | valid_json_chain_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | valid_schema_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_policy_rule | decision_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_policy_rule | escalation_correct_rate | 1.0 | 0.85 | -0.15 |
| missing_policy_rule | audit_passed_true_rate | 0.1 | 0.0 | -0.1 |
| missing_policy_rule | valid_json_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_policy_rule | valid_schema_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_one_required_unit | decision_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | escalation_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | audit_passed_true_rate | 0.55 | 0.7 | 0.15 |
| missing_one_required_unit | valid_json_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_one_required_unit | valid_schema_chain_rate | 1.0 | 1.0 | 0.0 |

## Paired agreement summary

| Condition | Metric | n pairs | Agreement | GLM only correct | Claude only correct | Both correct | Both wrong |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original_evidence | decision_correct | 20 | 20 (1.0) | 0 (0.0) | 0 (0.0) | 20 (1.0) | 0 (0.0) |
| original_evidence | escalation_correct | 20 | 20 (1.0) | 0 (0.0) | 0 (0.0) | 20 (1.0) | 0 (0.0) |
| original_evidence | audit_passed | 20 | 20 (1.0) | N/A | N/A | N/A | N/A |
| missing_policy_rule | decision_correct | 20 | 20 (1.0) | 0 (0.0) | 0 (0.0) | 10 (0.5) | 10 (0.5) |
| missing_policy_rule | escalation_correct | 20 | 17 (0.85) | 3 (0.15) | 0 (0.0) | 17 (0.85) | 0 (0.0) |
| missing_policy_rule | audit_passed | 20 | 18 (0.9) | N/A | N/A | N/A | N/A |
| missing_one_required_unit | decision_correct | 20 | 20 (1.0) | 0 (0.0) | 0 (0.0) | 10 (0.5) | 10 (0.5) |
| missing_one_required_unit | escalation_correct | 20 | 20 (1.0) | 0 (0.0) | 0 (0.0) | 10 (0.5) | 10 (0.5) |
| missing_one_required_unit | audit_passed | 20 | 15 (0.75) | N/A | N/A | N/A | N/A |

## Manifest

```json
{
  "created_at_utc": "2026-07-07T09:39:47+00:00",
  "models": [
    {
      "model_name": "glm-5.2",
      "provider": "zai"
    },
    {
      "model_name": "claude-opus-4-8",
      "provider": "anthropic"
    }
  ],
  "outputs": {
    "condition_delta_summary_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\condition_delta_summary.csv",
    "failure_pattern_comparison_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\failure_pattern_comparison.csv",
    "manifest_json": "reports\\pilot_03_glm_vs_claude_t0020_full\\manifest.json",
    "model_condition_summary_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\model_condition_summary.csv",
    "paired_agreement_summary_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\paired_agreement_summary.csv",
    "paired_chain_comparison_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\paired_chain_comparison.csv",
    "report_md": "reports\\pilot_03_glm_vs_claude_t0020_full\\glm_vs_claude_t0020_full_comparison_report.md"
  },
  "raw_response_inspection": false,
  "real_api_calls": 0,
  "row_counts": {
    "claude_chain_rows": 60,
    "condition_delta_summary": 15,
    "failure_pattern_comparison": 15,
    "glm_chain_rows": 60,
    "model_condition_summary": 6,
    "paired_agreement_summary": 9,
    "paired_chain_comparison": 60
  },
  "safe_note": "Descriptive full 20-task GLM-5.2 and Anthropic/Claude comparison under the controlled Pilot 03 setup. This report uses committed sanitized chain-level outputs only and should not be interpreted as broad deployment evidence, broad cross-provider conclusions, or general reliability claims.",
  "scope": "Pilot 03 full 20-task GLM-5.2 vs Anthropic/Claude comparison",
  "source_files": {
    "claude_chain_csv": "reports\\pilot_03_anthropic_t0020_valid\\anthropic_t0020_valid_chain_summary.csv",
    "glm_chain_csv": "reports\\pilot_03_stage_cascade\\glm20_sanitized_chain_summary.csv"
  },
  "source_policy": "committed sanitized chain-level CSVs only",
  "status": "PASS",
  "validity": {
    "claude_valid_json_chain_count": 60,
    "claude_valid_schema_chain_count": 60,
    "glm_valid_json_chain_count": 60,
    "glm_valid_schema_chain_count": 60
  }
}
```
