# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

## Abstract

Multi-stage large language model (LLM) pipelines can remain structurally well formed even when the evidence supplied to downstream stages has been degraded. This study formalises Evidence-State Reliability (ESR) as the extent to which intermediate evidence states remain sufficiently complete, grounded, and usable for evidence-sensitive stage objectives. The analysis uses one scaled run of GLM-5.2 over sanitized evidence packets derived from the Consumer Financial Protection Bureau complaint-data context. The design comprises 720 planned calls across decision, audit, and escalation stages; 713 sanitized execution rows were retained, with seven ledger-only rows disclosed as missing from execution-level analysis. Within this single-model, single-run experiment, controlled evidence degradation reduced stage success by -0.517241 to -0.406780 while parser-validity deltas increased by +0.067797 to +0.368421. Mean degraded-condition audit detection was 1.0, mean escalation recovery was 0.0, and the all-sequence cascade-failure rate was 0.929167. The results demonstrate reliability-layer divergence: outputs can become more parser-valid while the evidence-sensitive reliability of the pipeline deteriorates. This supports ESR as an evaluation layer distinct from parser validity, while remaining bounded to the evaluated GLM-5.2 configuration, sanitized CFPB-backed evidence states, one pipeline design, and one scaled run.

**Keywords:** Evidence-State Reliability; reliability cascades; multi-stage LLM pipelines; parser validity; audit; escalation; evidence sufficiency; CFPB

## 1. Introduction

LLM evaluation often concentrates on final-answer correctness, schema compliance, or whether an output can be parsed. Those signals are important, but they do not fully characterize a multi-stage decision pipeline. Evidence can be summarized, filtered, transformed, audited, and escalated before the final output is produced. A structurally valid final object may therefore conceal degradation that occurred in the evidence state passed between stages.

This paper studies that gap through Evidence-State Reliability (ESR): the reliability of the intermediate evidence state used by downstream functions. ESR asks whether the evidence available to a stage remains sufficiently complete, grounded, and usable for that stage's evidence-sensitive objective. Parser validity asks a different question: whether an output conforms to a required machine-readable structure. A parser-valid output can still be evidence-unsuccessful, so parser validity is not a sufficient proxy for ESR.

The central research question is: **How can Evidence-State Reliability be measured separately from parser validity in a multi-stage LLM decision pipeline?** The study addresses this question with controlled evidence-state interventions in a decision-audit-escalation pipeline. The strongest supported claim is:

> Within the committed Pilot 05 GLM-5.2 scaled CFPB-backed sanitized experiment, controlled evidence degradation reduced stage success while parser validity increased across decision, audit, and escalation stages, supporting Evidence-State Reliability as an evaluation layer distinct from parser validity.

The paper makes three bounded contributions. First, it formalises parser-validity rate, ESR, reliability-layer divergence, and false assurance at the format layer as separate evaluation constructs. Second, it operationalises controlled evidence-state degradation across decision, audit, and escalation stages. Third, it reports a reproducible within-run pattern in which parser validity improved while evidence-sensitive stage success deteriorated. The novelty claim is deliberately limited: bounded combination-and-operationalisation differentiation is supported; global priority or first-ever novelty is not established.

The evidence comes from one model configuration and one scaled run. The study does not establish universal LLM unreliability, general GLM-5.2 unreliability, provider superiority, deployment or regulatory validity, real-world financial-decision validity, or cross-model generalisation.

## 2. Related Work

### 2.1 Multidimensional evaluation

Model quality cannot be reduced to a single success indicator. Behavioral testing shows that aggregate held-out accuracy can conceal capability-specific weaknesses, while calibration separates confidence quality from predictive correctness (Ribeiro et al., 2020; Guo et al., 2017). Retrieval-augmented-generation evaluation similarly distinguishes context relevance, faithful context use, and answer relevance (Es et al., 2024; Saad-Falcon et al., 2024). ESR fits within this multidimensional view but targets a narrower object: the evidence state supplied to downstream pipeline functions.

