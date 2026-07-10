# Pilot 05AW Claim-Boundary Refinement

## Primary bounded claim

> Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that
> controlled evidence-state degradation produces measurable reliability-layer
> changes across decision, audit, and escalation stages. In this run, parser
> validity improved under degraded evidence while stage/evidence success
> deteriorated, supporting Evidence-State Reliability as distinct from parser
> validity.

## Permitted supporting claims

1. Pilot 05 evaluates a multi-stage decision, audit, and escalation pipeline under
   controlled evidence-state conditions.
2. Parser validity and stage/evidence success are analytically distinct metrics.
3. In the committed run, degraded evidence was associated with improved parser
   validity and deteriorated stage/evidence success.
4. The observed divergence motivates stage-aware and evidence-aware reliability
   evaluation.
5. Sanitized artefacts, manifests, source indexes, and claim-traceability outputs
   support bounded reproducibility auditing.

## Claims requiring explicit qualification

| Topic | Required qualifier |
|---|---|
| Causality | “Under the controlled Pilot 05 intervention” rather than unrestricted deployed-system causality |
| Generalisation | “In this GLM-5.2 run” rather than “LLMs generally” |
| Domain | “CFPB-backed experimental substrate” rather than real-world financial decision validity |
| Parser performance | “Structural validity” rather than correctness |
| Audit performance | “Experimental audit-stage behaviour” rather than regulatory assurance |
| Escalation | “Scored escalation behaviour” rather than optimal human oversight |
| Safety | “Reliability-layer evidence” rather than deployment safety certification |

## Prohibited claim expansions

The manuscript must not claim:

- broad GLM reliability;
- general LLM reliability;
- model or provider superiority;
- real-world financial validity;
- regulatory validity or compliance;
- deployment safety;
- consumer-harm prevalence;
- company misconduct;
- that parser validity equals answer correctness;
- that the evidence proves a universal causal mechanism;
- that journal acceptance or manuscript completion is guaranteed.

## Language substitutions

| Avoid | Use |
|---|---|
| “proves” | “supports within the evaluated design” |
| “shows LLMs are” | “shows that the evaluated pipeline was” |
| “financial decisions” | “CFPB-backed experimental cases” |
| “safe/unsafe” | “more or less reliable under the defined metric” |
| “audit succeeded” | “the audit-stage criterion was satisfied” |
| “correct output” when only parsed | “parser-valid output” |
| “caused” without design support | “was associated with” or “followed the controlled intervention” |

## Submission audit rule

Every empirical sentence in the final manuscript should be traceable to a committed
table, figure, manifest, or metric output. Every literature-dependent sentence
should carry an approved citation or an unresolved placeholder. No placeholder may
be converted into a named citation without source verification.
