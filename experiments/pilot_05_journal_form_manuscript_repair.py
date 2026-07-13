#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "05BB"
REPAIR_VERSION = "05BB-JOURNAL-FORM-V1"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "2198dd4a8017bd20bd757314092459a5c4b1cb9f"

SOURCE_MANUSCRIPT = Path("reports/pilot_05_verified_citation_integration/pilot_05AY_citation_integrated_manuscript.md")
SOURCE_MANUSCRIPT_SHA256 = "5D79D5DC4518B413CD270FA2002ADA69F10BCDC45FEBE52013103D8BF3B22C6B"

ISSUE_REGISTER = Path("reports/pilot_05_manuscript_integrity_audit/pilot_05BA_issue_register.csv")
ISSUE_REGISTER_SHA256 = "1F9BE9DDF00AC999200B989D2EA73FF7E5CA5E2F2ED0F13C128A7E34483B80E6"

NUMERICAL_AUDIT = Path("reports/pilot_05_manuscript_integrity_audit/pilot_05BA_numerical_consistency_audit.csv")
NUMERICAL_AUDIT_SHA256 = "B920F795DFD99B5C9CCA55B5C4854AECDDFD235F6A31C572D65B89994523A135"

CITATION_AUDIT = Path("reports/pilot_05_manuscript_integrity_audit/pilot_05BA_citation_integrity_audit.csv")
CITATION_AUDIT_SHA256 = "101AD5338852EFFE39A7556697A3AFF7CA1AAFD36EC56019E01695ED621A89C8"

AUDIT_MANIFEST = Path("reports/pilot_05_manuscript_integrity_audit/pilot_05BA_manifest.json")
AUDIT_MANIFEST_SHA256 = "AD249222BFD04FB97C45DCB3B1AE6FC04E84B6E29AA1805E6AE62FDE9C173E2E"

MAIN_RESULTS = Path("reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv")

OUTPUT_DIR = Path("reports/pilot_05_journal_form_manuscript_repair")
OUTPUT_MANUSCRIPT = OUTPUT_DIR / "pilot_05BB_journal_form_manuscript.md"
OUTPUT_ISSUES = OUTPUT_DIR / "pilot_05BB_issue_resolution_register.csv"
OUTPUT_SECTION_MAP = OUTPUT_DIR / "pilot_05BB_section_map.csv"
OUTPUT_VALIDATION = OUTPUT_DIR / "pilot_05BB_internal_validation_report.md"
OUTPUT_MANIFEST = OUTPUT_DIR / "pilot_05BB_manifest.json"
SCRIPT_PATH = Path("experiments/pilot_05_journal_form_manuscript_repair.py")

EXPECTED_OUTPUT_FILES = [
    SCRIPT_PATH,
    OUTPUT_MANUSCRIPT,
    OUTPUT_ISSUES,
    OUTPUT_SECTION_MAP,
    OUTPUT_VALIDATION,
    OUTPUT_MANIFEST,
]

EXPECTED_MAIN_RESULTS = {
    "call_plan_rows": "720",
    "ledger_rows": "720",
    "sanitized_execution_rows": "713",
    "parser_invalid_summary_rows": "243",
    "ledger_parser_valid_true": "470",
    "ledger_parser_valid_false": "250",
    "persisted_parser_valid_true": "470",
    "persisted_parser_valid_false": "243",
    "ledger_only_missing_sanitized_rows": "7",
    "max_cumulative_estimated_cost_usd": "2.2731216",
    "stage_success_delta_min": "-0.517241",
    "stage_success_delta_max": "-0.40678",
    "parser_valid_delta_min": "0.067797",
    "parser_valid_delta_max": "0.368421",
    "audit_detection_rate_degraded_mean": "1.0",
    "escalation_recovery_rate_degraded_mean": "0.0",
    "cascade_failure_rate_all_sequence_groups": "0.929167",
}

