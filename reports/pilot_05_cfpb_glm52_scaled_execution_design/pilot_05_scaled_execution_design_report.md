# TASK 05AM — Scaled Pilot 05 real-execution design and approval package

## Status

PASS is only valid if the terminal summary also reports PASS. This report is a design/approval artifact only. It does not add new model evidence.

## Verified checkpoint

- Branch: `main`
- HEAD: `a1d18a8 Add Pilot 05 GLM-5.2 results interpretation`
- `origin/main`: aligned with HEAD
- Working tree clean before generation: `True`
- Nothing staged before generation: `True`
- Required 05AK/05AL committed outputs: verified

## Existing empirical status

Pilot 05 already has a real GLM-5.2 micro-pilot, but it is still too small for the target paper-level claim. 05AM therefore prepares the next real execution rather than treating no-call work as an achievement by itself.

Detected sanitized evidence-state base-case capacity:

- Selected source: `reports/pilot_05_cfpb_evidence_state_conditions/pilot_05_cfpb_evidence_state_conditions.csv`
- Detected available sanitized base cases: `60`
- Sufficient for Option A / 720 calls: `True`
- Sufficient for 100-case options: `False`

## Related-work gap translated into design

- **Holistic LLM evaluation beyond accuracy**: Model-level benchmark transparency across multiple scenarios and metrics including accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency. Gap for this project: Does not isolate degraded intermediate evidence states inside a staged decision pipeline or measure decision-audit-escalation cascade propagation on paired cases.
- **RAG component evaluation and evidence/context quality**: Reference-free RAG evaluation across retrieval context quality, answer relevancy, and faithfulness dimensions. Gap for this project: RAG metrics test context-answer quality but do not directly model how controlled evidence degradation propagates through decision, audit, and escalation stages.
- **Automated RAG evaluation with domain shift**: Automated assessment of context relevance, answer faithfulness, and answer relevance using lightweight judges and prediction-powered inference. Gap for this project: Does not provide a reliability-cascade design for same-case evidence degradation across downstream decision/audit/escalation layers.
- **RAG faithfulness and hallucination benchmarking**: LLM faithfulness measurement for RAG/summarization settings where models can introduce unsupported information or contradictions even when given context. Gap for this project: Faithfulness leaderboards do not show whether degraded evidence states create stage-specific audit false assurance or escalation recovery/loss in decision pipelines.
- **LLM agents and multi-turn decision-making**: Agent evaluation across interactive environments, multi-turn reasoning, decision-making, and instruction-following failure reasons. Gap for this project: Primarily task/agent capability evaluation; not a same-case evidence-state degradation experiment with explicit audit/escalation reliability layers.
- **Agent cascading failures and recovery/debugging**: Systematic taxonomy of agent failures, annotated failure trajectories, and debugging/recovery in multi-step agent rollouts where root-cause errors can cascade. Gap for this project: Targets agent module failures and recovery, not controlled real-data-backed evidence-state degradation before downstream decision-support reasoning.
- **Fault injection in multi-agent LLM systems**: Fault-injection reliability evaluation for multi-agent LLM systems, including silent fault propagation and defensive responses. Gap for this project: Fault injection is close, but the 05AM target is not generic agent fault injection; it is evidence-state degradation in a public-data-backed staged decision pipeline.
- **AI risk management and generative AI governance**: Cross-sector risk-management guidance for trustworthy AI and generative AI validation, governance, monitoring, and risk controls. Gap for this project: Governance guidance does not itself provide a concrete empirical metric package for evidence-state cascade measurement in LLM decision systems.

Practical gap for this project: existing work strongly covers broad LLM benchmarking, RAG faithfulness/context evaluation, and agent failure analysis. The narrower head-turner is to evaluate whether degraded intermediate evidence states create measurable downstream reliability cascades across decision, audit, and escalation, while separating parser validity, final-output validity, evidence-state reliability, audit reliability, escalation reliability, and cascade reliability.

## Scaled run options

- Option A: 720 calls — RECOMMENDED NEXT RUN
- Option B: 1200 calls — requires more sanitized base cases
- Option C: 1440 calls — defer until Option A passes; use as replication
- Option D: 2400 calls — requires more sanitized base cases

## Recommendation

Recommended next run: **Option A — 60 cases × 4 conditions × 3 stages × 1 model(s) = 720 calls**.

Reason: Big enough to move beyond the 36-call micro-pilot, still cost-controlled, supports paired clean-vs-degraded comparisons, and avoids premature cross-model spending.

This recommendation is conservative: it moves beyond the 36-call micro-pilot without jumping immediately into cross-model spending. Cross-model replication should follow only if Option A produces a clean, interpretable, claim-bounded signal.

## Cost status

Exact GLM-5.2 pricing is marked as `requires_user_confirmation`. 05AM does not call provider billing APIs and does not read `.env`. Therefore, 05AN must not run until the user explicitly approves a hard GBP cost cap.

Cost formula:

`total_cost = call_count × ((avg_input_tokens_per_call × input_price_per_token) + (avg_output_tokens_per_call × output_price_per_token))`

## Safety contract

05AM wrote only design/approval artifacts. 05AN must preserve the same claim boundary and must store sanitized outputs only.

Forbidden for 05AN unless separately approved: raw prompt storage, raw response storage, JSONL storage, raw CFPB access, broad model/provider claims, financial/legal/deployment validity claims, staging/commit/push.

## Approval gate

Use `pilot_05_scaled_execution_approval_prompt.md` as the next approval text. It requires explicit model, call count, cost cap, storage contract, and abort-rule approval before any real model calls.
