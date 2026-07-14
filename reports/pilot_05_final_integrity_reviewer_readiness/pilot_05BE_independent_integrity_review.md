# Pilot 05BE — Independent Final Integrity and Reviewer-Readiness Review

## Executive verdict

**Audit execution status: PASS**

**Manuscript-text and numerical-integrity status: PASS**

**Figure-integrity status: FAIL**

**Submission-readiness verdict: NOT READY FOR JOURNAL SELECTION OR VENUE FORMATTING**

The final expanded manuscript is substantially stronger than the preceding journal-form draft. Its numerical accounting, condition-by-stage reporting, uncertainty disclosure, construct boundaries, citation set, and reviewer-risk responses are internally coherent and traceable to the committed sanitized evidence base. The independent review nevertheless found a submission-blocking figure-data mismatch that was not detected by the manuscript generator's path-level binding checks.

## 1. What passed independently

- The manuscript remains within the approved 6,320–8,000-word body range.
- All 12 condition-stage cells are present and agree with the authoritative condition-stage table.
- All 27 bootstrap rows are represented.
- All nine parser-validity point estimates are positive; the three partial-dropout intervals that include zero are disclosed.
- All nine stage-success intervals remain below zero.
- Audit detection, false assurance, escalation recovery, missing-row accounting, and 223/240 cascade failures are reported with bounded interpretations.
- The 22-item reference set is present, the seven preprints are labelled, and the FSB 2026 source remains labelled as consultation material.
- ESR is distinguished from parser validity and from its operational stage-success indicator.
- Single-model, single-run, sanitized-evidence, model-output-coded, and artifact-reproducibility limits remain explicit.
- No internal task identifiers, head-turning language, first-ever claim, or global-priority claim appears in publication prose.

## 2. Submission-blocking finding

### FIG-B01 — Figure 1 source data does not support its caption

The manuscript presents Figure 1 as a visual summary of nine positive parser-validity contrasts and nine negative stage-success contrasts. The committed data file bound to that asset contains only four rows. Their comparison-group fields are empty, each metric label is `value`, and the values are 243, 470, 250, and 470. Those are parser-accounting totals, not the condition-stage or bootstrap divergence results described in the caption.

Because Figure 1 visualises the paper's central empirical contrast, path existence and caption order are insufficient. The figure must be regenerated from the authoritative condition-stage or bootstrap table and then checked visually against its caption and the manuscript.

Severity: **BLOCKER**

Required repair:
1. Generate Figure 1 from the nine degraded parser-validity and nine degraded stage-success comparisons.
2. Use explicit condition and stage labels.
3. Preserve the three parser-validity intervals crossing zero where uncertainty is displayed.
4. Bind the new asset to a machine-readable source file whose rows reproduce the plotted values.
5. Repeat independent figure-data and visual-content validation.

## 3. Additional major figure finding

### FIG-M01 — Figure 4 uses row-presence fallback values

The Figure 4 source file contains three qualitative category rows, each with `value=1.0` and `source_column=row_presence_count_fallback`. It does not encode the actual sequence taxonomy reported in Table 4: 143 parser-failure cascades, 71 detected-not-recovered patterns, three audit-false-assurance patterns, six incomplete sequences, and 17 preserved successes.

The manuscript correctly calls Table 4 authoritative and describes Figure 4 as qualitative. Even so, an equal-value bar-like representation risks looking quantitative without carrying the actual counts. Figure 4 should therefore be redesigned from the sequence counts, converted into a clearly non-quantitative conceptual diagram, or removed if it adds no information beyond Table 4.

Severity: **MAJOR**

## 4. Residual editorial actions

These are not empirical blockers:

- Apply the selected journal's reference and URL style only after figure repair passes.
- Add the final release commit, archival DOI, or immutable version to Data and Code Availability after the repaired manuscript is secured.
- During typesetting, confirm that equations, Markdown tables, and figure captions render correctly in the target template.
- Preserve the current uncertainty-aware wording; do not upgrade directional parser-validity findings into uniform significance claims.

## 5. Final assessment

The manuscript's scientific text and reported numerical evidence are ready for a focused figure repair, not for journal formatting yet. No new experiment, model run, raw-data access, or literature search is required. The next task should modify only derivative figure assets, their source-data files, the corresponding manuscript bindings/captions if needed, and the associated validation artifacts. After that repair, an independent recheck should determine whether the project can proceed to journal selection and venue-specific formatting.
