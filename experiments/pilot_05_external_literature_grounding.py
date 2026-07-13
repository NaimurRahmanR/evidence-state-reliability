from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Iterable

TASK_ID = "05AX"
SEARCH_DATE = "2026-07-13"

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "pilot_05_external_literature_grounding"
INPUT_REGISTER = (
    ROOT
    / "reports"
    / "pilot_05_formal_definition_citation_refinement"
    / "pilot_05AW_citation_placeholder_register.csv"
)

EXPECTED_PLACEHOLDERS = [
    "CIT-ESR-01",
    "CIT-CASCADE-01",
    "CIT-PIPELINE-01",
    "CIT-PARSER-01",
    "CIT-AUDIT-01",
    "CIT-UNCERTAINTY-01",
    "CIT-FINAI-01",
    "CIT-CFPB-01",
    "CIT-VALIDITY-01",
    "CIT-REPRO-01",
]

OUTPUT_FILES = {
    "source_register": OUT_DIR / "pilot_05AX_verified_source_register.csv",
    "resolution_map": OUT_DIR / "pilot_05AX_citation_placeholder_resolution_map.csv",
    "evidence_matrix": OUT_DIR / "pilot_05AX_related_work_evidence_matrix.csv",
    "claim_map": OUT_DIR / "pilot_05AX_claim_to_source_map.csv",
    "novelty_analysis": OUT_DIR / "pilot_05AX_novelty_boundary_analysis.md",
    "related_work": OUT_DIR / "pilot_05AX_related_work_synthesis.md",
    "verification_report": OUT_DIR / "pilot_05AX_source_verification_report.md",
    "insertion_plan": OUT_DIR / "pilot_05AX_manuscript_citation_insertion_plan.md",
    "validation_report": OUT_DIR / "pilot_05AX_internal_validation_report.md",
    "manifest": OUT_DIR / "pilot_05AX_manifest.json",
}

