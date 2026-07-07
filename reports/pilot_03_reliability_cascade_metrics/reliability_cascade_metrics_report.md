# Pilot 03 reliability cascade metrics

Generated at UTC: 2026-07-07T09:57:49+00:00

## Scope

Reliability cascade metrics for the controlled Pilot 03 20-task comparison. Metrics are computed from committed sanitized paired-chain outputs only and should not be interpreted as broad deployment evidence or broad cross-provider conclusions.

The metrics summarize how decision-stage errors, audit behavior, and escalation-stage outcomes interact under each evidence condition.

## Model-condition cascade metrics

| Model | Condition | Decision failure | Audit false assurance | Undetected decision failure | Escalation recovery on decision failure | Cascade failure | Net escalation gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| glm-5.2 | original_evidence | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (None) | 0 (0.0) | 0.0 |
| glm-5.2 | missing_policy_rule | 10 (0.5) | 2 (0.1) | 2 (0.1) | 10 (1.0) | 0 (0.0) | 0.5 |
| glm-5.2 | missing_one_required_unit | 10 (0.5) | 9 (0.45) | 9 (0.45) | 0 (0.0) | 10 (0.5) | 0.0 |
| claude-opus-4-8 | original_evidence | 0 (0.0) | 0 (0.0) | 0 (0.0) | 0 (None) | 0 (0.0) | 0.0 |
| claude-opus-4-8 | missing_policy_rule | 10 (0.5) | 0 (0.0) | 0 (0.0) | 7 (0.7) | 3 (0.15) | 0.35 |
| claude-opus-4-8 | missing_one_required_unit | 10 (0.5) | 10 (0.5) | 10 (0.5) | 0 (0.0) | 10 (0.5) | 0.0 |

## Evidence-condition deltas from original evidence

| Model | Condition | Metric | Baseline | Condition value | Delta |
| --- | --- | --- | ---: | ---: | ---: |
| glm-5.2 | missing_policy_rule | decision_correct_rate | 1.0 | 0.5 | -0.5 |
| glm-5.2 | missing_policy_rule | decision_failure_rate | 0.0 | 0.5 | 0.5 |
| glm-5.2 | missing_policy_rule | audit_pass_rate | 1.0 | 0.1 | -0.9 |
| glm-5.2 | missing_policy_rule | audit_false_assurance_rate | 0.0 | 0.1 | 0.1 |
| glm-5.2 | missing_policy_rule | undetected_decision_failure_rate | 0.0 | 0.1 | 0.1 |
| glm-5.2 | missing_policy_rule | escalation_correct_rate | 1.0 | 1.0 | 0.0 |
| glm-5.2 | missing_policy_rule | cascade_failure_rate | 0.0 | 0.0 | 0.0 |
| glm-5.2 | missing_policy_rule | net_escalation_gain_rate | 0.0 | 0.5 | 0.5 |
| glm-5.2 | missing_one_required_unit | decision_correct_rate | 1.0 | 0.5 | -0.5 |
| glm-5.2 | missing_one_required_unit | decision_failure_rate | 0.0 | 0.5 | 0.5 |
| glm-5.2 | missing_one_required_unit | audit_pass_rate | 1.0 | 0.55 | -0.45 |
| glm-5.2 | missing_one_required_unit | audit_false_assurance_rate | 0.0 | 0.45 | 0.45 |
| glm-5.2 | missing_one_required_unit | undetected_decision_failure_rate | 0.0 | 0.45 | 0.45 |
| glm-5.2 | missing_one_required_unit | escalation_correct_rate | 1.0 | 0.5 | -0.5 |
| glm-5.2 | missing_one_required_unit | cascade_failure_rate | 0.0 | 0.5 | 0.5 |
| glm-5.2 | missing_one_required_unit | net_escalation_gain_rate | 0.0 | 0.0 | 0.0 |
| claude-opus-4-8 | missing_policy_rule | decision_correct_rate | 1.0 | 0.5 | -0.5 |
| claude-opus-4-8 | missing_policy_rule | decision_failure_rate | 0.0 | 0.5 | 0.5 |
| claude-opus-4-8 | missing_policy_rule | audit_pass_rate | 1.0 | 0.0 | -1.0 |
| claude-opus-4-8 | missing_policy_rule | audit_false_assurance_rate | 0.0 | 0.0 | 0.0 |
| claude-opus-4-8 | missing_policy_rule | undetected_decision_failure_rate | 0.0 | 0.0 | 0.0 |
| claude-opus-4-8 | missing_policy_rule | escalation_correct_rate | 1.0 | 0.85 | -0.15 |
| claude-opus-4-8 | missing_policy_rule | cascade_failure_rate | 0.0 | 0.15 | 0.15 |
| claude-opus-4-8 | missing_policy_rule | net_escalation_gain_rate | 0.0 | 0.35 | 0.35 |
| claude-opus-4-8 | missing_one_required_unit | decision_correct_rate | 1.0 | 0.5 | -0.5 |
| claude-opus-4-8 | missing_one_required_unit | decision_failure_rate | 0.0 | 0.5 | 0.5 |
| claude-opus-4-8 | missing_one_required_unit | audit_pass_rate | 1.0 | 0.7 | -0.3 |
| claude-opus-4-8 | missing_one_required_unit | audit_false_assurance_rate | 0.0 | 0.5 | 0.5 |
| claude-opus-4-8 | missing_one_required_unit | undetected_decision_failure_rate | 0.0 | 0.5 | 0.5 |
| claude-opus-4-8 | missing_one_required_unit | escalation_correct_rate | 1.0 | 0.5 | -0.5 |
| claude-opus-4-8 | missing_one_required_unit | cascade_failure_rate | 0.0 | 0.5 | 0.5 |
| claude-opus-4-8 | missing_one_required_unit | net_escalation_gain_rate | 0.0 | 0.0 | 0.0 |

