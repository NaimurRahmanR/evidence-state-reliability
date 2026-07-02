# Pilot 03 committed-output validation report

Generated at UTC: 2026-07-02T02:38:07+00:00

## Scope

Validation report for committed Pilot 03 outputs. This command checks internal consistency only and makes no real API calls.

Validation status: **PASS**

## Checks

| check_name | status | detail |
| --- | --- | --- |
| required_file_exists::reports\pilot_03_real_glm_t0020_condition_summary.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_glm_vs_claude_comparison\shared_5_task_condition_comparison.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_uncertainty\manifest.json | PASS | exists=True |
| required_file_exists::reports\pilot_03_uncertainty\glm20_condition_uncertainty.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_uncertainty\shared5_provider_condition_uncertainty.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_uncertainty\condition_difference_uncertainty.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_uncertainty\shared5_provider_difference_uncertainty.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_stage_cascade\manifest.json | PASS | exists=True |
| required_file_exists::reports\pilot_03_stage_cascade\glm20_sanitized_chain_summary.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_stage_cascade\shared5_sanitized_chain_summary.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_stage_cascade\cascade_pattern_summary.csv | PASS | exists=True |
| required_file_exists::reports\pilot_03_stage_cascade\stage_transition_summary.csv | PASS | exists=True |
| manifest_real_api_calls_zero::reports\pilot_03_uncertainty\manifest.json | PASS | real_api_calls=0 |
| manifest_row_count::glm_condition_uncertainty | PASS | actual=9; expected=9; path=reports\pilot_03_uncertainty\glm20_condition_uncertainty.csv |
| manifest_row_count::shared_provider_condition_uncertainty | PASS | actual=24; expected=24; path=reports\pilot_03_uncertainty\shared5_provider_condition_uncertainty.csv |
| manifest_row_count::condition_difference_uncertainty | PASS | actual=22; expected=22; path=reports\pilot_03_uncertainty\condition_difference_uncertainty.csv |
| manifest_row_count::provider_difference_uncertainty | PASS | actual=12; expected=12; path=reports\pilot_03_uncertainty\shared5_provider_difference_uncertainty.csv |
| manifest_real_api_calls_zero::reports\pilot_03_stage_cascade\manifest.json | PASS | real_api_calls=0 |
| manifest_row_count::glm20_sanitized_chain_summary | PASS | actual=60; expected=60; path=reports\pilot_03_stage_cascade\glm20_sanitized_chain_summary.csv |
| manifest_row_count::shared5_sanitized_chain_summary | PASS | actual=30; expected=30; path=reports\pilot_03_stage_cascade\shared5_sanitized_chain_summary.csv |
| manifest_row_count::cascade_pattern_summary | PASS | actual=20; expected=20; path=reports\pilot_03_stage_cascade\cascade_pattern_summary.csv |
| manifest_row_count::stage_transition_summary | PASS | actual=9; expected=9; path=reports\pilot_03_stage_cascade\stage_transition_summary.csv |
| stage_cascade_raw_prompt_response_export_flag_false | PASS | raw_prompt_or_response_columns_exported=False |
| glm_condition_vs_chain_n::original_evidence | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_decision_correct::original_evidence | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_escalation_correct::original_evidence | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_valid_chain::original_evidence | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_audit_passed::original_evidence | PASS | actual={'True': 20}; expected={'True': 20} |
| glm_condition_vs_chain_n::missing_policy_rule | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_decision_correct::missing_policy_rule | PASS | actual=10; expected=10 |
| glm_condition_vs_chain_escalation_correct::missing_policy_rule | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_valid_chain::missing_policy_rule | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_audit_passed::missing_policy_rule | PASS | actual={'False': 18, 'True': 2}; expected={'False': 18, 'True': 2} |
| glm_condition_vs_chain_n::missing_one_required_unit | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_decision_correct::missing_one_required_unit | PASS | actual=10; expected=10 |
| glm_condition_vs_chain_escalation_correct::missing_one_required_unit | PASS | actual=10; expected=10 |
| glm_condition_vs_chain_valid_chain::missing_one_required_unit | PASS | actual=20; expected=20 |
| glm_condition_vs_chain_audit_passed::missing_one_required_unit | PASS | actual={'False': 9, 'True': 11}; expected={'False': 9, 'True': 11} |
| shared_comparison_vs_chain::zai::missing_one_required_unit::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::missing_one_required_unit::decision_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::zai::missing_one_required_unit::escalation_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::zai::missing_one_required_unit::audit_passed_true | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::zai::missing_one_required_unit::valid_chain | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::missing_policy_rule::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::missing_policy_rule::decision_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::zai::missing_policy_rule::escalation_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::missing_policy_rule::audit_passed_true | PASS | actual=1; expected=1 |
| shared_comparison_vs_chain::zai::missing_policy_rule::valid_chain | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::original_evidence::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::original_evidence::decision_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::original_evidence::escalation_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::original_evidence::audit_passed_true | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::zai::original_evidence::valid_chain | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_one_required_unit::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_one_required_unit::decision_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::anthropic::missing_one_required_unit::escalation_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::anthropic::missing_one_required_unit::audit_passed_true | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_one_required_unit::valid_chain | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_policy_rule::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_policy_rule::decision_correct | PASS | actual=2; expected=2 |
| shared_comparison_vs_chain::anthropic::missing_policy_rule::escalation_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::missing_policy_rule::audit_passed_true | PASS | actual=0; expected=0 |
| shared_comparison_vs_chain::anthropic::missing_policy_rule::valid_chain | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::original_evidence::n | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::original_evidence::decision_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::original_evidence::escalation_correct | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::original_evidence::audit_passed_true | PASS | actual=5; expected=5 |
| shared_comparison_vs_chain::anthropic::original_evidence::valid_chain | PASS | actual=5; expected=5 |
| blocked_raw_prompt_response_like_columns | PASS | hits=[] |
| risky_public_wording_absent | PASS | hit_count=0 |

## Risky wording hits

None.

## Blocked column hits

None.

## Manifest

```json
{
  "created_at_utc": "2026-07-02T02:38:07+00:00",
  "n_blocked_column_hits": 0,
  "n_checks": 70,
  "n_failed_checks": 0,
  "n_risky_wording_hits": 0,
  "outputs": {
    "manifest_json": "reports\\pilot_03_validation\\manifest.json",
    "validation_report_md": "reports\\pilot_03_validation\\committed_output_validation_report.md",
    "validation_results_csv": "reports\\pilot_03_validation\\validation_results.csv"
  },
  "real_api_calls": 0,
  "safe_note": "Validation report for committed Pilot 03 outputs. This command checks internal consistency only and makes no real API calls.",
  "status": "PASS"
}
```