SOURCES = [
    {
        "source_id": "SRC-CHECKLIST-2020",
        "placeholder_ids": "CIT-ESR-01",
        "title": "Beyond Accuracy: Behavioral Testing of NLP Models with CheckList",
        "authors": "Marco Tulio Ribeiro; Tongshuang Wu; Carlos Guestrin; Sameer Singh",
        "year": "2020",
        "venue_or_institution": "ACL 2020",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.18653/v1/2020.acl-main.442",
        "stable_url": "https://aclanthology.org/2020.acl-main.442/",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Establishes that held-out accuracy alone is not an exhaustive evaluation of model behavior.",
        "overlap_level": "moderate",
        "novelty_boundary_note": "Broad multi-dimensional evaluation; it does not operationalize intermediate evidence-state reliability in decision-audit-escalation pipelines.",
    },
    {
        "source_id": "SRC-CALIBRATION-2017",
        "placeholder_ids": "CIT-ESR-01",
        "title": "On Calibration of Modern Neural Networks",
        "authors": "Chuan Guo; Geoff Pleiss; Yu Sun; Kilian Q. Weinberger",
        "year": "2017",
        "venue_or_institution": "ICML 2017, PMLR 70",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "PMLR 70:1321-1330",
        "stable_url": "https://proceedings.mlr.press/v70/guo17a.html",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "contextual",
        "manuscript_role": "Shows confidence calibration is a distinct evaluation dimension from predictive correctness.",
        "overlap_level": "low",
        "novelty_boundary_note": "Calibration concerns confidence-quality alignment, not completeness and usability of intermediate evidence states.",
    },
    {
        "source_id": "SRC-GCD-2023",
        "placeholder_ids": "CIT-PARSER-01",
        "title": "Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning",
        "authors": "Saibo Geng; Martin Josifoski; Maxime Peyrard; Robert West",
        "year": "2023",
        "venue_or_institution": "EMNLP 2023",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.18653/v1/2023.emnlp-main.674",
        "stable_url": "https://aclanthology.org/2023.emnlp-main.674/",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Provides an authoritative structured-generation reference and separates formal output constraints from task quality.",
        "overlap_level": "high",
        "novelty_boundary_note": "The intervention constrains output grammar; this project intervenes on evidence states and evaluates downstream decision, audit, and escalation.",
    },
    {
        "source_id": "SRC-CONSTRAINT-TAX-2026",
        "placeholder_ids": "CIT-PARSER-01;CIT-ESR-01",
        "title": "The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small Language Models",
        "authors": "Jaideep Ray",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2605.26128",
        "stable_url": "https://arxiv.org/abs/2605.26128",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Directly demonstrates that schema validity and answer/execution correctness can diverge under constrained decoding.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "This materially narrows any broad structural-versus-substantive novelty claim. The present distinction must rest on evidence-state degradation and multi-stage cascade operationalization, not on the mere existence of validity-correctness divergence.",
    },
    {
        "source_id": "SRC-STRUCTURED-BENCH-2026",
        "placeholder_ids": "CIT-PARSER-01;CIT-ESR-01",
        "title": "The Structured Output Benchmark",
        "authors": "Abhinav Kumar Singh; Harsha Vardhan Khurdula; Yoeven D Khemlani; Vineet Agarwal",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2604.25359",
        "stable_url": "https://arxiv.org/abs/2604.25359",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Reports schema-compliance and value-accuracy as separable structured-output dimensions.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "It concerns structured-output quality rather than controlled degradation of the evidence passed across decision, audit, and escalation stages.",
    },
    {
        "source_id": "SRC-AGENTBENCH-2024",
        "placeholder_ids": "CIT-PIPELINE-01;CIT-CASCADE-01",
        "title": "AgentBench: Evaluating LLMs as Agents",
        "authors": "Xiao Liu; Hao Yu; Hanchen Zhang; Yifan Xu; Xuanyu Lei; Hanyu Lai; Yu Gu; Hangliang Ding; Kaiwen Men; Kejuan Yang; Shudan Zhang; Xiang Deng; Aohan Zeng; Zhengxiao Du; Chenhui Zhang; Sheng Shen; Tianjun Zhang; Yu Su; Huan Sun; Minlie Huang; Yuxiao Dong; Jie Tang",
        "year": "2024",
        "venue_or_institution": "ICLR 2024",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "arXiv:2308.03688",
        "stable_url": "https://arxiv.org/abs/2308.03688",
        "verification_status": "VERIFIED_VENUE_AND_ARXIV_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Supports evaluation of interactive, multi-turn agent behavior and stage-specific failure analysis.",
        "overlap_level": "moderate",
        "novelty_boundary_note": "AgentBench evaluates agent capabilities across environments; it does not isolate evidence-state interventions or parser-versus-evidence reliability.",
    },
    {
        "source_id": "SRC-RAGAS-2024",
        "placeholder_ids": "CIT-ESR-01;CIT-PIPELINE-01",
        "title": "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
        "authors": "Shahul Es; Jithin James; Luis Espinosa-Anke; Steven Schockaert",
        "year": "2024",
        "venue_or_institution": "EACL 2024 System Demonstrations",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.18653/v1/2024.eacl-demo.16",
        "stable_url": "https://aclanthology.org/2024.eacl-demo.16/",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Separates context relevance, faithful use of context, and response quality.",
        "overlap_level": "high",
        "novelty_boundary_note": "RAG component evaluation is a close antecedent, but it does not model decision-audit-escalation cascade propagation under controlled evidence removal.",
    },
    {
        "source_id": "SRC-ARES-2024",
        "placeholder_ids": "CIT-ESR-01;CIT-PIPELINE-01",
        "title": "ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems",
        "authors": "Jon Saad-Falcon; Omar Khattab; Christopher Potts; Matei Zaharia",
        "year": "2024",
        "venue_or_institution": "NAACL 2024",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.18653/v1/2024.naacl-long.20",
        "stable_url": "https://aclanthology.org/2024.naacl-long.20/",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Provides component-level evaluation dimensions for context relevance, answer faithfulness, and answer relevance.",
        "overlap_level": "high",
        "novelty_boundary_note": "ARES evaluates RAG components; this project evaluates reliability changes caused by frozen evidence-state interventions across three downstream decision functions.",
    },
    {
        "source_id": "SRC-INSUFFICIENT-EVIDENCE-2022",
        "placeholder_ids": "CIT-ESR-01;CIT-CASCADE-01",
        "title": "Fact Checking with Insufficient Evidence",
        "authors": "Pepa Atanasova; Jakob Grue Simonsen; Christina Lioma; Isabelle Augenstein",
        "year": "2022",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_adjacent",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2204.02007",
        "stable_url": "https://arxiv.org/abs/2204.02007",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Shows controlled evidence omission and explicit evidence-sufficiency assessment in fact checking.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "This is a close antecedent for insufficiency interventions. The present contribution must be limited to the multi-stage reliability-layer operationalization and observed parser-stage divergence.",
    },
    {
        "source_id": "SRC-AUDIT-2020",
        "placeholder_ids": "CIT-AUDIT-01",
        "title": "Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing",
        "authors": "Inioluwa Deborah Raji; Andrew Smart; Rebecca N. White; Margaret Mitchell; Timnit Gebru; Ben Hutchinson; Jamila Smith-Loud; Daniel Theron; Parker Barnes",
        "year": "2020",
        "venue_or_institution": "FAccT 2020",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.1145/3351095.3372873",
        "stable_url": "https://doi.org/10.1145/3351095.3372873",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Supports lifecycle audit, documentation, traceability, and the distinction between procedural audit activity and substantive accountability.",
        "overlap_level": "moderate",
        "novelty_boundary_note": "The framework is organizational and lifecycle-oriented; it does not measure evidence-state degradation in an LLM stage cascade.",
    },
    {
        "source_id": "SRC-DEFER-2020",
        "placeholder_ids": "CIT-UNCERTAINTY-01",
        "title": "Consistent Estimators for Learning to Defer to an Expert",
        "authors": "Hussein Mozannar; David Sontag",
        "year": "2020",
        "venue_or_institution": "ICML 2020, PMLR 119",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "PMLR 119:7076-7087",
        "stable_url": "https://proceedings.mlr.press/v119/mozannar20b.html",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Provides a formal basis for deferral as a distinct downstream decision function.",
        "overlap_level": "moderate",
        "novelty_boundary_note": "Learning to defer optimizes allocation to an expert; the present escalation metric assesses whether recovery occurs under evidence degradation.",
    },
    {
        "source_id": "SRC-SELECTIVENET-2019",
        "placeholder_ids": "CIT-UNCERTAINTY-01",
        "title": "SelectiveNet: A Deep Neural Network with an Integrated Reject Option",
        "authors": "Yonatan Geifman; Ran El-Yaniv",
        "year": "2019",
        "venue_or_institution": "ICML 2019, PMLR 97",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "PMLR 97:2151-2159",
        "stable_url": "https://proceedings.mlr.press/v97/geifman19a.html",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Establishes reject-option and coverage-risk evaluation as distinct from unconditional prediction.",
        "overlap_level": "moderate",
        "novelty_boundary_note": "Selective prediction concerns abstention policies; this work evaluates escalation correctness and recovery after evidence degradation.",
    },
    {
        "source_id": "SRC-CFPB-DATABASE",
        "placeholder_ids": "CIT-CFPB-01",
        "title": "Consumer Complaint Database",
        "authors": "Consumer Financial Protection Bureau",
        "year": "2025",
        "venue_or_institution": "Consumer Financial Protection Bureau",
        "source_class": "official_institutional",
        "peer_review_status": "not_applicable",
        "identifier": "Official database documentation; page modified 2025-10-20",
        "stable_url": "https://www.consumerfinance.gov/data-research/consumer-complaints/",
        "verification_status": "VERIFIED_OFFICIAL_SOURCE",
        "central_or_contextual": "central",
        "manuscript_role": "Provides provenance and explicit limitations: complaints are not a statistical sample, narratives are consumer accounts, and interpretation requires contextual data.",
        "overlap_level": "low",
        "novelty_boundary_note": "This supports provenance and limitations only; it does not validate real-world financial decision performance or misconduct claims.",
    },
    {
        "source_id": "SRC-FSB-AI-2017",
        "placeholder_ids": "CIT-FINAI-01;CIT-AUDIT-01",
        "title": "Artificial intelligence and machine learning in financial services",
        "authors": "Financial Stability Board",
        "year": "2017",
        "venue_or_institution": "Financial Stability Board",
        "source_class": "official_institutional",
        "peer_review_status": "not_applicable",
        "identifier": "Official FSB report, 2017-11-01",
        "stable_url": "https://www.fsb.org/2017/11/artificial-intelligence-and-machine-learning-in-financial-service/",
        "verification_status": "VERIFIED_OFFICIAL_SOURCE",
        "central_or_contextual": "contextual",
        "manuscript_role": "Motivates high-assurance evaluation in financial services and notes interpretability, auditability, testing, and interconnectedness risks.",
        "overlap_level": "low",
        "novelty_boundary_note": "Domain motivation only; it cannot be used to claim deployment validity, regulatory compliance, or consumer-harm prevalence.",
    },
    {
        "source_id": "SRC-FSB-AI-2026",
        "placeholder_ids": "CIT-FINAI-01;CIT-AUDIT-01",
        "title": "Sound Practices for Responsible Adoption of Artificial Intelligence: Consultation report",
        "authors": "Financial Stability Board",
        "year": "2026",
        "venue_or_institution": "Financial Stability Board",
        "source_class": "official_institutional_consultation",
        "peer_review_status": "not_applicable",
        "identifier": "Consultation report, 2026-06-10",
        "stable_url": "https://www.fsb.org/2026/06/sound-practices-for-responsible-adoption-of-artificial-intelligence-consultation-report/",
        "verification_status": "VERIFIED_OFFICIAL_SOURCE_AND_CONSULTATION_STATUS",
        "central_or_contextual": "current_context_only",
        "manuscript_role": "Current institutional context for responsible AI adoption in finance.",
        "overlap_level": "low",
        "novelty_boundary_note": "Must be labelled a consultation report rather than final guidance; it is not empirical validation of this experiment.",
    },
    {
        "source_id": "SRC-WOHLIN-2012",
        "placeholder_ids": "CIT-VALIDITY-01",
        "title": "Experimentation in Software Engineering",
        "authors": "Claes Wohlin; Per Runeson; Martin Höst; Magnus C. Ohlsson; Björn Regnell; Anders Wesslén",
        "year": "2012",
        "venue_or_institution": "Springer",
        "source_class": "methods_book",
        "peer_review_status": "scholarly_book",
        "identifier": "DOI 10.1007/978-3-642-29044-2",
        "stable_url": "https://doi.org/10.1007/978-3-642-29044-2",
        "verification_status": "VERIFIED_PUBLISHER_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Provides the construct, internal, external, and conclusion-validity structure used for the threats-to-validity framework.",
        "overlap_level": "low",
        "novelty_boundary_note": "Methods framework only.",
    },
    {
        "source_id": "SRC-REPRO-2021",
        "placeholder_ids": "CIT-REPRO-01",
        "title": "Improving Reproducibility in Machine Learning Research",
        "authors": "Joelle Pineau et al.",
        "year": "2021",
        "venue_or_institution": "Journal of Machine Learning Research 22(164)",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "JMLR 22(164):1-20",
        "stable_url": "https://jmlr.org/papers/v22/20-303.html",
        "verification_status": "VERIFIED_PRIMARY_METADATA",
        "central_or_contextual": "central",
        "manuscript_role": "Supports transparent reporting, artefact availability, and reproducibility-oriented research workflows.",
        "overlap_level": "low",
        "novelty_boundary_note": "Reproducibility guidance does not validate the empirical result; it supports reporting practice.",
    },
    {
        "source_id": "SRC-CASCADE-NETWORKS-2002",
        "placeholder_ids": "CIT-CASCADE-01",
        "title": "Cascade-based attacks on complex networks",
        "authors": "Adilson E. Motter; Ying-Cheng Lai",
        "year": "2002",
        "venue_or_institution": "Physical Review E 66, 065102",
        "source_class": "peer_reviewed",
        "peer_review_status": "peer_reviewed",
        "identifier": "DOI 10.1103/PhysRevE.66.065102",
        "stable_url": "https://doi.org/10.1103/PhysRevE.66.065102",
        "verification_status": "VERIFIED_PUBLISHER_METADATA",
        "central_or_contextual": "conceptual_anchor",
        "manuscript_role": "Provides a canonical systems-level example of load redistribution and cascading failure.",
        "overlap_level": "low",
        "novelty_boundary_note": "The cascade concept is not new; the claimed contribution must be the narrower LLM evidence-state operationalization and empirical pattern.",
    },
    {
        "source_id": "SRC-SPARK-FIRE-2026",
        "placeholder_ids": "CIT-CASCADE-01;CIT-PIPELINE-01",
        "title": "From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration",
        "authors": "Yizhe Xie; Congcong Zhu; Xinyue Zhang; Tianqing Zhu; Dayong Ye; Minfeng Qi; Huajie Chen; Wanlei Zhou",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2603.04474",
        "stable_url": "https://arxiv.org/abs/2603.04474",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Studies seeded errors and propagation in multi-agent collaboration.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "The cascade terminology is already active in LLM research. This project must distinguish evidence-state degradation in a decision-audit-escalation pipeline from message-level multi-agent error diffusion.",
    },
    {
        "source_id": "SRC-HALLUCINATION-CASCADE-2026",
        "placeholder_ids": "CIT-CASCADE-01;CIT-PIPELINE-01",
        "title": "Hallucination Cascade: Analyzing Error Propagation in Multi-Agent LLM Systems",
        "authors": "Saeid Jamshidi; Arghavan Moradi Dakhel; Kawser Wazed Nafi; Foutse Khomh",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2606.07937",
        "stable_url": "https://arxiv.org/abs/2606.07937",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Provides emerging evidence on hallucination propagation across interacting LLM agents.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "It concerns multi-agent hallucination dynamics rather than controlled evidence-state interventions, parser validity, and recovery across decision, audit, and escalation.",
    },
    {
        "source_id": "SRC-SURE-RAG-2026",
        "placeholder_ids": "CIT-ESR-01;CIT-UNCERTAINTY-01",
        "title": "SURE-RAG: Sufficiency and Uncertainty-Aware Evidence Verification for Selective Retrieval-Augmented Generation",
        "authors": "Jingxi Qiu; Zeyu Han; Cheng Huang",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2605.03534",
        "stable_url": "https://arxiv.org/abs/2605.03534",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Treats evidence sufficiency as a set-level property and links it to abstention.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "This narrows broad evidence-sufficiency novelty. The present contribution is the stage-wise ESR operationalization and parser-versus-stage behavior under controlled degradation.",
    },
    {
        "source_id": "SRC-EVIDENCE-DELAY-2026",
        "placeholder_ids": "CIT-ESR-01;CIT-UNCERTAINTY-01;CIT-FINAI-01",
        "title": "Evidence Sufficiency Under Delayed Ground Truth",
        "authors": "Oleg Solozobov",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2604.15740",
        "stable_url": "https://arxiv.org/abs/2604.15740",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Frames evidence sufficiency in risk decision systems under delayed labels and drift.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "Terminology overlaps strongly. It differs in delayed-ground-truth risk monitoring rather than multi-stage LLM parser/evidence divergence, so the manuscript must cite and distinguish it explicitly.",
    },
    {
        "source_id": "SRC-STATE-TRACE-2026",
        "placeholder_ids": "CIT-ESR-01;CIT-AUDIT-01",
        "title": "World Models in Words: Auditing Physical State-Transition Commitments in VLMs",
        "authors": "Emmanuelle Bourigault",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2605.29585",
        "stable_url": "https://arxiv.org/abs/2605.29585",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "high_priority_adjacent",
        "manuscript_role": "Shows that correct answers can coexist with invalid state-transition traces.",
        "overlap_level": "very_high",
        "novelty_boundary_note": "This is close to state-level reliability but operates on typed physical traces in VLMs, not evidence packets across decision, audit, and escalation.",
    },
    {
        "source_id": "SRC-CITED-NOT-VERIFIED-2026",
        "placeholder_ids": "CIT-PARSER-01;CIT-AUDIT-01",
        "title": "Cited but Not Verified: Parsing and Evaluating Source Attribution in LLM Deep Research Agents",
        "authors": "Hailey Onweller; Elias Lumer; Austin Huber; Pia Ramchandani; Vamse Kumar Subbiah; Corey Feld",
        "year": "2026",
        "venue_or_institution": "arXiv preprint",
        "source_class": "preprint_emerging",
        "peer_review_status": "not_peer_reviewed_as_verified",
        "identifier": "arXiv:2605.06635",
        "stable_url": "https://arxiv.org/abs/2605.06635",
        "verification_status": "VERIFIED_ARXIV_METADATA",
        "central_or_contextual": "adjacent",
        "manuscript_role": "Separates surface source-attribution validity from substantive source verification.",
        "overlap_level": "high",
        "novelty_boundary_note": "Supports the broader structural-versus-substantive distinction, but not the paper's evidence-state manipulation or cascade metrics.",
    },
]