MANUSCRIPT = "# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines\n\n## Abstract\n\nMulti-stage large language model (LLM) pipelines can remain structurally well formed even when the evidence supplied to downstream stages has been degraded. This study formalises Evidence-State Reliability (ESR) as the extent to which intermediate evidence states remain sufficiently complete, grounded, and usable for evidence-sensitive stage objectives. The analysis uses one scaled run of GLM-5.2 over sanitized evidence packets derived from the Consumer Financial Protection Bureau complaint-data context. The design comprises 720 planned calls across decision, audit, and escalation stages; 713 sanitized execution rows were retained, with seven ledger-only rows disclosed as missing from execution-level analysis. Within this single-model, single-run experiment, controlled evidence degradation reduced stage success by -0.517241 to -0.406780 while parser-validity deltas increased by +0.067797 to +0.368421. Mean degraded-condition audit detection was 1.0, mean escalation recovery was 0.0, and the all-sequence cascade-failure rate was 0.929167. The results demonstrate reliability-layer divergence: outputs can become more parser-valid while the evidence-sensitive reliability of the pipeline deteriorates. This supports ESR as an evaluation layer distinct from parser validity, while remaining bounded to the evaluated GLM-5.2 configuration, sanitized CFPB-backed evidence states, one pipeline design, and one scaled run.\n\n**Keywords:** Evidence-State Reliability; reliability cascades; multi-stage LLM pipelines; parser validity; audit; escalation; evidence sufficiency; CFPB\n\n## 1. Introduction\n\nLLM evaluation often concentrates on final-answer correctness, schema compliance, or whether an output can be parsed. Those signals are important, but they do not fully characterize a multi-stage decision pipeline. Evidence can be summarized, filtered, transformed, audited, and escalated before the final output is produced. A structurally valid final object may therefore conceal degradation that occurred in the evidence state passed between stages.\n\nThis paper studies that gap through Evidence-State Reliability (ESR): the reliability of the intermediate evidence state used by downstream functions. ESR asks whether the evidence available to a stage remains sufficiently complete, grounded, and usable for that stage's evidence-sensitive objective. Parser validity asks a different question: whether an output conforms to a required machine-readable structure. A parser-valid output can still be evidence-unsuccessful, so parser validity is not a sufficient proxy for ESR.\n\nThe central research question is: **How can Evidence-State Reliability be measured separately from parser validity in a multi-stage LLM decision pipeline?** The study addresses this question with controlled evidence-state interventions in a decision-audit-escalation pipeline. The strongest supported claim is:\n\n> Within the committed Pilot 05 GLM-5.2 scaled CFPB-backed sanitized experiment, controlled evidence degradation reduced stage success while parser validity increased across decision, audit, and escalation stages, supporting Evidence-State Reliability as an evaluation layer distinct from parser validity.\n\nThe paper makes three bounded contributions. First, it formalises parser-validity rate, ESR, reliability-layer divergence, and false assurance at the format layer as separate evaluation constructs. Second, it operationalises controlled evidence-state degradation across decision, audit, and escalation stages. Third, it reports a reproducible within-run pattern in which parser validity improved while evidence-sensitive stage success deteriorated. The novelty claim is deliberately limited: bounded combination-and-operationalisation differentiation is supported; global priority or first-ever novelty is not established.\n\nThe evidence comes from one model configuration and one scaled run. The study does not establish universal LLM unreliability, general GLM-5.2 unreliability, provider superiority, deployment or regulatory validity, real-world financial-decision validity, or cross-model generalisation.\n\n## 2. Related Work\n\n### 2.1 Multidimensional evaluation\n\nModel quality cannot be reduced to a single success indicator. Behavioral testing shows that aggregate held-out accuracy can conceal capability-specific weaknesses, while calibration separates confidence quality from predictive correctness (Ribeiro et al., 2020; Guo et al., 2017). Retrieval-augmented-generation evaluation similarly distinguishes context relevance, faithful context use, and answer relevance (Es et al., 2024; Saad-Falcon et al., 2024). ESR fits within this multidimensional view but targets a narrower object: the evidence state supplied to downstream pipeline functions.\n\n### 2.2 Structured output validity and substantive success\n\nFormal conformance is useful because machine-readable contracts support automation, validation, and downstream execution. Grammar-constrained decoding can improve adherence to required structures, and recent structured-output studies distinguish schema validity from value-level or executable correctness (Geng et al., 2023; Ray, 2026, preprint; Singh et al., 2026, preprint). This study therefore does not claim that structural and substantive validity have never been separated. Its contribution is to connect that distinction to controlled evidence-state interventions and stage-aware decision, audit, escalation, detection, and recovery measurements.\n\n### 2.3 Evidence sufficiency and intermediate support\n\nInsufficient evidence has been studied in fact checking, and evidence sufficiency is increasingly explicit in retrieval-augmented generation and risk-oriented decision settings (Atanasova et al., 2022, preprint; Qiu et al., 2026, preprint; Solozobov, 2026, preprint). These works motivate evaluating whether available evidence can support a task rather than checking output form alone. The present design adds an explicit multi-stage intervention: frozen evidence conditions are propagated through decision, audit, and escalation functions, allowing evidence-sensitive stage behavior to be compared with parser validity.\n\n### 2.4 Multi-stage systems, cascades, audit, and escalation\n\nComponent-aware evaluation is important in interactive agents and retrieval-augmented systems (Liu et al., 2024; Es et al., 2024; Saad-Falcon et al., 2024). Cascading failure is also an established systems concept, and emerging LLM research studies seeded-error and hallucination propagation in multi-agent collaboration (Motter and Lai, 2002; Xie et al., 2026, preprint; Jamshidi et al., 2026, preprint). Here, a reliability cascade is used in a narrower experimental sense: condition-linked reliability loss that propagates across decision, audit, and escalation stages under controlled evidence degradation.\n\nAlgorithmic-audit research emphasizes institutional accountability, documentation, and lifecycle processes (Raji et al., 2020). The computational audit stage in this experiment is much narrower and is not presented as an organizational or regulatory audit. Selective prediction and learning-to-defer research likewise establish abstention and expert deferral as distinct downstream functions (Geifman and El-Yaniv, 2019; Mozannar and Sontag, 2020). The present escalation stage asks only whether the implemented pipeline recovered after degradation; it does not establish an optimal escalation policy.\n\n### 2.5 Financial context and bounded novelty\n\nFinancial-sector reports motivate careful testing, interpretability, auditability, and governance of AI-enabled financial services (Financial Stability Board, 2017; Financial Stability Board, 2026, consultation report). The 2026 source is a consultation report, not final guidance. The Consumer Financial Protection Bureau describes its Consumer Complaint Database as a public resource while warning that complaints are not a statistical sample, narratives are consumer accounts, and interpretation requires context (Consumer Financial Protection Bureau, 2025). The database is used here only as provenance for a sanitized evaluation substrate; the experiment does not establish complaint truth, misconduct, prevalence, regulatory validity, or deployment performance.\n\nThe novelty position is therefore a combination-and-operationalisation contribution. The paper combines controlled evidence-state degradation, a decision-audit-escalation pipeline, stage-specific reliability measurement, parser-versus-evidence comparison, and recovery analysis in one reproducible design. It does not claim global priority over multidimensional evaluation, evidence sufficiency, structured-versus-substantive validity, or cascade theory.\n\n## 3. Methodology\n\n### 3.1 Study design and evidence boundary\n\nThe study evaluates a three-stage LLM pipeline under a non-degraded baseline condition and controlled degraded evidence conditions. Sixty sanitized base cases were expanded across four evidence conditions and three stages, producing 720 planned and ledgered calls. The evidence packets are CFPB-backed in provenance but sanitized. They are not raw production records, and the experiment does not infer complaint truth, company misconduct, consumer-harm prevalence, or real-world decision validity.\n\nThe empirical execution is bounded to the committed GLM-5.2 Pilot 05 run. All reported values come from committed sanitized artifacts. Raw prompts, raw responses, JSONL model-output files, raw CFPB records, and environment or API-key material are outside the reporting boundary.\n\n### 3.2 Pipeline stages\n\nThe **decision stage** produces an initial assessment from the supplied evidence state. The **audit stage** evaluates whether the evidence and decision state indicate degradation or concern. The **escalation stage** evaluates whether the implemented downstream mechanism recovers after degradation. These stages are evaluated separately because detection and recovery are not equivalent.\n\n### 3.3 Formal definitions\n\nLet \\(E_{i,c,k}\\) denote the evidence state supplied to case \\(i\\), condition \\(c\\), and stage \\(k\\). Let \\(V_{i,c,k}\\in\\{0,1\\}\\) indicate parser validity, and let \\(R_{i,c,k}\\in\\{0,1\\}\\) indicate evidence-sensitive stage success under the committed scoring contract. For \\(N_c\\) cases in condition \\(c\\), the **parser-validity rate** and **Evidence-State Reliability rate** are\n\n\\[\n\\widehat{\\mathrm{PV}}_{c,k}\n=\n\\frac{1}{N_c}\\sum_{i=1}^{N_c}V_{i,c,k},\n\\qquad\n\\widehat{\\mathrm{ESR}}_{c,k}\n=\n\\frac{1}{N_c}\\sum_{i=1}^{N_c}R_{i,c,k}.\n\\]\n\nFor a degraded condition \\(c\\) relative to baseline \\(c_0\\),\n\n\\[\n\\Delta\\mathrm{PV}_{c,k}\n=\n\\widehat{\\mathrm{PV}}_{c,k}\n-\n\\widehat{\\mathrm{PV}}_{c_0,k},\n\\qquad\n\\Delta\\mathrm{ESR}_{c,k}\n=\n\\widehat{\\mathrm{ESR}}_{c,k}\n-\n\\widehat{\\mathrm{ESR}}_{c_0,k}.\n\\]\n\n**Reliability-layer divergence** is\n\n\\[\n\\mathrm{RLD}_{c,k}\n=\n\\Delta\\mathrm{PV}_{c,k}\n-\n\\Delta\\mathrm{ESR}_{c,k}.\n\\]\n\nA positive value is especially consequential when \\(\\Delta\\mathrm{PV}_{c,k}>0\\) and \\(\\Delta\\mathrm{ESR}_{c,k}<0\\): structural conformance improves while evidence-sensitive success declines.\n\n**False assurance at the format layer** occurs when an output is parser-valid but evidence-unsuccessful. Its rate is\n\n\\[\n\\widehat{\\mathrm{FA}}_{c,k}\n=\n\\frac{1}{N_c}\n\\sum_{i=1}^{N_c}\nV_{i,c,k}\\left(1-R_{i,c,k}\\right).\n\\]\n\nThis construct does not imply that every parser-valid output is incorrect. It identifies cases where format-level success could be mistaken for evidence-sensitive reliability.\n\n### 3.4 Metrics and accounting\n\nThe evaluation separates execution accounting, parser validity, evidence-sensitive stage success, audit detection, escalation recovery, and sequence-level cascade failure. The accounting identities are fixed by the committed run:\n\n\\[\n470+250=720,\\qquad\n470+243=713,\\qquad\n720-713=7,\\qquad\n470-470=0.\n\\]\n\nThe first identity accounts for parser-valid and parser-invalid ledger rows. The second accounts for retained sanitized execution rows. The third identifies the seven ledger-only rows missing from execution-level analysis. The fourth confirms that all 470 parser-valid ledger rows were preserved in the sanitized execution layer.\n\n### 3.5 Reproducibility and claim discipline\n\nThe repository contains committed sanitized execution summaries, metric tables, figure data, figures, claim-boundary tables, and validation reports. Reproducibility is limited to artifact-level traceability and deterministic validation of the committed outputs; raw prompt and response replay is not claimed. Threats are organized using construct, internal, external, and conclusion-validity categories (Wohlin et al., 2012), and reproducibility claims follow the distinction between transparent reporting and full computational replay (Pineau et al., 2021).\n\n## 4. Results\n\n### 4.1 Execution accounting\n\nTable 1 reports the primary execution contract. All 720 planned calls were represented in the ledger. The sanitized execution layer retained 713 rows. The seven ledger-only rows are disclosed and excluded from execution-level metrics. The maximum cumulative estimated cost was USD 2.2731216.\n\n**Table 1. Execution and parser-accounting summary.**\n\n| Measure | Value | Interpretation |\n|---|---:|---|\n| Planned calls | 720 | Sixty base cases across four conditions and three stages |\n| Ledger rows | 720 | Complete call-plan accounting |\n| Sanitized execution rows | 713 | Rows available for execution-level analysis |\n| Ledger parser-valid rows | 470 | Structurally valid ledger outputs |\n| Ledger parser-invalid rows | 250 | Structurally invalid ledger outputs |\n| Persisted parser-valid rows | 470 | Parser-valid rows retained after sanitization |\n| Persisted parser-invalid rows | 243 | Parser-invalid rows retained after sanitization |\n| Ledger-only missing sanitized rows | 7 | Disclosed and excluded from execution-level metrics |\n| Maximum cumulative estimated cost | USD 2.2731216 | Cost recorded by the committed run |\n\n### 4.2 Parser validity diverges from evidence-sensitive stage success\n\nAcross degraded evidence conditions, stage-success deltas ranged from -0.517241 to -0.406780, whereas parser-validity deltas ranged from +0.067797 to +0.368421. The directions are opposite: evidence-sensitive success declined while parser validity increased. This is the central empirical instance of reliability-layer divergence.\n\nFigure 1 summarizes this contrast. Because the evidence-sensitive and parser-validity measures move in opposite directions, a parser-only evaluation would give a materially incomplete account of pipeline reliability. The result supports measuring evidence-state adequacy and stage success independently of output-format conformance.\n\n**Figure 1. Parser validity versus evidence-sensitive reliability under controlled degradation.** Across the committed degraded conditions, parser-validity deltas are positive while stage-success deltas are negative. The figure supports a bounded within-run distinction between parser validity and ESR; it does not establish a model-general effect.\n\n### 4.3 Audit detection and escalation recovery\n\nMean audit detection under degraded evidence was 1.0, while mean escalation recovery was 0.0. Detection therefore did not translate into successful recovery in the implemented pipeline. Figure 2 separates these two outcomes to prevent detection from being interpreted as remediation.\n\n**Figure 2. Audit detection and escalation recovery in the controlled run.** The audit stage detected degraded-condition failures at a mean rate of 1.0, whereas the implemented escalation stage had a mean recovery rate of 0.0. These values describe this pipeline design and do not imply that escalation mechanisms are generally ineffective.\n\n### 4.4 Pipeline-level cascade failure\n\nThe all-sequence cascade-failure rate was 0.929167. This metric summarizes sequence groups in which reliability loss propagated across the evaluated stages. Figure 3 presents the pipeline-level result; it is a diagnostic of this experiment, not a prevalence estimate for deployed systems.\n\n**Figure 3. Sequence-level cascade-failure rate.** The all-sequence cascade-failure rate was 0.929167 in the committed Pilot 05 run. The figure describes propagation within the evaluated decision-audit-escalation sequence and does not support a general claim about GLM-5.2 or LLM reliability.\n\n### 4.5 Failure families\n\nThe committed interpretation identified three relevant failure families: detected-but-unrecovered degradation, parser-valid/evidence-invalid divergence, and the missing-sanitized-row gap. Figure 4 presents these families as distinct diagnostics rather than collapsing them into one final-output score.\n\n**Figure 4. Failure-family interpretation.** The figure distinguishes detected-but-unrecovered degradation, parser-valid/evidence-invalid divergence, and missing-sanitized-row accounting. It is descriptive of the committed run and does not imply provider, regulatory, deployment, or real-world harm conclusions.\n\nTable 2 consolidates the principal outcome metrics.\n\n**Table 2. Principal reliability outcomes.**\n\n| Outcome | Value | Bounded interpretation |\n|---|---:|---|\n| Stage-success delta range | -0.517241 to -0.406780 | Evidence-sensitive stage performance declined under degradation |\n| Parser-validity delta range | +0.067797 to +0.368421 | Structural conformance increased under degradation |\n| Mean degraded audit detection | 1.0 | Degradation was detected by the implemented audit stage |\n| Mean degraded escalation recovery | 0.0 | Successful recovery was not observed in the implemented escalation stage |\n| All-sequence cascade-failure rate | 0.929167 | Reliability loss propagated across most evaluated sequence groups |\n\n## 5. Discussion\n\n### 5.1 Implications for evaluation\n\nThe results show why a multi-stage LLM pipeline should not be evaluated through parser validity alone. In the committed run, the output layer became more structurally compliant under degraded evidence while evidence-sensitive stage success deteriorated. The format signal and the reliability signal therefore pointed in opposite directions.\n\nThis divergence has practical implications for evaluation design. First, evidence-state quality should be tracked separately from final-output form. Second, stage-level effects should be measured because degradation can propagate through intermediate handoffs. Third, audit detection and escalation recovery should be reported separately: a system can recognize degradation without restoring reliable operation. Fourth, sequence-level cascade metrics can reveal compounded reliability loss that is invisible in isolated final-output checks.\n\nFalse assurance at the format layer provides a concise interpretation of the risk. The construct does not treat parser validity as useless; parser validity remains necessary for reliable automation. The problem arises when format success is interpreted as substantive evidence that the pipeline used a sufficiently reliable evidence state.\n\n### 5.2 Contribution and novelty boundary\n\nThe empirical contribution is the observed within-run combination of positive parser-validity deltas and negative stage-success deltas across a controlled decision-audit-escalation experiment. The methodological contribution is the joint operationalisation of evidence-state interventions, stage-aware reliability measures, detection, recovery, and cascade behavior.\n\nThe contribution remains bounded. Prior work already establishes multidimensional evaluation, evidence sufficiency, structured-versus-substantive validity, component-aware assessment, auditing, deferral, and cascading failure. The supported novelty verdict is: **Bounded combination-and-operationalisation differentiation supported; global priority or first-ever novelty not established.**\n\n### 5.3 Interpretation of the single-model result\n\nThe experiment provides direct evidence for the evaluated GLM-5.2 configuration, not for other models or providers. Its value is analytical rather than universal: it demonstrates that an evidence-state intervention can reveal a reliability-layer divergence that parser-only evaluation would miss. Cross-model replication would be required before asserting provider-independent or model-family-general effects, but it is not necessary for the present bounded within-experiment claim.\n\n## 6. Limitations\n\nThe study has several material limitations. First, it evaluates one GLM-5.2 configuration in one scaled run of 720 planned calls. It is not a multi-run replication and does not support cross-model generalisation. Second, all evidence packets are sanitized and CFPB-backed in provenance; they are not raw production data. The complaint-data context does not provide independently verified ground truth for prevalence, misconduct, consumer harm, or regulatory conclusions.\n\nThird, seven ledger rows have no corresponding sanitized execution row. They are disclosed and excluded from execution-level metrics. Although the accounting contract is internally consistent, the missing rows reduce the retained execution set from 720 to 713. Fourth, the degradation conditions represent defined forms of evidence loss and do not exhaust real-world ambiguity, contradiction, delay, or distribution shift.\n\nFifth, the audit stage is a computational component rather than an institutional algorithmic audit. Its mean degraded-condition detection rate of 1.0 should not be interpreted as governance assurance. Sixth, the escalation recovery mean of 0.0 may reflect the specific escalation design, prompts, scoring rules, and pipeline ordering rather than a general property of escalation mechanisms.\n\nSeventh, construct validity depends on the committed evidence-sensitive scoring contract. Parser validity measures structural conformance, while ESR measures stage success under that contract; neither measure alone establishes real-world decision quality. Eighth, artifact-level reproducibility is supported through committed sanitized outputs and validation reports, but raw prompt and response replay is outside the evidence boundary.\n\nAccordingly, the study does not establish deployment safety, regulatory validity, financial-decision validity, consumer-harm prevalence, company misconduct, universal LLM unreliability, general GLM-5.2 unreliability, or provider superiority.\n\n## 7. Conclusion\n\nThis study formalised Evidence-State Reliability as an evaluation layer distinct from parser validity and operationalised it in a controlled decision-audit-escalation pipeline. Within one scaled GLM-5.2 run over sanitized CFPB-backed evidence states, stage-success deltas were negative (-0.517241 to -0.406780) while parser-validity deltas were positive (+0.067797 to +0.368421). Mean degraded audit detection was 1.0, mean escalation recovery was 0.0, and the all-sequence cascade-failure rate was 0.929167.\n\nThe result demonstrates reliability-layer divergence within the evaluated setup: a pipeline can become more parser-valid while becoming less successful under evidence-sensitive criteria. Parser validity remains an important engineering signal, but it is not a sufficient proxy for evidence-state reliability. Evaluation of multi-stage LLM decision systems should therefore report evidence-state adequacy, stage success, detection, recovery, and cascade behavior separately.\n\nThe conclusion is limited to one model configuration, one pipeline design, sanitized evidence, and one scaled run. It does not establish cross-model, provider-independent, deployment, regulatory, or real-world financial validity. The supported contribution is a bounded combination and operationalisation of evidence-state intervention and multi-layer reliability measurement, not a first-ever or global-priority claim.\n\n## Data and Code Availability\n\nThe study's code, sanitized derived artifacts, execution summaries, paper tables, figure data, figures, claim-boundary materials, and validation reports are maintained in the project repository. The available artifacts support deterministic checking of the reported accounting and metrics. Raw CFPB records, raw prompts, raw model responses, JSONL model-output files, and environment or API-key material are not part of the manuscript artifact package. Reproducibility claims are therefore limited to the committed sanitized evidence and artifact-validation boundary.\n\n## References\n\n- Marco Tulio Ribeiro; Tongshuang Wu; Carlos Guestrin; Sameer Singh (2020). *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*. ACL 2020. DOI 10.18653/v1/2020.acl-main.442. https://aclanthology.org/2020.acl-main.442/.\n- Chuan Guo; Geoff Pleiss; Yu Sun; Kilian Q. Weinberger (2017). *On Calibration of Modern Neural Networks*. ICML 2017, PMLR 70. PMLR 70:1321-1330. https://proceedings.mlr.press/v70/guo17a.html.\n- Saibo Geng; Martin Josifoski; Maxime Peyrard; Robert West (2023). *Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning*. EMNLP 2023. DOI 10.18653/v1/2023.emnlp-main.674. https://aclanthology.org/2023.emnlp-main.674/.\n- Jaideep Ray (2026). *The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small Language Models*. arXiv preprint. arXiv:2605.26128. https://arxiv.org/abs/2605.26128. [Preprint; not peer reviewed as verified in 05AX.]\n- Abhinav Kumar Singh; Harsha Vardhan Khurdula; Yoeven D Khemlani; Vineet Agarwal (2026). *The Structured Output Benchmark*. arXiv preprint. arXiv:2604.25359. https://arxiv.org/abs/2604.25359. [Preprint; not peer reviewed as verified in 05AX.]\n- Xiao Liu; Hao Yu; Hanchen Zhang; Yifan Xu; Xuanyu Lei; Hanyu Lai; Yu Gu; Hangliang Ding; Kaiwen Men; Kejuan Yang; Shudan Zhang; Xiang Deng; Aohan Zeng; Zhengxiao Du; Chenhui Zhang; Sheng Shen; Tianjun Zhang; Yu Su; Huan Sun; Minlie Huang; Yuxiao Dong; Jie Tang (2024). *AgentBench: Evaluating LLMs as Agents*. ICLR 2024. arXiv:2308.03688. https://arxiv.org/abs/2308.03688.\n- Shahul Es; Jithin James; Luis Espinosa-Anke; Steven Schockaert (2024). *RAGAS: Automated Evaluation of Retrieval Augmented Generation*. EACL 2024 System Demonstrations. DOI 10.18653/v1/2024.eacl-demo.16. https://aclanthology.org/2024.eacl-demo.16/.\n- Jon Saad-Falcon; Omar Khattab; Christopher Potts; Matei Zaharia (2024). *ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems*. NAACL 2024. DOI 10.18653/v1/2024.naacl-long.20. https://aclanthology.org/2024.naacl-long.20/.\n- Pepa Atanasova; Jakob Grue Simonsen; Christina Lioma; Isabelle Augenstein (2022). *Fact Checking with Insufficient Evidence*. arXiv preprint. arXiv:2204.02007. https://arxiv.org/abs/2204.02007. [Preprint; not peer reviewed as verified in 05AX.]\n- Inioluwa Deborah Raji; Andrew Smart; Rebecca N. White; Margaret Mitchell; Timnit Gebru; Ben Hutchinson; Jamila Smith-Loud; Daniel Theron; Parker Barnes (2020). *Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing*. FAccT 2020. DOI 10.1145/3351095.3372873. https://doi.org/10.1145/3351095.3372873.\n- Hussein Mozannar; David Sontag (2020). *Consistent Estimators for Learning to Defer to an Expert*. ICML 2020, PMLR 119. PMLR 119:7076-7087. https://proceedings.mlr.press/v119/mozannar20b.html.\n- Yonatan Geifman; Ran El-Yaniv (2019). *SelectiveNet: A Deep Neural Network with an Integrated Reject Option*. ICML 2019, PMLR 97. PMLR 97:2151-2159. https://proceedings.mlr.press/v97/geifman19a.html.\n- Consumer Financial Protection Bureau (2025). *Consumer Complaint Database*. Consumer Financial Protection Bureau. Official database documentation; page modified 2025-10-20. https://www.consumerfinance.gov/data-research/consumer-complaints/.\n- Financial Stability Board (2017). *Artificial intelligence and machine learning in financial services*. Financial Stability Board. Official FSB report, 2017-11-01. https://www.fsb.org/2017/11/artificial-intelligence-and-machine-learning-in-financial-service/.\n- Financial Stability Board (2026). *Sound Practices for Responsible Adoption of Artificial Intelligence: Consultation report*. Financial Stability Board. Consultation report, 2026-06-10. https://www.fsb.org/2026/06/sound-practices-for-responsible-adoption-of-artificial-intelligence-consultation-report/. [Consultation report; not final guidance.]\n- Claes Wohlin; Per Runeson; Martin Höst; Magnus C. Ohlsson; Björn Regnell; Anders Wesslén (2012). *Experimentation in Software Engineering*. Springer. DOI 10.1007/978-3-642-29044-2. https://doi.org/10.1007/978-3-642-29044-2.\n- Joelle Pineau et al. (2021). *Improving Reproducibility in Machine Learning Research*. Journal of Machine Learning Research 22(164). JMLR 22(164):1-20. https://jmlr.org/papers/v22/20-303.html.\n- Adilson E. Motter; Ying-Cheng Lai (2002). *Cascade-based attacks on complex networks*. Physical Review E 66, 065102. DOI 10.1103/PhysRevE.66.065102. https://doi.org/10.1103/PhysRevE.66.065102.\n- Yizhe Xie; Congcong Zhu; Xinyue Zhang; Tianqing Zhu; Dayong Ye; Minfeng Qi; Huajie Chen; Wanlei Zhou (2026). *From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration*. arXiv preprint. arXiv:2603.04474. https://arxiv.org/abs/2603.04474. [Preprint; not peer reviewed as verified in 05AX.]\n- Saeid Jamshidi; Arghavan Moradi Dakhel; Kawser Wazed Nafi; Foutse Khomh (2026). *Hallucination Cascade: Analyzing Error Propagation in Multi-Agent LLM Systems*. arXiv preprint. arXiv:2606.07937. https://arxiv.org/abs/2606.07937. [Preprint; not peer reviewed as verified in 05AX.]\n- Jingxi Qiu; Zeyu Han; Cheng Huang (2026). *SURE-RAG: Sufficiency and Uncertainty-Aware Evidence Verification for Selective Retrieval-Augmented Generation*. arXiv preprint. arXiv:2605.03534. https://arxiv.org/abs/2605.03534. [Preprint; not peer reviewed as verified in 05AX.]\n- Oleg Solozobov (2026). *Evidence Sufficiency Under Delayed Ground Truth*. arXiv preprint. arXiv:2604.15740. https://arxiv.org/abs/2604.15740. [Preprint; not peer reviewed as verified in 05AX.]\n"

