# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

This repository contains the experimental code, validated outputs, research audits, and current manuscript for a research programme on **Evidence-State Reliability (ESR)** and **reliability cascades in multi-stage LLM decision systems**.

> A pipeline can produce cleaner, parser-valid outputs while becoming less reliable at the evidence-state and downstream decision layers.

The project studies reliability across the full chain connecting evidence, decision, audit, and escalation—not only whether the final output is syntactically valid.

## Current research status

| Item | Status |
| --- | --- |
| Simulation and deterministic pilots | Completed |
| Controlled real-LLM pilot | Completed |
| Scaled CFPB-backed GLM-5.2 experiment | Completed |
| Pilot 05 results, figures, tables, and validation | Completed |
| External literature and novelty analysis | Completed |
| Citation-integrated manuscript | Completed as an advanced draft |
| Full submission-readiness audit | Not yet completed |
| Journal-specific formatting and submission package | Not yet completed |

### Current manuscript

**[Read the latest citation-integrated manuscript](reports/pilot_05_verified_citation_integration/pilot_05AY_citation_integrated_manuscript.md)**

Supporting manuscript files:

- [Verified reference list](reports/pilot_05_verified_citation_integration/pilot_05AY_reference_list.md)
- [Citation usage register](reports/pilot_05_verified_citation_integration/pilot_05AY_citation_usage_register.csv)
- [Empirical preservation report](reports/pilot_05_verified_citation_integration/pilot_05AY_empirical_preservation_report.md)
- [05AY validation report](reports/pilot_05_verified_citation_integration/pilot_05AY_internal_validation_report.md)
- [05AY manifest](reports/pilot_05_verified_citation_integration/pilot_05AY_manifest.json)

The manuscript is an advanced research draft, not yet a journal-formatted or submission-certified paper.

---

## Research question

The central research question is:

> **How can Evidence-State Reliability be measured separately from parser validity in a multi-stage LLM decision pipeline?**

Many evaluations focus on whether a final output is correct, parseable, calibrated, faithful, or schema-compliant. Those dimensions are important, but a multi-stage system can also fail because the evidence reaching a downstream stage has already become incomplete, distorted, or unusable.

This project therefore evaluates the intermediate evidence state and the reliability consequences that appear across later stages.

---

## Core concepts

### Evidence-State Reliability

Evidence-State Reliability concerns whether the evidence supplied to a downstream stage remains sufficiently complete, grounded, and usable for that stage's assigned function.

It is distinct from:

- parser or schema validity;
- final-answer correctness;
- confidence calibration;
- answer faithfulness;
- general robustness;
- deployment safety.

### Reliability cascade

Within this project, a reliability cascade is a condition-linked change across decision, audit, and escalation stages after a controlled evidence-state intervention.

This is a deliberately narrow operational definition. The project does not claim to invent general cascade theory.

### Parser validity boundary

Parser validity indicates that an output satisfies a machine-readable structural contract. It does not establish:

- substantive correctness;
- evidence sufficiency;
- decision reliability;
- successful recovery;
- regulatory or deployment validity.

---

## Main contribution

The contribution is a **controlled combination and operationalisation** of:

1. explicit evidence-state interventions;
2. stage-aware decision, audit, and escalation measurement;
3. separate parser-validity and evidence-sensitive success metrics;
4. cascade-level analysis;
5. reproducible claim and artefact traceability.

The project does **not** claim that prior research ignored evidence sufficiency, component-level evaluation, structured-output validity, error propagation, abstention, or auditing.

The bounded novelty is the way these elements are combined and measured in the committed experimental design.

---

## Headline empirical finding

Across the scaled Pilot 05 experiment, degraded evidence conditions produced:

- consistently negative paired changes in stage success; and
- positive changes in parser validity.

In other words:

> **The pipeline became more parser-valid while becoming less reliable under evidence-sensitive stage criteria.**

This is the central result motivating Evidence-State Reliability as a distinct evaluation layer.

### Pilot 05 headline metrics