RESOLUTIONS = [
    {
        "placeholder_id": "CIT-ESR-01",
        "resolution_status": "RESOLVED_WITH_BOUNDED_SYNTHESIS",
        "primary_source_ids": "SRC-CHECKLIST-2020;SRC-RAGAS-2024;SRC-ARES-2024",
        "adjacent_or_caution_source_ids": "SRC-CALIBRATION-2017;SRC-INSUFFICIENT-EVIDENCE-2022;SRC-SURE-RAG-2026;SRC-EVIDENCE-DELAY-2026;SRC-STATE-TRACE-2026",
        "proposed_bounded_insertion": "Prior evaluation work separates dimensions such as behavioral capability, calibration, context relevance, faithfulness, and answer relevance. The present study adds a bounded operational layer for the completeness and usability of evidence passed across decision, audit, and escalation stages.",
        "claim_limit": "Do not claim that prior work ignores intermediate evidence or that Evidence-State Reliability is globally unprecedented.",
    },
    {
        "placeholder_id": "CIT-CASCADE-01",
        "resolution_status": "RESOLVED_WITH_QUALIFICATION",
        "primary_source_ids": "SRC-CASCADE-NETWORKS-2002;SRC-AGENTBENCH-2024",
        "adjacent_or_caution_source_ids": "SRC-SPARK-FIRE-2026;SRC-HALLUCINATION-CASCADE-2026;SRC-INSUFFICIENT-EVIDENCE-2022",
        "proposed_bounded_insertion": "Cascade and propagation concepts are established in complex systems, and emerging LLM work studies multi-agent error diffusion. Here, reliability cascade is used more narrowly for condition-linked changes across decision, audit, and escalation under a controlled evidence-state intervention.",
        "claim_limit": "Do not claim invention of cascade concepts or deployed-system causality.",
    },
    {
        "placeholder_id": "CIT-PIPELINE-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-AGENTBENCH-2024;SRC-RAGAS-2024;SRC-ARES-2024",
        "adjacent_or_caution_source_ids": "SRC-SPARK-FIRE-2026;SRC-HALLUCINATION-CASCADE-2026",
        "proposed_bounded_insertion": "Interactive agents and retrieval-augmented systems motivate component- and stage-aware evaluation rather than reliance on a single end-to-end score.",
        "claim_limit": "Do not imply that all multi-stage systems share the same cascade mechanism.",
    },
    {
        "placeholder_id": "CIT-PARSER-01",
        "resolution_status": "RESOLVED_WITH_HIGH_OVERLAP_WARNING",
        "primary_source_ids": "SRC-GCD-2023",
        "adjacent_or_caution_source_ids": "SRC-CONSTRAINT-TAX-2026;SRC-STRUCTURED-BENCH-2026;SRC-CITED-NOT-VERIFIED-2026",
        "proposed_bounded_insertion": "Structured-generation work treats schema conformance as an explicit output property, while recent benchmarks show that validity and value-level correctness can diverge. The present experiment tests a different source of divergence: controlled degradation of the evidence state supplied to a multi-stage pipeline.",
        "claim_limit": "Do not claim that structural-versus-semantic divergence is new.",
    },
    {
        "placeholder_id": "CIT-AUDIT-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-AUDIT-2020",
        "adjacent_or_caution_source_ids": "SRC-FSB-AI-2017;SRC-FSB-AI-2026;SRC-STATE-TRACE-2026;SRC-CITED-NOT-VERIFIED-2026",
        "proposed_bounded_insertion": "End-to-end auditing emphasizes documentation, traceability, and lifecycle accountability. In this experiment, the audit stage is a narrower computational function whose success remains limited by the evidence available to it.",
        "claim_limit": "Do not equate the experimental audit stage with a full organizational or regulatory audit.",
    },
    {
        "placeholder_id": "CIT-UNCERTAINTY-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-DEFER-2020;SRC-SELECTIVENET-2019",
        "adjacent_or_caution_source_ids": "SRC-SURE-RAG-2026;SRC-EVIDENCE-DELAY-2026",
        "proposed_bounded_insertion": "Selective prediction and learning-to-defer establish abstention and deferral as distinct decision functions. The present escalation layer asks whether downstream recovery succeeds when the evidence state is degraded.",
        "claim_limit": "Do not claim an optimal escalation policy or identify escalation correctness with uncertainty calibration.",
    },
    {
        "placeholder_id": "CIT-FINAI-01",
        "resolution_status": "RESOLVED_FOR_DOMAIN_MOTIVATION_ONLY",
        "primary_source_ids": "SRC-FSB-AI-2017",
        "adjacent_or_caution_source_ids": "SRC-FSB-AI-2026;SRC-EVIDENCE-DELAY-2026",
        "proposed_bounded_insertion": "Financial-sector institutions identify interpretability, auditability, testing, and interconnectedness as important AI risk considerations, motivating careful reliability evaluation in this domain.",
        "claim_limit": "Domain context does not establish deployment, regulatory, financial, or consumer-harm validity.",
    },
    {
        "placeholder_id": "CIT-CFPB-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-CFPB-DATABASE",
        "adjacent_or_caution_source_ids": "",
        "proposed_bounded_insertion": "The CFPB database is a public complaint resource, but CFPB cautions that complaints are not a statistical sample, narratives are consumer accounts, and interpretation requires contextual information.",
        "claim_limit": "Do not infer prevalence, company misconduct, representativeness, or verified factual truth from complaint records.",
    },
    {
        "placeholder_id": "CIT-VALIDITY-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-WOHLIN-2012",
        "adjacent_or_caution_source_ids": "",
        "proposed_bounded_insertion": "Threats are organized using construct, internal, external, and conclusion-validity categories.",
        "claim_limit": "The framework structures limitations; it does not remove them.",
    },
    {
        "placeholder_id": "CIT-REPRO-01",
        "resolution_status": "RESOLVED",
        "primary_source_ids": "SRC-REPRO-2021",
        "adjacent_or_caution_source_ids": "",
        "proposed_bounded_insertion": "The study uses manifests, source indexes, deterministic validators, and bounded availability statements to strengthen computational traceability and reproducibility.",
        "claim_limit": "Sanitized artefact reproducibility is not equivalent to raw prompt-response replay.",
    },
]

