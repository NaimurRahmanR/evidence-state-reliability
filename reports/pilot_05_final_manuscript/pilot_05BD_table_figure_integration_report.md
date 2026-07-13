# Task 05BD Table and Figure Integration Report

## Table integration

| Item | Manuscript location | Authoritative source | Status |
|---|---|---|---|
| Table 1 | Results 4.1 | `pilot_05AR_paper_ready_main_results_table.csv`; `pilot_05AO_ledger_missing_sanitized_rows.csv` | PASS |
| Table 2 | Results 4.2 | `pilot_05AP_condition_stage_interaction.csv` | PASS — all 12 cells |
| Table 3 | Results 4.3 | `pilot_05AP_bootstrap_confidence_intervals.csv` | PASS — all 27 rows |
| Table 4 | Results 4.6 | `pilot_05AP_cascade_sequence_metrics.csv` | PASS — numerator, denominator, condition composition |

## Figure integration

| Figure | Exact committed asset | First in-text citation | Numerical authority | Status |
|---:|---|---|---|---|
| 1 | `reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png` | Results 4.2, before asset | Tables 2–3 and 05AP source tables | BOUND; numerical claims constrained to authoritative tables |
| 2 | `reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png` | Results 4.4, before asset | 05AP audit and escalation metrics | PASS |
| 3 | `reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png` | Results 4.6, before asset | 05AP cascade sequence metrics | PASS |
| 4 | `reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png` | Results 4.6, before asset | 05AR qualitative failure-family table; Table 4 for counts | PASS — qualitative figure, counts kept in Table 4 |

All figures use publication captions rather than internal filenames as visible captions. The exact filenames remain only in Markdown link destinations and this traceability report. Independent visual-content inspection remains part of Task 05BE.