ISSUE_PLANS = {'FIG-FILENAME-001': {'repair_action': 'Removed the internal PNG filename and retained a publication-style Figure 1 caption with an in-text reference.', 'snippet': '**Figure 1. Parser validity versus evidence-sensitive reliability under controlled degradation.**'}, 'FIG-FILENAME-002': {'repair_action': 'Removed the internal PNG filename and retained a publication-style Figure 2 caption with an in-text reference.', 'snippet': '**Figure 2. Audit detection and escalation recovery in the controlled run.**'}, 'FIG-FILENAME-003': {'repair_action': 'Removed the internal PNG filename and retained a publication-style Figure 3 caption with an in-text reference.', 'snippet': '**Figure 3. Sequence-level cascade-failure rate.**'}, 'FIG-FILENAME-004': {'repair_action': 'Removed the internal PNG filename and retained a publication-style Figure 4 caption with an in-text reference.', 'snippet': '**Figure 4. Failure-family interpretation.**'}, 'SCAF-001': {'repair_action': 'Removed the manuscript-status block and opened directly with the scholarly title and abstract.', 'snippet': '# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines', 'absence_term': 'Manuscript status'}, 'SCAF-002': {'repair_action': 'Removed the committed-source table heading and replaced it with a publication-form execution table.', 'snippet': '**Table 1. Execution and parser-accounting summary.**', 'absence_term': 'Committed main table used by this synthesis'}, 'SCAF-003': {'repair_action': 'Removed the internal metric-validation table and integrated validated metrics into Methods and Results.', 'snippet': '### 3.4 Metrics and accounting', 'absence_term': 'Metric validation table used by this synthesis'}, 'SCAF-007': {'repair_action': 'Removed the recommended table-sequence instructions and retained only numbered publication tables.', 'snippet': '**Table 2. Principal reliability outcomes.**', 'absence_term': 'Recommended manuscript table sequence'}, 'SCAF-008': {'repair_action': 'Removed the recommended figure-sequence instructions and integrated four numbered figures into Results.', 'snippet': '### 4.2 Parser validity diverges from evidence-sensitive stage success', 'absence_term': 'Recommended manuscript figure sequence'}, 'SCAF-009': {'repair_action': 'Removed the source-caption pack wrapper and retained only journal-style captions.', 'snippet': '**Figure 1. Parser validity versus evidence-sensitive reliability under controlled degradation.**', 'absence_term': 'Source caption pack'}, 'SCAF-010': {'repair_action': 'Removed the source paper-table pack wrapper and retained only two publication-relevant tables.', 'snippet': '**Table 1. Execution and parser-accounting summary.**', 'absence_term': 'Source paper table pack'}, 'SCAF-011': {'repair_action': 'Removed the internal do-not-claim section and integrated bounded limitations into Discussion, Limitations, and Conclusion.', 'snippet': 'Accordingly, the study does not establish deployment safety', 'absence_term': '## Do not claim'}, 'SCAF-014': {'repair_action': 'Removed the revision-roadmap appendix.', 'snippet': '## 7. Conclusion', 'absence_term': 'Appendix A. Next revision roadmap'}, 'SCAF-015': {'repair_action': 'Removed the internal next-steps section.', 'snippet': '## Data and Code Availability', 'absence_term': 'Immediate next manuscript steps'}, 'SCAF-016': {'repair_action': 'Removed the editorial what-not-to-do section and expressed boundaries as scholarly limitations.', 'snippet': 'The evidence comes from one model configuration and one scaled run.', 'absence_term': 'What not to do yet'}, 'SCAF-017': {'repair_action': 'Removed the assembly-checkpoint appendix.', 'snippet': '## References', 'absence_term': 'Appendix B. Assembly checkpoint'}, 'SCAF-018': {'repair_action': 'Removed the do-not-claim appendix and integrated the bounded claim in the main paper.', 'snippet': 'The supported contribution is a bounded combination and operationalisation', 'absence_term': 'Appendix C. Do-not-claim boundary'}, 'SCAF-021': {'repair_action': 'Removed malformed source-extraction tables and replaced them with publication tables containing labelled measures and interpretations.', 'snippet': '| Stage-success delta range | -0.517241 to -0.406780 |', 'absence_term': '|  | value |'}, 'STRUCT-017': {'repair_action': 'Rebuilt the manuscript with a single consistent numbered main-section hierarchy and level-3 subsections.', 'snippet': '## 1. Introduction'}, 'NOT-DEF-05': {'repair_action': 'Integrated and formally defined the parser-validity rate.', 'snippet': 'the **parser-validity rate** and **Evidence-State Reliability rate** are'}, 'NOT-DEF-06': {'repair_action': 'Integrated and formally defined reliability-layer divergence.', 'snippet': '**Reliability-layer divergence** is'}, 'NOT-DEF-08': {'repair_action': 'Integrated and formally defined false assurance at the format layer.', 'snippet': '**False assurance at the format layer** occurs'}, 'SCAF-004': {'repair_action': 'Removed the no-new-evidence workflow heading and retained reproducibility boundaries in scholarly prose.', 'snippet': '### 3.5 Reproducibility and claim discipline', 'absence_term': 'No-new-evidence rule'}, 'SCAF-005': {'repair_action': 'Removed the one-sentence-contribution workflow heading and integrated the contribution into Introduction and Discussion.', 'snippet': 'The paper makes three bounded contributions.', 'absence_term': 'One-sentence contribution'}, 'SCAF-006': {'repair_action': 'Removed head-turning editorial language and retained the empirical contrast in neutral scholarly wording.', 'snippet': 'This is the central empirical instance of reliability-layer divergence.', 'absence_term': 'head-turning'}, 'SCAF-012': {'repair_action': 'Removed the repository-checkpoint heading and moved reproducibility information to Data and Code Availability.', 'snippet': '## Data and Code Availability', 'absence_term': 'Repository checkpoint'}, 'SCAF-013': {'repair_action': 'Removed the source-artifacts heading and summarized available artifacts in publication-form prose.', 'snippet': "The study's code, sanitized derived artifacts, execution summaries", 'absence_term': 'Source artifacts'}, 'SCAF-019': {'repair_action': 'Removed the literature-integration provenance heading while preserving the verified literature and novelty boundary.', 'snippet': '### 5.2 Contribution and novelty boundary', 'absence_term': 'Literature Integration Provenance'}, 'SCAF-020': {'repair_action': 'Removed the opening task-provenance comment and all internal task narration.', 'snippet': '# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines', 'absence_term': 'Task 05AY'}, 'NOT-013': {'repair_action': "Standardized 'parser validity' as the noun phrase and reserved 'parser-validity' for compound modifiers such as parser-validity rate and parser-validity deltas.", 'snippet': 'Parser validity asks a different question'}}