| Metric | Committed value |
| --- | ---: |
| Planned and ledgered calls | 720 |
| Sanitized execution rows | 713 |
| Ledger-only rows without a sanitized execution row | 7 |
| Ledger parser-valid outputs | 470 |
| Ledger parser-invalid outputs | 250 |
| Persisted parser-valid outputs | 470 |
| Persisted parser-invalid outputs | 243 |
| Stage-success delta range under degradation | -0.517241 to -0.406780 |
| Parser-validity delta range under degradation | +0.067797 to +0.368421 |
| Mean degraded audit detection rate | 1.0 |
| Mean degraded escalation recovery rate | 0.0 |
| All-sequence cascade-failure rate | 0.929167 |
| Maximum cumulative estimated model cost | USD 2.2731216 |

### Interpretation

The audit stage detected degradation in the evaluated conditions, but the escalation stage did not achieve successful recovery in this run.

That distinction matters: **detection is not recovery**.

The results are bounded to the committed Pilot 05 design and should not be generalized to all LLMs, all GLM-5.2 configurations, financial deployments, or real-world regulatory systems.

---

## Experimental programme

The project progresses from controlled simulation to deterministic stress testing and real-model execution.

| Pilot | Purpose | Scale | Evidence type | Status |
| --- | --- | ---: | --- | --- |
| Pilot 01 | Pipeline-condition reliability study | 50 tasks × 5 conditions × 3 runs = 750 rows | Simulation | Completed |
| Pilot 02 | Graded degradation-severity study | 50 tasks × 5 severity levels × 3 runs = 750 rows | Simulation | Completed |
| Pilot 03 | Multi-stage real-LLM chain study | 60 GLM-5.2 chains plus 15 Claude subset chains | Controlled real-model outputs | Completed |
| Pilot 04 | Deterministic second-domain and robustness study | 24 tasks × 3 conditions = 72 chains | Deterministic | Completed |
| Pilot 05 | Scaled CFPB-backed decision–audit–escalation study | 60 base cases × 4 conditions × 3 stages = 720 calls | Sanitized real-model experiment | Completed |

---

## Pilot 01 — Pipeline-condition reliability study

Pilot 01 evaluates five pipeline conditions:

- direct answer;
- evidence preserving;
- summary only;
- visible audit;
- blind audit.

Design:

- 50 synthetic tasks;
- 5 conditions;
- 3 repeated runs;
- 750 rows.

Observed full-design relationships included approximately:

| Relationship | Value |
| --- | ---: |
| ESR versus final failure | -0.251 |
| ESR versus undetected failure | -0.206 |
| Evidence-state degradation versus final failure | +0.273 |
| Evidence-state degradation versus audit false assurance | +0.232 |

These are simulation results under the implemented assumptions, not claims about deployed LLM systems.

---

## Pilot 02 — Graded degradation-severity study

Pilot 02 evaluates degradation levels from none through severe.

Design:

- 50 synthetic tasks;
- 5 degradation-severity levels;
- 3 repeated runs;
- 750 rows.

The committed analysis reported:

- 6 of 6 directional relationship tests matching the expected direction; and
- 6 of 6 severity means behaving monotonically.

This pilot establishes controlled sensitivity to degradation severity within the simulation design.

---

## Pilot 03 — Controlled multi-stage real-LLM chains

Pilot 03 extends the framework to real model outputs across original and degraded evidence conditions.

### GLM-5.2 subset

Design:

- 20 tasks;
- 3 evidence conditions;
- 60 chains.

Decision correctness:

| Evidence condition | Decision correctness |
| --- | ---: |
| Original evidence | 1.0 |
| Missing policy rule | 0.5 |
| Missing one required unit | 0.4 |

Escalation correctness:

| Evidence condition | Escalation correctness |
| --- | ---: |
| Original evidence | 1.0 |
| Missing policy rule | 1.0 |
| Missing one required unit | 0.4 |

### Claude comparison subset

Design:

- 5 tasks;
- 3 evidence conditions;
- 15 chains.

Decision correctness:

| Evidence condition | Decision correctness |
| --- | ---: |
| Original evidence | 1.0 |
| Missing policy rule | 0.4 |
| Missing one required unit | 0.4 |

The Claude subset provides limited cross-provider directional corroboration. It is not a full replication of the scaled Pilot 05 experiment and does not establish provider superiority.

---

## Pilot 04 — Deterministic second-domain robustness study

