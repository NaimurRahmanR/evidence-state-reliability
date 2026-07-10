from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "05AW"
TASK_NAME = "formal definitions and citation-placeholder refinement"
SECURED_COMMIT = "b4ebf8a"
SECURED_COMMIT_MESSAGE = "Add Pilot 05 full manuscript draft"
SOURCE_BOUNDARY = "committed 05AV outputs only"
NO_NEW_EVIDENCE_STATEMENT = (
    "Task 05AW performs manuscript-structure, notation, citation-placeholder, "
    "related-work-slot, academic-wording, threats-to-validity, and claim-boundary "
    "refinement only. It does not create, infer, or add new empirical evidence."
)

REPO = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO / "reports" / "pilot_05_formal_definition_citation_refinement"

SOURCE_FILES = [
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_manifest.json",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_source_file_index.csv",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_full_manuscript_draft.md",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_manuscript_section_index.csv",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_claim_traceability_matrix.csv",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_submission_readiness_gap_analysis.md",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_internal_review_checklist.md",
    "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_full_manuscript_assembly_report.md",
]

OUTPUT_FILES = [
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_manifest.json",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_source_file_index.csv",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_formal_definitions_and_notation.md",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_citation_placeholder_register.csv",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_related_work_slot_map.md",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_refined_full_manuscript_draft.md",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_threats_to_validity_framework.md",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_claim_boundary_refinement.md",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_section_refinement_map.csv",
    "reports/pilot_05_formal_definition_citation_refinement/pilot_05AW_internal_validation_report.md",
]

EXPECTED_UNTRACKED = {
    "experiments/pilot_05_formal_definition_citation_refinement.py",
    *OUTPUT_FILES,
}

SAFETY_FLAGS = {
    "no_api_calls": True,
    "no_model_calls": True,
    "no_external_literature_search": True,
    "no_env_read": True,
    "no_raw_prompt_response_access": True,
    "no_jsonl_written": True,
    "no_raw_cfpb_data_touched": True,
    "no_new_empirical_evidence": True,
    "committed_files_modified": False,
    "staging_performed": False,
    "commit_performed": False,
    "push_performed": False,
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        fail(
            f"Git command failed: git {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def normalise(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def read_committed_text(relative_path: str) -> str:
    return run_git("show", f"HEAD:{relative_path}")


def verify_starting_state() -> None:
    branch = run_git("branch", "--show-current")
    if branch != "main":
        fail(f"Expected branch main, found {branch!r}.")

    short_head = run_git("rev-parse", "--short=7", "HEAD")
    if short_head != SECURED_COMMIT:
        fail(f"Expected HEAD {SECURED_COMMIT}, found {short_head}.")

    message = run_git("log", "-1", "--format=%s")
    if message != SECURED_COMMIT_MESSAGE:
        fail(
            f"Expected commit message {SECURED_COMMIT_MESSAGE!r}, found {message!r}."
        )

    full_head = run_git("rev-parse", "HEAD")
    origin_main = run_git("rev-parse", "origin/main")
    divergence = run_git(
        "rev-list", "--left-right", "--count", "origin/main...HEAD"
    ).split()
    if len(divergence) != 2 or divergence != ["0", "0"] or full_head != origin_main:
        fail(
            "main is not aligned with existing origin/main: "
            f"divergence={divergence}, HEAD={full_head}, origin/main={origin_main}."
        )

    staged = run_git("diff", "--cached", "--name-only")
    modified = run_git("diff", "--name-only")
    if staged:
        fail(f"Staged files exist before 05AW generation:\n{staged}")
    if modified:
        fail(f"Modified tracked files exist before 05AW generation:\n{modified}")

    status_lines = [
        line
        for line in run_git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line.strip()
    ]
    allowed_preexisting = EXPECTED_UNTRACKED
    unexpected = []
    for line in status_lines:
        path = normalise(line[3:])
        if not (line.startswith("?? ") and path in allowed_preexisting):
            unexpected.append(line)
    if unexpected:
        fail(
            "Unexpected repository state before 05AW generation:\n"
            + "\n".join(unexpected)
        )

    tracked = set(run_git("ls-files").splitlines())
    head_paths = set(run_git("ls-tree", "-r", "--name-only", "HEAD").splitlines())
    for relative in SOURCE_FILES:
        path = REPO / relative
        if not path.is_file():
            fail(f"Required committed 05AV source file is missing: {relative}")
        if relative not in tracked or relative not in head_paths:
            fail(f"Required 05AV source file is not committed at HEAD: {relative}")

    for relative in OUTPUT_FILES:
        output_path = REPO / relative
        if output_path.exists() and (
            relative in tracked or relative in head_paths
        ):
            fail(
                "05AW output path is already tracked or committed. "
                f"Refusing to overwrite committed work: {relative}"
            )


def load_source_materials() -> dict[str, str]:
    return {relative: read_committed_text(relative) for relative in SOURCE_FILES}


def extract_headings(markdown: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2)))
    return headings