### 2.2 Structured output validity and substantive success

Formal conformance is useful because machine-readable contracts support automation, validation, and downstream execution. Grammar-constrained decoding can improve adherence to required structures, and recent structured-output studies distinguish schema validity from value-level or executable correctness (Geng et al., 2023; Ray, 2026, preprint; Singh et al., 2026, preprint). This study therefore does not claim that structural and substantive validity have never been separated. Its contribution is to connect that distinction to controlled evidence-state interventions and stage-aware decision, audit, escalation, detection, and recovery measurements.

### 2.3 Evidence sufficiency and intermediate support

Insufficient evidence has been studied in fact checking, and evidence sufficiency is increasingly explicit in retrieval-augmented generation and risk-oriented decision settings (Atanasova et al., 2022, preprint; Qiu et al., 2026, preprint; Solozobov, 2026, preprint). These works motivate evaluating whether available evidence can support a task rather than checking output form alone. The present design adds an explicit multi-stage intervention: frozen evidence conditions are propagated through decision, audit, and escalation functions, allowing evidence-sensitive stage behavior to be compared with parser validity.

### 2.4 Multi-stage systems, cascades, audit, and escalation

Component-aware evaluation is important in interactive agents and retrieval-augmented systems (Liu et al., 2024; Es et al., 2024; Saad-Falcon et al., 2024). Cascading failure is also an established systems concept, and emerging LLM research studies seeded-error and hallucination propagation in multi-agent collaboration (Motter and Lai, 2002; Xie et al., 2026, preprint; Jamshidi et al., 2026, preprint). Here, a reliability cascade is used in a narrower experimental sense: condition-linked reliability loss that propagates across decision, audit, and escalation stages under controlled evidence degradation.

Algorithmic-audit research emphasizes institutional accountability, documentation, and lifecycle processes (Raji et al., 2020). The computational audit stage in this experiment is much narrower and is not presented as an organizational or regulatory audit. Selective prediction and learning-to-defer research likewise establish abstention and expert deferral as distinct downstream functions (Geifman and El-Yaniv, 2019; Mozannar and Sontag, 2020). The present escalation stage asks only whether the implemented pipeline recovered after degradation; it does not establish an optimal escalation policy.

### 2.5 Financial context and bounded novelty

Financial-sector reports motivate careful testing, interpretability, auditability, and governance of AI-enabled financial services (Financial Stability Board, 2017; Financial Stability Board, 2026, consultation report). The 2026 source is a consultation report, not final guidance. The Consumer Financial Protection Bureau describes its Consumer Complaint Database as a public resource while warning that complaints are not a statistical sample, narratives are consumer accounts, and interpretation requires context (Consumer Financial Protection Bureau, 2025). The database is used here only as provenance for a sanitized evaluation substrate; the experiment does not establish complaint truth, misconduct, prevalence, regulatory validity, or deployment performance.

The novelty position is therefore a combination-and-operationalisation contribution. The paper combines controlled evidence-state degradation, a decision-audit-escalation pipeline, stage-specific reliability measurement, parser-versus-evidence comparison, and recovery analysis in one reproducible design. It does not claim global priority over multidimensional evaluation, evidence sufficiency, structured-versus-substantive validity, or cascade theory.

## 3. Methodology

### 3.1 Study design and evidence boundary

The study evaluates a three-stage LLM pipeline under a non-degraded baseline condition and controlled degraded evidence conditions. Sixty sanitized base cases were expanded across four evidence conditions and three stages, producing 720 planned and ledgered calls. The evidence packets are CFPB-backed in provenance but sanitized. They are not raw production records, and the experiment does not infer complaint truth, company misconduct, consumer-harm prevalence, or real-world decision validity.

The empirical execution is bounded to the committed GLM-5.2 Pilot 05 run. All reported values come from committed sanitized artifacts. Raw prompts, raw responses, JSONL model-output files, raw CFPB records, and environment or API-key material are outside the reporting boundary.

### 3.2 Pipeline stages