Pilot 04 tests the framework outside the earlier simulation and real-model chains.

Design:

- 24 tasks;
- 3 conditions;
- 72 chains.

The robustness package includes:

- 18 leave-one-task-out checks;
- 12 condition-order checks;
- 30 threshold checks;
- 7 high-signal checks.

Pilot 04 strengthens the cross-design argument while remaining a deterministic experiment rather than a model-general validation.

---

## Pilot 05 — Scaled CFPB-backed experiment

Pilot 05 is the main scaled empirical track.

Design:

- 60 sanitized CFPB-backed base cases;
- 4 evidence conditions;
- 3 pipeline stages: decision, audit, and escalation;
- 720 planned and ledgered GLM-5.2 calls.

### Evidence and data boundary

The evaluation uses sanitized evidence packets derived from public CFPB complaint material.

The committed research package does not expose:

- raw CFPB data;
- raw prompts;
- raw model responses;
- API keys or `.env` contents;
- JSONL response archives.

CFPB complaint material is used as a bounded experimental substrate. Complaints are not treated as a representative statistical sample or as verified findings of company misconduct.

### Main result

The strongest observed pattern is a divergence:

```text
evidence-sensitive stage success decreases
while
parser validity increases
```

This supports measuring Evidence-State Reliability separately from structural output validity.

### Failure structure

The committed analysis distinguishes:

- parser-valid but evidence-unsuccessful behaviour;
- detected-but-unrecovered degradation;
- missing sanitized-row accounting;
- decision-stage effects;
- audit detection;
- escalation recovery;
- sequence-level cascade failure.

The project does not collapse these behaviours into one final-answer score.

---

## Cross-pilot findings

Across the completed pilots, the evidence supports the following bounded conclusions:

1. Evidence degradation can be measured independently from final parser validity.
2. Reliability loss can appear at different stages rather than only in the final answer.
3. Audit detection and escalation recovery are different reliability functions.
4. A structurally valid output can remain unsupported by the available evidence state.
5. Reliability should be evaluated across the state transitions connecting pipeline stages.
6. The observed effects are experiment-specific and do not establish universal model or deployment behaviour.

---

## Literature and novelty boundary

The external literature package contains:

- 24 verified source records;
- 10 resolved citation-placeholder mappings;
- 22 references selected for manuscript integration;
- claim-to-source and related-work matrices;
- a novelty-boundary analysis.

Key adjacent research areas include:

- behavioural and multidimensional model evaluation;
- confidence calibration;
- RAG context and faithfulness evaluation;
- structured-output and constrained decoding;
- evidence insufficiency;
- selective prediction and learning to defer;
- algorithmic auditing;
- cascading failure and multi-agent error propagation;
- reproducibility guidance.

The literature-grounded verdict is:

> **Bounded combination-and-operationalisation differentiation is supported; global priority or first-ever novelty is not claimed.**

Key literature package:

- [Verified source register](reports/pilot_05_external_literature_grounding/pilot_05AX_verified_source_register.csv)
- [Novelty boundary analysis](reports/pilot_05_external_literature_grounding/pilot_05AX_novelty_boundary_analysis.md)
- [Related-work synthesis](reports/pilot_05_external_literature_grounding/pilot_05AX_related_work_synthesis.md)
- [Source verification report](reports/pilot_05_external_literature_grounding/pilot_05AX_source_verification_report.md)
- [05AX manifest](reports/pilot_05_external_literature_grounding/pilot_05AX_manifest.json)

---

## Manuscript history

The manuscript evolved through several committed refinement stages.

### Current version

- [05AY citation-integrated manuscript](reports/pilot_05_verified_citation_integration/pilot_05AY_citation_integrated_manuscript.md)

### Earlier formal refinement

- [05AW refined manuscript draft](reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_refined_full_manuscript_draft.md)
- [Formal definitions and notation](reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_formal_definitions_and_notation.md)
- [Threats-to-validity framework](reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_threats_to_validity_framework.md)
- [Claim-boundary refinement](reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_claim_boundary_refinement.md)

Use 05AY as the current manuscript. The 05AW version is retained for traceability.

---

## Claim boundaries

### Supported wording

A defensible central statement is:

