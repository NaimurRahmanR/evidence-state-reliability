# Pilot 05BC — Binding Final Writing Specification for Task 05BD

## 1. Purpose

Task 05BD will create the full derivative final manuscript from committed 05BB and the committed sanitized evidence base. It will not modify 05BB, create empirical evidence, run models, search for new literature, or inspect raw prompts, responses, JSONL, `.env`, or raw CFPB records.

## 2. Manuscript role and claim scope

Pilot 05 remains the principal empirical study.

The supported central claim is:

> Within the committed Pilot 05 GLM-5.2 scaled CFPB-backed sanitized experiment, controlled evidence degradation reduced stage success while parser validity increased across decision, audit, and escalation stages, supporting Evidence-State Reliability as an evaluation layer distinct from parser validity.

The bounded novelty verdict remains:

> Bounded combination-and-operationalisation differentiation supported; global priority or first-ever novelty not established.

The final paper must not claim cross-model generality, provider independence, deployment safety, regulatory validity, real-world financial decision validity, complaint truth, consumer-harm prevalence, company misconduct, universal LLM unreliability, general GLM-5.2 unreliability, or guaranteed journal acceptance.

## 3. Required structure and body-word targets

| Order | Section | Target words | Binding content |
|---:|---|---:|---|
| 1 | Abstract | 220–250 | Problem, design, principal results, uncertainty-aware wording, bounded contribution and scope |
| 2 | Introduction | 750–900 | Pipeline problem, ESR gap, research question, design preview, contributions, scope, roadmap |
| 3 | Related Work | 900–1,200 | Critical synthesis and exact combination gap |
| 4 | Methodology | 1,400–1,700 | Data/evidence construction, four conditions, three stages, contracts, metrics, analysis, reproducibility |
| 5 | Results | 1,400–1,700 | Accounting, condition-stage results, uncertainty, audit/false assurance/recovery, cascades, figures/tables |
| 6 | Discussion | 900–1,200 | Interpretation, alternative explanations, implications, novelty, cross-pilot context, future work |
| 7 | Limitations | 400–550 | Construct, internal, external, conclusion, and reproducibility limits |
| 8 | Conclusion | 250–350 | Answer to research question, contribution, bounded result, next research step |
| 9 | Data and Code Availability | 100–150 | Exact repository/commit and artifact-level reproducibility boundary |
| 10 | References | Preserve verified set | Retain bibliographic facts and preprint status; apply venue style later |

Target body length excluding references: **6,320–8,000 words**.

## 4. Mandatory Methodology content

05BD must include all of the following:

1. **Study design**
   - 60 sanitized CFPB-backed base cases.
   - Four evidence states per case.
   - Three pipeline stages.
   - 720 planned and ledgered calls.
   - Paired comparisons within base case and stage.

2. **Evidence conditions**
   - `clean`: baseline evidence state.
   - `compressed_lossy`: information compression/loss.
   - `partial_dropout`: missing evidence elements.
   - `noisy_conflicting`: conflicting evidence.

3. **Pipeline stages**
   - Decision: stage validity, evidence adequacy, and recommendation behavior.
   - Audit: degradation detection and false-assurance behavior.
   - Escalation: recovery/loss behavior after degradation.
   - Detection and recovery must be defined as different functions.

4. **Operational measures**
   - Parser-valid rate: structural contract only.
   - Stage-success rate: parser-valid plus positive sanitized validity judgment.
   - Audit detection and false-assurance rates among parser-valid audit rows.
   - Escalation recovery among parser-valid escalation rows.
   - Paired degraded-minus-clean deltas.
   - Three-stage cascade pattern.

5. **Construct boundary**
   - ESR is the conceptual reliability of intermediate evidence states.
   - Stage success is the experiment's operational indicator.
   - Parser validity is necessary for automation but is not evidence sufficiency or correctness.
   - Neither metric alone establishes real-world decision quality.

6. **Analysis**
   - Condition-stage denominators.
   - Seven ledger-only rows excluded from execution-level metrics.
   - Nonparametric bootstrap over paired base cases.
   - 2,000 resamples.
   - Random seed 5205.
   - 95% confidence intervals.

7. **Execution and reproducibility**
   - Model identifier: GLM-5.2.
   - Sanitized artifact boundary.
   - Approved USD 8 cost cap and maximum cumulative estimated cost USD 2.2731216.
   - Artifact-level reproducibility, not raw-response replay.
   - Do not use ambiguous validation-only attempt counters as empirical results.

## 5. Mandatory Results content

### 5.1 Accounting

Preserve exactly:

- planned calls: 720;
- ledger rows: 720;
- sanitized execution rows: 713;
- ledger parser-valid/invalid: 470/250;
- persisted parser-valid/invalid: 470/243;
- ledger-only missing sanitized rows: 7;
- maximum cumulative estimated cost: USD 2.2731216.

### 5.2 Condition-by-stage table

Include all twelve cells from `pilot_05AP_condition_stage_interaction.csv`, with:

- row count;
- parser-valid count/rate;
- stage-success count/rate;
- paired parser-validity delta;
- paired stage-success delta.