## Descriptive cross-model cascade differences

Positive values mean the Anthropic/Claude value is higher than the GLM-5.2 value under the same condition.

| Condition | Metric | GLM-5.2 | Claude Opus 4.8 | Claude minus GLM |
| --- | --- | ---: | ---: | ---: |
| original_evidence | valid_chain_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | decision_correct_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | decision_failure_rate | 0.0 | 0.0 | 0.0 |
| original_evidence | audit_pass_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | audit_false_assurance_rate | 0.0 | 0.0 | 0.0 |
| original_evidence | undetected_decision_failure_rate | 0.0 | 0.0 | 0.0 |
| original_evidence | escalation_correct_rate | 1.0 | 1.0 | 0.0 |
| original_evidence | escalation_recovery_rate_on_decision_failure | None | None | None |
| original_evidence | cascade_failure_rate | 0.0 | 0.0 | 0.0 |
| original_evidence | net_escalation_gain_rate | 0.0 | 0.0 | 0.0 |
| missing_policy_rule | valid_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_policy_rule | decision_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_policy_rule | decision_failure_rate | 0.5 | 0.5 | 0.0 |
| missing_policy_rule | audit_pass_rate | 0.1 | 0.0 | -0.1 |
| missing_policy_rule | audit_false_assurance_rate | 0.1 | 0.0 | -0.1 |
| missing_policy_rule | undetected_decision_failure_rate | 0.1 | 0.0 | -0.1 |
| missing_policy_rule | escalation_correct_rate | 1.0 | 0.85 | -0.15 |
| missing_policy_rule | escalation_recovery_rate_on_decision_failure | 1.0 | 0.7 | -0.3 |
| missing_policy_rule | cascade_failure_rate | 0.0 | 0.15 | 0.15 |
| missing_policy_rule | net_escalation_gain_rate | 0.5 | 0.35 | -0.15 |
| missing_one_required_unit | valid_chain_rate | 1.0 | 1.0 | 0.0 |
| missing_one_required_unit | decision_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | decision_failure_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | audit_pass_rate | 0.55 | 0.7 | 0.15 |
| missing_one_required_unit | audit_false_assurance_rate | 0.45 | 0.5 | 0.05 |
| missing_one_required_unit | undetected_decision_failure_rate | 0.45 | 0.5 | 0.05 |
| missing_one_required_unit | escalation_correct_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | escalation_recovery_rate_on_decision_failure | 0.0 | 0.0 | 0.0 |
| missing_one_required_unit | cascade_failure_rate | 0.5 | 0.5 | 0.0 |
| missing_one_required_unit | net_escalation_gain_rate | 0.0 | 0.0 | 0.0 |