The **decision stage** produces an initial assessment from the supplied evidence state. The **audit stage** evaluates whether the evidence and decision state indicate degradation or concern. The **escalation stage** evaluates whether the implemented downstream mechanism recovers after degradation. These stages are evaluated separately because detection and recovery are not equivalent.

### 3.3 Formal definitions

Let \(E_{i,c,k}\) denote the evidence state supplied to case \(i\), condition \(c\), and stage \(k\). Let \(V_{i,c,k}\in\{0,1\}\) indicate parser validity, and let \(R_{i,c,k}\in\{0,1\}\) indicate evidence-sensitive stage success under the committed scoring contract. For \(N_c\) cases in condition \(c\), the **parser-validity rate** and **Evidence-State Reliability rate** are

\[
\widehat{\mathrm{PV}}_{c,k}
=
\frac{1}{N_c}\sum_{i=1}^{N_c}V_{i,c,k},
\qquad
\widehat{\mathrm{ESR}}_{c,k}
=
\frac{1}{N_c}\sum_{i=1}^{N_c}R_{i,c,k}.
\]

For a degraded condition \(c\) relative to baseline \(c_0\),

\[
\Delta\mathrm{PV}_{c,k}
=
\widehat{\mathrm{PV}}_{c,k}
-
\widehat{\mathrm{PV}}_{c_0,k},
\qquad
\Delta\mathrm{ESR}_{c,k}
=
\widehat{\mathrm{ESR}}_{c,k}
-
\widehat{\mathrm{ESR}}_{c_0,k}.
\]

**Reliability-layer divergence** is

\[
\mathrm{RLD}_{c,k}
=
\Delta\mathrm{PV}_{c,k}
-
\Delta\mathrm{ESR}_{c,k}.
\]

A positive value is especially consequential when \(\Delta\mathrm{PV}_{c,k}>0\) and \(\Delta\mathrm{ESR}_{c,k}<0\): structural conformance improves while evidence-sensitive success declines.

**False assurance at the format layer** occurs when an output is parser-valid but evidence-unsuccessful. Its rate is

\[
\widehat{\mathrm{FA}}_{c,k}
=
\frac{1}{N_c}
\sum_{i=1}^{N_c}
V_{i,c,k}\left(1-R_{i,c,k}\right).
\]

This construct does not imply that every parser-valid output is incorrect. It identifies cases where format-level success could be mistaken for evidence-sensitive reliability.

### 3.4 Metrics and accounting

The evaluation separates execution accounting, parser validity, evidence-sensitive stage success, audit detection, escalation recovery, and sequence-level cascade failure. The accounting identities are fixed by the committed run:

\[
470+250=720,\qquad
470+243=713,\qquad
720-713=7,\qquad
470-470=0.
\]

The first identity accounts for parser-valid and parser-invalid ledger rows. The second accounts for retained sanitized execution rows. The third identifies the seven ledger-only rows missing from execution-level analysis. The fourth confirms that all 470 parser-valid ledger rows were preserved in the sanitized execution layer.

### 3.5 Reproducibility and claim discipline

The repository contains committed sanitized execution summaries, metric tables, figure data, figures, claim-boundary tables, and validation reports. Reproducibility is limited to artifact-level traceability and deterministic validation of the committed outputs; raw prompt and response replay is not claimed. Threats are organized using construct, internal, external, and conclusion-validity categories (Wohlin et al., 2012), and reproducibility claims follow the distinction between transparent reporting and full computational replay (Pineau et al., 2021).

## 4. Results

### 4.1 Execution accounting

Table 1 reports the primary execution contract. All 720 planned calls were represented in the ledger. The sanitized execution layer retained 713 rows. The seven ledger-only rows are disclosed and excluded from execution-level metrics. The maximum cumulative estimated cost was USD 2.2731216.

**Table 1. Execution and parser-accounting summary.**

