# Pilot 05AV Internal Review Checklist

## Core claim checks

- [ ] Does the manuscript clearly define Evidence-State Reliability?
- [ ] Does it separate Evidence-State Reliability from parser validity?
- [ ] Does it avoid saying parser validity equals answer correctness?
- [ ] Does it present the parser-validity/evidence-state divergence as the central result?
- [ ] Does it keep all empirical claims bounded to Pilot 05?

## Methods checks

- [ ] Does the methods section explain the decision, audit, and escalation stages?
- [ ] Does it state that the experiment uses sanitized CFPB-backed evidence packets?
- [ ] Does it state that 05AV uses committed 05AU outputs only?
- [ ] Does it avoid raw CFPB, raw prompt, raw response, JSONL, and .env claims?

## Results checks

- [ ] Does the results section use the 05AS table and figure sequence?
- [ ] Does it distinguish audit detection from escalation recovery?
- [ ] Does it frame cascade failure as a pipeline-level reliability signal?
- [ ] Does it avoid provider superiority or broad model-generalization claims?

## Reproducibility checks

- [ ] Does the paper cite the committed checkpoint chain?
- [ ] Does it include 05AT repo validation as a reproducibility safeguard?
- [ ] Does it avoid claiming that audit validity equals real-world deployment validity?

## Submission-readiness checks

- [ ] Related work added with citations.
- [ ] Formal framing tightened.
- [ ] Figures placed in manuscript order.
- [ ] Tables placed in manuscript order.
- [ ] Limitations expanded.
- [ ] Abstract shortened for target venue.