EVIDENCE_MATRIX = [
    {
        "topic": "Evaluation beyond a single final score",
        "adjacent_concept": "Behavioral testing, calibration, holistic and component-level evaluation",
        "source_ids": "SRC-CHECKLIST-2020;SRC-CALIBRATION-2017;SRC-RAGAS-2024;SRC-ARES-2024",
        "what_prior_work_establishes": "Model quality is multidimensional; accuracy, confidence calibration, context relevance, faithfulness, and response relevance should be measured separately.",
        "what_prior_work_does_not_establish": "It does not collectively establish the Pilot 05 evidence-state metric or its parser-versus-stage divergence.",
        "project_distinction": "Controls evidence completeness and measures decision, audit, and escalation separately.",
        "review_risk": "medium",
    },
    {
        "topic": "Structured output validity",
        "adjacent_concept": "Grammar-constrained decoding, schema compliance, value accuracy",
        "source_ids": "SRC-GCD-2023;SRC-CONSTRAINT-TAX-2026;SRC-STRUCTURED-BENCH-2026",
        "what_prior_work_establishes": "Formal validity is a distinct measurable output property and can diverge from value-level or executable correctness.",
        "what_prior_work_does_not_establish": "It does not test evidence-state degradation across a multi-stage decision-control pipeline.",
        "project_distinction": "The manipulated variable is the evidence state rather than the decoding constraint.",
        "review_risk": "very_high",
    },
    {
        "topic": "Evidence sufficiency",
        "adjacent_concept": "Insufficient evidence detection, RAG sufficiency, delayed-ground-truth evidence quality",
        "source_ids": "SRC-INSUFFICIENT-EVIDENCE-2022;SRC-SURE-RAG-2026;SRC-EVIDENCE-DELAY-2026",
        "what_prior_work_establishes": "Evidence completeness or sufficiency can be treated as an explicit evaluation and abstention variable.",
        "what_prior_work_does_not_establish": "It does not reproduce this study's decision-audit-escalation cascade and parser-validity movement.",
        "project_distinction": "Operationalizes condition-level evidence-state interventions and downstream stage-specific success.",
        "review_risk": "very_high",
    },
    {
        "topic": "Process and state trace reliability",
        "adjacent_concept": "Process supervision and typed state-transition auditing",
        "source_ids": "SRC-STATE-TRACE-2026",
        "what_prior_work_establishes": "Outcome correctness can conceal flawed intermediate processes or state transitions.",
        "what_prior_work_does_not_establish": "It does not define the evidence packets and cascade metrics used in Pilot 05.",
        "project_distinction": "Focuses on evidence availability and usability across distinct downstream functions.",
        "review_risk": "high",
    },
    {
        "topic": "Error cascades",
        "adjacent_concept": "Complex-system cascading failure and multi-agent error propagation",
        "source_ids": "SRC-CASCADE-NETWORKS-2002;SRC-SPARK-FIRE-2026;SRC-HALLUCINATION-CASCADE-2026",
        "what_prior_work_establishes": "Upstream perturbations can propagate and compound through connected components or interacting agents.",
        "what_prior_work_does_not_establish": "It does not establish the narrower evidence-state cascade in this controlled decision pipeline.",
        "project_distinction": "Links a frozen evidence intervention to decision, audit detection, and escalation recovery metrics.",
        "review_risk": "very_high",
    },
    {
        "topic": "Audit and assurance",
        "adjacent_concept": "End-to-end internal auditing and responsible-AI assurance",
        "source_ids": "SRC-AUDIT-2020;SRC-FSB-AI-2017;SRC-FSB-AI-2026",
        "what_prior_work_establishes": "Traceability, documentation, testing, and lifecycle accountability are necessary assurance practices.",
        "what_prior_work_does_not_establish": "It does not show that an experimental audit stage can recover from degraded evidence.",
        "project_distinction": "Separates detection from recovery and treats the audit stage as evidence-constrained.",
        "review_risk": "medium",
    },
    {
        "topic": "Abstention and escalation",
        "adjacent_concept": "Selective prediction, reject option, learning to defer",
        "source_ids": "SRC-DEFER-2020;SRC-SELECTIVENET-2019",
        "what_prior_work_establishes": "Abstention and deferral are separate decision functions with their own evaluation criteria.",
        "what_prior_work_does_not_establish": "It does not measure this experiment's escalation recovery under evidence-state degradation.",
        "project_distinction": "Evaluates whether a downstream stage recovers after an evidence manipulation.",
        "review_risk": "medium",
    },
    {
        "topic": "Financial and CFPB context",
        "adjacent_concept": "Financial-sector AI risk and public complaint-data provenance",
        "source_ids": "SRC-CFPB-DATABASE;SRC-FSB-AI-2017;SRC-FSB-AI-2026",
        "what_prior_work_establishes": "The domain merits high-assurance evaluation and the complaint database has explicit representativeness and verification limitations.",
        "what_prior_work_does_not_establish": "It does not validate this study as a deployed financial or regulatory system.",
        "project_distinction": "Uses sanitized CFPB-backed packets as a controlled evaluation substrate only.",
        "review_risk": "medium",
    },
]

