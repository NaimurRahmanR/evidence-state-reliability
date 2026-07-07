# Pilot 05 CFPB Evidence-State Condition Construction

Status: PASS

This no-call step constructs evidence-state condition variants from the committed sanitized CFPB evidence packets.

## Balanced subset

- Base packets selected: 60
- No labels selected: 30
- Yes labels selected: 30
- Selection method: deterministic seeded balanced sample
- Random seed: 20260707

## Evidence-state conditions

- clean
- compressed
- partial_dropout
- noisy_conflicting

Each base packet is represented under all four conditions.

## Counts

- Evidence-state rows written: 240
- Evidence-state labels written separately: 240
- Conditions per packet: 4

## Safety boundary

No raw CFPB export is read by this script. The construction uses only the committed sanitized evidence packets and separate labels.

Evidence-state text does not include raw complaint narratives, company names, complaint IDs, ZIP codes, company-response fields, raw prompts, raw responses, API outputs, model outputs, or target labels.

## Claim boundary

This output is a no-call evidence-construction layer for later controlled evidence-state reliability experiments. It does not claim model reliability, provider ranking, financial safety, legal safety, consumer harm prevalence, real-world deployment validity, or regulated lending validity.