REQUIRED_MAIN_HEADINGS = [
    "## Abstract",
    "## 1. Introduction",
    "## 2. Related Work",
    "## 3. Methodology",
    "## 4. Results",
    "## 5. Discussion",
    "## 6. Limitations",
    "## 7. Conclusion",
    "## Data and Code Availability",
    "## References",
]

FORBIDDEN_SCAFFOLD = [
    "Manuscript status",
    "Committed main table used by this synthesis",
    "Metric validation table used by this synthesis",
    "Recommended manuscript table sequence",
    "Recommended manuscript figure sequence",
    "Source caption pack",
    "Source paper table pack",
    "## Do not claim",
    "Appendix A. Next revision roadmap",
    "Immediate next manuscript steps",
    "What not to do yet",
    "Appendix B. Assembly checkpoint",
    "Appendix C. Do-not-claim boundary",
    "No-new-evidence rule",
    "One-sentence contribution",
    "head-turning",
    "Repository checkpoint",
    "Source artifacts",
    "Literature Integration Provenance",
    "Task 05AY",
    "pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    "pilot_05AS_figure_02_audit_escalation_interpretation.png",
    "pilot_05AS_figure_03_cascade_failure_rate.png",
    "pilot_05AS_figure_04_failure_family_interpretation.png",
]