CLAIM_MAP = [
    {
        "claim_id": "CLM-LIT-01",
        "claim_text": "Final accuracy or parser compliance does not exhaust reliability evaluation.",
        "support_type": "direct_and_synthetic",
        "external_source_ids": "SRC-CHECKLIST-2020;SRC-CALIBRATION-2017;SRC-RAGAS-2024;SRC-ARES-2024;SRC-GCD-2023",
        "internal_source_boundary": "None required for the literature proposition.",
        "allowed_wording": "Prior work motivates separating behavioral, calibration, context, faithfulness, and structural dimensions.",
        "prohibited_extension": "Prior work entirely ignores intermediate evidence.",
    },
    {
        "claim_id": "CLM-LIT-02",
        "claim_text": "Schema validity and substantive correctness can diverge.",
        "support_type": "direct",
        "external_source_ids": "SRC-GCD-2023;SRC-CONSTRAINT-TAX-2026;SRC-STRUCTURED-BENCH-2026",
        "internal_source_boundary": "Pilot 05 internal evidence is required for the specific direction and magnitude observed in this run.",
        "allowed_wording": "Structured-output research separates schema conformance from value-level correctness.",
        "prohibited_extension": "This paper is the first to show any validity-correctness divergence.",
    },
    {
        "claim_id": "CLM-LIT-03",
        "claim_text": "Evidence sufficiency is an established adjacent concern.",
        "support_type": "direct",
        "external_source_ids": "SRC-INSUFFICIENT-EVIDENCE-2022;SRC-SURE-RAG-2026;SRC-EVIDENCE-DELAY-2026",
        "internal_source_boundary": "Pilot 05 defines its own operational evidence-state conditions.",
        "allowed_wording": "Adjacent work explicitly evaluates insufficient or sufficient evidence.",
        "prohibited_extension": "Evidence-State Reliability has no conceptual antecedents.",
    },
    {
        "claim_id": "CLM-LIT-04",
        "claim_text": "Error propagation and cascades are established concepts, including emerging LLM-specific work.",
        "support_type": "direct_and_contextual",
        "external_source_ids": "SRC-CASCADE-NETWORKS-2002;SRC-SPARK-FIRE-2026;SRC-HALLUCINATION-CASCADE-2026",
        "internal_source_boundary": "Pilot 05 evidence is required for the project-specific cascade definition and rates.",
        "allowed_wording": "The paper adopts a narrower evidence-state cascade operationalization.",
        "prohibited_extension": "The paper invents cascading failure as a concept.",
    },
    {
        "claim_id": "CLM-EMP-01",
        "claim_text": "In Pilot 05, parser validity improved under degraded evidence while stage/evidence success deteriorated.",
        "support_type": "internal_empirical_only",
        "external_source_ids": "",
        "internal_source_boundary": "Committed 05AR/05AS/05AT/05AW artifacts at repository checkpoint f05ae265706bff5e408ae80c35f07e019a850d4d.",
        "allowed_wording": "Within this experiment, the two metric families moved in opposite directions.",
        "prohibited_extension": "External literature proves this Pilot 05 result or its universal generality.",
    },
    {
        "claim_id": "CLM-EMP-02",
        "claim_text": "Pilot 05 supports Evidence-State Reliability as distinct from parser validity.",
        "support_type": "internal_empirical_plus_external_positioning",
        "external_source_ids": "SRC-CHECKLIST-2020;SRC-RAGAS-2024;SRC-ARES-2024;SRC-GCD-2023;SRC-CONSTRAINT-TAX-2026",
        "internal_source_boundary": "Committed Pilot 05 outputs supply the actual evidence; literature supplies adjacent distinctions.",
        "allowed_wording": "The result supports a bounded operational distinction in the studied pipeline.",
        "prohibited_extension": "The distinction is universally established for all LLM systems.",
    },
    {
        "claim_id": "CLM-AUDIT-01",
        "claim_text": "An audit stage is not equivalent to full organizational assurance.",
        "support_type": "direct_boundary",
        "external_source_ids": "SRC-AUDIT-2020;SRC-FSB-AI-2017",
        "internal_source_boundary": "Pilot 05 defines a computational audit stage only.",
        "allowed_wording": "The experiment uses a narrower stage-level audit function.",
        "prohibited_extension": "The experiment validates regulatory or enterprise auditability.",
    },
    {
        "claim_id": "CLM-ESC-01",
        "claim_text": "Deferral, abstention, and escalation should be evaluated separately from base prediction.",
        "support_type": "direct",
        "external_source_ids": "SRC-DEFER-2020;SRC-SELECTIVENET-2019",
        "internal_source_boundary": "Pilot 05 supplies escalation recovery results.",
        "allowed_wording": "Escalation is a distinct downstream reliability function.",
        "prohibited_extension": "The tested escalation rule is optimal.",
    },
    {
        "claim_id": "CLM-CFPB-01",
        "claim_text": "CFPB complaint data require bounded interpretation.",
        "support_type": "direct_official",
        "external_source_ids": "SRC-CFPB-DATABASE",
        "internal_source_boundary": "The project uses sanitized CFPB-backed packets, not a prevalence sample.",
        "allowed_wording": "Use as an evaluation substrate with explicit provenance limitations.",
        "prohibited_extension": "Infer consumer-harm prevalence, verified narratives, representativeness, or company misconduct.",
    },
    {
        "claim_id": "CLM-REPRO-01",
        "claim_text": "Transparent artefacts and reporting strengthen computational reproducibility.",
        "support_type": "direct",
        "external_source_ids": "SRC-REPRO-2021",
        "internal_source_boundary": "Committed manifests and validators document what is reproducible.",
        "allowed_wording": "Sanitized artefact-level reproducibility and traceability are supported.",
        "prohibited_extension": "Raw prompt-response replay is available or full computational reproducibility is guaranteed.",
    },
]

