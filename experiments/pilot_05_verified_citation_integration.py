from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path

TASK_ID = "05AY"
EXPECTED_COMMIT = "1c2731b9f9a3bf696b2e8055ff703b1d41e42f5a"

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "reports" / "pilot_05_verified_citation_integration"

BASE_MANUSCRIPT = (
    ROOT
    / "reports"
    / "pilot_05_formal_definition_citation_refinement"
    / "pilot_05AW_refined_full_manuscript_draft.md"
)
SOURCE_REGISTER = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_verified_source_register.csv"
)
PLACEHOLDER_MAP = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_citation_placeholder_resolution_map.csv"
)
RELATED_SYNTHESIS = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_related_work_synthesis.md"
)
INSERTION_PLAN = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_manuscript_citation_insertion_plan.md"
)
CLAIM_MAP = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_claim_to_source_map.csv"
)
NOVELTY_ANALYSIS = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_novelty_boundary_analysis.md"
)
SOURCE_VERIFICATION = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_source_verification_report.md"
)
AX_MANIFEST = (
    ROOT
    / "reports"
    / "pilot_05_external_literature_grounding"
    / "pilot_05AX_manifest.json"
)

OUTPUT_FILES = {
    "manuscript": OUTPUT_DIR / "pilot_05AY_citation_integrated_manuscript.md",
    "references": OUTPUT_DIR / "pilot_05AY_reference_list.md",
    "usage": OUTPUT_DIR / "pilot_05AY_citation_usage_register.csv",
    "placeholder_audit": OUTPUT_DIR / "pilot_05AY_placeholder_resolution_audit.csv",
    "section_map": OUTPUT_DIR / "pilot_05AY_section_integration_map.csv",
    "novelty_audit": OUTPUT_DIR / "pilot_05AY_novelty_wording_audit.md",
    "empirical_report": OUTPUT_DIR / "pilot_05AY_empirical_preservation_report.md",
    "source_index": OUTPUT_DIR / "pilot_05AY_source_file_index.csv",
    "validation": OUTPUT_DIR / "pilot_05AY_internal_validation_report.md",
    "manifest": OUTPUT_DIR / "pilot_05AY_manifest.json",
}

PLACEHOLDER_SOURCES = {
    "CIT-ESR-01": [
        "SRC-CHECKLIST-2020",
        "SRC-CALIBRATION-2017",
        "SRC-RAGAS-2024",
        "SRC-ARES-2024",
        "SRC-INSUFFICIENT-EVIDENCE-2022",
        "SRC-SURE-RAG-2026",
        "SRC-EVIDENCE-DELAY-2026",
    ],
    "CIT-CASCADE-01": [
        "SRC-CASCADE-NETWORKS-2002",
        "SRC-AGENTBENCH-2024",
        "SRC-SPARK-FIRE-2026",
        "SRC-HALLUCINATION-CASCADE-2026",
    ],
    "CIT-PIPELINE-01": [
        "SRC-AGENTBENCH-2024",
        "SRC-RAGAS-2024",
        "SRC-ARES-2024",
    ],
    "CIT-PARSER-01": [
        "SRC-GCD-2023",
        "SRC-CONSTRAINT-TAX-2026",
        "SRC-STRUCTURED-BENCH-2026",
    ],
    "CIT-AUDIT-01": [
        "SRC-AUDIT-2020",
        "SRC-FSB-AI-2017",
        "SRC-FSB-AI-2026",
    ],
    "CIT-UNCERTAINTY-01": [
        "SRC-DEFER-2020",
        "SRC-SELECTIVENET-2019",
        "SRC-SURE-RAG-2026",
        "SRC-EVIDENCE-DELAY-2026",
    ],
    "CIT-FINAI-01": [
        "SRC-FSB-AI-2017",
        "SRC-FSB-AI-2026",
    ],
    "CIT-CFPB-01": ["SRC-CFPB-DATABASE"],
    "CIT-VALIDITY-01": ["SRC-WOHLIN-2012"],
    "CIT-REPRO-01": ["SRC-REPRO-2021"],
}

CITATION_LABELS = {
    "SRC-CHECKLIST-2020": "Ribeiro et al., 2020",
    "SRC-CALIBRATION-2017": "Guo et al., 2017",
    "SRC-GCD-2023": "Geng et al., 2023",
    "SRC-CONSTRAINT-TAX-2026": "Ray, 2026, preprint",
    "SRC-STRUCTURED-BENCH-2026": "Singh et al., 2026, preprint",
    "SRC-AGENTBENCH-2024": "Liu et al., 2024",
    "SRC-RAGAS-2024": "Es et al., 2024",
    "SRC-ARES-2024": "Saad-Falcon et al., 2024",
    "SRC-INSUFFICIENT-EVIDENCE-2022": "Atanasova et al., 2022, preprint",
    "SRC-AUDIT-2020": "Raji et al., 2020",
    "SRC-DEFER-2020": "Mozannar and Sontag, 2020",
    "SRC-SELECTIVENET-2019": "Geifman and El-Yaniv, 2019",
    "SRC-CFPB-DATABASE": "Consumer Financial Protection Bureau, 2025",
    "SRC-FSB-AI-2017": "Financial Stability Board, 2017",
    "SRC-FSB-AI-2026": "Financial Stability Board, 2026, consultation report",
    "SRC-WOHLIN-2012": "Wohlin et al., 2012",
    "SRC-REPRO-2021": "Pineau et al., 2021",
    "SRC-CASCADE-NETWORKS-2002": "Motter and Lai, 2002",
    "SRC-SPARK-FIRE-2026": "Xie et al., 2026, preprint",
    "SRC-HALLUCINATION-CASCADE-2026": "Jamshidi et al., 2026, preprint",
    "SRC-SURE-RAG-2026": "Qiu et al., 2026, preprint",
    "SRC-EVIDENCE-DELAY-2026": "Solozobov, 2026, preprint",
}