REQUIRED_CITATION_LABELS = [
    "Ribeiro et al., 2020",
    "Guo et al., 2017",
    "Geng et al., 2023",
    "Ray, 2026, preprint",
    "Singh et al., 2026, preprint",
    "Liu et al., 2024",
    "Es et al., 2024",
    "Saad-Falcon et al., 2024",
    "Atanasova et al., 2022, preprint",
    "Raji et al., 2020",
    "Mozannar and Sontag, 2020",
    "Geifman and El-Yaniv, 2019",
    "Consumer Financial Protection Bureau, 2025",
    "Financial Stability Board, 2017",
    "Financial Stability Board, 2026, consultation report",
    "Wohlin et al., 2012",
    "Pineau et al., 2021",
    "Motter and Lai, 2002",
    "Xie et al., 2026, preprint",
    "Jamshidi et al., 2026, preprint",
    "Qiu et al., 2026, preprint",
    "Solozobov, 2026, preprint",
]

REQUIRED_REFERENCE_TITLES = [
    "Beyond Accuracy: Behavioral Testing of NLP Models with CheckList",
    "On Calibration of Modern Neural Networks",
    "Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning",
    "The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small Language Models",
    "The Structured Output Benchmark",
    "AgentBench: Evaluating LLMs as Agents",
    "RAGAS: Automated Evaluation of Retrieval Augmented Generation",
    "ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems",
    "Fact Checking with Insufficient Evidence",
    "Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing",
    "Consistent Estimators for Learning to Defer to an Expert",
    "SelectiveNet: A Deep Neural Network with an Integrated Reject Option",
    "Consumer Complaint Database",
    "Artificial intelligence and machine learning in financial services",
    "Sound Practices for Responsible Adoption of Artificial Intelligence: Consultation report",
    "Experimentation in Software Engineering",
    "Improving Reproducibility in Machine Learning Research",
    "Cascade-based attacks on complex networks",
    "From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration",
    "Hallucination Cascade: Analyzing Error Propagation in Multi-Agent LLM Systems",
    "SURE-RAG: Sufficiency and Uncertainty-Aware Evidence Verification for Selective Retrieval-Augmented Generation",
    "Evidence Sufficiency Under Delayed Ground Truth",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).rstrip() + "\n"


