# Pilot 03 Validity Threats and Limitations

This document records the main validity threats for Pilot 03.

The purpose is to protect the research from overclaiming and to prepare the limitations section for a conservative paper draft.

## Required wording standard

Use Level 1 wording only.

Safe phrases:

- observed result under current Pilot 03 real LLM experimental conditions
- observed comparison subset under current Pilot 03 real LLM experimental conditions
- controlled Pilot 03 setup
- local empirical result
- early real LLM evidence

Unsafe phrases:

- proven
- general reliability
- real-world deployment proof
- universally valid
- Q1-ready evidence already complete
- no one has ever done this

## 1. Small task count

The current main real LLM checkpoint uses 20 Pilot 03 tasks for GLM-5.2.
The Claude comparison subset uses 5 Pilot 03 tasks.

This is enough for a controlled pilot, but not enough for broad statistical generalisation.

Paper handling:

- Report exact task counts.
- Avoid broad model-level claims.
- Treat Claude as a comparison subset, not as a full replication.

## 2. Synthetic task construction

Pilot 03 tasks are controlled synthetic decision tasks.

This improves experimental control because evidence units and missing-evidence conditions are known.
However, synthetic tasks do not fully represent real institutional, legal, medical, financial, or operational deployment environments.

Paper handling:

- Present the task design as a controlled benchmark-style pilot.
- Do not claim real-world deployment validity.
- Explain that synthetic construction is used to isolate evidence-state degradation.

## 3. Provider and model specificity

The current real LLM evidence uses GLM-5.2 through Z.ai and Claude Opus 4.8 through Anthropic.

Observed behaviour may change with:

- provider infrastructure
- model version
- API changes
- undocumented provider-side changes
- future model updates

Paper handling:

- Report provider and model names exactly.
- Avoid claims about all GLM models, all Claude models, or all LLMs.
- State that findings are local to the tested models and conditions.

## 4. Prompt specificity

The results depend on the Pilot 03 prompt templates for decision, audit, and escalation stages.

Different prompts may produce different correctness, audit, and escalation behaviour.

Paper handling:

- Treat prompts as part of the experimental condition.
- Include prompt versioning in reproducibility material.
- Do not claim prompt-independent behaviour.

## 5. Parser and schema dependence

Pilot 03 uses a parser and schema validation procedure.

High valid JSON and valid schema rates show structured-output compliance under this parser.
They do not mean the model reasoning is correct.

Paper handling:

- Separate structured validity from decision correctness.
- Report valid JSON, valid schema, decision correctness, and escalation correctness as different measurements.

## 6. Difference between structured validity and correctness

A chain can be structurally valid while still making an incorrect decision.

This distinction is central to the project.

Paper handling:

- Do not treat 100 percent schema validity as system reliability.
- Use schema validity as evidence that outputs were parseable and analysable.
- Use correctness metrics separately.

## 7. Claude subset smaller than GLM checkpoint

The GLM main evidence track currently has 20 tasks.
The Claude comparison subset currently has 5 tasks.

The shared five-task comparison is the safest direct comparison.
The full 20-task GLM result should be treated as a larger GLM checkpoint, not as an equal-scope comparison against Claude.

Paper handling:

- Use the shared five-task GLM-vs-Claude comparison for direct provider comparison.
- Use the GLM 20-task result as the main evidence track.
- Avoid general model ranking.

## 8. Limited domain coverage

Pilot 03 currently uses a narrow controlled task family.

Results may not transfer to other domains such as healthcare, law, finance, education, or public-sector decision-making without further testing.

Paper handling:

- Present domain coverage as limited.
- Frame future work around additional domains and larger task sets.

## 9. No real deployment validation

Pilot 03 does not test live deployed systems.

It does not include real users, real institutional workflows, real legal stakes, or real operational feedback loops.

Paper handling:

- Do not claim deployment proof.
- Present Pilot 03 as controlled empirical evidence for a measurement framework.

## 10. No human-subject validation

Pilot 03 does not include human decision-makers or human auditors.

It studies LLM-only decision, audit, and escalation chains.

Paper handling:

- Do not claim human-AI workflow validity.
- State that human-in-the-loop evaluation is future work.

## 11. API and reproducibility instability

Real LLM APIs can change over time.

Even with the same prompts and tasks, future reruns may differ due to model updates or provider-side changes.

Paper handling:

- Record dates, provider, model, prompt versions, and parser versions.
- Keep committed summaries and figure-generation scripts.
- Treat raw real LLM result folders as local ignored artifacts unless explicitly approved.

## 12. Cost and run-size constraints

Real LLM comparison runs have cost and quota implications.

Pilot 03 therefore uses guarded real-call commands and small comparison subsets before larger runs.

Paper handling:

- Report call counts.
- Explain why the Claude comparison was first run as a subset.

## 13. Statistical limitation

The current task counts are small.

Rates such as 0.4, 0.5, and 1.0 should be read as observed proportions in the current Pilot 03 setup, not as stable population estimates.

Paper handling:

- Avoid p-values or strong statistical claims unless a larger powered experiment is added later.
- Use descriptive statistics and exact counts.

## 14. Main mitigation already implemented

Current mitigations include:

- exact task IDs
- exact evidence conditions
- fixed chain stages
- parser validation
- committed CSV summaries
- committed markdown reports
- committed figure-generation script
- committed reproducibility command document
- ignored raw real LLM outputs
- explicit real-call confirmation requirement

## Bottom line

The current Pilot 03 results are credible as controlled early real LLM evidence.

They support a cautious claim that evidence-state degradation can change downstream chain correctness while structured-output validity remains high under current Pilot 03 conditions.

They do not support broad claims about general LLM reliability, provider ranking, or real-world deployment validity.
