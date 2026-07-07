# Cross-Pilot Figure and Table Index

## Scope

These tables and figures are generated from committed sanitized outputs only. They support controlled evidence-state reliability reporting across Pilot 03 and Pilot 04.

They do not export prompt text, raw model outputs, or secret values.

## Tables

- table_01_framework_summary: `reports\cross_pilot_figures_tables\tables\table_01_framework_summary.csv`
- table_02_validation_status: `reports\cross_pilot_figures_tables\tables\table_02_validation_status.csv`
- table_03_condition_metric_alignment: `reports\cross_pilot_figures_tables\tables\table_03_condition_metric_alignment.csv`
- table_04_pilot04_reliability_by_condition: `reports\cross_pilot_figures_tables\tables\table_04_pilot04_reliability_by_condition.csv`
- table_05_pilot04_stage_cascade_summary: `reports\cross_pilot_figures_tables\tables\table_05_pilot04_stage_cascade_summary.csv`
- table_06_pilot04_uncertainty_summary: `reports\cross_pilot_figures_tables\tables\table_06_pilot04_uncertainty_summary.csv`
- table_07_metric_inventory_compact: `reports\cross_pilot_figures_tables\tables\table_07_metric_inventory_compact.csv`

## Figures

- figure_01_validation_steps: `reports\cross_pilot_figures_tables\figures\figure_01_validation_steps.png`
- figure_02_validation_checks: `reports\cross_pilot_figures_tables\figures\figure_02_validation_checks.png`
- figure_03_pilot04_reliability_index: `reports\cross_pilot_figures_tables\figures\figure_03_pilot04_reliability_index.png`
- figure_04_pilot04_structural_gap: `reports\cross_pilot_figures_tables\figures\figure_04_pilot04_structural_gap.png`
- figure_05_pilot04_escalation_rate: `reports\cross_pilot_figures_tables\figures\figure_05_pilot04_escalation_rate.png`
- figure_06_metric_inventory_numeric_counts: `reports\cross_pilot_figures_tables\figures\figure_06_metric_inventory_numeric_counts.png`

## Framework summary preview

| pilot_id | domain | domain_status | condition_metric_rows | claim_boundary |
| --- | --- | --- | --- | --- |
| pilot_03 | synthetic administrative approval | locked | 6 | controlled synthetic domain only |
| pilot_04 | synthetic loan-risk decision support | new second domain | 3 | controlled synthetic domain only |

## Validation summary preview

| pilot_id | status | n_steps | n_failed_steps | n_checks | n_failed_checks | real_api_calls |
| --- | --- | --- | --- | --- | --- | --- |
| pilot_03 | PASS | 14 | 0 |  |  | 0 |
| pilot_03 | PASS |  |  | 171 | 0 | 0 |
| pilot_04 | PASS | 13 | 0 |  |  | 0 |
| pilot_04 | PASS |  |  | 124 | 0 | 0 |

## Pilot 04 reliability-condition preview

| condition | structural_validity_rate | reliability_cascade_index | structural_validity_gap |
| --- | --- | --- | --- |
| complete | 1.0 | 0.9825 | 0.0175 |
| partial | 1.0 | 0.326666 | 0.673334 |
| conflicted | 1.0 | 0.510833 | 0.489167 |

## Safe interpretation

The tables and figures support a controlled measurement claim: structural validity and reliability-layer behaviour can be represented separately across the current evidence-state pipeline outputs.

- real_api_calls: 0
- raw_response_inspection: False
