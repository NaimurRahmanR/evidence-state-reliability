# Task 05BF Figure Repair Traceability

## Purpose

This derivative package repairs only the two visual-evidence contracts rejected by the committed independent 05BE audit. It does not alter the committed 05AS assets or the committed 05BD manuscript.

## Figure 1 repair

- 05BE finding closed candidate: `FIG-B01`
- Authoritative source: `reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv`
- Source rows used: 18
- Parser-validity rows: 9
- Stage-success rows: 9
- Parser-validity point estimates above zero: 9/9
- Parser-validity intervals crossing zero: 3/9, all `partial_dropout`
- Stage-success intervals below zero: 9/9
- Bootstrap contract: 2,000 resamples; seed 5205
- Corrected data: `reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv`
- Corrected asset: `reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_parser_vs_esr_divergence.png`
- PNG SHA-256: `7A3EA7C709E7F6DB47BA9FC383D8A0F13CA988F77FC6FDC5CD675CAACB33F0D8`

The corrected asset is a paired forest plot. Each evidence-condition and stage row contains one parser-validity estimate and one stage-success estimate with its 95% bootstrap interval and a zero reference line.

## Figure 4 repair

- 05BE finding closed candidate: `FIG-M01`
- Authoritative source: `reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv`
- Corrected data rows: 5
- Counts: parser failure 143; detected but not recovered 71; audit false assurance 3; incomplete sequence 6; preserved success 17
- Count sum: 240/240
- Corrected data: `reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_data.csv`
- Corrected asset: `reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_counts.png`
- PNG SHA-256: `6588B474A94B95DDF0389C2B2EE18CB4EF7BD10388E6ABD3E6290B7D090E0417`

The corrected asset reports the authoritative sequence-family counts rather than row-presence fallback values.

## Manuscript rebinding

The repaired derivative manuscript is `reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md`. It differs from committed 05BD only through:

1. the Figure 1 asset path;
2. the Figure 1 caption;
3. the Figure 4 asset path;
4. the Figure 4 caption.

Undoing those four replacements restores the committed 05BD manuscript byte for byte. Figures 2 and 3, all four tables, all 22 references, numerical prose, uncertainty statements, conclusions, and limitations remain unchanged.

## Scope

This package creates no empirical evidence, model output, literature claim, or journal-readiness verdict. It prepares a traceable candidate for independent 05BG revalidation.