Do not report only the minimum and maximum.

### 5.3 Uncertainty

State accurately:

- all nine degraded parser-validity point estimates are positive;
- three partial-dropout parser-validity 95% intervals include zero;
- all nine stage-success point estimates are negative;
- all nine stage-success 95% intervals remain below zero.

Avoid significance language unless it is defined explicitly.

### 5.4 Audit and false assurance

Report condition-level parser-valid audit results:

- compressed_lossy detection 1.0; false assurance 0.062500;
- partial_dropout detection 1.0; false assurance 0.048780;
- noisy_conflicting detection 1.0; false assurance 0.019231.

Call these model-output-coded computational audit indicators, not institutional or regulatory audit outcomes.

### 5.5 Escalation

Report:

- clean parser-valid escalation stage success 1.0 among parser-valid rows;
- degraded escalation recovery 0.0 for all three degraded conditions;
- degraded escalation loss proxy 1.0 among parser-valid rows.

Interpret only for the implemented escalation design.

### 5.6 Cascades

Report:

- all sequence groups: 240;
- complete persisted sequences: 234;
- cascade failures: 223;
- cascade-failure rate: 0.929167;
- condition-level cascade-failure rates;
- pattern composition: parser-failure cascade, detected-not-recovered, audit false assurance, incomplete persisted sequence, preserved/clean success.

The Results section must provide numerator and denominator, not only the proportion.

## 6. Tables and figures

Minimum publication set:

- **Table 1:** execution and row accounting.
- **Table 2:** condition-by-stage parser validity and stage success.
- **Table 3 or Supplementary Table S1:** bootstrap confidence intervals.
- **Table 4 or compact panel:** audit detection, false assurance, escalation recovery, and cascade counts.

Figures must be integrated in this order:

1. `pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png`
2. `pilot_05AS_figure_02_audit_escalation_interpretation.png`
3. `pilot_05AS_figure_03_cascade_failure_rate.png`
4. `pilot_05AS_figure_04_failure_family_interpretation.png`

Each figure requires:

- exact asset path;
- first in-text citation before the figure;
- publication caption;
- data-source traceability;
- bounded interpretation;
- no internal filename as the visible caption.

## 7. Required Discussion content

The Discussion must address:

- why format validity and evidence-sensitive reliability can diverge;
- why low clean parser validity matters;
- whether the parser/prompt/scoring contract may contribute to the observed contrast;
- why detection is not recovery;
- why non-zero false assurance remains relevant despite detection=1.0;
- why zero recovery is design-specific;
- uncertainty in parser-validity changes;
- implications for multi-stage evaluation and governance;
- alternative explanations;
- bounded novelty;
- future cross-model and multi-run replication.

## 8. Cross-pilot handling

Pilots 01–04 may appear only as bounded developmental context or supplementary triangulation:

- do not pool their metrics with Pilot 05;
- do not call them replication of Pilot 05;
- do not let simulated or deterministic results validate real-model claims;
- one concise paragraph and, if useful, one supplementary programme table are sufficient;
- Pilot 05 remains the only principal scaled experiment in the main Results.

## 9. Prose and terminology rules

- Use `parser validity` as a noun and `parser-validity` as a compound modifier.
- Use `behaviour` consistently in prose unless an official source title uses `behavior`.
- Use `sanitized` consistently because it is embedded in the committed artifact terminology, unless the selected journal later requires house style.
- Replace repeated defensive disclaimers with strategically placed scope statements.
- Avoid `head-turning`, `groundbreaking`, `Q1-ready`, `first-ever`, and global-priority language.
- Do not expose internal task IDs in publication prose.
- Do not describe repository validation as scientific replication.
- Rewrite the Abstract last.

## 10. 05BD acceptance criteria

05BD passes only if:

1. the committed 05BB manuscript remains byte-identical;
2. every protected empirical value is preserved;
3. all twelve condition-stage rows are represented;
4. all twenty-seven bootstrap rows are traceable, with at least the full intervals in a table or supplement;
5. the three parser-validity intervals crossing zero are disclosed;
6. all nine stage-success intervals below zero are disclosed;
7. audit false-assurance rates are reported;
8. the 223/240 cascade count is reported;
9. each figure is bound to the exact committed asset;
10. no new citation or empirical claim is invented;
11. all central claims map to committed evidence;
12. body length falls within 6,320–8,000 words unless a documented journal constraint is selected later;
13. the manuscript contains no internal workflow scaffolding;
14. single-model, single-run, sanitized-data, and artifact-reproducibility limits remain explicit;
15. the repository remains unstaged and uncommitted until separate approval.

## 11. Work that remains after 05BD

Task 05BE must independently check:

- numerical preservation;
- condition-stage and CI completeness;
- citation/reference consistency;
- figure/table integration;
- claim-evidence traceability;
- construct and terminology consistency;
- reviewer-risk responses;
- internal scaffold removal;
- abstract–results–conclusion alignment;
- no unsupported generalisation.

Journal selection and venue-specific formatting occur only after 05BE passes.
