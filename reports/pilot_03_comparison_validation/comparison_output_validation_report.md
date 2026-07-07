# Pilot 03 comparison-output validation report

Generated at UTC: 2026-07-07T10:49:48+00:00

## Scope

Validation report for committed Pilot 03 comparison outputs. This command checks internal consistency only and makes no real API calls.

Validation status: **PASS**

## Checks

| check_name | status | detail |
| --- | --- | --- |
| required_csv_exists::full_paired_chain_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\paired_chain_comparison.csv; exists=True |
| required_csv_exists::full_model_condition_summary | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\model_condition_summary.csv; exists=True |
| required_csv_exists::full_condition_delta_summary | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\condition_delta_summary.csv; exists=True |
| required_csv_exists::full_paired_agreement_summary | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\paired_agreement_summary.csv; exists=True |
| required_csv_exists::full_failure_pattern_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\failure_pattern_comparison.csv; exists=True |
| required_csv_exists::uncertainty_model_metric_uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\model_metric_uncertainty.csv; exists=True |
| required_csv_exists::uncertainty_paired_delta_uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\paired_delta_uncertainty.csv; exists=True |
| required_csv_exists::paired_task_condition_paired_outcomes | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_condition_paired_outcomes.csv; exists=True |
| required_csv_exists::paired_task_level_summary | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_level_summary.csv; exists=True |
| required_csv_exists::paired_condition_pair_profile | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\condition_pair_profile.csv; exists=True |
| required_csv_exists::paired_high_signal_cases | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\high_signal_cases.csv; exists=True |
| required_csv_exists::cascade_model_condition_cascade_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\model_condition_cascade_metrics.csv; exists=True |
| required_csv_exists::cascade_evidence_condition_delta_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\evidence_condition_delta_metrics.csv; exists=True |
| required_csv_exists::cascade_cross_model_cascade_comparison | PASS | path=reports\pilot_03_reliability_cascade_metrics\cross_model_cascade_comparison.csv; exists=True |
| required_csv_exists::cascade_metric_definitions | PASS | path=reports\pilot_03_reliability_cascade_metrics\metric_definitions.csv; exists=True |
| required_manifest_exists::full_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\manifest.json; exists=True |
| required_manifest_exists::uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\manifest.json; exists=True |
| required_manifest_exists::paired_task_analysis | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\manifest.json; exists=True |
| required_manifest_exists::cascade_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\manifest.json; exists=True |
| required_manifest_exists::final_figures | PASS | path=reports\pilot_03_final_figures\manifest.json; exists=True |
| required_final_figure_notes_exists | PASS | path=reports\pilot_03_final_figures\figure_notes.md; exists=True |
| csv_row_count::full_paired_chain_comparison | PASS | actual=60; expected=60; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_chain_comparison.csv |
| csv_required_columns::full_paired_chain_comparison | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_chain_comparison.csv |
| csv_safe_note_nonempty::full_paired_chain_comparison | PASS | rows=60; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_chain_comparison.csv |
| csv_row_count::full_model_condition_summary | PASS | actual=6; expected=6; path=reports\pilot_03_glm_vs_claude_t0020_full\model_condition_summary.csv |
| csv_required_columns::full_model_condition_summary | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_full\model_condition_summary.csv |
| csv_safe_note_nonempty::full_model_condition_summary | PASS | rows=6; path=reports\pilot_03_glm_vs_claude_t0020_full\model_condition_summary.csv |
| csv_row_count::full_condition_delta_summary | PASS | actual=15; expected=15; path=reports\pilot_03_glm_vs_claude_t0020_full\condition_delta_summary.csv |
| csv_required_columns::full_condition_delta_summary | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_full\condition_delta_summary.csv |
| csv_safe_note_nonempty::full_condition_delta_summary | PASS | rows=15; path=reports\pilot_03_glm_vs_claude_t0020_full\condition_delta_summary.csv |
| csv_row_count::full_paired_agreement_summary | PASS | actual=9; expected=9; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_agreement_summary.csv |
| csv_required_columns::full_paired_agreement_summary | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_agreement_summary.csv |
| csv_safe_note_nonempty::full_paired_agreement_summary | PASS | rows=9; path=reports\pilot_03_glm_vs_claude_t0020_full\paired_agreement_summary.csv |
| csv_row_count::full_failure_pattern_comparison | PASS | actual=15; expected=15; path=reports\pilot_03_glm_vs_claude_t0020_full\failure_pattern_comparison.csv |
| csv_required_columns::full_failure_pattern_comparison | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_full\failure_pattern_comparison.csv |
| csv_safe_note_nonempty::full_failure_pattern_comparison | PASS | rows=15; path=reports\pilot_03_glm_vs_claude_t0020_full\failure_pattern_comparison.csv |
| csv_row_count::uncertainty_model_metric_uncertainty | PASS | actual=30; expected=30; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\model_metric_uncertainty.csv |
| csv_required_columns::uncertainty_model_metric_uncertainty | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\model_metric_uncertainty.csv |
| csv_safe_note_nonempty::uncertainty_model_metric_uncertainty | PASS | rows=30; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\model_metric_uncertainty.csv |
| csv_row_count::uncertainty_paired_delta_uncertainty | PASS | actual=15; expected=15; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\paired_delta_uncertainty.csv |
| csv_required_columns::uncertainty_paired_delta_uncertainty | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\paired_delta_uncertainty.csv |
| csv_safe_note_nonempty::uncertainty_paired_delta_uncertainty | PASS | rows=15; path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\paired_delta_uncertainty.csv |
| csv_row_count::paired_task_condition_paired_outcomes | PASS | actual=60; expected=60; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_condition_paired_outcomes.csv |
| csv_required_columns::paired_task_condition_paired_outcomes | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_condition_paired_outcomes.csv |
| csv_safe_note_nonempty::paired_task_condition_paired_outcomes | PASS | rows=60; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_condition_paired_outcomes.csv |
| csv_row_count::paired_task_level_summary | PASS | actual=20; expected=20; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_level_summary.csv |
| csv_required_columns::paired_task_level_summary | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_level_summary.csv |
| csv_safe_note_nonempty::paired_task_level_summary | PASS | rows=20; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\task_level_summary.csv |
| csv_row_count::paired_condition_pair_profile | PASS | actual=3; expected=3; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\condition_pair_profile.csv |
| csv_required_columns::paired_condition_pair_profile | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\condition_pair_profile.csv |
| csv_safe_note_nonempty::paired_condition_pair_profile | PASS | rows=3; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\condition_pair_profile.csv |
| csv_row_count::paired_high_signal_cases | PASS | actual=24; expected=24; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\high_signal_cases.csv |
| csv_required_columns::paired_high_signal_cases | PASS | missing_columns=[]; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\high_signal_cases.csv |
| csv_safe_note_nonempty::paired_high_signal_cases | PASS | rows=24; path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\high_signal_cases.csv |
| csv_row_count::cascade_model_condition_cascade_metrics | PASS | actual=6; expected=6; path=reports\pilot_03_reliability_cascade_metrics\model_condition_cascade_metrics.csv |
| csv_required_columns::cascade_model_condition_cascade_metrics | PASS | missing_columns=[]; path=reports\pilot_03_reliability_cascade_metrics\model_condition_cascade_metrics.csv |
| csv_safe_note_nonempty::cascade_model_condition_cascade_metrics | PASS | rows=6; path=reports\pilot_03_reliability_cascade_metrics\model_condition_cascade_metrics.csv |
| csv_row_count::cascade_evidence_condition_delta_metrics | PASS | actual=48; expected=48; path=reports\pilot_03_reliability_cascade_metrics\evidence_condition_delta_metrics.csv |
| csv_required_columns::cascade_evidence_condition_delta_metrics | PASS | missing_columns=[]; path=reports\pilot_03_reliability_cascade_metrics\evidence_condition_delta_metrics.csv |
| csv_safe_note_nonempty::cascade_evidence_condition_delta_metrics | PASS | rows=48; path=reports\pilot_03_reliability_cascade_metrics\evidence_condition_delta_metrics.csv |
| csv_row_count::cascade_cross_model_cascade_comparison | PASS | actual=30; expected=30; path=reports\pilot_03_reliability_cascade_metrics\cross_model_cascade_comparison.csv |
| csv_required_columns::cascade_cross_model_cascade_comparison | PASS | missing_columns=[]; path=reports\pilot_03_reliability_cascade_metrics\cross_model_cascade_comparison.csv |
| csv_safe_note_nonempty::cascade_cross_model_cascade_comparison | PASS | rows=30; path=reports\pilot_03_reliability_cascade_metrics\cross_model_cascade_comparison.csv |
| csv_row_count::cascade_metric_definitions | PASS | actual=12; expected=12; path=reports\pilot_03_reliability_cascade_metrics\metric_definitions.csv |
| csv_required_columns::cascade_metric_definitions | PASS | missing_columns=[]; path=reports\pilot_03_reliability_cascade_metrics\metric_definitions.csv |
| csv_safe_note_nonempty::cascade_metric_definitions | PASS | rows=12; path=reports\pilot_03_reliability_cascade_metrics\metric_definitions.csv |
| manifest_real_api_calls_zero::full_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\manifest.json; real_api_calls=0 |
| manifest_raw_response_inspection_false::full_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\manifest.json; raw_response_inspection=False |
| manifest_status_pass::full_comparison | PASS | path=reports\pilot_03_glm_vs_claude_t0020_full\manifest.json; status=PASS |
| manifest_real_api_calls_zero::uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\manifest.json; real_api_calls=0 |
| manifest_raw_response_inspection_false::uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\manifest.json; raw_response_inspection=False |
| manifest_status_pass::uncertainty | PASS | path=reports\pilot_03_glm_vs_claude_t0020_uncertainty\manifest.json; status=PASS |
| manifest_real_api_calls_zero::paired_task_analysis | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\manifest.json; real_api_calls=0 |
| manifest_raw_response_inspection_false::paired_task_analysis | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\manifest.json; raw_response_inspection=False |
| manifest_status_pass::paired_task_analysis | PASS | path=reports\pilot_03_glm_vs_claude_t0020_paired_task_analysis\manifest.json; status=PASS |
| manifest_real_api_calls_zero::cascade_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\manifest.json; real_api_calls=0 |
| manifest_raw_response_inspection_false::cascade_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\manifest.json; raw_response_inspection=False |
| manifest_status_pass::cascade_metrics | PASS | path=reports\pilot_03_reliability_cascade_metrics\manifest.json; status=PASS |
| manifest_real_api_calls_zero::final_figures | PASS | path=reports\pilot_03_final_figures\manifest.json; real_api_calls=0 |
| manifest_raw_response_inspection_false::final_figures | PASS | path=reports\pilot_03_final_figures\manifest.json; raw_response_inspection=False |
| full_summary_n_chains_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_escalation_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_audit_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_valid_json_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::zai::original_evidence | PASS | actual=20; expected=20 |
| full_summary_n_chains_matches_paired::zai::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::zai::missing_policy_rule | PASS | actual=10; expected=10 |
| full_summary_escalation_matches_paired::zai::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_audit_matches_paired::zai::missing_policy_rule | PASS | actual=2; expected=2 |
| full_summary_valid_json_matches_paired::zai::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::zai::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_n_chains_matches_paired::zai::missing_one_required_unit | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::zai::missing_one_required_unit | PASS | actual=10; expected=10 |
| full_summary_escalation_matches_paired::zai::missing_one_required_unit | PASS | actual=10; expected=10 |
| full_summary_audit_matches_paired::zai::missing_one_required_unit | PASS | actual=11; expected=11 |
| full_summary_valid_json_matches_paired::zai::missing_one_required_unit | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::zai::missing_one_required_unit | PASS | actual=20; expected=20 |
| full_summary_n_chains_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_escalation_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_audit_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_valid_json_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::anthropic::original_evidence | PASS | actual=20; expected=20 |
| full_summary_n_chains_matches_paired::anthropic::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::anthropic::missing_policy_rule | PASS | actual=10; expected=10 |
| full_summary_escalation_matches_paired::anthropic::missing_policy_rule | PASS | actual=17; expected=17 |
| full_summary_audit_matches_paired::anthropic::missing_policy_rule | PASS | actual=0; expected=0 |
| full_summary_valid_json_matches_paired::anthropic::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::anthropic::missing_policy_rule | PASS | actual=20; expected=20 |
| full_summary_n_chains_matches_paired::anthropic::missing_one_required_unit | PASS | actual=20; expected=20 |
| full_summary_decision_matches_paired::anthropic::missing_one_required_unit | PASS | actual=10; expected=10 |
| full_summary_escalation_matches_paired::anthropic::missing_one_required_unit | PASS | actual=10; expected=10 |
| full_summary_audit_matches_paired::anthropic::missing_one_required_unit | PASS | actual=14; expected=14 |
| full_summary_valid_json_matches_paired::anthropic::missing_one_required_unit | PASS | actual=20; expected=20 |
| full_summary_valid_schema_matches_paired::anthropic::missing_one_required_unit | PASS | actual=20; expected=20 |
| delta_arithmetic::full_condition_delta_summary | PASS | n_failures=0; first_failure=[] |
| delta_arithmetic::uncertainty_paired_delta_uncertainty | PASS | n_failures=0; first_failure=[] |
| delta_arithmetic::cascade_evidence_condition_delta_metrics | PASS | n_failures=0; first_failure=[] |
| delta_arithmetic::cascade_cross_model_cascade_comparison | PASS | n_failures=0; first_failure=[] |
| rate_columns_within_unit_interval | PASS | n_failures=0; first_failure=[] |
| count_rate_consistency::full_model_condition_summary | PASS | n_failures=0; first_failure=[] |
| count_rate_consistency::cascade_model_condition_cascade_metrics | PASS | n_failures=0; first_failure=[] |
| count_rate_consistency::full_paired_agreement_summary | PASS | n_failures=0; first_failure=[] |
| paired_condition_profile_sum::decision | PASS | n_failures=0; first_failure=[] |
| paired_condition_profile_sum::escalation | PASS | n_failures=0; first_failure=[] |
| paired_condition_profile_sum::audit | PASS | n_failures=0; first_failure=[] |
| uncertainty_success_estimate_ci_consistency | PASS | n_failures=0; first_failure=[] |
| final_figures_report_name | PASS | report_name=pilot_03_final_figures |
| final_figures_source_file_count | PASS | actual=7; expected=7 |
| final_figures_figure_count | PASS | actual=7; expected=7 |
| final_figures_output_count | PASS | actual=15; expected=15 |
| final_figures_paths_repo_relative | PASS | n_paths=15 |
| final_figures_all_outputs_exist | PASS | n_paths=15 |
| final_figures_png_pdf_presence | PASS | png=7; pdf=7 |
| blocked_raw_prompt_response_like_columns | PASS | n_hits=0 |
| risky_public_wording_absent | PASS | n_hits=0 |

## Risky wording hits

None.

## Blocked column hits

None.

## Manifest

```json
{
  "created_at_utc": "2026-07-07T10:49:48+00:00",
  "n_blocked_column_hits": 0,
  "n_checks": 137,
  "n_failed_checks": 0,
  "n_risky_wording_hits": 0,
  "outputs": {
    "manifest_json": "reports\\pilot_03_comparison_validation\\manifest.json",
    "validation_report_md": "reports\\pilot_03_comparison_validation\\comparison_output_validation_report.md",
    "validation_results_csv": "reports\\pilot_03_comparison_validation\\comparison_validation_results.csv"
  },
  "raw_response_inspection": false,
  "real_api_calls": 0,
  "safe_note": "Validation report for committed Pilot 03 comparison outputs. This command checks internal consistency only and makes no real API calls.",
  "status": "PASS",
  "validated_csv_count": 15,
  "validated_manifest_count": 5
}
```
