# Pilot 05 — Paper Results Section Outline (Draft Bridge)

## 1. Setup recap
- 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states.
- Pipeline stages: evidence state -> decision -> audit -> escalation -> final governable output.

## 2. Headline result
Across 720 planned GLM-5.2 calls over CFPB-backed sanitized evidence states, degraded evidence conditions produced consistently negative paired deltas in stage success while parser validity increased. This divergence supports Evidence-State Reliability as a distinct evaluation layer from parser validity in multi-stage LLM decision pipelines.

## 3. Key sub-results
- Stage success delta range: [-0.517241, -0.40678] (all negative)
- Parser validity delta range: [0.067797, 0.368421] (all positive)
- Audit detection rate (degraded, parser-valid cases): 1.0
- Escalation recovery rate (degraded cases): 0.0
- Cascade failure rate across sequence groups: 0.929167

## 4. Boundary statement
This is a controlled scaled pilot, not a deployment validation, not a proof of real-world financial safety, and not a broad claim about GLM-5.2 or LLM reliability.

## 5. What remains before full paper writing
- Additional pilot replications beyond this single scaled run.
- Figures per `pilot_05AR_figure_specifications.csv`.
- Related-work framing tying divergence result to existing evaluation literature.
- Full limitations discussion expanded from `pilot_05AR_limitations_and_validity_threats.csv`.
