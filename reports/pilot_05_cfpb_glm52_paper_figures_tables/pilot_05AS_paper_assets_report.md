# Pilot 05AS Paper Figures and Final Main Tables Report

## Status

PASS

## Purpose

Task 05AS converts committed and validated 05AR interpretation outputs into paper-facing assets: final tables, figure-data CSVs, PNG figures, and caption/table packs.

## Claim boundary

05AS does not create new empirical evidence and does not make model/API calls. It reformats committed 05AR outputs for manuscript use.

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting the claim that Evidence-State Reliability is distinct from parser validity.

## Not claimed

- broad GLM reliability
- general LLM reliability
- model/provider superiority
- real-world financial validity
- regulatory validity
- deployment safety
- consumer harm prevalence
- company misconduct
- parser validity equals answer correctness
- full paper completion
- Q1 acceptance or ground-breaking proof

## Git checkpoint

- branch: `main`
- latest commit: `5bc4d3d Add Pilot 05 scaled results interpretation`
- latest subject: `Add Pilot 05 scaled results interpretation`
- origin/main alignment: `0	0`

## Generated figures

### pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png

- rendering_backend: `matplotlib`

Figure 1. Parser-vs-evidence-state divergence under controlled degradation. The figure is generated from committed 05AR outputs and supports the bounded claim that parser validity and Evidence-State Reliability are separate evaluation layers in this Pilot 05 run.

### pilot_05AS_figure_02_audit_escalation_interpretation.png

- rendering_backend: `matplotlib`

Figure 2. Audit/escalation behavior in the controlled Pilot 05 run. The interpretation is intentionally bounded: degraded evidence can be detected, but escalation recovery was not observed as successful recovery in this run.

### pilot_05AS_figure_03_cascade_failure_rate.png

- rendering_backend: `matplotlib`

Figure 3. Cascade-failure interpretation from committed 05AR outputs. The figure supports the manuscript need to measure evidence-state, decision, audit, escalation, and sequence-level behavior separately.

### pilot_05AS_figure_04_failure_family_interpretation.png

- rendering_backend: `matplotlib`

Figure 4. Failure-family interpretation from committed 05AR outputs. This is a descriptive reliability-cascade diagnostic and does not imply broad model, provider, regulatory, or real-world harm claims.

## Generated output contract

| output_file | exists | size_bytes |
| --- | --- | --- |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_manifest.json | True | 9194 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_input_file_index.csv | True | 1927 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.csv | True | 874 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.md | True | 1185 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.tex | True | 1240 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv | True | 321 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png | True | 105492 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv | True | 280 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png | True | 72640 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv | True | 155 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png | True | 67915 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv | True | 388 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png | True | 87865 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_claim_boundary_table_final.csv | True | 1710 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_limitations_and_validity_threats_final.csv | True | 642 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_metric_validation_summary.csv | True | 3913 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_caption_pack.md | True | 1284 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_table_pack.md | True | 3816 |
| reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_assets_report.md | True | 5093 |


## Safety flags

- no_api_calls: True
- no_model_calls: True
- no_env_read: True
- no_raw_prompt_response_access: True
- no_jsonl_written: True
- no_raw_cfpb_data_touched: True