SELECTED_SOURCE_IDS = [
    "SRC-CHECKLIST-2020",
    "SRC-CALIBRATION-2017",
    "SRC-GCD-2023",
    "SRC-CONSTRAINT-TAX-2026",
    "SRC-STRUCTURED-BENCH-2026",
    "SRC-AGENTBENCH-2024",
    "SRC-RAGAS-2024",
    "SRC-ARES-2024",
    "SRC-INSUFFICIENT-EVIDENCE-2022",
    "SRC-AUDIT-2020",
    "SRC-DEFER-2020",
    "SRC-SELECTIVENET-2019",
    "SRC-CFPB-DATABASE",
    "SRC-FSB-AI-2017",
    "SRC-FSB-AI-2026",
    "SRC-WOHLIN-2012",
    "SRC-REPRO-2021",
    "SRC-CASCADE-NETWORKS-2002",
    "SRC-SPARK-FIRE-2026",
    "SRC-HALLUCINATION-CASCADE-2026",
    "SRC-SURE-RAG-2026",
    "SRC-EVIDENCE-DELAY-2026",
]

PROTECTED_LITERALS = [
    "720 planned/ledgered pipeline calls",
    "713 retained rows",
    "-0.517241 to -0.40678",
    "0.067797 to 0.368421",
    "0.929167",
    "1.0",
    "0.0",
    "parser validity improves while stage/evidence success deteriorates",
    "7 ledger rows have no corresponding sanitized execution row",
]

PROHIBITED_PRIORITY_PATTERNS = [
    r"\bfirst[- ]ever\b",
    r"\bfirst study\b",
    r"\bfirst work\b",
    r"\bwe are the first\b",
    r"\bno prior work\b",
    r"\bprevious research has ignored\b",
    r"\bcompletely novel\b",
    r"\buniversally novel\b",
]

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")

def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def cite(*source_ids: str) -> str:
    missing = [source_id for source_id in source_ids if source_id not in CITATION_LABELS]
    if missing:
        raise RuntimeError(f"Missing citation label(s): {missing}")
    return "(" + "; ".join(CITATION_LABELS[source_id] for source_id in source_ids) + ")"

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)

def replace_heading_section(
    text: str,
    start_heading: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    start = text.find(start_heading)
    if start < 0:
        raise RuntimeError(f"{label}: start heading not found")
    end = text.find(end_marker, start + len(start_heading))
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]

def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"Missing section start: {start_marker}")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"Missing section end: {end_marker}")
    return text[start:end]

