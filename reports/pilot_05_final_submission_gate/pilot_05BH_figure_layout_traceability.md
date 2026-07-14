# Task 05BH Final Figure Layout Traceability

## Closed finding

- Finding: `FIG-L01`
- Prior state: OPEN layout blocker for submission
- Repair: Figure 1 legend moved completely outside the plotting axes
- Scientific data changed: NO
- Caption changed: NO
- Numerical prose changed: NO

## Authoritative data contract

- Source: `reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv`
- Source rows: 18/18
- Parser-validity rows: 9/9
- Stage-success rows: 9/9
- Parser-validity intervals crossing zero: 3/9, partial-dropout only
- Stage-success intervals below zero: 9/9
- Bootstrap resamples: 2,000
- Random seed: 5205

## Export layout contract

- Canvas: 3200 × 2000 pixels
- Axes top: 0.84
- Legend anchor: (0.5, 0.975)
- Legend location: `upper center`
- Legend columns: 2
- Minimum normalized vertical separation between axes top and legend anchor: 0.135
- Legend created with `figure.legend`, not `axes.legend`
- Legend overlaps plotting axes: NO

## Manuscript binding

- Source manuscript: `reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md`
- Final manuscript: `reports/pilot_05_final_submission_gate/pilot_05BH_final_manuscript.md`
- Approved manuscript differences relative to 05BF: 1
- Difference: Figure 1 asset path only
- Reverse restoration to byte-identical 05BF manuscript: YES

The final export remains subject to the separate 05BH submission-gate validator.