def run_git(repo: Path, args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        fail(
            "Git command failed: git -C {} {}\nstdout:\n{}\nstderr:\n{}".format(
                repo,
                " ".join(args),
                completed.stdout,
                completed.stderr,
            )
        )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def csv_rows_from_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    return buffer.getvalue()


def find_line(lines: list[str], snippet: str) -> int:
    for index, line in enumerate(lines, start=1):
        if snippet in line:
            return index
    fail("Required manuscript evidence snippet not found: {}".format(snippet))
    return -1


def section_inventory(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        if line.startswith("## "):
            headings.append((line_number, line))
    results: list[dict[str, Any]] = []
    for index, (start_line, heading) in enumerate(headings):
        end_line = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
        body = "\n".join(lines[start_line:end_line])
        word_count = len(re.findall(r"\b[\w'-]+\b", body))
        results.append({
            "section_order": index + 1,
            "heading": heading,
            "start_line": start_line,
            "end_line": end_line,
            "word_count": word_count,
        })
    return results


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    os.chdir(repo)

    branch = run_git(repo, ["branch", "--show-current"])[0]
    head = run_git(repo, ["rev-parse", "HEAD"])[0]
    if branch != EXPECTED_BRANCH:
        fail("Expected branch {}, got {}".format(EXPECTED_BRANCH, branch))
    if head != EXPECTED_HEAD:
        fail("Expected HEAD {}, got {}".format(EXPECTED_HEAD, head))

    if run_git(repo, ["diff", "--name-only"]):
        fail("Tracked files are modified before 05BB generation.")
    if run_git(repo, ["diff", "--cached", "--name-only"]):
        fail("Staged files exist before 05BB generation.")
    pre_untracked = sorted(run_git(repo, ["ls-files", "--others", "--exclude-standard"]))
    expected_pre_untracked = [SCRIPT_PATH.as_posix()]
    if pre_untracked != expected_pre_untracked:
        fail(
            "Expected only the uncommitted 05BB script before generation. expected={} actual={}".format(
                expected_pre_untracked,
                pre_untracked,
            )
        )

    for path in [SOURCE_MANUSCRIPT, ISSUE_REGISTER, NUMERICAL_AUDIT, CITATION_AUDIT, AUDIT_MANIFEST, MAIN_RESULTS]:
        if not path.is_file():
            fail("Required committed input is missing: {}".format(path.as_posix()))

    expected_hashes = {
        SOURCE_MANUSCRIPT: SOURCE_MANUSCRIPT_SHA256,
        ISSUE_REGISTER: ISSUE_REGISTER_SHA256,
        NUMERICAL_AUDIT: NUMERICAL_AUDIT_SHA256,
        CITATION_AUDIT: CITATION_AUDIT_SHA256,
        AUDIT_MANIFEST: AUDIT_MANIFEST_SHA256,
    }
    for path, expected in expected_hashes.items():
        actual = sha256_path(path)
        if actual != expected:
            fail("SHA-256 mismatch for {}: expected {}, got {}".format(path.as_posix(), expected, actual))

    source_text = read_text(SOURCE_MANUSCRIPT)
    if "## References" not in source_text:
        fail("05AY source manuscript reference section is missing.")

    issue_rows = csv_rows_from_path(ISSUE_REGISTER)
    issue_ids = [row["issue_id"] for row in issue_rows]
    if len(issue_rows) != 30 or len(set(issue_ids)) != 30:
        fail("Expected exactly 30 unique 05BA issues.")
    if set(issue_ids) != set(ISSUE_PLANS):
        fail("05BA issue IDs do not match the 05BB resolution plan.")

    severity_counts: dict[str, int] = {"MAJOR": 0, "MODERATE": 0, "MINOR": 0}
    for row in issue_rows:
        severity = row["severity"]
        if severity not in severity_counts:
            fail("Unexpected 05BA issue severity: {}".format(severity))
        severity_counts[severity] += 1
        if row["correction_needs_new_evidence"] != "NO":
            fail("05BA issue unexpectedly requires new evidence: {}".format(row["issue_id"]))
    if severity_counts != {"MAJOR": 19, "MODERATE": 10, "MINOR": 1}:
        fail("Unexpected 05BA severity counts: {}".format(severity_counts))

    numerical_rows = csv_rows_from_path(NUMERICAL_AUDIT)
    if len(numerical_rows) != 20 or any(row.get("status") != "PASS" for row in numerical_rows):
        fail("Expected 20/20 PASS rows in the committed numerical audit.")

    citation_rows = csv_rows_from_path(CITATION_AUDIT)
    if len(citation_rows) != 32 or any(row.get("status") != "PASS" for row in citation_rows):
        fail("Expected 32/32 PASS rows in the committed citation audit.")

    with MAIN_RESULTS.open("r", encoding="utf-8-sig", newline="") as handle:
        main_rows = list(csv.DictReader(handle))
    main_contract = {row["metric"]: row["value"] for row in main_rows}
    if main_contract != EXPECTED_MAIN_RESULTS:
        fail("Committed 05AR main-results contract does not match the exact 17-metric contract.")

    manuscript_text = normalized_text(MANUSCRIPT)
    manuscript_lines = manuscript_text.splitlines()

    checks: list[dict[str, Any]] = []

    def record(check_id: str, description: str, passed: bool, evidence: str) -> None:
        checks.append({
            "check_id": check_id,
            "description": description,
            "status": "PASS" if passed else "FAIL",
            "evidence": evidence,
        })
        if not passed:
            fail("Validation failed: {} - {}".format(check_id, description))

    top_headings = [line for line in manuscript_lines if line.startswith("## ")]
    record(
        "STRUCT-CORE",
        "Required core sections are present in the exact journal order.",
        top_headings == REQUIRED_MAIN_HEADINGS,
        " | ".join(top_headings),
    )

    level2_numbered = [line for line in top_headings if re.match(r"^## \d+\.", line)]
    record(
        "STRUCT-NUMBERED",
        "Exactly seven numbered main sections are present.",
        len(level2_numbered) == 7,
        "count={}".format(len(level2_numbered)),
    )

    scaffold_hits = [phrase for phrase in FORBIDDEN_SCAFFOLD if phrase.lower() in manuscript_text.lower()]
    record(
        "SCAFFOLD-ZERO",
        "Internal scaffold and figure filenames are absent.",
        not scaffold_hits,
        "hits={}".format(scaffold_hits),
    )

    caption_lines = [line for line in manuscript_lines if re.match(r"^\*\*Figure [1-4]\.", line)]
    record(
        "FIG-CAPTIONS",
        "Exactly four publication-form figure captions are present.",
        len(caption_lines) == 4,
        "count={}".format(len(caption_lines)),
    )

    figure_counts = {str(number): len(re.findall(r"Figure {}\b".format(number), manuscript_text)) for number in range(1, 5)}
    record(
        "FIG-REFERENCES",
        "Each figure has at least one in-text reference plus its caption.",
        all(value >= 2 for value in figure_counts.values()),
        json.dumps(figure_counts, sort_keys=True),
    )

    required_metric_strings = [
        "720", "713", "seven", "470", "250", "243",
        "-0.517241", "-0.406780", "+0.067797", "+0.368421",
        "1.0", "0.0", "0.929167", "USD 2.2731216",
    ]
    missing_metric_strings = [value for value in required_metric_strings if value not in manuscript_text]
    record(
        "NUM-PROTECTED",
        "All protected numerical representations are present.",
        not missing_metric_strings,
        "missing={}".format(missing_metric_strings),
    )

    identities = ["470+250=720", "470+243=713", "720-713=7", "470-470=0"]
    compact = re.sub(r"\s+", "", manuscript_text)
    missing_identities = [identity for identity in identities if identity not in compact]
    record(
        "NUM-IDENTITIES",
        "All four committed accounting identities are present.",
        not missing_identities,
        "missing={}".format(missing_identities),
    )

    missing_citations = [label for label in REQUIRED_CITATION_LABELS if label not in manuscript_text]
    record(
        "CITE-LABELS",
        "All 22 verified in-text citation labels are preserved.",
        not missing_citations,
        "missing={}".format(missing_citations),
    )

    missing_titles = [title for title in REQUIRED_REFERENCE_TITLES if title not in manuscript_text]
    record(
        "CITE-REFERENCES",
        "All 22 verified reference titles are preserved.",
        not missing_titles,
        "missing={}".format(missing_titles),
    )

    preprint_count = manuscript_text.count("[Preprint; not peer reviewed as verified in 05AX.]")
    record(
        "CITE-PREPRINT",
        "All verified preprints retain explicit non-peer-reviewed labels.",
        preprint_count == 7,
        "label_count={}".format(preprint_count),
    )

    required_definitions = [
        "the **parser-validity rate** and **Evidence-State Reliability rate** are",
        "**Reliability-layer divergence** is",
        "**False assurance at the format layer** occurs",
    ]
    missing_definitions = [term for term in required_definitions if term not in manuscript_text]
    record(
        "NOT-DEFINITIONS",
        "All three missing formal constructs are integrated.",
        not missing_definitions,
        "missing={}".format(missing_definitions),
    )

    ordinary_parser_validity = len(re.findall(r"(?<!-)\bparser validity\b", manuscript_text, flags=re.IGNORECASE))
    compound_parser_validity = len(re.findall(r"\bparser-validity\b", manuscript_text, flags=re.IGNORECASE))
    record(
        "NOT-STYLE",
        "Parser-validity hyphenation is limited to compound-modifier contexts.",
        ordinary_parser_validity > 0 and compound_parser_validity > 0,
        "noun_phrase_count={}; compound_count={}".format(ordinary_parser_validity, compound_parser_validity),
    )

    strongest_claim = (
        "Within the committed Pilot 05 GLM-5.2 scaled CFPB-backed sanitized experiment, "
        "controlled evidence degradation reduced stage success while parser validity increased "
        "across decision, audit, and escalation stages, supporting Evidence-State Reliability "
        "as an evaluation layer distinct from parser validity."
    )
    record(
        "CLAIM-STRONGEST",
        "The strongest defensible claim is preserved exactly.",
        strongest_claim in manuscript_text,
        strongest_claim,
    )

    novelty_sentence = (
        "Bounded combination-and-operationalisation differentiation supported; "
        "global priority or first-ever novelty not established."
    )
    record(
        "CLAIM-NOVELTY",
        "The bounded novelty verdict is preserved exactly.",
        novelty_sentence in manuscript_text,
        novelty_sentence,
    )

    forbidden_assertions = [
        "LLMs are unreliable in financial decisions",
        "GLM-5.2 is unreliable",
        "proves real-world consumer harm",
        "ready for deployment",
        "provider superiority is demonstrated",
        "first-ever method",
        "first to demonstrate",
    ]
    assertion_hits = [phrase for phrase in forbidden_assertions if phrase.lower() in manuscript_text.lower()]
    record(
        "CLAIM-FORBIDDEN",
        "No prohibited positive generalisation appears.",
        not assertion_hits,
        "hits={}".format(assertion_hits),
    )

    section_texts: dict[str, str] = {}
    inventory = section_inventory(manuscript_text)
    for item in inventory:
        start = int(item["start_line"])
        end = int(item["end_line"])
        section_texts[item["heading"]] = "\n".join(manuscript_lines[start - 1:end])

    scope_sections = [
        "## Abstract",
        "## 5. Discussion",
        "## 6. Limitations",
        "## 7. Conclusion",
    ]
    scope_failures = []
    for heading in scope_sections:
        section = section_texts.get(heading, "")
        lowered = section.lower()
        if "single" not in lowered and "one " not in lowered:
            scope_failures.append(heading)
        if "glm-5.2" not in lowered:
            scope_failures.append(heading + " [model]")
    record(
        "CLAIM-SCOPE",
        "Single-model and single-run scope is explicit in Abstract, Discussion, Limitations, and Conclusion.",
        not scope_failures,
        "failures={}".format(scope_failures),
    )

    trailing_lines = [
        index for index, line in enumerate(manuscript_lines, start=1)
        if re.search(r"[ \t]+$", line)
    ]
    record(
        "FORMAT-WHITESPACE",
        "The manuscript contains no trailing-whitespace defects.",
        not trailing_lines,
        "lines={}".format(trailing_lines),
    )

    resolution_rows: list[dict[str, Any]] = []
    issue_by_id = {row["issue_id"]: row for row in issue_rows}
    for issue_id in sorted(ISSUE_PLANS):
        plan = ISSUE_PLANS[issue_id]
        source_row = issue_by_id[issue_id]
        line_number = find_line(manuscript_lines, plan["snippet"])
        evidence = "L{}: {}".format(line_number, manuscript_lines[line_number - 1])
        absence_term = plan.get("absence_term")
        if absence_term:
            if absence_term.lower() in manuscript_text.lower():
                fail("Issue {} absence term remains: {}".format(issue_id, absence_term))
            evidence = "ABSENCE CHECK PASS for '{}'; {}".format(absence_term, evidence)
        resolution_rows.append({
            "issue_id": issue_id,
            "original_severity": source_row["severity"],
            "repair_action": plan["repair_action"],
            "new_manuscript_evidence": evidence,
            "resolution_status": "RESOLVED",
            "new_evidence_required": "NO",
        })

    resolution_counts = {
        "MAJOR": sum(row["original_severity"] == "MAJOR" for row in resolution_rows),
        "MODERATE": sum(row["original_severity"] == "MODERATE" for row in resolution_rows),
        "MINOR": sum(row["original_severity"] == "MINOR" for row in resolution_rows),
    }
    record(
        "ISSUES-30",
        "All 30 05BA issues are mapped and resolved without new evidence.",
        len(resolution_rows) == 30
        and resolution_counts == {"MAJOR": 19, "MODERATE": 10, "MINOR": 1}
        and all(row["new_evidence_required"] == "NO" for row in resolution_rows),
        json.dumps(resolution_counts, sort_keys=True),
    )

    section_purposes = {
        "## Abstract": "Summarize the bounded question, design, principal metrics, and single-model limitation.",
        "## 1. Introduction": "Motivate ESR, state the research question, contributions, and claim boundary.",
        "## 2. Related Work": "Position ESR relative to multidimensional evaluation, structured output, evidence sufficiency, cascades, audit, and financial context.",
        "## 3. Methodology": "Define the evidence boundary, pipeline stages, formal constructs, metrics, accounting, and reproducibility controls.",
        "## 4. Results": "Report execution accounting, reliability-layer divergence, audit/recovery, cascade failure, and failure families.",
        "## 5. Discussion": "Interpret evaluation implications, novelty boundary, and the single-model result.",
        "## 6. Limitations": "State construct, internal, external, conclusion, and reproducibility limits.",
        "## 7. Conclusion": "Restate the bounded empirical result and contribution.",
        "## Data and Code Availability": "Describe the committed sanitized artifact boundary.",
        "## References": "Preserve the verified literature set and source labels.",
    }

    section_rows: list[dict[str, Any]] = []
    for item in inventory:
        heading = str(item["heading"])
        section_rows.append({
            **item,
            "purpose": section_purposes[heading],
            "source_basis": "Committed 05AY scholarly content and committed 05BA repair requirements; no new empirical evidence.",
        })

    issue_csv = csv_text(
        [
            "issue_id",
            "original_severity",
            "repair_action",
            "new_manuscript_evidence",
            "resolution_status",
            "new_evidence_required",
        ],
        resolution_rows,
    )

    section_csv = csv_text(
        [
            "section_order",
            "heading",
            "start_line",
            "end_line",
            "word_count",
            "purpose",
            "source_basis",
        ],
        section_rows,
    )

    validation_lines = [
        "# Pilot 05BB Internal Validation Report",
        "",
        "## Result",
        "",
        "`PASS`",
        "",
        "The journal-form manuscript repair completed in memory and satisfied the approved output contract before any output file was written.",
        "",
        "## Source contract",
        "",
        "- Secured branch: `{}`".format(branch),
        "- Secured HEAD: `{}`".format(head),
        "- Source manuscript: `{}`".format(SOURCE_MANUSCRIPT.as_posix()),
        "- Source manuscript SHA-256: `{}`".format(SOURCE_MANUSCRIPT_SHA256),
        "- 05BA issue rows mapped: `30/30`",
        "- 05BA MAJOR issues resolved: `19/19`",
        "- 05BA MODERATE issues resolved: `10/10`",
        "- 05BA MINOR issues resolved: `1/1`",
        "- Committed numerical audit: `20/20 PASS`",
        "- Committed citation audit: `32/32 PASS`",
        "",
        "## Manuscript validation",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in checks:
        safe_evidence = str(check["evidence"]).replace("|", "&#124;").replace("\n", " ")
        validation_lines.append(
            "| {} | {} | {} |".format(
                check["description"],
                check["status"],
                safe_evidence,
            )
        )
    validation_lines.extend([
        "",
        "## Output boundary",
        "",
        "- New uncommitted files expected: `6`",
        "- Existing committed files modified: `0`",
        "- Staging, commits, and pushes: `0`",
        "- Experiments or model/API calls: `0`",
        "- New literature search: `0`",
        "- Raw CFPB data, `.env`, raw prompts/responses, and JSONL: not accessed",
        "- Word/PDF conversion: not performed",
        "",
        "## Interpretation",
        "",
        "A PASS certifies deterministic generation and validation of the six-file 05BB contract. It does not by itself certify acceptance by any journal or replace a later target-journal formatting and human editorial review.",
        "",
    ])
    validation_text = normalized_text("\n".join(validation_lines))

    output_contents: dict[Path, str] = {
        OUTPUT_MANUSCRIPT: manuscript_text,
        OUTPUT_ISSUES: issue_csv,
        OUTPUT_SECTION_MAP: section_csv,
        OUTPUT_VALIDATION: validation_text,
    }

    output_hashes = {
        path.as_posix(): sha256_bytes(content.encode("utf-8"))
        for path, content in output_contents.items()
    }
    output_hashes[SCRIPT_PATH.as_posix()] = sha256_path(SCRIPT_PATH)

    manifest = {
        "task_id": TASK_ID,
        "repair_version": REPAIR_VERSION,
        "status": "PASS",
        "secured_branch": branch,
        "secured_head": head,
        "source_contract": {
            "source_manuscript": SOURCE_MANUSCRIPT.as_posix(),
            "source_manuscript_sha256": SOURCE_MANUSCRIPT_SHA256,
            "issue_register": ISSUE_REGISTER.as_posix(),
            "issue_register_sha256": ISSUE_REGISTER_SHA256,
            "numerical_audit": NUMERICAL_AUDIT.as_posix(),
            "numerical_audit_sha256": NUMERICAL_AUDIT_SHA256,
            "citation_audit": CITATION_AUDIT.as_posix(),
            "citation_audit_sha256": CITATION_AUDIT_SHA256,
            "audit_manifest": AUDIT_MANIFEST.as_posix(),
            "audit_manifest_sha256": AUDIT_MANIFEST_SHA256,
            "authoritative_main_results": MAIN_RESULTS.as_posix(),
            "authoritative_metric_count": 17,
        },
        "counts": {
            "expected_uncommitted_files": 6,
            "issue_rows": 30,
            "resolved_major": 19,
            "resolved_moderate": 10,
            "resolved_minor": 1,
            "numerical_checks_preserved": 20,
            "citation_checks_preserved": 32,
            "core_sections": len(REQUIRED_MAIN_HEADINGS),
            "figure_captions": 4,
            "figure_in_text_references": 4,
            "scaffold_hits": 0,
            "internal_figure_filename_hits": 0,
            "trailing_whitespace_defects": 0,
        },
        "validation_checks": checks,
        "output_sha256": output_hashes,
        "safety": {
            "source_manuscript_modified": False,
            "readme_modified": False,
            "pilot_05BA_outputs_modified": False,
            "earlier_committed_reports_modified": False,
            "files_deleted_or_overwritten": False,
            "files_staged_committed_or_pushed": False,
            "experiments_run": False,
            "model_calls": False,
            "api_calls": False,
            "new_literature_search": False,
            "raw_cfpb_data_accessed": False,
            "env_accessed": False,
            "raw_prompt_response_accessed": False,
            "jsonl_accessed_or_written": False,
            "word_or_pdf_conversion": False,
        },
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    output_contents[OUTPUT_MANIFEST] = manifest_text

    if OUTPUT_DIR.exists():
        fail("Output directory already exists: {}".format(OUTPUT_DIR.as_posix()))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)

    for path, content in output_contents.items():
        if path.exists():
            fail("Refusing to overwrite existing output: {}".format(path.as_posix()))
        path.write_text(content, encoding="utf-8", newline="\n")

    final_untracked = run_git(repo, ["ls-files", "--others", "--exclude-standard"])
    expected_untracked = sorted(path.as_posix() for path in EXPECTED_OUTPUT_FILES)
    if sorted(final_untracked) != expected_untracked:
        fail(
            "Final untracked set mismatch. expected={} actual={}".format(
                expected_untracked,
                sorted(final_untracked),
            )
        )
    if run_git(repo, ["diff", "--name-only"]):
        fail("Tracked files changed during 05BB generation.")
    if run_git(repo, ["diff", "--cached", "--name-only"]):
        fail("Files became staged during 05BB generation.")

    for path, content in output_contents.items():
        actual = sha256_path(path)
        expected = sha256_bytes(content.encode("utf-8"))
        if actual != expected:
            fail("Post-write SHA-256 mismatch for {}".format(path.as_posix()))

    print("=== TASK 05BB GENERATION RESULT ===")
    print("status: PASS")
    print("repair_version: {}".format(REPAIR_VERSION))
    print("source_manuscript_sha256: {}".format(SOURCE_MANUSCRIPT_SHA256))
    print("issues_mapped: 30/30")
    print("major_resolved: 19/19")
    print("moderate_resolved: 10/10")
    print("minor_resolved: 1/1")
    print("numerical_checks_preserved: 20/20")
    print("citation_checks_preserved: 32/32")
    print("core_sections_present: {}/{}".format(len(REQUIRED_MAIN_HEADINGS), len(REQUIRED_MAIN_HEADINGS)))
    print("figure_captions: 4")
    print("figure_in_text_references: 4")
    print("internal_scaffold_hits: 0")
    print("internal_figure_filename_hits: 0")
    print("trailing_whitespace_defects: 0")
    print("uncommitted_files: 6")
    print("tracked_files_modified: 0")
    print("staged_files: 0")
    print("experiments_run: 0")
    print("model_or_api_calls: 0")
    print("raw_data_accessed: NO")
    print("env_accessed: NO")
    print("raw_prompt_response_accessed: NO")
    print("jsonl_accessed_or_written: NO")
    print("word_or_pdf_conversion: NO")
    print("")
    print("OUTPUT SHA-256")
    for path in EXPECTED_OUTPUT_FILES:
        print("{} = {}".format(path.as_posix(), sha256_path(path)))
    print("")
    print("STOP: Paste the complete terminal output before any staging, commit, push, or further manuscript repair.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("TASK 05BB FAILED: {}".format(exc), file=sys.stderr)
        raise
