# Pilot 03 Next-Stage Status After Interruption-Safe Runner

Latest confirmed commit: 0ac1f6d Handle Pilot 03 real runner interruptions safely

At this checkpoint, main and origin/main were aligned and the working tree was clean.

Pilot 03 current strongest observed checkpoint: 3 tasks x 3 evidence conditions, 9 complete chains, 27 real GLM-5.2 calls, 27/27 valid JSON, 27/27 valid schema, decision_correct_rate = 0.555556, escalation_correct_rate = 0.777778.

Safe interpretation: these are observed results under current Pilot 03 real LLM experimental conditions. They should not be generalised beyond the current setup, model, prompts, parser, tasks, evidence conditions, and aggregation method.

Runner safety improvement: pilot_03_zai_small_chain_run_v4 now handles KeyboardInterrupt safely. Interrupted runs write run_status = interrupted_partial.

Reliability rule: interrupted or partial runs must not be reported as completed Pilot 03 results. Partial stage call records are not completed chain results.

Recommended next empirical step: run only P03-T0004, one condition at a time, and only after explicit confirmation to make real API calls.

Recommended order: P03-T0004 original_evidence, then P03-T0004 missing_policy_rule, then P03-T0004 missing_one_required_unit.

Reliability Level 1 limitation: Pilot 03 currently supports early controlled observations only. It does not prove general GLM-5.2 reliability or real-world LLM decision-system reliability.