NOVELTY_ANALYSIS = """# Pilot 05AX Novelty-Boundary Analysis

## Reliability verdict

**BOUNDED DIFFERENTIATION IS SUPPORTED; GLOBAL PRIORITY OR “FIRST-EVER” NOVELTY IS NOT ESTABLISHED.**

The targeted literature search did not identify the exact phrase **Evidence-State Reliability** as a settled evaluation term. That observation is not proof of global terminological novelty: the search was targeted rather than systematic, terminology varies across fields, and very recent work overlaps strongly with several components of the proposed framing.

## What prior work already establishes

The literature already establishes that:

1. model evaluation should extend beyond a single accuracy score;
2. confidence calibration is distinct from answer correctness;
3. retrieval relevance, answer faithfulness, and answer relevance can be evaluated separately;
4. grammar or schema conformance is a distinct output property;
5. schema validity can diverge from value-level or executable correctness;
6. evidence sufficiency and insufficient-evidence detection are explicit research problems;
7. correct final answers can conceal invalid intermediate processes or state traces;
8. cascading failures and propagated errors are established systems concepts;
9. recent LLM work explicitly studies error cascades in multi-agent collaboration;
10. abstention and deferral are distinct downstream decision functions.

Accordingly, the manuscript must not claim that it invents multi-dimensional evaluation, evidence sufficiency, structural-versus-semantic divergence, process evaluation, cascade concepts, auditing, or escalation.

## High-overlap adjacent clusters

### 1. Structured validity versus substantive correctness

Grammar-constrained decoding and recent 2026 structured-output studies directly separate schema validity from semantic or executable correctness. This is the most important limitation on a broad novelty claim. Pilot 05 remains differentiable only if the paper makes clear that its intervention is **evidence-state degradation**, not constrained decoding, and that the measured consequences span decision, audit, and escalation.

### 2. Evidence sufficiency

Fact-checking and RAG research already treats omitted or insufficient evidence as a measurable condition. Recent work also uses “evidence sufficiency” in risk decision systems. The manuscript therefore should not present evidence adequacy itself as an untouched topic.

### 3. Process and state-trace evaluation

Process-supervision and state-transition auditing show that final correctness may conceal flawed intermediate states. Evidence-State Reliability must be distinguished by the type of state under examination: the evidence available to downstream decision functions rather than a reasoning trace or physical-state trace.

### 4. Error cascades

Cascading failure is an established systems concept, and 2026 LLM preprints use “error cascade” and “hallucination cascade” for multi-agent propagation. The manuscript’s defensible use is narrower: condition-linked reliability changes across a decision-audit-escalation sequence under a controlled evidence-state intervention.

## Defensible contribution boundary

The strongest defensible contribution is the **combination and operationalization** of:

1. a frozen, controlled manipulation of intermediate evidence states;
2. separate measurement of parser validity and evidence-sensitive stage success;
3. a multi-stage decision, audit, and escalation pipeline;
4. explicit separation of detection from recovery;
5. an observed within-run divergence in which parser validity improves while stage/evidence success deteriorates;
6. a sanitized, CFPB-backed real-model execution with deterministic traceability controls.

No single adjacent source identified in this targeted search was verified as combining all six elements. This supports a bounded differentiation claim, not a universal priority claim.

## Recommended novelty wording

> This study operationalizes Evidence-State Reliability as a stage-aware evaluation layer for the completeness and usability of evidence passed across a multi-stage LLM decision pipeline. Building on prior work that separates behavioral, calibration, structured-output, faithfulness, sufficiency, and process dimensions, the study contributes a controlled decision-audit-escalation design and documents a within-experiment divergence between parser validity and evidence-sensitive stage success.


## Wording that should not be used

- “the first study ever”
- “no prior work considers evidence sufficiency”
- “prior evaluation only measures final accuracy”
- “parser-validity divergence is entirely novel”
- “reliability cascades have not been studied in LLMs”
- “the framework proves general LLM unreliability”
- “the CFPB-backed experiment establishes real-world financial validity”

## Current novelty confidence

- **Term-level uniqueness:** unresolved; targeted search found no settled exact-match term, but this is not conclusive.
- **Component novelty:** low to moderate; most components have clear antecedents.
- **Combination and operationalization novelty:** moderate and defensible with careful related-work integration.
- **Empirical-pattern novelty:** promising within the precise controlled pipeline design, but must be stated as a bounded result.
- **Universal novelty:** unsupported.

## Decision for the next manuscript task

Proceed to citation integration only after preserving the bounded claim above. A further Claude replication may strengthen external validity, but it is not required to establish the literature boundary and should be decided separately after manuscript and journal-target review.
"""

RELATED_WORK = """# Pilot 05AX Related-Work Synthesis

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
"""

