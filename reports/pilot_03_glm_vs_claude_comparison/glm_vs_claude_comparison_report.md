# Pilot 03 GLM-vs-Claude comparison report

Generated at UTC: 2026-07-02T01:18:27+00:00

## Reliability framing

- GLM wording: observed result under current Pilot 03 real LLM experimental conditions
- Claude wording: observed comparison subset under current Pilot 03 real LLM experimental conditions
- This report is descriptive only.
- It must not be read as a general model ranking.
- The shared-task comparison is the safer comparison because both providers are evaluated on the same five task IDs.
- The 20-task GLM result is included only as a larger GLM checkpoint reference.

## Shared 5-task condition comparison

Shared task IDs: `['P03-T0001', 'P03-T0002', 'P03-T0003', 'P03-T0004', 'P03-T0005']`

| provider | model | condition | n_chains | decision rate | escalation rate | audit passed true rate | valid chain rate |
|---|---|---|---:|---:|---:|---:|---:|
| zai | glm-5.2 | missing_one_required_unit | 5 | 0.4 | 0.4 | 0.4 | 1.0 |
| zai | glm-5.2 | missing_policy_rule | 5 | 0.4 | 1.0 | 0.2 | 1.0 |
| zai | glm-5.2 | original_evidence | 5 | 1.0 | 1.0 | 1.0 | 1.0 |
| anthropic | claude-opus-4-8 | missing_one_required_unit | 5 | 0.4 | 0.4 | 1.0 | 1.0 |
| anthropic | claude-opus-4-8 | missing_policy_rule | 5 | 0.4 | 1.0 | 0.0 | 1.0 |
| anthropic | claude-opus-4-8 | original_evidence | 5 | 1.0 | 1.0 | 1.0 | 1.0 |

## Scope reference condition comparison

This table places the full 20-task GLM checkpoint beside the 5-task Claude comparison subset. The sample sizes are different, so this section should be used as context only.

| scope | provider | model | condition | n_chains | decision rate | escalation rate | valid chain rate |
|---|---|---|---|---:|---:|---:|---:|
| GLM full 20-task checkpoint | zai | glm-5.2 | original_evidence | 20 | 1.0 | 1.0 | 1.0 |
| GLM full 20-task checkpoint | zai | glm-5.2 | missing_policy_rule | 20 | 0.5 | 1.0 | 1.0 |
| GLM full 20-task checkpoint | zai | glm-5.2 | missing_one_required_unit | 20 | 0.5 | 0.5 | 1.0 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_one_required_unit | 5 | 0.4 | 0.4 | 1.0 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | missing_policy_rule | 5 | 0.4 | 1.0 | 1.0 |
| Claude 5-task comparison subset | anthropic | claude-opus-4-8 | original_evidence | 5 | 1.0 | 1.0 | 1.0 |

## Conservative interpretation

Under the shared five-task Pilot 03 comparison, both providers show preserved structured-output validity while decision and escalation correctness vary by evidence condition. This is an observed comparison subset under current Pilot 03 real LLM experimental conditions only.

The result supports continued analysis of evidence-state degradation as a pipeline-level phenomenon, but it does not establish general reliability properties of GLM-5.2, Claude Opus 4.8, Z.ai, Anthropic, or deployed systems.

For paper writing, the safest claim is that Pilot 03 demonstrates a reproducible method for comparing how downstream decision-audit-escalation chains behave when required evidence is removed under controlled tasks and prompts.