def refine_academic_wording(text: str) -> str:
    replacements = [
        (
            "This proves that",
            "Within the bounded Pilot 05 design, this supports the interpretation that",
        ),
        (
            "This demonstrates that",
            "Within the evaluated conditions, this provides evidence that",
        ),
        (
            "clearly shows",
            "indicates",
        ),
        (
            "always",
            "in the evaluated run",
        ),
        (
            "all LLMs",
            "the evaluated GLM-5.2 pipeline",
        ),
        (
            "real-world financial",
            "CFPB-backed experimental",
        ),
    ]
    refined = text
    for old, new in replacements:
        refined = refined.replace(old, new)
    return refined


def build_formal_definitions() -> str:
    return """# Pilot 05AW Formal Definitions and Notation

## Scope

These definitions formalise concepts already present in the committed 05AV manuscript.
They are analytical and editorial refinements only. They do not create new empirical
evidence, recompute results, or widen the manuscript's claim boundary.

## Pipeline and stage notation

Let a multi-stage AI decision pipeline be represented as

\\[
\\mathcal{P} = (S_1, S_2, \\ldots, S_K),
\\]

where each stage \\(S_k\\) receives an evidence state, produces a stage output, and may
pass a transformed evidence state to the next stage. Pilot 05 uses three operational
stage families: decision, audit, and escalation.

For case \\(i\\), evidence condition \\(c\\), and stage \\(k\\):

- \\(E_{i,c,k}\\) denotes the evidence state available to stage \\(k\\).
- \\(Y_{i,c,k}\\) denotes the stage output.
- \\(V_{i,c,k} \\in \\{0,1\\}\\) denotes parser validity.
- \\(R_{i,c,k} \\in \\{0,1\\}\\) denotes stage/evidence success under the committed
  Pilot 05 scoring contract.
- \\(U_{i,c,k}\\) denotes any recorded uncertainty or escalation-related indicator
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

\\[
V_{i,c,k} =
\\begin{cases}
1, & \\text{if the stage output satisfies the expected machine-readable contract},\\\\
0, & \\text{otherwise.}
\\end{cases}
\\]

Parser validity evaluates structural acceptability only. It is not equivalent to
answer correctness, evidence fidelity, decision validity, regulatory validity, or
deployment safety.

## Definition 3: Stage/evidence success

**Stage/evidence success** is the indicator \\(R_{i,c,k}\\) assigned under the
precommitted Pilot 05 evaluation contract for whether the stage output satisfies the
relevant evidence-sensitive success criterion.

The interpretation of \\(R_{i,c,k}\\) remains tied to the committed Pilot 05 task,
condition, and scoring definitions.

## Definition 4: Evidence-State Reliability

For a fixed condition \\(c\\) and stage \\(k\\), define empirical Evidence-State
Reliability as

\\[
\\widehat{\\mathrm{ESR}}_{c,k}
=
\\frac{1}{N_c}
\\sum_{i=1}^{N_c} R_{i,c,k},
\\]

where \\(N_c\\) is the number of evaluated cases under condition \\(c\\).

A pipeline-level aggregate may be written as

\\[
\\widehat{\\mathrm{ESR}}_{c}
=
\\sum_{k=1}^{K} w_k\\widehat{\\mathrm{ESR}}_{c,k},
\\qquad
w_k \\geq 0,
\\quad
\\sum_{k=1}^{K} w_k = 1.
\\]

Pilot 05 should report only the aggregation actually supported by its committed
outputs. The notation does not authorise retrospective metric invention.

## Definition 5: Parser-validity rate

For condition \\(c\\) and stage \\(k\\),

\\[
\\widehat{\\mathrm{PV}}_{c,k}
=
\\frac{1}{N_c}
\\sum_{i=1}^{N_c} V_{i,c,k}.
\\]

This is a format-layer metric and must remain analytically separate from
\\(\\widehat{\\mathrm{ESR}}_{c,k}\\).

## Definition 6: Reliability-layer divergence

For a degraded condition \\(d\\) relative to reference condition \\(r\\), define

\\[
\\Delta \\mathrm{PV}_{d,r,k}
=
\\widehat{\\mathrm{PV}}_{d,k}
-
\\widehat{\\mathrm{PV}}_{r,k},
\\]

and

\\[
\\Delta \\mathrm{ESR}_{d,r,k}
=
\\widehat{\\mathrm{ESR}}_{d,k}
-
\\widehat{\\mathrm{ESR}}_{r,k}.
\\]

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

\\[
V_{i,c,k}=1 \\quad \\text{while} \\quad R_{i,c,k}=0.
\\]

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
"""


