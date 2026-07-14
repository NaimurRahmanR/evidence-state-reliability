# Task 05BG Independent Corrected-Figure Revalidation

## Audit result

- Revalidation execution: **PASS**
- Source checkpoint: `120f05840f90e05c9b7101e50ff68f9fbde588e3`
- Original 05BE finding `FIG-B01`: **CLOSED**
- Original 05BE finding `FIG-M01`: **CLOSED**
- New layout finding `FIG-L01`: **OPEN — mandatory before submission**
- Journal selection: **AUTHORIZED**
- Venue formatting: **AUTHORIZED**
- Final submission: **NOT YET AUTHORIZED**

## Independent evidence checks

The corrected Figure 1 data were compared row by row with the committed 05AP bootstrap table. All 18 plotted records match the authoritative paired-case counts, means, 95% intervals, 2,000-resample contract, and seed 5205. The original Figure 1 data-contract blocker is therefore closed.

The corrected Figure 4 data were compared with the `ALL` row of the committed cascade table. The five counts are 143, 71, 3, 6, and 17 and sum to 240. The original Figure 4 fallback-value finding is therefore closed.

## Rendered-asset review

Figure 1 is the exact SHA-256-reviewed PNG and has dimensions 3210 × 2006. Its title, axis label, zero line, nine condition-stage labels, series distinction, and legend labels are readable. However, the legend occupies the lower-right data region and obscures the right segment and cap of the noisy-conflicting escalation parser-validity confidence interval. This is a presentation defect rather than a numerical or claim-integrity defect, but it must be repaired before final submission.

Figure 4 is the exact SHA-256-reviewed PNG and has dimensions 2849 × 1645. All five labels, bars, and numerical annotations are clear and unobstructed.

## Manuscript binding

The derivative manuscript is an exact four-replacement transformation of committed 05BD and is reversible to it byte for byte. Figures 2 and 3 remain unchanged; all four tables, all 22 references, numerical prose, limitations, conclusions, and bounded claim language remain preserved.

## Finding accounting

- Figure 1 register failures: 2
- Figure 4 register failures: 0
- Original findings closed: 2/2
- New scientific-integrity blockers: 0
- New layout blockers for submission: 1

## Gate

The evidence package is sufficiently repaired to begin journal selection and venue-specific formatting. Final submission remains blocked until the Figure 1 legend is moved outside the data region or to a non-overlapping location and the final exported asset is checked against the unchanged 18-row data contract.
