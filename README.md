# Evidence-State Reliability in Multi-Stage LLM Pipelines

This repository contains the first simulation code for a doctoral-level research project on **Evidence-State Reliability in Multi-Stage LLM Pipelines**.

The core idea is:

> A downstream LLM can be strong and still fail if the evidence reaching it has already been degraded by an upstream component.

This project is currently simulation-first. It does not yet claim real LLM behaviour. The goal of the first pilot is to test whether the experimental design can measure evidence-state degradation, final failure, undetected failure, audit false assurance, escalation contamination, and cost per governable output.

---

## Research concept

In a multi-stage LLM pipeline, evidence may pass through several stages:

```text
original evidence
→ retrieved evidence
→ compressed/summarised evidence
→ decision evidence
→ audit evidence
→ escalation evidence
→ final output