def citation_rows() -> list[dict[str, str]]:
    return [
        {
            "placeholder_id": "CIT-ESR-01",
            "manuscript_slot": "Introduction: evaluation-layer distinction",
            "evidence_needed": "Foundational work distinguishing output validity, task correctness, calibration, and process or evidence reliability",
            "preferred_source_type": "Peer-reviewed conceptual or evaluation paper",
            "claim_supported": "Evaluation at the format layer does not exhaust reliability assessment",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-CASCADE-01",
            "manuscript_slot": "Introduction/Related Work: cascading failure",
            "evidence_needed": "Research on error propagation, cascading failures, or compounding reliability loss in multi-stage AI or decision systems",
            "preferred_source_type": "Peer-reviewed empirical or systems paper",
            "claim_supported": "Upstream state degradation can propagate through downstream stages",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-PIPELINE-01",
            "manuscript_slot": "Related Work: multi-stage LLM pipelines",
            "evidence_needed": "Research on chained, tool-using, agentic, or multi-stage LLM evaluation",
            "preferred_source_type": "Peer-reviewed paper or authoritative benchmark description",
            "claim_supported": "Multi-stage LLM systems require stage-aware evaluation",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-PARSER-01",
            "manuscript_slot": "Related Work: structured-output evaluation",
            "evidence_needed": "Research or technical standards on schema adherence, constrained decoding, or structured-output validity",
            "preferred_source_type": "Peer-reviewed paper or authoritative technical documentation",
            "claim_supported": "Parser validity captures structure rather than semantic or evidential correctness",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-AUDIT-01",
            "manuscript_slot": "Related Work: AI auditing and assurance",
            "evidence_needed": "Research on AI auditability, assurance, oversight, and evaluation mismatch",
            "preferred_source_type": "Peer-reviewed governance or auditing paper",
            "claim_supported": "Audit stages can inherit or amplify evidence-state limitations",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-UNCERTAINTY-01",
            "manuscript_slot": "Related Work: uncertainty and escalation",
            "evidence_needed": "Research on uncertainty communication, selective prediction, abstention, or escalation in AI decision systems",
            "preferred_source_type": "Peer-reviewed methods paper",
            "claim_supported": "Escalation behaviour is a distinct reliability layer",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-FINAI-01",
            "manuscript_slot": "Domain context: financial or complaint decision support",
            "evidence_needed": "Carefully bounded literature on AI-supported financial decision processes or consumer complaint analysis",
            "preferred_source_type": "Peer-reviewed domain paper or official institutional source",
            "claim_supported": "The domain motivates high assurance without validating deployment",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-CFPB-01",
            "manuscript_slot": "Data provenance",
            "evidence_needed": "Official CFPB documentation describing the public complaint database and its limitations",
            "preferred_source_type": "Official CFPB source",
            "claim_supported": "Dataset provenance and documented limitations",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-VALIDITY-01",
            "manuscript_slot": "Threats to validity",
            "evidence_needed": "Canonical empirical software engineering, ML evaluation, or experimental-design validity framework",
            "preferred_source_type": "Peer-reviewed methods source",
            "claim_supported": "Construct, internal, external, and conclusion validity structure",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
        {
            "placeholder_id": "CIT-REPRO-01",
            "manuscript_slot": "Reproducibility statement",
            "evidence_needed": "Research or reporting guideline for reproducible computational experiments",
            "preferred_source_type": "Peer-reviewed guideline or recognised reporting standard",
            "claim_supported": "Transparent artefact and claim traceability supports reproducibility",
            "fabricated_citation": "NO",
            "status": "PLACEHOLDER_ONLY",
        },
    ]


def build_related_work_map() -> str:
    return """# Pilot 05AW Related-Work Slot Map

No external literature was searched or cited in Task 05AW. Every bracketed identifier
below is a placeholder that must later be replaced only after an explicitly approved
literature-search task.

## Slot RW-1: Reliability beyond final-output validity

**Purpose:** Position Evidence-State Reliability relative to evaluation traditions
that focus on correctness, calibration, robustness, or structured-output validity.

**Required synthesis:**

1. Define what conventional output-level evaluation captures.
2. Identify why a validly parsed output may remain unsupported by the available
   evidence state.
3. Avoid claiming that prior work entirely ignores intermediate evidence.

**Placeholders:** [CIT-ESR-01], [CIT-PARSER-01]

## Slot RW-2: Multi-stage and agentic pipeline evaluation

**Purpose:** Connect the decision-audit-escalation structure to research on chained
or multi-component AI systems.

**Required synthesis:**

1. Explain stage dependency and information transfer.
2. Distinguish component performance from end-to-end reliability.
3. Identify the gap addressed by controlled evidence-state interventions.

**Placeholders:** [CIT-PIPELINE-01], [CIT-CASCADE-01]

## Slot RW-3: Cascading failure and error propagation

**Purpose:** Situate reliability cascades within broader work on propagated,
compounded, or hidden failures.

**Required synthesis:**

1. Review definitions of cascade or propagation used in adjacent fields.
2. State where the present operationalisation is narrower.
3. Avoid implying deployed-system causality from this experimental run.

**Placeholder:** [CIT-CASCADE-01]

## Slot RW-4: Audit, oversight, and false assurance

**Purpose:** Explain why an audit stage may appear structurally successful while
remaining constrained by degraded evidence.

**Required synthesis:**

1. Cover AI assurance or auditability concepts.
2. Distinguish procedural visibility from substantive evidence adequacy.
3. Keep “false assurance” as an evaluation-risk concept rather than a prevalence
   claim.

**Placeholder:** [CIT-AUDIT-01]

## Slot RW-5: Uncertainty, abstention, and escalation

**Purpose:** Position escalation as a separate downstream reliability function.

**Required synthesis:**

1. Cover uncertainty-aware decision support, abstention, selective prediction, or
   human escalation.
2. Explain why escalation correctness cannot be inferred from parser validity.
3. Avoid claiming optimal escalation policy.

**Placeholder:** [CIT-UNCERTAINTY-01]

## Slot RW-6: Domain context and data provenance

**Purpose:** Describe why consumer-finance complaint material is a meaningful
evaluation substrate without asserting regulatory or real-world decision validity.

**Required synthesis:**

1. Use official CFPB documentation for provenance and limitations.
2. Add bounded domain literature only where it directly motivates the study.
3. Avoid claims about individual companies, misconduct, or consumer-harm
   prevalence.

**Placeholders:** [CIT-CFPB-01], [CIT-FINAI-01]

## Slot RW-7: Reproducibility and claim traceability

**Purpose:** Position the committed manifests, source indexes, safety boundaries, and
claim matrices as reproducibility mechanisms.

**Required synthesis:**

1. Connect artefact traceability to recognised reproducibility guidance.
2. Describe exactly what is reproducible from sanitized committed outputs.
3. State what is intentionally unavailable, including raw prompts and responses.

**Placeholder:** [CIT-REPRO-01]
"""


def build_threats_framework() -> str:
    return """# Pilot 05AW Threats-to-Validity Framework

## Framing rule

The threats below qualify interpretation of the committed Pilot 05 findings. They do
not negate the observed run, and they do not introduce new empirical evidence.

## Construct validity

1. **Evidence-State Reliability operationalisation.** The empirical success
   indicators are tied to the committed task and scoring contract. They may not
   capture every relevant dimension of evidence reliability.
2. **Parser validity scope.** Parser validity measures structural conformance only.
   It must not be interpreted as correctness, faithfulness, or decision quality.
3. **Evidence degradation representation.** The selected controlled degradations are
   experimental proxies. They do not exhaust real-world evidence loss, ambiguity,
   contradiction, or manipulation.
4. **Stage-label interpretation.** “Decision,” “audit,” and “escalation” describe the
   experimental pipeline functions and should not be equated automatically with
   regulated institutional processes.

## Internal validity

1. **Prompt and protocol dependence.** Results may depend on the committed pipeline
   instructions, ordering, parser, and scoring implementation.
2. **Deterministic analysis dependence.** Derived metrics depend on the correctness
   of the committed parser and analysis code, although the repository includes
   operation-aware validation and traceability artefacts.
3. **Unobserved model-state variation.** Provider-side or runtime factors may affect
   outputs and are not fully identifiable from sanitized artefacts.
4. **No raw-response reinspection.** The safety boundary prevents independent
   qualitative reinspection of raw model responses in this task.
5. **Single-run interpretation.** The reported scaled run should not be treated as
   proof of invariance across repeated executions.

## External validity

1. **Single primary model/provider configuration.** The core result is bounded to
   the evaluated GLM-5.2 configuration.
2. **Domain boundary.** CFPB-backed complaint material provides a real-data substrate
   but does not establish validity for lending, underwriting, adjudication, or other
   financial decisions.
3. **Task boundary.** The selected cases and evidence conditions may not represent
   other document types, jurisdictions, languages, or organisational settings.
4. **Deployment boundary.** The experiment does not evaluate live users, production
   workflows, institutional controls, or downstream consumer outcomes.
5. **Temporal boundary.** Findings may not transfer unchanged across future model,
   provider, policy, or data versions.

## Conclusion validity

1. **Descriptive emphasis.** The central result is a measured contrast in this run,
   not a universal law.
2. **Multiple metrics and stages.** Interpretation should preserve the distinction
   among parser validity, stage/evidence success, audit behaviour, and escalation
   behaviour.
3. **Effect-size reporting.** Final submission should report denominators, absolute
   rates, and condition deltas rather than relying only on directional language.
4. **Uncertainty reporting.** Any inferential claims must match the committed
   robustness and sample structure; unsupported significance language must not be
   introduced.
5. **No prevalence inference.** Experimental failure rates must not be translated
   into prevalence estimates for consumer harm, company misconduct, or deployed AI
   failure.

## Reproducibility limitations

1. Sanitized outputs support artefact-level verification but not raw
   prompt/response replay.
2. No API keys, environment secrets, raw CFPB data, or JSONL traces are committed.
3. Provider availability and model-version continuity may limit exact future replay.
4. Citation placeholders remain unresolved until an explicitly approved literature
   task is completed.

**Future citation placeholder:** [CIT-VALIDITY-01]
"""


def build_claim_boundary() -> str:
    return """# Pilot 05AW Claim-Boundary Refinement

## Primary bounded claim

> Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that
> controlled evidence-state degradation produces measurable reliability-layer
> changes across decision, audit, and escalation stages. In this run, parser
> validity improved under degraded evidence while stage/evidence success
> deteriorated, supporting Evidence-State Reliability as distinct from parser
> validity.

## Permitted supporting claims

1. Pilot 05 evaluates a multi-stage decision, audit, and escalation pipeline under
   controlled evidence-state conditions.
2. Parser validity and stage/evidence success are analytically distinct metrics.
3. In the committed run, degraded evidence was associated with improved parser
   validity and deteriorated stage/evidence success.
4. The observed divergence motivates stage-aware and evidence-aware reliability
   evaluation.
5. Sanitized artefacts, manifests, source indexes, and claim-traceability outputs
   support bounded reproducibility auditing.

## Claims requiring explicit qualification

| Topic | Required qualifier |
|---|---|
| Causality | “Under the controlled Pilot 05 intervention” rather than unrestricted deployed-system causality |
| Generalisation | “In this GLM-5.2 run” rather than “LLMs generally” |
| Domain | “CFPB-backed experimental substrate” rather than real-world financial decision validity |
| Parser performance | “Structural validity” rather than correctness |
| Audit performance | “Experimental audit-stage behaviour” rather than regulatory assurance |
| Escalation | “Scored escalation behaviour” rather than optimal human oversight |
| Safety | “Reliability-layer evidence” rather than deployment safety certification |

## Prohibited claim expansions

The manuscript must not claim:

- broad GLM reliability;
- general LLM reliability;
- model or provider superiority;
- real-world financial validity;
- regulatory validity or compliance;
- deployment safety;
- consumer-harm prevalence;
- company misconduct;
- that parser validity equals answer correctness;
- that the evidence proves a universal causal mechanism;
- that journal acceptance or manuscript completion is guaranteed.

## Language substitutions

| Avoid | Use |
|---|---|
| “proves” | “supports within the evaluated design” |
| “shows LLMs are” | “shows that the evaluated pipeline was” |
| “financial decisions” | “CFPB-backed experimental cases” |
| “safe/unsafe” | “more or less reliable under the defined metric” |
| “audit succeeded” | “the audit-stage criterion was satisfied” |
| “correct output” when only parsed | “parser-valid output” |
| “caused” without design support | “was associated with” or “followed the controlled intervention” |

## Submission audit rule

Every empirical sentence in the final manuscript should be traceable to a committed
table, figure, manifest, or metric output. Every literature-dependent sentence
should carry an approved citation or an unresolved placeholder. No placeholder may
be converted into a named citation without source verification.
"""


def inject_sections(draft: str) -> str:
    refined = refine_academic_wording(draft)
    formal_insert = """
## Formal Definitions and Notation

The manuscript distinguishes evidence-state reliability from structural output
validity. Let \\(E_{i,c,k}\\) denote the evidence state supplied to case \\(i\\),
condition \\(c\\), and stage \\(k\\); let \\(V_{i,c,k}\\) indicate parser validity;
and let \\(R_{i,c,k}\\) indicate stage/evidence success under the committed Pilot 05
scoring contract.

For condition \\(c\\) and stage \\(k\\),

\\[
\\widehat{\\mathrm{PV}}_{c,k}
=
\\frac{1}{N_c}\\sum_{i=1}^{N_c}V_{i,c,k},
\\qquad
\\widehat{\\mathrm{ESR}}_{c,k}
=
\\frac{1}{N_c}\\sum_{i=1}^{N_c}R_{i,c,k}.
\\]

The central analytical distinction is that
\\(\\widehat{\\mathrm{PV}}_{c,k}\\) measures machine-readable structural
conformance, whereas \\(\\widehat{\\mathrm{ESR}}_{c,k}\\) measures success under an
evidence-sensitive stage criterion. A parser-valid output may therefore remain
evidence-unsuccessful. Full definitions and claim qualifications are provided in
the companion 05AW formalisation artefact.

[CIT-ESR-01] [CIT-PARSER-01] [CIT-PIPELINE-01]
""".strip()

    related_insert = """
## Related Work Structure

The final literature review should position this study across seven bounded areas:
output-level versus process-level reliability; multi-stage LLM pipelines; cascading
failure and error propagation; audit and assurance; uncertainty and escalation;
consumer-finance data provenance; and reproducible computational evaluation.

No external literature was searched during Task 05AW. The following identifiers are
unresolved placeholders rather than citations:
[CIT-ESR-01], [CIT-CASCADE-01], [CIT-PIPELINE-01], [CIT-PARSER-01],
[CIT-AUDIT-01], [CIT-UNCERTAINTY-01], [CIT-FINAI-01], [CIT-CFPB-01],
[CIT-VALIDITY-01], and [CIT-REPRO-01].
""".strip()

    threats_insert = """
## Threats to Validity

### Construct validity

Evidence-State Reliability is operationalised through the committed Pilot 05
stage/evidence criteria. Parser validity captures structural conformance only, and
the controlled degradation conditions do not represent every form of real-world
evidence loss or ambiguity.

### Internal validity

The result is conditional on the committed prompts, pipeline ordering, parser,
scoring rules, runtime, and model configuration. Sanitization and the prohibition on
raw-response access prevent qualitative reinspection in this refinement task.

### External validity

The main evidence is bounded to the evaluated GLM-5.2 configuration, selected
CFPB-backed cases, defined evidence conditions, and experimental decision-audit-
escalation pipeline. It does not establish deployment, jurisdictional, provider,
model-family, or financial-decision generality.

### Conclusion validity

The central pattern is descriptive of the committed run. Final reporting must
preserve denominators, absolute rates, condition deltas, and metric distinctions.
Experimental failure rates must not be converted into prevalence estimates for
consumer harm, company misconduct, or deployed-system failure.

### Reproducibility limitations

Committed sanitized outputs permit artefact-level validation but not raw prompt or
response replay. Citation placeholders remain unresolved pending an explicitly
approved literature-search task.

[CIT-VALIDITY-01] [CIT-REPRO-01]
""".strip()

    boundary_insert = """
## Claim Boundary

The strongest supported interpretation is:

> Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that
> controlled evidence-state degradation produces measurable reliability-layer
> changes across decision, audit, and escalation stages. In this run, parser
> validity improved under degraded evidence while stage/evidence success
> deteriorated, supporting Evidence-State Reliability as distinct from parser
> validity.

This result does not establish broad GLM reliability, general LLM reliability,
provider superiority, real-world financial validity, regulatory validity,
deployment safety, consumer-harm prevalence, company misconduct, or equivalence
between parser validity and answer correctness.
""".strip()

    preamble = f"""<!--
Task 05AW editorial refinement.
Source boundary: {SOURCE_BOUNDARY}.
{NO_NEW_EVIDENCE_STATEMENT}
Citation identifiers in square brackets are unresolved placeholders, not citations.
-->

"""

    blocks = [preamble + refined.rstrip(), formal_insert, related_insert, threats_insert, boundary_insert]
    return "\n\n---\n\n".join(blocks) + "\n"


def section_refinement_rows(original: str, refined: str) -> list[dict[str, str]]:
    original_headings = extract_headings(original)
    rows: list[dict[str, str]] = []
    for index, (level, heading) in enumerate(original_headings, start=1):
        rows.append(
            {
                "sequence": str(index),
                "source_heading": heading,
                "source_level": str(level),
                "refinement_action": "PRESERVED_AND_ACADEMIC_WORDING_TIGHTENED",
                "new_evidence_added": "NO",
                "citation_status": "PLACEHOLDERS_ONLY_WHERE_NEEDED",
            }
        )
    additions = [
        "Formal Definitions and Notation",
        "Related Work Structure",
        "Threats to Validity",
        "Claim Boundary",
    ]
    start = len(rows) + 1
    for offset, heading in enumerate(additions):
        rows.append(
            {
                "sequence": str(start + offset),
                "source_heading": heading,
                "source_level": "2",
                "refinement_action": "NEW_EDITORIAL_STRUCTURE_FROM_COMMITTED_05AV_ONLY",
                "new_evidence_added": "NO",
                "citation_status": "PLACEHOLDERS_ONLY",
            }
        )
    return rows


def validate_outputs(
    original_draft: str,
    refined_draft: str,
    citation_register: list[dict[str, str]],
) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    checks["source_boundary_declared"] = SOURCE_BOUNDARY in refined_draft
    checks["no_new_evidence_declared"] = "does not create, infer, or add new empirical evidence" in refined_draft
    checks["formal_notation_present"] = all(
        token in refined_draft
        for token in [
            "\\widehat{\\mathrm{PV}}",
            "\\widehat{\\mathrm{ESR}}",
            "parser validity",
            "stage/evidence success",
        ]
    )
    checks["threats_structure_present"] = all(
        heading in refined_draft
        for heading in [
            "### Construct validity",
            "### Internal validity",
            "### External validity",
            "### Conclusion validity",
            "### Reproducibility limitations",
        ]
    )
    checks["claim_boundary_present"] = "## Claim Boundary" in refined_draft
    original_nonblank_lines = [
        line
        for line in original_draft.replace("\r\n", "\n").split("\n")
        if line.strip()
    ]
    refined_lines = refined_draft.replace("\r\n", "\n").split("\n")
    retained_original_lines = [
        line for line in original_nonblank_lines if line in refined_lines
    ]
    original_line_retention_rate = (
        len(retained_original_lines) / len(original_nonblank_lines)
        if original_nonblank_lines
        else 0.0
    )

    ordered_cursor = 0
    ordered_retained_count = 0
    for original_line in original_nonblank_lines:
        while (
            ordered_cursor < len(refined_lines)
            and refined_lines[ordered_cursor] != original_line
        ):
            ordered_cursor += 1
        if ordered_cursor < len(refined_lines):
            ordered_retained_count += 1
            ordered_cursor += 1

    ordered_original_line_retention_rate = (
        ordered_retained_count / len(original_nonblank_lines)
        if original_nonblank_lines
        else 0.0
    )

    checks["original_draft_retention_rate"] = round(
        original_line_retention_rate,
        6,
    )
    checks["ordered_original_draft_retention_rate"] = round(
        ordered_original_line_retention_rate,
        6,
    )
    minimum_original_line_retention_rate = 0.95
    checks["minimum_original_draft_retention_rate"] = (
        minimum_original_line_retention_rate
    )
    checks["refined_draft_not_truncated"] = (
        len(refined_draft) >= len(original_draft)
    )
    checks["original_draft_retained"] = (
        original_line_retention_rate
        >= minimum_original_line_retention_rate
        and checks["refined_draft_not_truncated"]
    )
    checks["citation_placeholders_only"] = all(
        row["fabricated_citation"] == "NO"
        and row["status"] == "PLACEHOLDER_ONLY"
        for row in citation_register
    )
    checks["placeholder_count"] = len(citation_register)
    checks["no_named_reference_list_added"] = not bool(
        re.search(r"(?im)^##\s+References\s*$", refined_draft)
    )
    affirmative_overclaim_patterns = [
        r"(?im)^\s*(?![-*|])all\s+llms\s+are\s+unreliable[.!]?\s*$",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?|concludes?|finds?)\s+(?:that\s+)?all\s+llms\s+are\s+unreliable\b",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?)\s+(?:that\s+)?deployment\s+safety\b",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?)\s+(?:that\s+)?regulatory\s+validity\b",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?)\s+(?:that\s+)?company\s+misconduct\b",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:guarantees?|ensures?|proves?|establishes?)\s+(?:that\s+)?q1\s+acceptance\b",
        r"(?im)^\s*(?![-*|])parser\s+validity\s+(?:equals|establishes|proves)\s+answer\s+correctness[.!]?\s*$",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?|concludes?|finds?)\s+(?:that\s+)?parser\s+validity\s+(?:equals|establishes|proves)\s+answer\s+correctness\b",
        r"(?im)^\s*(?![-*|])(?:the\s+)?(?:model|provider)\s+is\s+superior[.!]?\s*$",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?|concludes?|finds?)\s+(?:that\s+)?(?:the\s+)?(?:model|provider)\s+is\s+superior\b",
        r"(?i)\b(?:this|the\s+(?:study|paper|experiment|result|analysis|evidence)|we)\s+(?:shows?|demonstrates?|proves?|establishes?|concludes?|finds?)\s+(?:that\s+)?(?:broad\s+glm|general\s+llm)\s+reliability\b",
    ]
    checks["prohibited_overclaims_absent_in_added_sections"] = not any(
        re.search(pattern, refined_draft)
        for pattern in affirmative_overclaim_patterns
    )

    boolean_checks = {
        key: value for key, value in checks.items() if isinstance(value, bool)
    }
    if not all(boolean_checks.values()):
        failed = [key for key, value in boolean_checks.items() if not value]
        fail("05AW content validation failed: " + ", ".join(failed))
    return checks