## Metric definitions

| Metric | Definition |
| --- | --- |
| valid_chain_rate | Share of selected chains with both valid JSON and valid schema indicators. |
| decision_correct_rate | Share of chains where the decision-stage final decision matched the gold decision. |
| decision_failure_rate | Share of chains where the decision-stage final decision did not match the gold decision. |
| audit_pass_rate | Share of chains where the audit stage returned pass. |
| audit_false_assurance_rate | Share of chains where the audit stage passed although the decision-stage output was incorrect. |
| audit_detection_rate_on_decision_failure | Among decision-stage failures, share where audit did not pass. |
| undetected_decision_failure_rate | Share of all chains where the decision-stage output was incorrect and audit still passed. |
| escalation_correct_rate | Share of chains where the escalation-stage final decision matched the gold decision. |
| escalation_recovery_rate_on_decision_failure | Among decision-stage failures, share recovered to the correct decision at escalation. |
| escalation_loss_rate_on_decision_success | Among decision-stage successes, share that became incorrect at escalation. |
| cascade_failure_rate | Share of chains where the escalation-stage final decision was incorrect. |
| net_escalation_gain_rate | Escalation correct rate minus decision correct rate. |

## Manifest

```json
{
  "created_at_utc": "2026-07-07T09:57:49+00:00",
  "metrics": [
    "valid_chain_rate",
    "decision_correct_rate",
    "decision_failure_rate",
    "audit_pass_rate",
    "audit_false_assurance_rate",
    "audit_detection_rate_on_decision_failure",
    "undetected_decision_failure_rate",
    "escalation_correct_rate",
    "escalation_recovery_rate_on_decision_failure",
    "escalation_loss_rate_on_decision_success",
    "cascade_failure_rate",
    "net_escalation_gain_rate"
  ],
  "outputs": {
    "cross_model_cascade_comparison_csv": "reports\\pilot_03_reliability_cascade_metrics\\cross_model_cascade_comparison.csv",
    "evidence_condition_delta_metrics_csv": "reports\\pilot_03_reliability_cascade_metrics\\evidence_condition_delta_metrics.csv",
    "manifest_json": "reports\\pilot_03_reliability_cascade_metrics\\manifest.json",
    "metric_definitions_csv": "reports\\pilot_03_reliability_cascade_metrics\\metric_definitions.csv",
    "model_condition_cascade_metrics_csv": "reports\\pilot_03_reliability_cascade_metrics\\model_condition_cascade_metrics.csv",
    "report_md": "reports\\pilot_03_reliability_cascade_metrics\\reliability_cascade_metrics_report.md"
  },
  "raw_response_inspection": false,
  "real_api_calls": 0,
  "row_counts": {
    "cross_model_cascade_comparison": 30,
    "evidence_condition_delta_metrics": 48,
    "metric_definitions": 12,
    "model_condition_cascade_metrics": 6,
    "paired_chain_rows": 60
  },
  "safe_note": "Reliability cascade metrics for the controlled Pilot 03 20-task comparison. Metrics are computed from committed sanitized paired-chain outputs only and should not be interpreted as broad deployment evidence or broad cross-provider conclusions.",
  "scope": "Pilot 03 reliability cascade metrics for full 20-task GLM-5.2 and Anthropic/Claude comparison",
  "source_files": {
    "paired_chain_csv": "reports\\pilot_03_glm_vs_claude_t0020_full\\paired_chain_comparison.csv"
  },
  "source_policy": "committed sanitized paired-chain comparison CSV only",
  "status": "PASS"
}
```