| Measure | Value | Interpretation |
|---|---:|---|
| Planned calls | 720 | Sixty base cases across four conditions and three stages |
| Ledger rows | 720 | Complete call-plan accounting |
| Sanitized execution rows | 713 | Rows available for execution-level analysis |
| Ledger parser-valid rows | 470 | Structurally valid ledger outputs |
| Ledger parser-invalid rows | 250 | Structurally invalid ledger outputs |
| Persisted parser-valid rows | 470 | Parser-valid rows retained after sanitization |
| Persisted parser-invalid rows | 243 | Parser-invalid rows retained after sanitization |
| Ledger-only missing sanitized rows | 7 | Disclosed and excluded from execution-level metrics |
| Maximum cumulative estimated cost | USD 2.2731216 | Cost recorded by the committed run |

### 4.2 Parser validity diverges from evidence-sensitive stage success

Across degraded evidence conditions, stage-success deltas ranged from -0.517241 to -0.406780, whereas parser-validity deltas ranged from +0.067797 to +0.368421. The directions are opposite: evidence-sensitive success declined while parser validity increased. This is the central empirical instance of reliability-layer divergence.

Figure 1 summarizes this contrast. Because the evidence-sensitive and parser-validity measures move in opposite directions, a parser-only evaluation would give a materially incomplete account of pipeline reliability. The result supports measuring evidence-state adequacy and stage success independently of output-format conformance.

**Figure 1. Parser validity versus evidence-sensitive reliability under controlled degradation.** Across the committed degraded conditions, parser-validity deltas are positive while stage-success deltas are negative. The figure supports a bounded within-run distinction between parser validity and ESR; it does not establish a model-general effect.

### 4.3 Audit detection and escalation recovery

Mean audit detection under degraded evidence was 1.0, while mean escalation recovery was 0.0. Detection therefore did not translate into successful recovery in the implemented pipeline. Figure 2 separates these two outcomes to prevent detection from being interpreted as remediation.

**Figure 2. Audit detection and escalation recovery in the controlled run.** The audit stage detected degraded-condition failures at a mean rate of 1.0, whereas the implemented escalation stage had a mean recovery rate of 0.0. These values describe this pipeline design and do not imply that escalation mechanisms are generally ineffective.

### 4.4 Pipeline-level cascade failure

The all-sequence cascade-failure rate was 0.929167. This metric summarizes sequence groups in which reliability loss propagated across the evaluated stages. Figure 3 presents the pipeline-level result; it is a diagnostic of this experiment, not a prevalence estimate for deployed systems.

**Figure 3. Sequence-level cascade-failure rate.** The all-sequence cascade-failure rate was 0.929167 in the committed Pilot 05 run. The figure describes propagation within the evaluated decision-audit-escalation sequence and does not support a general claim about GLM-5.2 or LLM reliability.

### 4.5 Failure families

The committed interpretation identified three relevant failure families: detected-but-unrecovered degradation, parser-valid/evidence-invalid divergence, and the missing-sanitized-row gap. Figure 4 presents these families as distinct diagnostics rather than collapsing them into one final-output score.

**Figure 4. Failure-family interpretation.** The figure distinguishes detected-but-unrecovered degradation, parser-valid/evidence-invalid divergence, and missing-sanitized-row accounting. It is descriptive of the committed run and does not imply provider, regulatory, deployment, or real-world harm conclusions.

Table 2 consolidates the principal outcome metrics.

**Table 2. Principal reliability outcomes.**

| Outcome | Value | Bounded interpretation |
|---|---:|---|
| Stage-success delta range | -0.517241 to -0.406780 | Evidence-sensitive stage performance declined under degradation |
| Parser-validity delta range | +0.067797 to +0.368421 | Structural conformance increased under degradation |
| Mean degraded audit detection | 1.0 | Degradation was detected by the implemented audit stage |
| Mean degraded escalation recovery | 0.0 | Successful recovery was not observed in the implemented escalation stage |
| All-sequence cascade-failure rate | 0.929167 | Reliability loss propagated across most evaluated sequence groups |

## 5. Discussion

### 5.1 Implications for evaluation

