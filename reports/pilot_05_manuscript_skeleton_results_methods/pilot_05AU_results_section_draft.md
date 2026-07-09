# Pilot 05AU Results Section Draft

## Results overview

The committed run is organized around 720 planned/ledgered pipeline calls. The sanitized execution layer contains 713 retained rows after parser and execution accounting. The stage-success degradation range is reported as -0.517241 to -0.40678. The parser-validity delta range is reported as 0.067797 to 0.368421. The all-sequence cascade-failure rate is reported as 0.929167. The degraded audit detection mean is reported as 1.0. The degraded escalation recovery mean is reported as 0.0.

The central empirical finding is a divergence between parser validity and evidence-state reliability. Under controlled evidence-state degradation, parser validity improves while stage/evidence success deteriorates. This means parser validity cannot be used as a sufficient proxy for reliability in this pipeline.

## Result 1: Parser validity diverges from evidence-state reliability

The committed parser-versus-evidence-state table supports the paper's main contrast: parser-validity behavior and evidence-state reliability do not move together under degradation.

| comparison_group | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
|  | value | 243.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 470.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 250.0 | pilot_05AR_paper_ready_main_results_table.csv | value |
|  | value | 470.0 | pilot_05AR_paper_ready_main_results_table.csv | value |


### Interpretation

This is the central head-turning result. A system may become more parser-valid under degraded evidence while becoming less reliable at the evidence-state layer. That pattern is exactly why Evidence-State Reliability needs to be measured separately from final-output parser validity.

## Result 2: Audit and escalation expose downstream cascade behavior

The audit and escalation outputs show how degradation affects downstream pipeline behavior after the initial decision stage.

| label | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
| audit_detection_rate_degraded_mean | observed_rate | 1.0 | pilot_05AR_audit_escalation_interpretation.csv | observed_rate |
| escalation_recovery_rate_degraded_mean | observed_rate | 0.0 | pilot_05AR_audit_escalation_interpretation.csv | observed_rate |


### Interpretation

The audit/escalation layer is important because a downstream stage may detect degradation without recovering from it. The distinction between detection and recovery should be explicit in the paper.

## Result 3: Cascade failure rate summarizes pipeline-level reliability loss

The cascade-failure output provides a pipeline-level view of how often reliability loss propagates across sequence groups.

| label | metric | value | source_file | source_column |
| --- | --- | --- | --- | --- |
| cascade_failure_rate_all_sequence_groups | value | 0.929167 | pilot_05AR_cascade_failure_interpretation.csv | value |


### Interpretation

Cascade failure should be framed as a pipeline reliability phenomenon, not as a model-general claim. The study shows this behavior within the committed Pilot 05 design.

## Result 4: Failure-family interpretation clarifies where degradation concentrates

The failure-family interpretation separates different kinds of reliability failures instead of collapsing them into a single final-output score.

| failure_family | value | source_file | source_column |
| --- | --- | --- | --- |
| Detected-but-unrecovered degradation | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |
| Parser-valid / evidence-invalid divergence | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |
| Missing-sanitized-row gap | 1.0 | pilot_05AR_failure_family_interpretation.csv | row_presence_count_fallback |


### Interpretation

Failure-family structure helps make the paper stronger because it shows that reliability loss is not monolithic. Different pipeline stages and reliability layers can fail in different ways.

## Results claim boundary

The results support the Evidence-State Reliability distinction within the committed Pilot 05 GLM-5.2 experiment. They do not establish broad GLM reliability, general LLM reliability, real-world financial validity, regulatory validity, deployment safety, or consumer harm prevalence.