VERIFICATION_REPORT = """# Pilot 05AX Source-Verification Report

## Scope

Task 05AX performed a targeted external literature search on 13 July 2026. The search was designed to resolve the ten committed 05AW citation placeholders and test the manuscript's novelty boundary against close adjacent work.

This was **not** a registered systematic review, exhaustive bibliometric review, or proof of global novelty.

## Verification rules applied

1. Central metadata were checked against primary publication pages where available: ACL Anthology, PMLR, JMLR, publisher DOI pages, official CFPB pages, official FSB pages, and arXiv records.
2. Peer-reviewed and official institutional sources were prioritized for foundational claims.
3. Recent arXiv work was included where it materially narrows novelty, but every such source is labelled as a preprint or as not peer-reviewed in the verified metadata.
4. Official consultation material is explicitly labelled as consultation material rather than final guidance.
5. No citation is used as external proof of Pilot 05's internal empirical numbers.
6. No exact-title, author, venue, year, or identifier was intentionally fabricated.

## Source-quality result

- Foundational evaluation, structured-output, agent, RAG, audit, deferral, validity, and reproducibility slots have peer-reviewed or scholarly-method anchors.
- CFPB provenance is grounded in the official database documentation.
- Financial-domain motivation is grounded in official FSB reports.
- LLM-specific cascade and several closest 2026 overlap sources are emerging preprints; they should be cited for novelty caution, not treated as settled consensus.
- The exact Evidence-State Reliability phrase was not located as an established term in the targeted searches performed, but this is not evidence of global uniqueness.

## Highest novelty risks

1. Recent structured-output work already reports validity-correctness tradeoffs.
2. Evidence sufficiency is an established adjacent topic in fact checking, RAG, and risk decision systems.
3. State-trace and process evaluation already show that final correctness can conceal intermediate defects.
4. Recent LLM papers explicitly use cascade terminology for propagated errors.

## Required bibliographic cleanup before manuscript integration

The 2026 preprints and older arXiv-only adjacent works should be rechecked for later peer-reviewed versions at the time of submission. If a preprint has been superseded, the published version should replace it.

## Conclusion

All ten placeholders can be resolved with verified sources, but several require bounded synthesis rather than a single citation. The literature supports a careful combination-and-operationalization novelty claim. It does not support “first-ever,” “no prior work,” or universal novelty language.
"""

