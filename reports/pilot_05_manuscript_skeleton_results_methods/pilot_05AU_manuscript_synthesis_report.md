# Pilot 05AU Manuscript Synthesis Report

## Status

PASS

## Purpose

Task 05AU creates a manuscript skeleton and results-methods synthesis package from committed 05AR, 05AS, and 05AT outputs only.

## Source boundary

- 05AR: scaled results interpretation.
- 05AS: paper figures and final tables.
- 05AT: repo-wide validation and reproducibility audit.

## Git checkpoint

- latest_commit: `725c8dd Add Pilot 05 repo validation audit`
- latest_hash: `725c8dd`
- latest_subject: `Add Pilot 05 repo validation audit`
- origin_main_alignment: `0 behind, 0 ahead`

## Synthesis summary

The committed run is organized around 720 planned/ledgered pipeline calls. The sanitized execution layer contains 713 retained rows after parser and execution accounting. The stage-success degradation range is reported as -0.517241 to -0.40678. The parser-validity delta range is reported as 0.067797 to 0.368421. The all-sequence cascade-failure rate is reported as 0.929167. The degraded audit detection mean is reported as 1.0. The degraded escalation recovery mean is reported as 0.0.

## Central manuscript claim

Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

## Generated manuscript artifacts

- `pilot_05AU_manuscript_skeleton.md`
- `pilot_05AU_methods_section_draft.md`
- `pilot_05AU_results_section_draft.md`
- `pilot_05AU_contribution_novelty_framing.md`
- `pilot_05AU_claim_boundary_and_limitations.md`
- `pilot_05AU_table_figure_callouts.md`
- `pilot_05AU_title_abstract_keywords.md`
- `pilot_05AU_reproducibility_statement.md`
- `pilot_05AU_next_revision_roadmap.md`

## Safety and claim boundary

05AU does not create new empirical evidence. It does not inspect raw CFPB data, raw prompts, raw responses, JSONL model-output files, or `.env` files. It makes no API/model calls.

## Next step

After 05AU is reviewed and committed, the next task should convert these artifacts into a full manuscript draft package while preserving all claim boundaries.