def validate_inputs() -> tuple[str, list[dict[str, str]], dict[str, dict[str, str]]]:
    required_paths = [
        BASE_MANUSCRIPT,
        SOURCE_REGISTER,
        PLACEHOLDER_MAP,
        RELATED_SYNTHESIS,
        INSERTION_PLAN,
        CLAIM_MAP,
        NOVELTY_ANALYSIS,
        SOURCE_VERIFICATION,
        AX_MANIFEST,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required_paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing committed input files: {missing}")

    ax_manifest = json.loads(read_text(AX_MANIFEST))
    if ax_manifest.get("task_id") != "05AX" or ax_manifest.get("status") != "PASS":
        raise RuntimeError("Committed 05AX manifest is not PASS")
    if ax_manifest.get("secured_input_commit") != "f05ae265706bff5e408ae80c35f07e019a850d4d":
        raise RuntimeError("Unexpected secured input commit in 05AX manifest")
    if int(ax_manifest["counts"]["verified_source_rows"]) != 24:
        raise RuntimeError("05AX verified source count is not 24")
    if int(ax_manifest["counts"]["resolution_rows"]) != 10:
        raise RuntimeError("05AX placeholder resolution count is not 10")

    with SOURCE_REGISTER.open("r", encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    if len(source_rows) != 24:
        raise RuntimeError(f"Expected 24 verified source rows, found {len(source_rows)}")

    source_by_id = {row["source_id"]: row for row in source_rows}
    if len(source_by_id) != len(source_rows):
        raise RuntimeError("Duplicate source_id values in verified source register")

    missing_sources = [
        source_id for source_id in SELECTED_SOURCE_IDS if source_id not in source_by_id
    ]
    if missing_sources:
        raise RuntimeError(f"Selected source IDs missing from register: {missing_sources}")

    non_verified = [
        source_id
        for source_id in SELECTED_SOURCE_IDS
        if not source_by_id[source_id]["verification_status"].startswith("VERIFIED_")
    ]
    if non_verified:
        raise RuntimeError(f"Selected sources are not verified: {non_verified}")

    with PLACEHOLDER_MAP.open("r", encoding="utf-8", newline="") as handle:
        resolution_rows = list(csv.DictReader(handle))
    if len(resolution_rows) != 10:
        raise RuntimeError(f"Expected 10 placeholder rows, found {len(resolution_rows)}")

    base = read_text(BASE_MANUSCRIPT)
    for placeholder_id in PLACEHOLDER_SOURCES:
        token = f"[{placeholder_id}]"
        if token not in base:
            raise RuntimeError(f"Base manuscript is missing placeholder token {token}")

    return base, resolution_rows, source_by_id

def build_related_work() -> str:
    return f"""## 2.4 Related work and bounded novelty position

### Evaluation beyond a single output signal

Model evaluation is multidimensional rather than reducible to one success indicator. Behavioral testing demonstrates that held-out accuracy can conceal capability-specific weaknesses, calibration separates confidence quality from predictive correctness, and retrieval-augmented-generation evaluation separates context relevance, faithful context use, and answer relevance {cite("SRC-CHECKLIST-2020", "SRC-CALIBRATION-2017", "SRC-RAGAS-2024", "SRC-ARES-2024")}. Evidence-State Reliability is positioned as a narrower operational layer within this broader landscape: it concerns whether the evidence supplied to downstream functions remains sufficiently complete and usable for those functions. It does not replace accuracy, calibration, robustness, or faithfulness.

### Structured output validity and substantive correctness

Formal conformance is an established and useful output property. Grammar-constrained decoding can improve or guarantee adherence to required structures, and emerging structured-output studies explicitly separate schema validity from value-level or executable correctness {cite("SRC-GCD-2023", "SRC-CONSTRAINT-TAX-2026", "SRC-STRUCTURED-BENCH-2026")}. Consequently, this study does not claim that structural and substantive validity have never been distinguished. Its narrower contribution is to manipulate the evidence state supplied to a multi-stage decision pipeline and measure the resulting decision, audit, escalation, parser-validity, and recovery behavior.

### Evidence sufficiency and intermediate support

Prior work has directly examined insufficient evidence in fact checking and evidence sufficiency in retrieval-augmented generation {cite("SRC-INSUFFICIENT-EVIDENCE-2022", "SRC-SURE-RAG-2026")}. Emerging work also considers evidence sufficiency in risk decision systems with delayed ground truth {cite("SRC-EVIDENCE-DELAY-2026")}. These are close antecedents. The present operational distinction is that explicit evidence conditions are frozen and propagated through decision, audit, and escalation functions, enabling stage-specific comparison with parser validity and recovery.

### Multi-stage systems and reliability cascades

Interactive-agent benchmarks and RAG evaluation frameworks motivate component-aware evaluation in multi-component systems {cite("SRC-AGENTBENCH-2024", "SRC-RAGAS-2024", "SRC-ARES-2024")}. Cascading failure is also an established systems concept {cite("SRC-CASCADE-NETWORKS-2002")}, and emerging LLM preprints study seeded-error and hallucination propagation in multi-agent collaboration {cite("SRC-SPARK-FIRE-2026", "SRC-HALLUCINATION-CASCADE-2026")}. “Reliability cascade” is therefore used here in a deliberately narrower experimental sense: condition-linked reliability changes across decision, audit, and escalation under a controlled evidence-state intervention. The study does not claim to invent cascade theory or establish deployed-system causality.

### Audit, assurance, abstention, and escalation

Algorithmic-audit research emphasizes lifecycle accountability, documentation, traceability, and institutional processes {cite("SRC-AUDIT-2020")}. The computational audit stage in Pilot 05 is much narrower and must not be equated with organizational or regulatory audit. Selective prediction and learning-to-defer likewise establish abstention and expert deferral as distinct downstream decision functions {cite("SRC-SELECTIVENET-2019", "SRC-DEFER-2020")}. Pilot 05 asks a different bounded question: whether escalation recovers after controlled evidence degradation. It does not establish an optimal escalation policy.

### Financial context and CFPB provenance

Financial-sector reports motivate careful testing, interpretability, auditability, and governance of AI-enabled financial services {cite("SRC-FSB-AI-2017", "SRC-FSB-AI-2026")}. The 2026 source is a consultation report rather than final guidance. The CFPB describes its Consumer Complaint Database as a public resource while warning that complaints are not a statistical sample, narratives are consumer accounts, and interpretation requires contextual information {cite("SRC-CFPB-DATABASE")}. The database is used here only as a bounded provenance and evaluation substrate; the experiment does not establish complaint truth, misconduct, prevalence, regulatory validity, or deployment performance.

### Bounded novelty statement

The literature supports a combination-and-operationalisation contribution rather than a global-priority claim. The paper combines controlled evidence-state degradation, a decision–audit–escalation pipeline, stage-specific reliability measurement, parser-versus-evidence comparison, and recovery analysis in one reproducible experimental design. Its strongest contribution is the committed empirical pattern that parser validity increased while evidence-sensitive stage success deteriorated within Pilot 05. Adjacent research narrows the claim but does not eliminate this specific operational and empirical contribution."""

def build_references(source_by_id: dict[str, dict[str, str]]) -> tuple[str, str]:
    entries = []
    for source_id in SELECTED_SOURCE_IDS:
        row = source_by_id[source_id]
        status_note = ""
        if row["peer_review_status"].startswith("not_peer_reviewed"):
            status_note = " [Preprint; not peer reviewed as verified in 05AX.]"
        elif row["source_class"] == "official_institutional_consultation":
            status_note = " [Consultation report; not final guidance.]"

        identifier = row["identifier"].strip()
        identifier_part = f" {identifier}." if identifier else ""
        entry = (
            f"- {row['authors']} ({row['year']}). *{row['title']}*. "
            f"{row['venue_or_institution']}.{identifier_part} "
            f"{row['stable_url']}.{status_note}"
        )
        entries.append(entry.replace("..", "."))

    reference_section = "## References\n\n" + "\n".join(entries)
    standalone = (
        "# Pilot 05AY Verified Reference List\n\n"
        "All entries below are generated only from the committed 05AX verified source "
        "register. Preprints and consultation material are explicitly labelled.\n\n"
        + "\n".join(entries)
    )
    return reference_section, standalone

def integrate_manuscript(
    base: str,
    source_by_id: dict[str, dict[str, str]],
) -> tuple[str, list[dict[str, str]], str]:
    text = base
    section_rows: list[dict[str, str]] = []

    old_comment = """<!--
Task 05AW editorial refinement.
Source boundary: committed 05AV outputs only.
Task 05AW performs manuscript-structure, notation, citation-placeholder, related-work-slot, academic-wording, threats-to-validity, and claim-boundary refinement only. It does not create, infer, or add new empirical evidence.
Citation identifiers in square brackets are unresolved placeholders, not citations.
-->"""
    new_comment = """<!--
Task 05AY verified citation and related-work integration.
Source boundary: committed 05AW manuscript plus committed 05AX literature-grounding artifacts only.
Task 05AY creates a new derivative manuscript; it does not modify the committed 05AW manuscript, create empirical evidence, run experiments, or make model/API calls.
External citations support literature context and claim boundaries only. Pilot 05 empirical results remain sourced exclusively to committed internal artifacts.
-->"""
    text = replace_once(text, old_comment, new_comment, "header comment")
    section_rows.append(
        {
            "section": "Document provenance",
            "operation": "replace",
            "source_artifacts": "05AW manuscript; 05AX manifest",
            "empirical_content_changed": "NO",
        }
    )

    old_status = (
        "Draft assembled by Task 05AV from committed 05AU synthesis artifacts only. "
        "This draft does not create new empirical evidence."
    )
    new_status = (
        "Citation-integrated derivative produced from the committed 05AW manuscript "
        "and committed 05AX verified literature artifacts. This draft does not create "
        "new empirical evidence."
    )
    text = replace_once(text, old_status, new_status, "manuscript status")

    intro_anchor = (
        "The strongest empirical pattern is that parser validity can improve while "
        "evidence-state reliability deteriorates. This makes the work more than another "
        "LLM error-analysis exercise. The paper targets a reliability layer that parser-level "
        "checks can miss."
    )
    intro_addition = intro_anchor + f"""

Evaluation research already treats model quality as multidimensional: behavioral tests, calibration, and RAG evaluation distinguish capabilities, confidence, context relevance, faithfulness, and answer quality {cite("SRC-CHECKLIST-2020", "SRC-CALIBRATION-2017", "SRC-RAGAS-2024", "SRC-ARES-2024")}. Structured-output research also distinguishes formal conformance from substantive correctness {cite("SRC-GCD-2023", "SRC-CONSTRAINT-TAX-2026", "SRC-STRUCTURED-BENCH-2026")}. The contribution claimed here is therefore not the first recognition that evaluation has multiple dimensions or that schema validity can diverge from correctness. It is the controlled combination and operationalisation of evidence-state interventions, stage-aware decision–audit–escalation measurement, and parser-versus-evidence comparison in the committed Pilot 05 design."""
    text = replace_once(text, intro_anchor, intro_addition, "introduction grounding")
    section_rows.append(
        {
            "section": "Introduction",
            "operation": "insert verified evaluation and structured-output context",
            "source_artifacts": "05AX source register; insertion plan",
            "empirical_content_changed": "NO",
        }
    )

    related_work = build_related_work()
    text = replace_once(
        text,
        "## 3. Methods",
        related_work + "\n\n## 3. Methods",
        "main related-work insertion",
    )
    section_rows.append(
        {
            "section": "2.4 Related work and bounded novelty position",
            "operation": "insert",
            "source_artifacts": "05AX related-work synthesis; source register",
            "empirical_content_changed": "NO",
        }
    )

    data_anchor = (
        "The study uses sanitized CFPB-backed evidence packets and committed derived "
        "outputs only. The manuscript synthesis does not read raw CFPB data, raw model "
        "prompts, raw model responses, JSONL model-output files, or environment/API-key material."
    )
    data_replacement = data_anchor + f"""

The CFPB Consumer Complaint Database is used only as a provenance source for the sanitized evaluation substrate. The CFPB states that complaints are not a statistical sample, narratives are consumer accounts, and analysis requires contextual information {cite("SRC-CFPB-DATABASE")}. Accordingly, this study does not treat complaint narratives as independently verified facts or infer prevalence, misconduct, regulatory validity, or real-world decision performance."""
    text = replace_once(text, data_anchor, data_replacement, "CFPB provenance")
    section_rows.append(
        {
            "section": "Methods: data and evidence-state boundary",
            "operation": "insert provenance and limitation citation",
            "source_artifacts": "SRC-CFPB-DATABASE",
            "empirical_content_changed": "NO",
        }
    )

    audit_line = (
        "2. **Audit stage**: evaluates whether the evidence and decision state should "
        "trigger detection or concern."
    )
    audit_replacement = (
        audit_line
        + f" This computational stage is narrower than lifecycle or organizational "
        f"algorithmic auditing {cite('SRC-AUDIT-2020')}."
    )
    text = replace_once(text, audit_line, audit_replacement, "audit boundary citation")

    escalation_line = (
        "3. **Escalation stage**: evaluates whether downstream recovery or escalation "
        "behavior succeeds under degraded evidence conditions."
    )
    escalation_replacement = (
        escalation_line
        + f" Treating escalation separately is consistent with selective-prediction and "
        f"learning-to-defer research, without implying that the present policy is optimal "
        f"{cite('SRC-SELECTIVENET-2019', 'SRC-DEFER-2020')}."
    )
    text = replace_once(
        text,
        escalation_line,
        escalation_replacement,
        "escalation boundary citation",
    )
    section_rows.append(
        {
            "section": "Methods: pipeline stages",
            "operation": "add audit and escalation boundaries",
            "source_artifacts": "SRC-AUDIT-2020; SRC-SELECTIVENET-2019; SRC-DEFER-2020",
            "empirical_content_changed": "NO",
        }
    )

    old_novelty = """## Main novelty

The novelty is not that LLMs can make mistakes. The novelty is that a multi-stage LLM decision pipeline can become more parser-valid while becoming less reliable at the evidence-state layer. This creates a reliability cascade that final-output parser checks can miss.

## Why this is stronger than a normal LLM evaluation paper

A normal evaluation paper often asks whether the final answer is correct, valid, or parseable. This work asks whether the evidence state passed through the system remains reliable enough for downstream decision, audit, and escalation behavior."""
    new_novelty = f"""## Bounded novelty position

The contribution is not a global-priority claim about multidimensional evaluation, evidence sufficiency, structural-versus-substantive validity, or cascade theory. Each has established or emerging antecedents {cite("SRC-GCD-2023", "SRC-INSUFFICIENT-EVIDENCE-2022", "SRC-CASCADE-NETWORKS-2002", "SRC-SURE-RAG-2026")}. The distinct contribution is the controlled combination and operationalisation of evidence-state degradation across decision, audit, and escalation, together with stage-specific parser, success, detection, recovery, and cascade measurements.

## Why the contribution remains distinct

The manuscript asks whether evidence supplied across pipeline stages remains sufficiently usable for downstream functions and whether parser behavior can diverge from evidence-sensitive stage behavior. Within the committed Pilot 05 run, the observed divergence provides the empirical contribution; external literature is used only to position that result and delimit the claim."""
    text = replace_once(text, old_novelty, new_novelty, "novelty paragraph")
    section_rows.append(
        {
            "section": "Contribution and novelty",
            "operation": "replace broad novelty language with bounded differentiation",
            "source_artifacts": "05AX novelty analysis; close-antecedent sources",
            "empirical_content_changed": "NO",
        }
    )

    formal_placeholder_line = "[CIT-ESR-01] [CIT-PARSER-01] [CIT-PIPELINE-01]"
    formal_citations = cite(
        "SRC-RAGAS-2024",
        "SRC-ARES-2024",
        "SRC-GCD-2023",
        "SRC-AGENTBENCH-2024",
    )
    text = replace_once(
        text,
        formal_placeholder_line,
        (
            "This formal separation is positioned relative to component-aware RAG "
            "evaluation, structured generation, and agent evaluation "
            f"{formal_citations}."
        ),
        "formal-definition placeholders",
    )

    literature_provenance = """## Literature Integration Provenance

Task 05AY resolves all ten 05AW citation placeholders using only the committed 05AX verified source register, placeholder-resolution map, related-work synthesis, novelty analysis, and citation-insertion plan. External sources position the conceptual framing, related work, domain provenance, validity framework, and reproducibility statement. They do not validate or alter Pilot 05 empirical values.

The 05AX novelty verdict is preserved: bounded combination-and-operationalisation differentiation is supported, while global priority is not established."""
    text = replace_heading_section(
        text,
        "## Related Work Structure",
        "---",
        literature_provenance,
        "late related-work placeholder section",
    )
    section_rows.append(
        {
            "section": "Literature integration provenance",
            "operation": "replace obsolete placeholder list",
            "source_artifacts": "05AX manifest; resolution map",
            "empirical_content_changed": "NO",
        }
    )

    old_repro = (
        "Committed sanitized outputs permit artefact-level validation but not raw prompt or\n"
        "response replay. Citation placeholders remain unresolved pending an explicitly\n"
        "approved literature-search task.\n\n"
        "[CIT-VALIDITY-01] [CIT-REPRO-01]"
    )
    new_repro = (
        "Committed sanitized outputs permit artefact-level validation but not raw prompt or\n"
        "response replay. Threats are organized using construct, internal, external, and\n"
        f"conclusion-validity categories {cite('SRC-WOHLIN-2012')}. Reproducibility claims\n"
        f"are limited to transparent reporting and sanitized artefact traceability\n"
        f"{cite('SRC-REPRO-2021')}; full raw-response replay is not claimed."
    )
    text = replace_once(text, old_repro, new_repro, "validity/reproducibility placeholders")
    section_rows.append(
        {
            "section": "Threats to validity and reproducibility",
            "operation": "resolve validity and reproducibility placeholders",
            "source_artifacts": "SRC-WOHLIN-2012; SRC-REPRO-2021",
            "empirical_content_changed": "NO",
        }
    )

    old_checkpoint = """- latest_commit: `725c8dd Add Pilot 05 repo validation audit`
- latest_hash: `725c8dd`
- latest_subject: `Add Pilot 05 repo validation audit`
- origin_main_alignment: `0 behind, 0 ahead`"""
    new_checkpoint = """- 05AY source checkpoint: `1c2731b9f9a3bf696b2e8055ff703b1d41e42f5a`
- source checkpoint subject: `Add Pilot 05 literature grounding and novelty analysis`
- source branch: `main`
- source alignment at task start: `0 behind, 0 ahead`"""
    text = replace_once(text, old_checkpoint, new_checkpoint, "reproducibility checkpoint")
    section_rows.append(
        {
            "section": "Reproducibility statement",
            "operation": "update source checkpoint and integrate reporting citation",
            "source_artifacts": "Git checkpoint; SRC-REPRO-2021",
            "empirical_content_changed": "NO",
        }
    )

    reference_section, standalone_references = build_references(source_by_id)
    appendix_marker = "## Appendix A. Next revision roadmap"
    text = replace_once(
        text,
        appendix_marker,
        reference_section + "\n\n" + appendix_marker,
        "reference-section insertion",
    )
    section_rows.append(
        {
            "section": "References",
            "operation": "insert verified reference list",
            "source_artifacts": "05AX verified source register",
            "empirical_content_changed": "NO",
        }
    )

    text = text.replace(
        "- Do not submit before a full literature-grounded related-work section is built.",
        "- Do not submit before citation formatting and reference metadata are rechecked against the selected journal style.",
    )

    for placeholder_id in PLACEHOLDER_SOURCES:
        if f"[{placeholder_id}]" in text:
            raise RuntimeError(f"Unresolved placeholder remains: {placeholder_id}")
    if "[CIT-" in text:
        raise RuntimeError("An unresolved CIT placeholder remains in the manuscript")

    return text, section_rows, standalone_references

def build_usage_rows(source_by_id: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    roles = {
        "SRC-CHECKLIST-2020": "Introduction and related work: multidimensional evaluation",
        "SRC-CALIBRATION-2017": "Introduction and related work: confidence as separate dimension",
        "SRC-GCD-2023": "Parser validity and structured generation boundary",
        "SRC-CONSTRAINT-TAX-2026": "Close emerging antecedent: validity-correctness trade-off",
        "SRC-STRUCTURED-BENCH-2026": "Close emerging antecedent: schema versus value accuracy",
        "SRC-AGENTBENCH-2024": "Multi-stage and interactive-agent evaluation context",
        "SRC-RAGAS-2024": "Component-aware RAG evaluation context",
        "SRC-ARES-2024": "Component-aware RAG evaluation context",
        "SRC-INSUFFICIENT-EVIDENCE-2022": "Close antecedent: insufficient evidence intervention",
        "SRC-AUDIT-2020": "Audit boundary and lifecycle-accountability context",
        "SRC-DEFER-2020": "Escalation and expert-deferral context",
        "SRC-SELECTIVENET-2019": "Escalation and reject-option context",
        "SRC-CFPB-DATABASE": "Official data provenance and limitations",
        "SRC-FSB-AI-2017": "Financial-domain motivation and auditability context",
        "SRC-FSB-AI-2026": "Current financial-domain context; consultation only",
        "SRC-WOHLIN-2012": "Threats-to-validity framework",
        "SRC-REPRO-2021": "Reproducibility and reporting framework",
        "SRC-CASCADE-NETWORKS-2002": "General cascade concept anchor",
        "SRC-SPARK-FIRE-2026": "Close emerging LLM cascade antecedent",
        "SRC-HALLUCINATION-CASCADE-2026": "Close emerging LLM cascade antecedent",
        "SRC-SURE-RAG-2026": "Close emerging evidence-sufficiency antecedent",
        "SRC-EVIDENCE-DELAY-2026": "Close emerging evidence-sufficiency antecedent",
    }
    return [
        {
            "source_id": source_id,
            "citation_label": CITATION_LABELS[source_id],
            "manuscript_role": roles[source_id],
            "verification_status": source_by_id[source_id]["verification_status"],
            "source_class": source_by_id[source_id]["source_class"],
            "peer_review_status": source_by_id[source_id]["peer_review_status"],
            "central_or_contextual": source_by_id[source_id]["central_or_contextual"],
        }
        for source_id in SELECTED_SOURCE_IDS
    ]

def main() -> None:
    if OUTPUT_DIR.exists():
        raise RuntimeError(f"Output directory already exists: {OUTPUT_DIR}")

    base, resolution_rows, source_by_id = validate_inputs()
    integrated, section_rows, standalone_references = integrate_manuscript(base, source_by_id)

    base_results = extract_between(base, "## 4. Results", "## 5. Contribution and novelty")
    integrated_results = extract_between(
        integrated, "## 4. Results", "## 5. Contribution and novelty"
    )
    results_preserved = base_results == integrated_results
    if not results_preserved:
        raise RuntimeError("The committed Results section changed during citation integration")

    protected_failures = [
        literal for literal in PROTECTED_LITERALS if literal not in integrated
    ]
    if protected_failures:
        raise RuntimeError(f"Protected empirical literal(s) missing: {protected_failures}")

    priority_hits = []
    for pattern in PROHIBITED_PRIORITY_PATTERNS:
        if re.search(pattern, integrated, flags=re.IGNORECASE):
            priority_hits.append(pattern)
    if priority_hits:
        raise RuntimeError(f"Prohibited global-priority language detected: {priority_hits}")

    all_registered_ids = set(source_by_id)
    unknown_selected = [sid for sid in SELECTED_SOURCE_IDS if sid not in all_registered_ids]
    if unknown_selected:
        raise RuntimeError(f"Unknown selected source IDs: {unknown_selected}")

    reference_section, standalone_reference_text = build_references(source_by_id)
    if len(SELECTED_SOURCE_IDS) != 22:
        raise RuntimeError("Expected 22 selected references")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)

    write_text(OUTPUT_FILES["manuscript"], integrated)
    write_text(OUTPUT_FILES["references"], standalone_reference_text)

    usage_rows = build_usage_rows(source_by_id)
    write_csv(
        OUTPUT_FILES["usage"],
        usage_rows,
        [
            "source_id",
            "citation_label",
            "manuscript_role",
            "verification_status",
            "source_class",
            "peer_review_status",
            "central_or_contextual",
        ],
    )

    placeholder_rows = []
    for placeholder_id, source_ids in PLACEHOLDER_SOURCES.items():
        placeholder_rows.append(
            {
                "placeholder_id": placeholder_id,
                "status": "RESOLVED",
                "source_ids": ";".join(source_ids),
                "literal_token_remaining": "NO",
                "resolution_boundary": (
                    "Context and related-work support only; external sources do not "
                    "validate Pilot 05 empirical values."
                ),
            }
        )
    write_csv(
        OUTPUT_FILES["placeholder_audit"],
        placeholder_rows,
        [
            "placeholder_id",
            "status",
            "source_ids",
            "literal_token_remaining",
            "resolution_boundary",
        ],
    )

    write_csv(
        OUTPUT_FILES["section_map"],
        section_rows,
        [
            "section",
            "operation",
            "source_artifacts",
            "empirical_content_changed",
        ],
    )

    novelty_audit = f"""# Pilot 05AY Novelty Wording Audit

## Status

PASS

## Preserved novelty boundary

The integrated manuscript presents the contribution as a bounded
combination-and-operationalisation contribution. It does not claim global priority,
global-priority novelty, invention of cascade theory, or first recognition of evidence
insufficiency or structured-versus-substantive divergence.

## Defensible contribution

The specific contribution is the combination of:

1. controlled evidence-state degradation;
2. a decision–audit–escalation pipeline;
3. stage-specific parser and evidence-sensitive success metrics;
4. detection-versus-recovery separation;
5. cascade-sequence measurement; and
6. the committed Pilot 05 empirical divergence in which parser validity improved while
   evidence-sensitive stage success deteriorated.

## Close antecedents explicitly acknowledged

Structured-output validity/correctness, insufficient-evidence evaluation, evidence
sufficiency, selective prediction, learning to defer, component-aware RAG evaluation,
and emerging LLM error-cascade research are cited and distinguished.

## Prohibited priority-language matches

{len(priority_hits)}
"""
    write_text(OUTPUT_FILES["novelty_audit"], novelty_audit)

    base_results_hash = sha256_bytes(base_results.encode("utf-8"))
    integrated_results_hash = sha256_bytes(integrated_results.encode("utf-8"))
    empirical_report = f"""# Pilot 05AY Empirical Preservation Report

## Status

PASS

## Results-section preservation

- base_results_section_sha256: `{base_results_hash}`
- integrated_results_section_sha256: `{integrated_results_hash}`
- byte_identical_results_section: `{str(results_preserved).upper()}`

## Protected empirical literals

All {len(PROTECTED_LITERALS)} protected literals were retained.

## Empirical source boundary

No external citation is used to validate Pilot 05 numbers. External sources support
only literature positioning, data provenance, validity organization, and
reproducibility/reporting context.

## Input manuscript integrity

- committed_05AW_manuscript_sha256: `{file_sha256(BASE_MANUSCRIPT)}`
- committed_05AW_manuscript_modified: `NO`
"""
    write_text(OUTPUT_FILES["empirical_report"], empirical_report)

    input_paths = [
        BASE_MANUSCRIPT,
        SOURCE_REGISTER,
        PLACEHOLDER_MAP,
        RELATED_SYNTHESIS,
        INSERTION_PLAN,
        CLAIM_MAP,
        NOVELTY_ANALYSIS,
        SOURCE_VERIFICATION,
        AX_MANIFEST,
    ]
    source_index_rows = [
        {
            "source_file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": file_sha256(path),
            "role": {
                BASE_MANUSCRIPT: "Base committed manuscript",
                SOURCE_REGISTER: "Verified bibliographic metadata",
                PLACEHOLDER_MAP: "Ten-placeholder resolution contract",
                RELATED_SYNTHESIS: "Related-work wording source",
                INSERTION_PLAN: "Section-specific insertion boundaries",
                CLAIM_MAP: "Claim-to-source traceability",
                NOVELTY_ANALYSIS: "Bounded novelty verdict",
                SOURCE_VERIFICATION: "Source verification evidence",
                AX_MANIFEST: "Committed 05AX counts and safety contract",
            }[path],
            "read_only": "YES",
        }
        for path in input_paths
    ]
    write_csv(
        OUTPUT_FILES["source_index"],
        source_index_rows,
        ["source_file", "sha256", "role", "read_only"],
    )

    validation_checks = {
        "input_05AX_manifest_pass": True,
        "verified_source_rows_24": len(source_by_id) == 24,
        "placeholder_rows_10": len(placeholder_rows) == 10,
        "all_placeholders_resolved": all(
            f"[{placeholder_id}]" not in integrated
            for placeholder_id in PLACEHOLDER_SOURCES
        ),
        "no_CIT_tokens_remaining": "[CIT-" not in integrated,
        "selected_references_22": len(SELECTED_SOURCE_IDS) == 22,
        "all_cited_sources_registered": not unknown_selected,
        "preprints_explicitly_labelled": all(
            "preprint" in CITATION_LABELS[source_id].lower()
            for source_id in SELECTED_SOURCE_IDS
            if source_by_id[source_id]["peer_review_status"].startswith(
                "not_peer_reviewed"
            )
        ),
        "results_section_byte_identical": results_preserved,
        "protected_empirical_literals_retained": not protected_failures,
        "no_global_priority_language": not priority_hits,
        "committed_manuscript_unchanged": file_sha256(BASE_MANUSCRIPT)
        == "88561B2ED6455A324C2D9323B4D4A0603597BF7A55CF1AF0183C43C3960FFCD5",
        "no_api_calls": True,
        "no_model_calls": True,
        "no_new_experiments": True,
        "no_raw_data_access": True,
        "no_env_access": True,
        "no_jsonl_writing": True,
        "no_staging": True,
        "no_commit": True,
        "no_push": True,
    }
    failed_checks = [name for name, passed in validation_checks.items() if not passed]
    validation_status = "PASS" if not failed_checks else "FAIL"

    validation_lines = [
        "# Pilot 05AY Internal Validation Report",
        "",
        f"status: {validation_status}",
        "",
        "## Checks",
        "",
    ]
    validation_lines.extend(
        f"- {name}: {'PASS' if passed else 'FAIL'}"
        for name, passed in validation_checks.items()
    )
    validation_lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- verified_source_rows: {len(source_by_id)}",
            f"- selected_reference_rows: {len(SELECTED_SOURCE_IDS)}",
            f"- placeholder_resolution_rows: {len(placeholder_rows)}",
            f"- citation_usage_rows: {len(usage_rows)}",
            f"- section_integration_rows: {len(section_rows)}",
            f"- failed_checks: {len(failed_checks)}",
        ]
    )
    if failed_checks:
        validation_lines.extend(["", "## Failed checks", ""])
        validation_lines.extend(f"- {name}" for name in failed_checks)
    write_text(OUTPUT_FILES["validation"], "\n".join(validation_lines))

    if failed_checks:
        raise RuntimeError(f"05AY internal validation failed: {failed_checks}")

    output_hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): file_sha256(path)
        for key, path in OUTPUT_FILES.items()
        if key != "manifest"
    }
    output_hashes[
        str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/")
    ] = file_sha256(Path(__file__).resolve())

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_date": date.today().isoformat(),
        "secured_input_commit": EXPECTED_COMMIT,
        "source_boundary": {
            "committed_manuscript": str(BASE_MANUSCRIPT.relative_to(ROOT)).replace(
                "\\", "/"
            ),
            "committed_literature_package": "reports/pilot_05_external_literature_grounding",
            "new_external_research": False,
        },
        "counts": {
            "verified_source_rows": len(source_by_id),
            "selected_reference_rows": len(SELECTED_SOURCE_IDS),
            "placeholder_resolution_rows": len(placeholder_rows),
            "citation_usage_rows": len(usage_rows),
            "section_integration_rows": len(section_rows),
            "expected_uncommitted_files_including_script": 11,
        },
        "novelty_verdict": (
            "Bounded combination-and-operationalization differentiation preserved; "
            "global priority is not claimed."
        ),
        "empirical_preservation": {
            "results_section_byte_identical": results_preserved,
            "base_results_section_sha256": base_results_hash,
            "integrated_results_section_sha256": integrated_results_hash,
            "protected_empirical_literals_retained": True,
            "external_sources_validate_empirical_results": False,
        },
        "safety": {
            "new_external_literature_research_performed": False,
            "no_api_calls": True,
            "no_model_calls": True,
            "no_new_experiments": True,
            "no_raw_data_access": True,
            "no_env_access": True,
            "no_jsonl_writing": True,
            "committed_manuscript_modified": False,
            "no_staging": True,
            "no_commit": True,
            "no_push": True,
        },
        "output_sha256_excluding_manifest": output_hashes,
        "notes": [
            "The integrated manuscript is a new derivative output; the committed 05AW manuscript remains unchanged.",
            "All citations originate from the committed 05AX verified source register.",
            "Preprints and the 2026 FSB consultation report are explicitly labelled.",
            "No external source is used as evidence for Pilot 05 empirical numbers.",
        ],
    }
    write_text(OUTPUT_FILES["manifest"], json.dumps(manifest, indent=2, ensure_ascii=False))

    expected_created = {Path(__file__).resolve(), *OUTPUT_FILES.values()}
    actual_created = {
        path for path in [Path(__file__).resolve(), *OUTPUT_DIR.rglob("*")] if path.is_file()
    }
    if actual_created != expected_created:
        unexpected = sorted(str(path) for path in actual_created - expected_created)
        missing = sorted(str(path) for path in expected_created - actual_created)
        raise RuntimeError(
            f"Generated file-set mismatch. Unexpected={unexpected}; missing={missing}"
        )

    print("=== TASK 05AY GENERATION COMPLETE ===")
    print("status: PASS")
    print(f"verified_source_rows: {len(source_by_id)}")
    print(f"selected_reference_rows: {len(SELECTED_SOURCE_IDS)}")
    print(f"placeholder_resolution_rows: {len(placeholder_rows)}")
    print(f"citation_usage_rows: {len(usage_rows)}")
    print(f"section_integration_rows: {len(section_rows)}")
    print("results_section_byte_identical: True")
    print("unresolved_placeholders: 0")
    print(
        "novelty_verdict: "
        "BOUNDED_COMBINATION_OPERATIONALIZATION_GLOBAL_PRIORITY_NOT_CLAIMED"
    )
    print(f"output_dir: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