The results show why a multi-stage LLM pipeline should not be evaluated through parser validity alone. In the committed run, the output layer became more structurally compliant under degraded evidence while evidence-sensitive stage success deteriorated. The format signal and the reliability signal therefore pointed in opposite directions.

This divergence has practical implications for evaluation design. First, evidence-state quality should be tracked separately from final-output form. Second, stage-level effects should be measured because degradation can propagate through intermediate handoffs. Third, audit detection and escalation recovery should be reported separately: a system can recognize degradation without restoring reliable operation. Fourth, sequence-level cascade metrics can reveal compounded reliability loss that is invisible in isolated final-output checks.

False assurance at the format layer provides a concise interpretation of the risk. The construct does not treat parser validity as useless; parser validity remains necessary for reliable automation. The problem arises when format success is interpreted as substantive evidence that the pipeline used a sufficiently reliable evidence state.

### 5.2 Contribution and novelty boundary

The empirical contribution is the observed within-run combination of positive parser-validity deltas and negative stage-success deltas across a controlled decision-audit-escalation experiment. The methodological contribution is the joint operationalisation of evidence-state interventions, stage-aware reliability measures, detection, recovery, and cascade behavior.

The contribution remains bounded. Prior work already establishes multidimensional evaluation, evidence sufficiency, structured-versus-substantive validity, component-aware assessment, auditing, deferral, and cascading failure. The supported novelty verdict is: **Bounded combination-and-operationalisation differentiation supported; global priority or first-ever novelty not established.**

### 5.3 Interpretation of the single-model result

The experiment provides direct evidence for the evaluated GLM-5.2 configuration, not for other models or providers. Its value is analytical rather than universal: it demonstrates that an evidence-state intervention can reveal a reliability-layer divergence that parser-only evaluation would miss. Cross-model replication would be required before asserting provider-independent or model-family-general effects, but it is not necessary for the present bounded within-experiment claim.

## 6. Limitations

The study has several material limitations. First, it evaluates one GLM-5.2 configuration in one scaled run of 720 planned calls. It is not a multi-run replication and does not support cross-model generalisation. Second, all evidence packets are sanitized and CFPB-backed in provenance; they are not raw production data. The complaint-data context does not provide independently verified ground truth for prevalence, misconduct, consumer harm, or regulatory conclusions.

Third, seven ledger rows have no corresponding sanitized execution row. They are disclosed and excluded from execution-level metrics. Although the accounting contract is internally consistent, the missing rows reduce the retained execution set from 720 to 713. Fourth, the degradation conditions represent defined forms of evidence loss and do not exhaust real-world ambiguity, contradiction, delay, or distribution shift.

Fifth, the audit stage is a computational component rather than an institutional algorithmic audit. Its mean degraded-condition detection rate of 1.0 should not be interpreted as governance assurance. Sixth, the escalation recovery mean of 0.0 may reflect the specific escalation design, prompts, scoring rules, and pipeline ordering rather than a general property of escalation mechanisms.

Seventh, construct validity depends on the committed evidence-sensitive scoring contract. Parser validity measures structural conformance, while ESR measures stage success under that contract; neither measure alone establishes real-world decision quality. Eighth, artifact-level reproducibility is supported through committed sanitized outputs and validation reports, but raw prompt and response replay is outside the evidence boundary.

Accordingly, the study does not establish deployment safety, regulatory validity, financial-decision validity, consumer-harm prevalence, company misconduct, universal LLM unreliability, general GLM-5.2 unreliability, or provider superiority.

## 7. Conclusion

This study formalised Evidence-State Reliability as an evaluation layer distinct from parser validity and operationalised it in a controlled decision-audit-escalation pipeline. Within one scaled GLM-5.2 run over sanitized CFPB-backed evidence states, stage-success deltas were negative (-0.517241 to -0.406780) while parser-validity deltas were positive (+0.067797 to +0.368421). Mean degraded audit detection was 1.0, mean escalation recovery was 0.0, and the all-sequence cascade-failure rate was 0.929167.