> Within the committed Pilot 05 GLM-5.2 experiment, controlled evidence-state degradation produced measurable changes across decision, audit, and escalation stages. Parser validity increased while evidence-sensitive stage success deteriorated, supporting Evidence-State Reliability as distinct from parser validity.

### Not supported

This repository does not establish:

- broad GLM-5.2 unreliability;
- general LLM unreliability;
- provider superiority;
- real-world financial decision validity;
- regulatory compliance or regulatory validity;
- deployment safety;
- consumer-harm prevalence;
- company misconduct;
- parser validity as equivalent to correctness;
- universal causality;
- guaranteed journal acceptance.

---

## Limitations

The main current limitations are:

1. **Single-model scaled run:** Pilot 05 is bounded to one GLM-5.2 configuration.
2. **Limited cross-provider evidence:** Claude appears only in the smaller Pilot 03 subset.
3. **Single scaled pilot execution:** Pilot 05 is not yet a multi-run replication.
4. **Sanitized evidence:** the committed package does not expose raw CFPB records, prompts, or responses.
5. **Seven ledger-only rows:** 7 of 720 ledger entries do not have corresponding sanitized execution rows.
6. **No deployment validation:** the experiment does not test a live financial or regulatory system.
7. **Escalation design dependence:** zero observed recovery may reflect the specific experimental recovery design.
8. **Artefact-level reproducibility:** committed outputs can be validated, but raw-response replay is intentionally unavailable.
9. **Submission audit pending:** the current manuscript still requires a full consistency and journal-readiness review.

---

## Reproducibility and validation

The repository uses:

- deterministic generators where applicable;
- explicit source-file indexes;
- SHA-256 file checks;
- manifests;
- internal validation reports;
- claim-boundary audits;
- parser and execution accounting;
- sanitized committed outputs;
- clean Git checkpoints.

The citation-integrated manuscript preserves the committed Results section byte-for-byte relative to its source manuscript, and external literature is not used to validate the internal empirical numbers.

### Safety boundary

Validation and synthesis tasks are designed to avoid:

- unapproved model/API calls;
- `.env` access;
- raw prompt or response inspection;
- raw CFPB access;
- JSONL response writing;
- silent staging, committing, or pushing.

Real model execution requires separate explicit approval and is not triggered by manuscript or validation scripts.

---

## Repository navigation

```text
experiments/
    Experimental generators, analysis scripts, validators, and manuscript tooling

reports/
    Pilot-specific metrics, figures, tables, manifests, validation reports,
    literature grounding, and manuscript outputs

results/
    Earlier simulation tables and plots

data/
    Controlled project data and derived outputs subject to repository boundaries

README.md
    Public-facing research report and navigation page
```

Important current directories:

```text
reports/pilot_05_verified_citation_integration/
reports/pilot_05_external_literature_grounding/
reports/pilot_05_formal_definition_citation_refinement/
```

---

## Reading order

For a rapid review of the project:

1. Read this README.
2. Open the [current manuscript](reports/pilot_05_verified_citation_integration/pilot_05AY_citation_integrated_manuscript.md).
3. Review the [empirical preservation report](reports/pilot_05_verified_citation_integration/pilot_05AY_empirical_preservation_report.md).
4. Review the [novelty boundary analysis](reports/pilot_05_external_literature_grounding/pilot_05AX_novelty_boundary_analysis.md).
5. Inspect the relevant manifests and validation reports.
6. Use the committed experiment and analysis scripts for deeper reproducibility inspection.

---

## Current next step

The next research task is a full manuscript integrity and submission-readiness audit covering:

- numerical consistency;
- claim-to-evidence traceability;
- citation correctness;
- terminology and notation;
- manuscript structure;
- table and figure references;
- abstract–results–conclusion alignment;
- limitations;
- stale scaffold material;
- journal-target requirements.

No additional scaled experiment should be assumed necessary until that audit determines whether the single-model scope is an acceptance-critical gap.

---

## Evidence boundary for this README

This README synthesis is based on committed project evidence through:

```text
2c39f5d7239895d4165724181980bb847e5323f0
Add Pilot 05 verified citation integration
```

The README summarizes committed outputs; it does not create new empirical evidence.
