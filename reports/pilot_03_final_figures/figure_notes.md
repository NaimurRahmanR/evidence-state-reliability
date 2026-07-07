# Pilot 03 final figure notes

These figures were generated from committed sanitized Pilot 03 CSV outputs only.

Scope:

- Controlled Pilot 03 setup.
- Observed local result under the current committed sanitized outputs.
- Descriptive comparison only.
- No external API calls were made by the generator.
- The generator does not inspect raw prompts, raw responses, JSONL API outputs, or ignored aggregate JSON.

Safe interpretation:

The figures support later paper drafting, but they should not be read as broad model claims. They show observed behavior under the current Pilot 03 real LLM experimental conditions.

Generated figures:

1. **Condition degradation: decision correctness**
   - Figure id: `fig01_condition_degradation_decision_correctness`
   - Source keys: `model_metric_uncertainty`
   - Files: `fig01_condition_degradation_decision_correctness.png, fig01_condition_degradation_decision_correctness.pdf`

2. **Decision-stage vs escalation-stage correctness**
   - Figure id: `fig02_decision_vs_escalation_correctness`
   - Source keys: `model_condition_summary`
   - Files: `fig02_decision_vs_escalation_correctness.png, fig02_decision_vs_escalation_correctness.pdf`

3. **Audit false assurance and undetected decision failure**
   - Figure id: `fig03_audit_false_assurance_undetected_failure`
   - Source keys: `model_condition_cascade_metrics`
   - Files: `fig03_audit_false_assurance_undetected_failure.png, fig03_audit_false_assurance_undetected_failure.pdf`

4. **GLM vs Claude descriptive paired comparison**
   - Figure id: `fig04_glm_vs_claude_descriptive_paired_comparison`
   - Source keys: `paired_delta_uncertainty`
   - Files: `fig04_glm_vs_claude_descriptive_paired_comparison.png, fig04_glm_vs_claude_descriptive_paired_comparison.pdf`

5. **Reliability cascade metrics by model and evidence condition**
   - Figure id: `fig05_reliability_cascade_metric_table`
   - Source keys: `model_condition_cascade_metrics`
   - Files: `fig05_reliability_cascade_metric_table.png, fig05_reliability_cascade_metric_table.pdf`

6. **Paired task-level outcome profile**
   - Figure id: `fig06_paired_task_level_outcome_profile`
   - Source keys: `condition_pair_profile`
   - Files: `fig06_paired_task_level_outcome_profile.png, fig06_paired_task_level_outcome_profile.pdf`

7. **Reliability cascade metric differences: Claude minus GLM**
   - Figure id: `fig07_cascade_metric_descriptive_differences`
   - Source keys: `cross_model_cascade_comparison`
   - Files: `fig07_cascade_metric_descriptive_differences.png, fig07_cascade_metric_descriptive_differences.pdf`

Reproducibility note:

The companion `manifest.json` records source paths, row counts, SHA-256 hashes, generated files, and the no-call status.