def verify_final_repository_state() -> list[str]:
    staged = run_git("diff", "--cached", "--name-only")
    modified = run_git("diff", "--name-only")
    if staged:
        fail(f"05AW generation unexpectedly staged files:\n{staged}")
    if modified:
        fail(f"05AW generation modified tracked files:\n{modified}")

    status_lines = [
        line
        for line in run_git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line.strip()
    ]

    observed_untracked: set[str] = set()
    unexpected_status: list[str] = []
    for line in status_lines:
        path = normalise(line[3:])
        if line.startswith("?? "):
            observed_untracked.add(path)
        else:
            unexpected_status.append(line)

    if unexpected_status:
        fail(
            "Unexpected non-untracked repository changes after 05AW generation:\n"
            + "\n".join(unexpected_status)
        )

    missing = sorted(EXPECTED_UNTRACKED - observed_untracked)
    unexpected = sorted(observed_untracked - EXPECTED_UNTRACKED)
    if missing or unexpected:
        fail(
            "05AW untracked-file contract failed.\n"
            f"Missing expected files: {missing}\n"
            f"Unexpected untracked files: {unexpected}"
        )

    return sorted(observed_untracked)


def main() -> None:
    verify_starting_state()
    sources = load_source_materials()

    manifest = json.loads(
        sources[
            "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_manifest.json"
        ]
    )
    if str(manifest.get("status", "")).upper() != "PASS":
        fail("Committed 05AV manifest status is not PASS.")

    original_draft = sources[
        "reports/pilot_05_full_manuscript_draft_assembly/pilot_05AV_full_manuscript_draft.md"
    ]
    if not original_draft.strip():
        fail("Committed 05AV full manuscript draft is empty.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = []
    for relative in SOURCE_FILES:
        source_rows.append(
            {
                "source_path": relative,
                "git_object": f"HEAD:{relative}",
                "sha256": hashlib.sha256(
                    sources[relative].encode("utf-8")
                ).hexdigest(),
                "source_task": "05AV",
                "committed_at_secured_checkpoint": "YES",
                "empirical_role": "SOURCE_ONLY_NO_NEW_EVIDENCE",
            }
        )
    write_csv(
        OUTPUT_DIR / "pilot_05AW_source_file_index.csv",
        [
            "source_path",
            "git_object",
            "sha256",
            "source_task",
            "committed_at_secured_checkpoint",
            "empirical_role",
        ],
        source_rows,
    )

    formal_definitions = build_formal_definitions()
    write_text(
        OUTPUT_DIR / "pilot_05AW_formal_definitions_and_notation.md",
        formal_definitions,
    )

    citations = citation_rows()
    write_csv(
        OUTPUT_DIR / "pilot_05AW_citation_placeholder_register.csv",
        [
            "placeholder_id",
            "manuscript_slot",
            "evidence_needed",
            "preferred_source_type",
            "claim_supported",
            "fabricated_citation",
            "status",
        ],
        citations,
    )

    write_text(
        OUTPUT_DIR / "pilot_05AW_related_work_slot_map.md",
        build_related_work_map(),
    )

    refined_draft = inject_sections(original_draft)
    write_text(
        OUTPUT_DIR / "pilot_05AW_refined_full_manuscript_draft.md",
        refined_draft,
    )

    write_text(
        OUTPUT_DIR / "pilot_05AW_threats_to_validity_framework.md",
        build_threats_framework(),
    )

    write_text(
        OUTPUT_DIR / "pilot_05AW_claim_boundary_refinement.md",
        build_claim_boundary(),
    )

    refinement_rows = section_refinement_rows(original_draft, refined_draft)
    write_csv(
        OUTPUT_DIR / "pilot_05AW_section_refinement_map.csv",
        [
            "sequence",
            "source_heading",
            "source_level",
            "refinement_action",
            "new_evidence_added",
            "citation_status",
        ],
        refinement_rows,
    )

    validation = validate_outputs(original_draft, refined_draft, citations)

    validation_report = f"""# Pilot 05AW Internal Validation Report

## Result

**Status: PASS**

## Task boundary

- Task: {TASK_ID} — {TASK_NAME}
- Secured source checkpoint: `{SECURED_COMMIT} {SECURED_COMMIT_MESSAGE}`
- Source boundary: `{SOURCE_BOUNDARY}`
- New empirical evidence: **NONE**
- External literature search: **NOT PERFORMED**
- Citation mode: **PLACEHOLDERS ONLY**

## Content checks

- Formal definitions and notation present: {validation['formal_notation_present']}
- Original committed 05AV manuscript retained: {validation['original_draft_retained']}
- Threats-to-validity structure present: {validation['threats_structure_present']}
- Claim-boundary section present: {validation['claim_boundary_present']}
- Citation placeholders validated: {validation['citation_placeholders_only']}
- Citation placeholder count: {validation['placeholder_count']}
- Named reference list added: {not validation['no_named_reference_list_added']}
- Prohibited overclaims detected in added sections: {not validation['prohibited_overclaims_absent_in_added_sections']}

## Safety checks

- No API calls
- No model calls
- No external literature search
- No `.env` read
- No raw prompt/response access
- No raw CFPB data access
- No JSONL writing
- No staging, commit, or push
- No committed file modification

## Interpretation

{NO_NEW_EVIDENCE_STATEMENT}
"""
    write_text(
        OUTPUT_DIR / "pilot_05AW_internal_validation_report.md",
        validation_report,
    )

    output_hashes = {}
    for relative in OUTPUT_FILES:
        if relative.endswith("pilot_05AW_manifest.json"):
            continue
        path = REPO / relative
        if not path.is_file():
            fail(f"Expected 05AW output missing before manifest creation: {relative}")
        output_hashes[relative] = sha256_file(path)

    manifest_output = {
        "task_id": TASK_ID,
        "task_name": TASK_NAME,
        "status": "PASS",
        "secured_source_commit": SECURED_COMMIT,
        "secured_source_commit_message": SECURED_COMMIT_MESSAGE,
        "source_boundary": SOURCE_BOUNDARY,
        "source_file_count": len(SOURCE_FILES),
        "output_file_count_including_manifest": len(OUTPUT_FILES),
        "citation_placeholder_count": len(citations),
        "new_empirical_evidence": False,
        "external_literature_search_performed": False,
        "citation_placeholders_only": True,
        "safety_flags": SAFETY_FLAGS,
        "no_new_evidence_statement": NO_NEW_EVIDENCE_STATEMENT,
        "output_sha256_excluding_manifest": output_hashes,
    }
    write_text(
        OUTPUT_DIR / "pilot_05AW_manifest.json",
        json.dumps(manifest_output, indent=2, ensure_ascii=False),
    )

    observed = verify_final_repository_state()

    print("=== TASK 05AW: FORMAL DEFINITIONS AND CITATION-PLACEHOLDER REFINEMENT ===")
    print("status: PASS")
    print(f"secured_checkpoint: {SECURED_COMMIT} {SECURED_COMMIT_MESSAGE}")
    print(f"source_boundary: {SOURCE_BOUNDARY}")
    print(f"source_files: {len(SOURCE_FILES)}")
    print(f"expected_untracked_files: {len(EXPECTED_UNTRACKED)}")
    print(f"observed_untracked_files: {len(observed)}")
    print(f"citation_placeholders: {len(citations)}")
    print("new_empirical_evidence: NONE")
    print("external_literature_search: NOT PERFORMED")
    print("api_or_model_calls: 0")
    print("env_read: NO")
    print("raw_prompt_response_access: NO")
    print("raw_cfpb_data_access: NO")
    print("jsonl_written: NO")
    print("staged_files: NONE")
    print("modified_tracked_files: NONE")
    print("commit_or_push: NO")
    print("")
    print("05AW local artifacts generated and validated:")
    for relative in observed:
        print(f"  - {relative}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"05AW FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
