# Pilot 05 CFPB complaint dataset audit

Generated at UTC: 2026-07-07T18:26:19+00:00

## Scope

This report is a sanitized aggregate audit of a local CFPB Consumer Complaint Database export.
It does not include raw rows, raw complaint narratives, raw prompts, raw responses, secrets, or model/API outputs.

## Source summary

- Source route: CFPB Consumer Complaint Database official browser-export CSV; product=Credit card or prepaid card; date_received=2026-01-01..2026-03-31; Task 05P strict row-quality gate; Task 05Q CFPB datetime accepted; Task 05R deterministic csv.excel parsing
- Input filename only: cfpb_complaints_2026_q1_credit_card_browser_export_raw.csv
- Rows audited: 26823
- Columns detected: 16
- Max rows setting: 0
- Target column detected: Timely response?
- Narrative column detected: Consumer complaint narrative

## Claim boundary

This audit supports a recorded complaint-resolution outcome review simulation only.
It does not claim company misconduct.
It does not claim consumer harm prevalence.
It does not claim financial safety.
It does not claim legal safety.
It does not claim real-world deployment proof.
It does not claim provider ranking.

## Safety status

- real_api_calls: 0
- model_calls: 0
- dataset_downloads: 0
- raw_response_inspection: False
- raw_rows_written_to_reports: False
- raw_narratives_written_to_reports: False
- raw_data_committed: False

## Output files

- selected_source_manifest.json
- dataset_audit_summary.csv
- column_inventory.csv
- target_distribution.csv
- missingness_summary.csv
- sensitive_field_inventory.csv
- temporal_field_audit.csv
- leakage_risk_notes.csv
- narrative_availability_summary.csv
- product_issue_summary.csv
- pilot_05_cfpb_complaints_dataset_audit_report.md

## Next step

Use this audit to decide the exact sanitized evidence-packet construction.
Do not run real LLM chains until provider/model/sample size/prompt family are explicitly approved.
