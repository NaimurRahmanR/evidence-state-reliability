# Pilot 05AW Threats-to-Validity Framework

## Framing rule

The threats below qualify interpretation of the committed Pilot 05 findings. They do
not negate the observed run, and they do not introduce new empirical evidence.

## Construct validity

1. **Evidence-State Reliability operationalisation.** The empirical success
   indicators are tied to the committed task and scoring contract. They may not
   capture every relevant dimension of evidence reliability.
2. **Parser validity scope.** Parser validity measures structural conformance only.
   It must not be interpreted as correctness, faithfulness, or decision quality.
3. **Evidence degradation representation.** The selected controlled degradations are
   experimental proxies. They do not exhaust real-world evidence loss, ambiguity,
   contradiction, or manipulation.
4. **Stage-label interpretation.** “Decision,” “audit,” and “escalation” describe the
   experimental pipeline functions and should not be equated automatically with
   regulated institutional processes.

## Internal validity

1. **Prompt and protocol dependence.** Results may depend on the committed pipeline
   instructions, ordering, parser, and scoring implementation.
2. **Deterministic analysis dependence.** Derived metrics depend on the correctness
   of the committed parser and analysis code, although the repository includes
   operation-aware validation and traceability artefacts.
3. **Unobserved model-state variation.** Provider-side or runtime factors may affect
   outputs and are not fully identifiable from sanitized artefacts.
4. **No raw-response reinspection.** The safety boundary prevents independent
   qualitative reinspection of raw model responses in this task.
5. **Single-run interpretation.** The reported scaled run should not be treated as
   proof of invariance across repeated executions.

## External validity

1. **Single primary model/provider configuration.** The core result is bounded to
   the evaluated GLM-5.2 configuration.
2. **Domain boundary.** CFPB-backed complaint material provides a real-data substrate
   but does not establish validity for lending, underwriting, adjudication, or other
   financial decisions.
3. **Task boundary.** The selected cases and evidence conditions may not represent
   other document types, jurisdictions, languages, or organisational settings.
4. **Deployment boundary.** The experiment does not evaluate live users, production
   workflows, institutional controls, or downstream consumer outcomes.
5. **Temporal boundary.** Findings may not transfer unchanged across future model,
   provider, policy, or data versions.

## Conclusion validity

1. **Descriptive emphasis.** The central result is a measured contrast in this run,
   not a universal law.
2. **Multiple metrics and stages.** Interpretation should preserve the distinction
   among parser validity, stage/evidence success, audit behaviour, and escalation
   behaviour.
3. **Effect-size reporting.** Final submission should report denominators, absolute
   rates, and condition deltas rather than relying only on directional language.
4. **Uncertainty reporting.** Any inferential claims must match the committed
   robustness and sample structure; unsupported significance language must not be
   introduced.
5. **No prevalence inference.** Experimental failure rates must not be translated
   into prevalence estimates for consumer harm, company misconduct, or deployed AI
   failure.

## Reproducibility limitations

1. Sanitized outputs support artefact-level verification but not raw
   prompt/response replay.
2. No API keys, environment secrets, raw CFPB data, or JSONL traces are committed.
3. Provider availability and model-version continuity may limit exact future replay.
4. Citation placeholders remain unresolved until an explicitly approved literature
   task is completed.

**Future citation placeholder:** [CIT-VALIDITY-01]
