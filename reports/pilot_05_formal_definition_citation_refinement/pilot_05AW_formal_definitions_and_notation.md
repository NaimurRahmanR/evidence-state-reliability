# Pilot 05AW Formal Definitions and Notation

## Scope

These definitions formalise concepts already present in the committed 05AV manuscript.
They are analytical and editorial refinements only. They do not create new empirical
evidence, recompute results, or widen the manuscript's claim boundary.

## Pipeline and stage notation

Let a multi-stage AI decision pipeline be represented as

\[
\mathcal{P} = (S_1, S_2, \ldots, S_K),
\]

where each stage \(S_k\) receives an evidence state, produces a stage output, and may
pass a transformed evidence state to the next stage. Pilot 05 uses three operational
stage families: decision, audit, and escalation.

For case \(i\), evidence condition \(c\), and stage \(k\):

- \(E_{i,c,k}\) denotes the evidence state available to stage \(k\).
- \(Y_{i,c,k}\) denotes the stage output.
- \(V_{i,c,k} \in \{0,1\}\) denotes parser validity.
- \(R_{i,c,k} \in \{0,1\}\) denotes stage/evidence success under the committed
  Pilot 05 scoring contract.
- \(U_{i,c,k}\) denotes any recorded uncertainty or escalation-related indicator
  already defined by the committed analysis outputs.

## Definition 1: Evidence state

An **evidence state** is the bounded set of task-relevant information made available
to a pipeline stage after any controlled preservation, omission, degradation, or
transformation applied by the experimental condition.

This definition concerns the informational state supplied to a stage. It does not
assert that the evidence is legally sufficient, factually complete outside the
experiment, or valid for deployment.

## Definition 2: Parser validity

**Parser validity** is the indicator

\[
V_{i,c,k} =
\begin{cases}
1, & \text{if the stage output satisfies the expected machine-readable contract},\\
0, & \text{otherwise.}
\end{cases}
\]

Parser validity evaluates structural acceptability only. It is not equivalent to
answer correctness, evidence fidelity, decision validity, regulatory validity, or
deployment safety.

## Definition 3: Stage/evidence success

**Stage/evidence success** is the indicator \(R_{i,c,k}\) assigned under the
precommitted Pilot 05 evaluation contract for whether the stage output satisfies the
relevant evidence-sensitive success criterion.

The interpretation of \(R_{i,c,k}\) remains tied to the committed Pilot 05 task,
condition, and scoring definitions.

## Definition 4: Evidence-State Reliability

For a fixed condition \(c\) and stage \(k\), define empirical Evidence-State
Reliability as

\[
\widehat{\mathrm{ESR}}_{c,k}
=
\frac{1}{N_c}
\sum_{i=1}^{N_c} R_{i,c,k},
\]

where \(N_c\) is the number of evaluated cases under condition \(c\).

A pipeline-level aggregate may be written as

\[
\widehat{\mathrm{ESR}}_{c}
=
\sum_{k=1}^{K} w_k\widehat{\mathrm{ESR}}_{c,k},
\qquad
w_k \geq 0,
\quad
\sum_{k=1}^{K} w_k = 1.
\]

Pilot 05 should report only the aggregation actually supported by its committed
outputs. The notation does not authorise retrospective metric invention.

## Definition 5: Parser-validity rate

For condition \(c\) and stage \(k\),

\[
\widehat{\mathrm{PV}}_{c,k}
=
\frac{1}{N_c}
\sum_{i=1}^{N_c} V_{i,c,k}.
\]

This is a format-layer metric and must remain analytically separate from
\(\widehat{\mathrm{ESR}}_{c,k}\).

## Definition 6: Reliability-layer divergence

For a degraded condition \(d\) relative to reference condition \(r\), define

\[
\Delta \mathrm{PV}_{d,r,k}
=
\widehat{\mathrm{PV}}_{d,k}
-
\widehat{\mathrm{PV}}_{r,k},
\]

and

\[
\Delta \mathrm{ESR}_{d,r,k}
=
\widehat{\mathrm{ESR}}_{d,k}
-
\widehat{\mathrm{ESR}}_{r,k}.
\]

A **reliability-layer divergence** occurs when the two deltas move in substantively
different directions. The central Pilot 05 pattern is the bounded case in which
parser validity improves under degraded evidence while stage/evidence success
deteriorates.

## Definition 7: Reliability cascade

A **reliability cascade** is a sequence in which a change to an upstream evidence
state is associated with measurable downstream changes across one or more pipeline
stages.

This definition is structural and experimental. It does not by itself establish
causal effects in deployed systems, consumer harm, or regulatory non-compliance.

## Definition 8: False assurance at the format layer

**Format-layer false assurance** is the risk that structurally valid outputs are
mistaken for evidence-reliable outputs. In notation, the relevant case is

\[
V_{i,c,k}=1 \quad \text{while} \quad R_{i,c,k}=0.
\]

This term describes an evaluation mismatch. It is not a claim that every
parser-valid but evidence-unsuccessful output would mislead a real operator.

## Definition 9: Controlled evidence degradation

A **controlled evidence degradation condition** is an experimental intervention that
removes, suppresses, or alters a predefined component of the evidence state while
holding the remaining task protocol fixed as specified by the committed design.

## Claim-preserving interpretation rule

All notation must be interpreted within the following boundary:

> Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that
> controlled evidence-state degradation produces measurable reliability-layer
> changes across decision, audit, and escalation stages. In this run, parser
> validity improved under degraded evidence while stage/evidence success
> deteriorated, supporting Evidence-State Reliability as distinct from parser
> validity.

The formalisation does not support claims about broad GLM reliability, general LLM
reliability, provider superiority, real-world financial validity, regulatory
validity, deployment safety, consumer harm prevalence, or company misconduct.
