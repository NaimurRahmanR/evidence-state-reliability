# Pilot 03 Claude comparison subset summary

Generated at UTC: 2026-07-02T01:13:53+00:00

## Scope

- Safe wording: observed comparison subset under current Pilot 03 real LLM experimental conditions
- Source run directory: `results\pilot_03_real_llm_analysis\pilot_03_anthropic_small_chain_selected5_20260702T010932Z`
- Provider counts: `{'anthropic': 15}`
- Model counts: `{'claude-opus-4-8': 15}`
- Selected task IDs: `['P03-T0001', 'P03-T0002', 'P03-T0003', 'P03-T0004', 'P03-T0005']`
- Conditions: `['original_evidence', 'missing_policy_rule', 'missing_one_required_unit']`

## Validation

- Completed chains: 15
- Saved call records: 45
- Expected call count: 45
- Parser summary: `{'error_counts': {}, 'n_invalid_json': 0, 'n_invalid_schema': 0, 'n_parsed_responses': 45, 'parser_version': 'pilot_03_parser_v2', 'stage_counts': {'audit': 15, 'decision': 15, 'escalation': 15}, 'valid_json_counts': {'True': 45}, 'valid_schema_counts': {'True': 45}}`
- Valid schema chains: 15/15 = 1.0

## Aggregate observed results

- Decision correct: 9/15 = 0.6
- Escalation correct: 12/15 = 0.8

## Condition-level observed results

| condition | n | decision correct | decision rate | escalation correct | escalation rate | audit passed true | audit passed true rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| missing_one_required_unit | 5 | 2 | 0.4 | 2 | 0.4 | 5 | 1.0 |
| missing_policy_rule | 5 | 2 | 0.4 | 5 | 1.0 | 0 | 0.0 |
| original_evidence | 5 | 5 | 1.0 | 5 | 1.0 | 5 | 1.0 |

## Conservative interpretation

This is a small Claude comparison subset under the current Pilot 03 real LLM experimental setup. It should not be interpreted as a general claim about Claude, Anthropic models, or real-world deployment reliability. The subset is useful because it applies the same Pilot 03 tasks, evidence conditions, prompts, parser, and decision-audit-escalation chain structure used in the GLM track.

The observed subset pattern is consistent with the evidence-state reliability thesis: when required evidence is removed, downstream decision and escalation behaviour can change even though the model remains capable of producing valid structured outputs. This wording is local to the current Pilot 03 setup only.
