# Pilot 03 Final Status Summary

This document records the final repository status after completing the current Pilot 03 code, evidence, comparison, figure, and documentation checkpoints.

## Latest repository state

Latest confirmed commit before this summary file:

f15f57d Update README real LLM roadmap status

Working tree status:

clean

Remote status:

origin/main up to date

## Completed Pilot 03 components

- Pilot 03 dry-run scaffold
- Pilot 03 real GLM-5.2 main evidence track
- Pilot 03 Anthropic/Claude comparison-runner support
- Guarded Anthropic no-call safety test
- Claude Opus 4.8 one-task smoke test
- Claude Opus 4.8 five-task comparison subset
- Claude subset summary report
- GLM-vs-Claude comparison report
- Paper-ready figure-generation script
- Paper-ready figures
- Reproducibility command document
- Results interpretation document
- Validity-threats and limitations document
- Paper outline document
- README updated to current real LLM checkpoint
- README real LLM roadmap status updated

## Main GLM-5.2 evidence track

Scope:

- 20 tasks
- 3 evidence conditions per task
- 60 complete decision-audit-escalation chains
- 180 real GLM-5.2 calls/responses
- 180/180 valid JSON
- 180/180 valid schema
- valid_chain_rate = 1.0

Observed condition-level result:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.5, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.5, escalation_correct_rate = 0.5

Safe wording:

observed result under current Pilot 03 real LLM experimental conditions

## Claude Opus 4.8 comparison subset

Scope:

- 5 tasks
- 3 evidence conditions per task
- 15 complete decision-audit-escalation chains
- 45 real Claude calls/responses
- 45/45 valid JSON
- 45/45 valid schema

Observed condition-level result:

- original_evidence: decision_correct_rate = 1.0, escalation_correct_rate = 1.0
- missing_policy_rule: decision_correct_rate = 0.4, escalation_correct_rate = 1.0
- missing_one_required_unit: decision_correct_rate = 0.4, escalation_correct_rate = 0.4

Safe wording:

observed comparison subset under current Pilot 03 real LLM experimental conditions

## Current safe central claim

Under current Pilot 03 real LLM experimental conditions, downstream decision-audit-escalation chains can remain structurally valid while their correctness changes when required evidence is removed.

This is an observed local result only.

## What the current evidence supports

The current evidence supports a controlled pilot-paper claim that evidence-state degradation can be measured in multi-stage LLM decision pipelines using task-level evidence conditions, chained decision-audit-escalation stages, parser validation, and condition-level correctness summaries.

## What the current evidence does not support

The current evidence does not support:

- general GLM-5.2 reliability
- general Claude reliability
- general provider ranking
- real-world deployment proof
- universal LLM pipeline reliability claims
- complete evidence already available
- claims that no one has ever studied related issues

## Committed reports and documents

- reports/pilot_03_real_glm_t0020_results.md
- reports/pilot_03_claude_comparison_subset/claude_subset_report.md
- reports/pilot_03_glm_vs_claude_comparison/glm_vs_claude_comparison_report.md
- reports/pilot_03_figures/figure_notes.md
- docs/pilot_03_reproducibility_commands.md
- docs/pilot_03_results_interpretation.md
- docs/pilot_03_validity_threats.md
- docs/pilot_03_paper_outline.md

## Paper-writing readiness

Ready:

- methods structure
- results structure
- figures
- safe interpretation
- limitations
- reproducibility notes
- repository evidence checkpoint

Still needed before full paper submission:

- related work search
- citation integration
- abstract draft
- introduction draft
- methods draft
- results draft
- discussion draft
- final reliability check

Important: related work and citation integration must use up-to-date web or literature search before final paper writing.

## Recommended next thread goal

The next thread should focus on paper writing only, starting from:

1. related work search and citation map
2. abstract
3. introduction
4. methods
5. results
6. discussion
7. limitations
8. conclusion

The paper must preserve Level 1 reliability wording throughout.