The result demonstrates reliability-layer divergence within the evaluated setup: a pipeline can become more parser-valid while becoming less successful under evidence-sensitive criteria. Parser validity remains an important engineering signal, but it is not a sufficient proxy for evidence-state reliability. Evaluation of multi-stage LLM decision systems should therefore report evidence-state adequacy, stage success, detection, recovery, and cascade behavior separately.

The conclusion is limited to one model configuration, one pipeline design, sanitized evidence, and one scaled run. It does not establish cross-model, provider-independent, deployment, regulatory, or real-world financial validity. The supported contribution is a bounded combination and operationalisation of evidence-state intervention and multi-layer reliability measurement, not a first-ever or global-priority claim.

## Data and Code Availability

The study's code, sanitized derived artifacts, execution summaries, paper tables, figure data, figures, claim-boundary materials, and validation reports are maintained in the project repository. The available artifacts support deterministic checking of the reported accounting and metrics. Raw CFPB records, raw prompts, raw model responses, JSONL model-output files, and environment or API-key material are not part of the manuscript artifact package. Reproducibility claims are therefore limited to the committed sanitized evidence and artifact-validation boundary.

## References

- Marco Tulio Ribeiro; Tongshuang Wu; Carlos Guestrin; Sameer Singh (2020). *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList*. ACL 2020. DOI 10.18653/v1/2020.acl-main.442. https://aclanthology.org/2020.acl-main.442/.
- Chuan Guo; Geoff Pleiss; Yu Sun; Kilian Q. Weinberger (2017). *On Calibration of Modern Neural Networks*. ICML 2017, PMLR 70. PMLR 70:1321-1330. https://proceedings.mlr.press/v70/guo17a.html.
- Saibo Geng; Martin Josifoski; Maxime Peyrard; Robert West (2023). *Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning*. EMNLP 2023. DOI 10.18653/v1/2023.emnlp-main.674. https://aclanthology.org/2023.emnlp-main.674/.
- Jaideep Ray (2026). *The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small Language Models*. arXiv preprint. arXiv:2605.26128. https://arxiv.org/abs/2605.26128. [Preprint; not peer reviewed as verified in 05AX.]
- Abhinav Kumar Singh; Harsha Vardhan Khurdula; Yoeven D Khemlani; Vineet Agarwal (2026). *The Structured Output Benchmark*. arXiv preprint. arXiv:2604.25359. https://arxiv.org/abs/2604.25359. [Preprint; not peer reviewed as verified in 05AX.]
- Xiao Liu; Hao Yu; Hanchen Zhang; Yifan Xu; Xuanyu Lei; Hanyu Lai; Yu Gu; Hangliang Ding; Kaiwen Men; Kejuan Yang; Shudan Zhang; Xiang Deng; Aohan Zeng; Zhengxiao Du; Chenhui Zhang; Sheng Shen; Tianjun Zhang; Yu Su; Huan Sun; Minlie Huang; Yuxiao Dong; Jie Tang (2024). *AgentBench: Evaluating LLMs as Agents*. ICLR 2024. arXiv:2308.03688. https://arxiv.org/abs/2308.03688.
- Shahul Es; Jithin James; Luis Espinosa-Anke; Steven Schockaert (2024). *RAGAS: Automated Evaluation of Retrieval Augmented Generation*. EACL 2024 System Demonstrations. DOI 10.18653/v1/2024.eacl-demo.16. https://aclanthology.org/2024.eacl-demo.16/.
- Jon Saad-Falcon; Omar Khattab; Christopher Potts; Matei Zaharia (2024). *ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems*. NAACL 2024. DOI 10.18653/v1/2024.naacl-long.20. https://aclanthology.org/2024.naacl-long.20/.
- Pepa Atanasova; Jakob Grue Simonsen; Christina Lioma; Isabelle Augenstein (2022). *Fact Checking with Insufficient Evidence*. arXiv preprint. arXiv:2204.02007. https://arxiv.org/abs/2204.02007. [Preprint; not peer reviewed as verified in 05AX.]
- Inioluwa Deborah Raji; Andrew Smart; Rebecca N. White; Margaret Mitchell; Timnit Gebru; Ben Hutchinson; Jamila Smith-Loud; Daniel Theron; Parker Barnes (2020). *Closing the AI Accountability Gap: Defining an End-to-End Framework for Internal Algorithmic Auditing*. FAccT 2020. DOI 10.1145/3351095.3372873. https://doi.org/10.1145/3351095.3372873.
- Hussein Mozannar; David Sontag (2020). *Consistent Estimators for Learning to Defer to an Expert*. ICML 2020, PMLR 119. PMLR 119:7076-7087. https://proceedings.mlr.press/v119/mozannar20b.html.
- Yonatan Geifman; Ran El-Yaniv (2019). *SelectiveNet: A Deep Neural Network with an Integrated Reject Option*. ICML 2019, PMLR 97. PMLR 97:2151-2159. https://proceedings.mlr.press/v97/geifman19a.html.
- Consumer Financial Protection Bureau (2025). *Consumer Complaint Database*. Consumer Financial Protection Bureau. Official database documentation; page modified 2025-10-20. https://www.consumerfinance.gov/data-research/consumer-complaints/.
- Financial Stability Board (2017). *Artificial intelligence and machine learning in financial services*. Financial Stability Board. Official FSB report, 2017-11-01. https://www.fsb.org/2017/11/artificial-intelligence-and-machine-learning-in-financial-service/.
- Financial Stability Board (2026). *Sound Practices for Responsible Adoption of Artificial Intelligence: Consultation report*. Financial Stability Board. Consultation report, 2026-06-10. https://www.fsb.org/2026/06/sound-practices-for-responsible-adoption-of-artificial-intelligence-consultation-report/. [Consultation report; not final guidance.]
- Claes Wohlin; Per Runeson; Martin Höst; Magnus C. Ohlsson; Björn Regnell; Anders Wesslén (2012). *Experimentation in Software Engineering*. Springer. DOI 10.1007/978-3-642-29044-2. https://doi.org/10.1007/978-3-642-29044-2.
- Joelle Pineau et al. (2021). *Improving Reproducibility in Machine Learning Research*. Journal of Machine Learning Research 22(164). JMLR 22(164):1-20. https://jmlr.org/papers/v22/20-303.html.
- Adilson E. Motter; Ying-Cheng Lai (2002). *Cascade-based attacks on complex networks*. Physical Review E 66, 065102. DOI 10.1103/PhysRevE.66.065102. https://doi.org/10.1103/PhysRevE.66.065102.
- Yizhe Xie; Congcong Zhu; Xinyue Zhang; Tianqing Zhu; Dayong Ye; Minfeng Qi; Huajie Chen; Wanlei Zhou (2026). *From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration*. arXiv preprint. arXiv:2603.04474. https://arxiv.org/abs/2603.04474. [Preprint; not peer reviewed as verified in 05AX.]
- Saeid Jamshidi; Arghavan Moradi Dakhel; Kawser Wazed Nafi; Foutse Khomh (2026). *Hallucination Cascade: Analyzing Error Propagation in Multi-Agent LLM Systems*. arXiv preprint. arXiv:2606.07937. https://arxiv.org/abs/2606.07937. [Preprint; not peer reviewed as verified in 05AX.]
- Jingxi Qiu; Zeyu Han; Cheng Huang (2026). *SURE-RAG: Sufficiency and Uncertainty-Aware Evidence Verification for Selective Retrieval-Augmented Generation*. arXiv preprint. arXiv:2605.03534. https://arxiv.org/abs/2605.03534. [Preprint; not peer reviewed as verified in 05AX.]
- Oleg Solozobov (2026). *Evidence Sufficiency Under Delayed Ground Truth*. arXiv preprint. arXiv:2604.15740. https://arxiv.org/abs/2604.15740. [Preprint; not peer reviewed as verified in 05AX.]