INSERTION_PLAN = """# Pilot 05AX Manuscript Citation-Insertion Plan

This plan does not edit the committed manuscript.

## Introduction: evaluation-layer distinction

Replace `[CIT-ESR-01]` with a synthesis anchored in:
- SRC-CHECKLIST-2020
- SRC-CALIBRATION-2017
- SRC-RAGAS-2024
- SRC-ARES-2024

Required wording boundary: evaluation is multidimensional; do not say prior work only checks final answers.

## Introduction and Related Work: reliability cascades

Replace `[CIT-CASCADE-01]` with:
- SRC-CASCADE-NETWORKS-2002 as the general cascade anchor
- SRC-SPARK-FIRE-2026 and SRC-HALLUCINATION-CASCADE-2026 as explicitly labelled emerging LLM preprints
- SRC-AGENTBENCH-2024 for interactive-agent evaluation context

Required wording boundary: define the present cascade operationalization narrowly and do not claim invention of cascade theory.

## Related Work: multi-stage pipelines

Replace `[CIT-PIPELINE-01]` with:
- SRC-AGENTBENCH-2024
- SRC-RAGAS-2024
- SRC-ARES-2024

Required wording boundary: component-aware evaluation is established; the new contribution is the controlled evidence-state and decision-audit-escalation design.

## Related Work: parser and structured output validity

Replace `[CIT-PARSER-01]` with:
- SRC-GCD-2023
- SRC-CONSTRAINT-TAX-2026
- SRC-STRUCTURED-BENCH-2026

Required wording boundary: recent preprints directly narrow the claim. Do not call structural-versus-semantic divergence new.

## Related Work: audit and assurance

Replace `[CIT-AUDIT-01]` with:
- SRC-AUDIT-2020
- SRC-FSB-AI-2017
- optionally SRC-FSB-AI-2026, clearly labelled as a consultation report

Required wording boundary: the experimental audit stage is not an organizational or regulatory audit.

## Related Work: uncertainty and escalation

Replace `[CIT-UNCERTAINTY-01]` with:
- SRC-DEFER-2020
- SRC-SELECTIVENET-2019
- contextual novelty cautions SRC-SURE-RAG-2026 and SRC-EVIDENCE-DELAY-2026

Required wording boundary: escalation is distinct; no optimal-policy claim.

## Domain context

Replace `[CIT-FINAI-01]` with:
- SRC-FSB-AI-2017
- optional current context from SRC-FSB-AI-2026

Required wording boundary: motivation only, not deployment or regulatory validity.

## Data provenance

Replace `[CIT-CFPB-01]` with:
- SRC-CFPB-DATABASE

Required wording boundary: state nonrepresentativeness and narrative-verification limits explicitly.

## Threats to validity

Replace `[CIT-VALIDITY-01]` with:
- SRC-WOHLIN-2012

Use construct, internal, external, and conclusion validity as organizing categories.

## Reproducibility statement

Replace `[CIT-REPRO-01]` with:
- SRC-REPRO-2021

Required wording boundary: claim sanitized artefact traceability, not raw replay.

## Novelty paragraph replacement direction

The current novelty paragraph should be revised in the next approved manuscript-edit task to say that the contribution is a **controlled combination and operationalization**, not that no adjacent work exists. The empirical result itself must remain sourced only to committed Pilot 05 artefacts.
"""


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    require(INPUT_REGISTER.is_file(), f"Missing committed 05AW register: {INPUT_REGISTER}")

    with INPUT_REGISTER.open(newline="", encoding="utf-8-sig") as handle:
        input_rows = list(csv.DictReader(handle))

    input_ids = sorted(row["placeholder_id"].strip() for row in input_rows)
    require(
        input_ids == sorted(EXPECTED_PLACEHOLDERS),
        f"05AW placeholder set mismatch. Expected {EXPECTED_PLACEHOLDERS}, found {input_ids}",
    )
    require(
        all(row.get("status", "").strip() == "PLACEHOLDER_ONLY" for row in input_rows),
        "05AW input register contains a non-placeholder status.",
    )

    require(not OUT_DIR.exists(), f"Output directory already exists: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=False)

    source_fields = [
        "source_id",
        "placeholder_ids",
        "title",
        "authors",
        "year",
        "venue_or_institution",
        "source_class",
        "peer_review_status",
        "identifier",
        "stable_url",
        "verification_status",
        "central_or_contextual",
        "manuscript_role",
        "overlap_level",
        "novelty_boundary_note",
    ]
    write_csv(OUTPUT_FILES["source_register"], SOURCES, source_fields)

    resolution_fields = [
        "placeholder_id",
        "resolution_status",
        "primary_source_ids",
        "adjacent_or_caution_source_ids",
        "proposed_bounded_insertion",
        "claim_limit",
    ]
    write_csv(OUTPUT_FILES["resolution_map"], RESOLUTIONS, resolution_fields)

    matrix_fields = [
        "topic",
        "adjacent_concept",
        "source_ids",
        "what_prior_work_establishes",
        "what_prior_work_does_not_establish",
        "project_distinction",
        "review_risk",
    ]
    write_csv(OUTPUT_FILES["evidence_matrix"], EVIDENCE_MATRIX, matrix_fields)

    claim_fields = [
        "claim_id",
        "claim_text",
        "support_type",
        "external_source_ids",
        "internal_source_boundary",
        "allowed_wording",
        "prohibited_extension",
    ]
    write_csv(OUTPUT_FILES["claim_map"], CLAIM_MAP, claim_fields)

    OUTPUT_FILES["novelty_analysis"].write_text(NOVELTY_ANALYSIS, encoding="utf-8")
    OUTPUT_FILES["related_work"].write_text(RELATED_WORK, encoding="utf-8")
    OUTPUT_FILES["verification_report"].write_text(VERIFICATION_REPORT, encoding="utf-8")
    OUTPUT_FILES["insertion_plan"].write_text(INSERTION_PLAN, encoding="utf-8")

    source_ids = [row["source_id"] for row in SOURCES]
    require(len(source_ids) == len(set(source_ids)), "Duplicate source_id found.")
    source_id_set = set(source_ids)

    resolution_ids = [row["placeholder_id"] for row in RESOLUTIONS]
    require(
        sorted(resolution_ids) == sorted(EXPECTED_PLACEHOLDERS),
        "Resolution map does not cover exactly the 10 committed placeholders.",
    )
    require(
        len(resolution_ids) == len(set(resolution_ids)),
        "A placeholder appears more than once in the resolution map.",
    )

    referenced_source_ids: set[str] = set()
    for row in RESOLUTIONS:
        referenced_source_ids.update(split_ids(row["primary_source_ids"]))
        referenced_source_ids.update(split_ids(row["adjacent_or_caution_source_ids"]))
    for row in EVIDENCE_MATRIX:
        referenced_source_ids.update(split_ids(row["source_ids"]))
    for row in CLAIM_MAP:
        referenced_source_ids.update(split_ids(row["external_source_ids"]))

    unknown_ids = sorted(referenced_source_ids - source_id_set)
    require(not unknown_ids, f"Unknown source IDs referenced: {unknown_ids}")

    central_placeholder_ids = set(EXPECTED_PLACEHOLDERS)
    authoritative_classes = {
        "peer_reviewed",
        "official_institutional",
        "official_institutional_consultation",
        "methods_book",
    }
    for placeholder in central_placeholder_ids:
        resolution = next(row for row in RESOLUTIONS if row["placeholder_id"] == placeholder)
        primary_ids = split_ids(resolution["primary_source_ids"])
        require(primary_ids, f"No primary sources assigned to {placeholder}")
        primary_rows = [row for row in SOURCES if row["source_id"] in primary_ids]
        require(
            any(row["source_class"] in authoritative_classes for row in primary_rows),
            f"{placeholder} lacks a peer-reviewed, official, or scholarly-method primary anchor.",
        )

    for row in SOURCES:
        if row["source_class"].startswith("preprint"):
            require(
                row["peer_review_status"] == "not_peer_reviewed_as_verified",
                f"Preprint incorrectly labelled: {row['source_id']}",
            )

    all_markdown = "\n".join(
        path.read_text(encoding="utf-8")
        for key, path in OUTPUT_FILES.items()
        if key in {
            "novelty_analysis",
            "related_work",
            "verification_report",
            "insertion_plan",
        }
    ).lower()

    prohibited_affirmative_phrases = [
        "this is the first study ever",
        "no prior work considers evidence sufficiency",
        "prior evaluation only measures final accuracy",
        "the framework proves general llm unreliability",
    ]
    found_prohibited = [
        phrase for phrase in prohibited_affirmative_phrases if phrase in all_markdown
    ]
    # Wording listed under explicit “should not be used” is allowed only in the novelty file.
    # Remove that section from the check rather than weakening the phrase boundary.
    novelty_without_forbidden_examples = NOVELTY_ANALYSIS.split(
        "## Wording that should not be used"
    )[0].lower()
    other_markdown = "\n".join(
        [RELATED_WORK, VERIFICATION_REPORT, INSERTION_PLAN]
    ).lower()
    checked_text = novelty_without_forbidden_examples + "\n" + other_markdown
    found_prohibited = [
        phrase for phrase in prohibited_affirmative_phrases if phrase in checked_text
    ]
    require(
        not found_prohibited,
        f"Prohibited affirmative novelty/overclaim wording detected: {found_prohibited}",
    )

    validation_lines = [
        "# Pilot 05AX Internal Validation Report",
        "",
        "status: PASS",
        "",
        f"- task_id: {TASK_ID}",
        f"- search_date: {SEARCH_DATE}",
        f"- committed_placeholder_count: {len(EXPECTED_PLACEHOLDERS)}",
        f"- resolution_row_count: {len(RESOLUTIONS)}",
        f"- verified_source_row_count: {len(SOURCES)}",
        f"- related_work_matrix_row_count: {len(EVIDENCE_MATRIX)}",
        f"- claim_to_source_row_count: {len(CLAIM_MAP)}",
        "- exact_placeholder_coverage: PASS",
        "- duplicate_placeholder_ids: 0",
        "- duplicate_source_ids: 0",
        "- unknown_source_references: 0",
        "- authoritative_primary_anchor_for_every_placeholder: PASS",
        "- preprint_status_labelling: PASS",
        "- prohibited_affirmative_overclaims: 0",
        "- manuscript_edits: NO",
        "- model_or_api_calls: NO",
        "- new_experiments: NO",
        "- raw_data_access: NO",
        "- jsonl_writing: NO",
        "- staging_commit_push: NO",
        "",
        "Novelty verdict: bounded combination-and-operationalization differentiation is supported; global priority is not established.",
    ]
    OUTPUT_FILES["validation_report"].write_text(
        "\n".join(validation_lines) + "\n", encoding="utf-8"
    )

    hash_targets = [Path(__file__).resolve()] + [
        path for key, path in OUTPUT_FILES.items() if key != "manifest"
    ]
    output_hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in hash_targets
    }

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_date": SEARCH_DATE,
        "secured_input_commit": "f05ae265706bff5e408ae80c35f07e019a850d4d",
        "source_boundary": {
            "committed_input": str(INPUT_REGISTER.relative_to(ROOT)).replace("\\", "/"),
            "external_literature_research": "targeted, source-verified, not systematic",
        },
        "counts": {
            "placeholders": len(EXPECTED_PLACEHOLDERS),
            "resolution_rows": len(RESOLUTIONS),
            "verified_source_rows": len(SOURCES),
            "evidence_matrix_rows": len(EVIDENCE_MATRIX),
            "claim_map_rows": len(CLAIM_MAP),
            "expected_uncommitted_files_including_script": 11,
        },
        "novelty_verdict": (
            "Bounded combination-and-operationalization differentiation supported; "
            "global priority or first-ever novelty not established."
        ),
        "safety": {
            "internet_literature_research_performed": True,
            "no_api_calls": True,
            "no_model_calls": True,
            "no_new_experiments": True,
            "no_raw_data_access": True,
            "no_env_access": True,
            "no_jsonl_writing": True,
            "no_manuscript_edits": True,
            "no_staging": True,
            "no_commit": True,
            "no_push": True,
        },
        "output_sha256_excluding_manifest": output_hashes,
        "notes": [
            "Internet browsing was used only for literature and official-source verification.",
            "No provider/model/data API was invoked.",
            "Preprints are explicitly labelled and must be rechecked for published versions before submission.",
            "External sources do not validate Pilot 05 empirical numbers; those remain bounded to committed internal artifacts.",
        ],
    }
    OUTPUT_FILES["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    expected_paths = [Path(__file__).resolve()] + list(OUTPUT_FILES.values())
    missing = [str(path) for path in expected_paths if not path.is_file()]
    require(not missing, f"Expected files missing after generation: {missing}")

    print("=== TASK 05AX GENERATION COMPLETE ===")
    print(f"status: PASS")
    print(f"verified_source_rows: {len(SOURCES)}")
    print(f"placeholder_resolution_rows: {len(RESOLUTIONS)}")
    print(f"evidence_matrix_rows: {len(EVIDENCE_MATRIX)}")
    print(f"claim_map_rows: {len(CLAIM_MAP)}")
    print("novelty_verdict: BOUNDED_DIFFERENTIATION_SUPPORTED_GLOBAL_PRIORITY_NOT_ESTABLISHED")
    print(f"output_dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
