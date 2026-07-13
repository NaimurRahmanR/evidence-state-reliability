# Pilot 05AX Related-Work Synthesis

This document is a verified literature-grounding artefact. It is not an edit of the committed manuscript.

## Evaluation beyond final-output validity

Model evaluation has long been recognized as multidimensional. Behavioral testing frameworks show that held-out accuracy can conceal capability-specific weaknesses, while calibration research separates predictive correctness from confidence quality. RAG evaluation further distinguishes context relevance, faithful use of retrieved material, and answer relevance. Together, these traditions support the general premise that one observable success signal cannot stand in for every reliability layer [SRC-CHECKLIST-2020; SRC-CALIBRATION-2017; SRC-RAGAS-2024; SRC-ARES-2024].

Evidence-State Reliability should be positioned as a narrower operational addition to this landscape. It concerns whether the evidence made available to downstream stages remains sufficiently complete and usable for their assigned functions. It should not be described as replacing accuracy, calibration, faithfulness, or robustness.

## Structured output and parser validity

Structured-generation research treats formal conformance as a measurable output property. Grammar-constrained decoding can guarantee or improve adherence to required structures, while recent structured-output benchmarks explicitly distinguish schema validity from value-level or executable correctness [SRC-GCD-2023; SRC-CONSTRAINT-TAX-2026; SRC-STRUCTURED-BENCH-2026].

This prior work means the paper cannot claim that structural and substantive validity have never been separated. The project-specific distinction is the source of the divergence: Pilot 05 manipulates the evidence state supplied to a multi-stage decision pipeline and measures downstream decision, audit, and escalation behavior, rather than manipulating output decoding constraints.

## Evidence sufficiency and intermediate support

Adjacent fact-checking and RAG research directly studies insufficient evidence, evidence sufficiency, and abstention [SRC-INSUFFICIENT-EVIDENCE-2022; SRC-SURE-RAG-2026]. Emerging work also frames evidence sufficiency in risk decision systems under delayed ground truth [SRC-EVIDENCE-DELAY-2026]. These sources are close conceptual antecedents and must be acknowledged.

The bounded distinction is that Pilot 05 freezes explicit evidence conditions and observes stage-specific reliability changes across decision, audit, and escalation, including parser validity and recovery behavior. Evidence-State Reliability should therefore be presented as an operational pipeline layer, not as the first recognition that evidence can be insufficient.

## Multi-stage pipelines and propagated failure

Agent benchmarks and RAG frameworks motivate component-aware evaluation in interactive or multi-component systems [SRC-AGENTBENCH-2024; SRC-RAGAS-2024; SRC-ARES-2024]. Cascading failure is also an established systems concept [SRC-CASCADE-NETWORKS-2002]. Recent preprints explicitly examine error and hallucination cascades in LLM-based multi-agent collaboration [SRC-SPARK-FIRE-2026; SRC-HALLUCINATION-CASCADE-2026].

The present work uses “reliability cascade” more narrowly. It refers to condition-linked changes across decision, audit, and escalation under a controlled evidence-state intervention. It does not claim to invent cascade theory, and it should not infer real-world causal propagation from a controlled run.

## Audit, oversight, and false assurance

End-to-end algorithmic auditing emphasizes documentation, traceability, institutional processes, and lifecycle accountability [SRC-AUDIT-2020]. Financial-sector reports likewise identify testing, interpretability, auditability, and interconnectedness as relevant AI risk considerations [SRC-FSB-AI-2017; SRC-FSB-AI-2026].

Pilot 05 uses a narrower computational audit stage. The manuscript should state that a structurally successful audit output may still be constrained by the evidence supplied to it, while avoiding any equivalence between this stage and a full organizational, regulatory, or assurance audit.

## Uncertainty, abstention, and escalation

Selective prediction and learning-to-defer treat rejection or expert deferral as distinct decision functions [SRC-SELECTIVENET-2019; SRC-DEFER-2020]. These traditions support evaluating escalation separately from the base decision.

Pilot 05 adds a specific recovery question: whether escalation succeeds after controlled evidence degradation. The results do not establish an optimal abstention or escalation policy.

## Financial context and CFPB provenance

Financial-sector AI motivates high-assurance evaluation, but institutional context does not validate deployment [SRC-FSB-AI-2017; SRC-FSB-AI-2026]. The CFPB describes its Consumer Complaint Database as a public resource while warning that complaints are not a statistical sample, narratives are consumer accounts, and analysis requires contextual information [SRC-CFPB-DATABASE].

The manuscript should use the CFPB material solely as a bounded provenance and evaluation-substrate statement. It must not infer prevalence, verified truth of narratives, company misconduct, regulatory compliance, or consumer harm.

## Validity and reproducibility

The threats-to-validity section can use construct, internal, external, and conclusion-validity categories from empirical software-engineering methodology [SRC-WOHLIN-2012]. Reproducibility guidance supports transparent artefacts, reporting, and traceability [SRC-REPRO-2021].

The project’s manifests, source indexes, deterministic validators, and sanitized outputs strengthen artefact-level reproducibility. Because raw prompts and responses are intentionally unavailable, the paper must not claim full replay reproducibility.
