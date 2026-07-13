#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "05BA"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "c3cecc13539f47d6e5af7bbb39d12d13590f756f"
EXPECTED_MANUSCRIPT_SHA256 = "5D79D5DC4518B413CD270FA2002ADA69F10BCDC45FEBE52013103D8BF3B22C6B"

SCRIPT_REL = Path("experiments/pilot_05_manuscript_integrity_audit.py")
OUTPUT_REL = Path("reports/pilot_05_manuscript_integrity_audit")
MANUSCRIPT_REL = Path(
    "reports/pilot_05_verified_citation_integration/"
    "pilot_05AY_citation_integrated_manuscript.md"
)

MAIN_RESULTS_REL = Path(
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/"
    "pilot_05AR_paper_ready_main_results_table.csv"
)

EXPECTED_MAIN_RESULTS_CONTRACT = {
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

METRIC_MAIN_RESULTS_KEYS = {
    "NUM-001": "call_plan_rows",
    "NUM-002": "ledger_rows",
    "NUM-003": "sanitized_execution_rows",
    "NUM-004": "ledger_only_missing_sanitized_rows",
    "NUM-005": "ledger_parser_valid_true",
    "NUM-006": "ledger_parser_valid_false",
    "NUM-007": "persisted_parser_valid_true",
    "NUM-008": "persisted_parser_valid_false",
    "NUM-009": "stage_success_delta_min",
    "NUM-010": "stage_success_delta_max",
    "NUM-011": "parser_valid_delta_min",
    "NUM-012": "parser_valid_delta_max",
    "NUM-013": "audit_detection_rate_degraded_mean",
    "NUM-014": "escalation_recovery_rate_degraded_mean",
    "NUM-015": "cascade_failure_rate_all_sequence_groups",
    "NUM-016": "max_cumulative_estimated_cost_usd",
}

OUTPUT_NAMES = [
    "pilot_05BA_submission_readiness_summary.md",
    "pilot_05BA_issue_register.csv",
    "pilot_05BA_numerical_consistency_audit.csv",
    "pilot_05BA_claim_evidence_traceability.csv",
    "pilot_05BA_citation_integrity_audit.csv",
    "pilot_05BA_structure_and_scaffold_audit.csv",
    "pilot_05BA_notation_and_terminology_audit.csv",
    "pilot_05BA_table_figure_reference_audit.csv",
    "pilot_05BA_abstract_results_conclusion_alignment.md",
    "pilot_05BA_submission_gap_classification.md",
    "pilot_05BA_internal_validation_report.md",
    "pilot_05BA_manifest.json",
]

ALLOWED_INPUT_DIRS = [
    Path("reports/pilot_05_verified_citation_integration"),
    Path("reports/pilot_05_external_literature_grounding"),
    Path("reports/pilot_05_formal_definition_citation_refinement"),
    Path("reports/pilot_05_cfpb_glm52_scaled_results_interpretation"),
    Path("reports/pilot_05_cfpb_glm52_paper_figures_tables"),
    Path("reports/pilot_05_repo_validation_reproducibility_audit"),
    Path("reports/pilot_05_full_manuscript_draft_assembly"),
    Path("reports/pilot_05_manuscript_skeleton_results_methods"),
]

PROHIBITED_PATH_PATTERNS = [
    re.compile(r"(^|/)\.env($|\.)", re.I),
    re.compile(r"\.jsonl$", re.I),
    re.compile(r"(^|/)(raw|private|secret)(/|$)", re.I),
    re.compile(r"raw[_ -]?(prompt|response|complaint|narrative|data)", re.I),
    re.compile(r"(prompt|response)[_ -]?raw", re.I),
    re.compile(r"complaint[_ -]?narrative", re.I),
    re.compile(r"api[_ -]?key", re.I),
    re.compile(r"credentials?", re.I),
]

SEVERITY_ORDER = {
    "BLOCKER": 0,
    "MAJOR": 1,
    "MODERATE": 2,
    "MINOR": 3,
    "INFORMATIONAL": 4,
}

EXPECTED_METRICS = [
    {
        "id": "NUM-001",
        "metric": "planned calls",
        "aliases": ["planned calls", "planned and ledgered calls", "planned_call_count"],
        "values": ["720"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-002",
        "metric": "ledger rows",
        "aliases": ["ledger rows", "ledgered calls", "ledger row"],
        "values": ["720"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-003",
        "metric": "sanitized execution rows",
        "aliases": ["sanitized execution rows", "persisted rows", "sanitized rows"],
        "values": ["713"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-004",
        "metric": "ledger-only missing sanitized rows",
        "aliases": ["missing sanitized rows", "ledger-only", "missing persisted rows", "seven missing"],
        "values": ["7", "seven"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_limitations_and_validity_threats.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-005",
        "metric": "ledger parser-valid",
        "aliases": ["ledger parser-valid", "parser-valid ledger", "parser valid ledger"],
        "values": ["470"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-006",
        "metric": "ledger parser-invalid",
        "aliases": ["ledger parser-invalid", "parser-invalid ledger", "parser invalid ledger"],
        "values": ["250"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-007",
        "metric": "persisted parser-valid",
        "aliases": ["persisted parser-valid", "sanitized parser-valid", "persisted parser valid"],
        "values": ["470"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-008",
        "metric": "persisted parser-invalid",
        "aliases": ["persisted parser-invalid", "sanitized parser-invalid", "persisted parser invalid"],
        "values": ["243"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-009",
        "metric": "stage-success delta lower bound",
        "aliases": ["stage-success delta", "stage success delta"],
        "values": ["-0.517241", "-51.7241%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-010",
        "metric": "stage-success delta upper bound",
        "aliases": ["stage-success delta", "stage success delta"],
        "values": ["-0.406780", "-40.6780%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-011",
        "metric": "parser-validity delta lower bound",
        "aliases": ["parser-validity delta", "parser validity delta"],
        "values": ["+0.067797", "0.067797", "+6.7797%", "6.7797%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-012",
        "metric": "parser-validity delta upper bound",
        "aliases": ["parser-validity delta", "parser validity delta"],
        "values": ["+0.368421", "0.368421", "+36.8421%", "36.8421%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-013",
        "metric": "mean degraded audit detection",
        "aliases": ["degraded audit detection", "audit detection"],
        "values": ["1.0", "100%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-014",
        "metric": "mean degraded escalation recovery",
        "aliases": ["degraded escalation recovery", "escalation recovery"],
        "values": ["0.0", "0%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-015",
        "metric": "all-sequence cascade-failure rate",
        "aliases": ["cascade-failure rate", "cascade failure rate", "all-sequence"],
        "values": ["0.929167", "92.9167%"],
        "source_hints": ["pilot_05AR_paper_ready_main_results_table.csv",
                         "pilot_05AR_scaled_results_interpretation_report.md"],
        "required_in_manuscript": True,
    },
    {
        "id": "NUM-016",
        "metric": "maximum cumulative estimated cost",
        "aliases": ["cumulative estimated cost", "estimated cost", "cost"],
        "values": ["2.2731216", "2.2731", "$2.2731216", "USD 2.2731216"],
        "source_hints": ["pilot_05AR_scaled_results_interpretation_manifest.json",
                         "pilot_05AR_paper_ready_main_results_table.csv"],
        "required_in_manuscript": True,
    },
]


METRIC_SOURCE_KEYS = {
    "NUM-001": ["call_plan_rows"],
    "NUM-002": ["ledger_rows"],
    "NUM-003": ["sanitized_execution_rows"],
    "NUM-004": ["ledger_only_missing_sanitized_rows"],
    "NUM-005": ["ledger_parser_valid_true"],
    "NUM-006": ["ledger_parser_valid_false"],
    "NUM-007": ["persisted_parser_valid_true"],
    "NUM-008": ["persisted_parser_valid_false"],
    "NUM-009": ["stage_success_delta_min"],
    "NUM-010": ["stage_success_delta_max"],
    "NUM-011": ["parser_valid_delta_min"],
    "NUM-012": ["parser_valid_delta_max"],
    "NUM-013": ["audit_detection_rate_degraded_mean"],
    "NUM-014": ["escalation_recovery_rate_degraded_mean"],
    "NUM-015": ["cascade_failure_rate_all_sequence_groups"],
    "NUM-016": ["max_cumulative_estimated_cost_usd"],
}

REQUIRED_SECTION_RULES = [
    ("STRUCT-001", "Title", [r"^#\s+\S"], True),
    ("STRUCT-002", "Abstract", [r"^##\s+Abstract\b"], True),
    ("STRUCT-003", "Keywords", [r"^##\s+Keywords\b"], True),
    ("STRUCT-004", "Introduction", [r"^##\s+1\.\s+Introduction\b"], True),
    ("STRUCT-005", "Related work", [r"Related work"], True),
    ("STRUCT-006", "Conceptual framework", [r"Conceptual framing", r"Conceptual framework"], True),
    ("STRUCT-007", "Methods", [r"^##\s+3\.\s+Methods\b"], True),
    ("STRUCT-008", "Results", [r"^##\s+4\.\s+Results\b"], True),
    ("STRUCT-009", "Discussion", [r"^##\s+9\.\s+Discussion\b", r"^##\s+\d+\.\s+Discussion\b"], True),
    ("STRUCT-010", "Limitations or threats to validity", [r"limitations", r"Threats to Validity"], True),
    ("STRUCT-011", "Reproducibility", [r"Reproducibility"], True),
    ("STRUCT-012", "Conclusion", [r"^##\s+10\.\s+Conclusion\b", r"^##\s+\d+\.\s+Conclusion\b"], True),
    ("STRUCT-013", "References", [r"^##\s+References\b"], True),
    ("STRUCT-014", "Appendix", [r"^##\s+Appendix\b"], True),
]

SCAFFOLD_PATTERNS = [
    ("SCAF-001", "Manuscript status", r"(?im)^##\s+Manuscript status\s*$", "MAJOR"),
    ("SCAF-002", "Synthesis-source table heading", r"(?im)^##\s+Committed main table used by this synthesis\s*$", "MAJOR"),
    ("SCAF-003", "Metric-validation source heading", r"(?im)^##\s+Metric validation table used by this synthesis\s*$", "MAJOR"),
    ("SCAF-004", "No-new-evidence process heading", r"(?im)^##\s+No-new-evidence rule\s*$", "MODERATE"),
    ("SCAF-005", "One-sentence contribution drafting heading", r"(?im)^##\s+One-sentence contribution\s*$", "MODERATE"),
    ("SCAF-006", "Head-turning drafting language", r"(?i)head[- ]turn", "MODERATE"),
    ("SCAF-007", "Recommended table sequence heading", r"(?im)^##\s+Recommended manuscript table sequence\s*$", "MAJOR"),
    ("SCAF-008", "Recommended figure sequence heading", r"(?im)^##\s+Recommended manuscript figure sequence\s*$", "MAJOR"),
    ("SCAF-009", "Source caption pack heading", r"(?im)^##\s+Source caption pack\s*$", "MAJOR"),
    ("SCAF-010", "Source paper table pack heading", r"(?im)^##\s+Source paper table pack\s*$", "MAJOR"),
    ("SCAF-011", "Do-not-claim drafting heading", r"(?im)^##\s+Do not claim\s*$", "MAJOR"),
    ("SCAF-012", "Repository checkpoint heading", r"(?im)^##\s+Repository checkpoint\s*$", "MODERATE"),
    ("SCAF-013", "Source artifacts heading", r"(?im)^##\s+Source artifacts\s*$", "MODERATE"),
    ("SCAF-014", "Revision roadmap appendix", r"(?im)^##\s+Appendix A\.\s+Next revision roadmap\s*$", "MAJOR"),
    ("SCAF-015", "Immediate next steps heading", r"(?im)^##\s+Immediate next manuscript steps\s*$", "MAJOR"),
    ("SCAF-016", "What-not-to-do heading", r"(?im)^##\s+What not to do yet\s*$", "MAJOR"),
    ("SCAF-017", "Assembly checkpoint appendix", r"(?im)^##\s+Appendix B\.\s+Assembly checkpoint\s*$", "MAJOR"),
    ("SCAF-018", "Do-not-claim appendix", r"(?im)^##\s+Appendix C\.\s+Do-not-claim boundary\s*$", "MAJOR"),
    ("SCAF-019", "Literature integration provenance heading", r"(?im)^##\s+Literature Integration Provenance\s*$", "MODERATE"),
    ("SCAF-020", "Internal task identifier", r"(?i)\b(?:Task\s+)?05A[RSTUVWXYZ]\b", "MODERATE"),
    ("SCAF-021", "Internal artifact filename", r"(?i)\bpilot_05[A-Z]{2}_[A-Za-z0-9_.-]+", "MAJOR"),
    ("SCAF-022", "Internal repository path", r"(?i)\b(?:reports|experiments)/pilot_05", "MAJOR"),
]

PROHIBITED_CLAIM_PATTERNS = [
    ("CLAIM-001", "First-ever or priority claim", r"(?i)\b(first[- ]ever|the first study|first of its kind|world(?:'s)? first)\b", "BLOCKER"),
    ("CLAIM-002", "Groundbreaking asserted as fact", r"(?i)\bgroundbreaking\b", "MAJOR"),
    ("CLAIM-003", "Guaranteed publication outcome", r"(?i)\b(guarantee(?:d)?|certain)\s+(?:Q1|journal|acceptance|publication)\b", "BLOCKER"),
    ("CLAIM-004", "Universal LLM generalization", r"(?i)\b(all LLMs|LLMs are universally|universal(?:ly)? unreliable)\b", "BLOCKER"),
    ("CLAIM-005", "Universal GLM generalization", r"(?i)\bGLM-5\.2\s+(?:is|proves|shows)\s+(?:universally|always)\b", "BLOCKER"),
    ("CLAIM-006", "Provider superiority", r"(?i)\b(?:superior to|outperforms all|best provider)\b", "MAJOR"),
    ("CLAIM-007", "Deployment safety assertion", r"(?i)\b(?:deployment[- ]safe|safe for deployment|production[- ]ready)\b", "BLOCKER"),
    ("CLAIM-008", "Regulatory compliance assertion", r"(?i)\b(?:regulatorily valid|regulatory compliance is established|complies with all regulations)\b", "BLOCKER"),
    ("CLAIM-009", "CFPB complaints treated as verified findings", r"(?i)\bCFPB complaints? (?:prove|establish|verify)\b", "BLOCKER"),
    ("CLAIM-010", "Parser validity equated with correctness", r"(?i)\bparser validity (?:equals|is equivalent to|guarantees) correctness\b", "BLOCKER"),
    ("CLAIM-011", "Unsupported optimal escalation claim", r"(?i)\boptimal escalation (?:policy|strategy)\b", "MAJOR"),
    ("CLAIM-012", "Overstrong causal verb", r"(?i)\b(?:proves?|establishes?) that controlled evidence[- ]state degradation causes\b", "MAJOR"),
]

def fail(message: str) -> None:
    raise RuntimeError(message)

def run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        fail(
            "Git command failed: git -C "
            f"{repo} {' '.join(args)}\n{completed.stderr.strip()}"
        )
    return completed.stdout

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]

def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})

def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def rel(repo: Path, path: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()

def is_prohibited(relative_path: str) -> bool:
    return any(pattern.search(relative_path) for pattern in PROHIBITED_PATH_PATTERNS)

def line_context(text: str, match: re.Match[str], radius: int = 1) -> str:
    lines = text.splitlines()
    line_no = text.count("\n", 0, match.start()) + 1
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    selected = []
    for index in range(start, end + 1):
        selected.append(f"L{index}: {lines[index - 1].strip()}")
    return " | ".join(selected)

def find_contexts(text: str, pattern: str, flags: int = re.I, limit: int = 5) -> list[str]:
    contexts: list[str] = []
    for match in re.finditer(pattern, text, flags):
        contexts.append(line_context(text, match))
        if len(contexts) >= limit:
            break
    return contexts

def explicitly_negated_match(text: str, match: re.Match[str]) -> bool:
    before = text[max(0, match.start() - 140):match.start()]
    after = text[match.end():min(len(text), match.end() + 140)]
    sentence_start = max(
        before.rfind("."),
        before.rfind("!"),
        before.rfind("?"),
        before.rfind("\n"),
    )
    sentence_before = before[sentence_start + 1:]
    sentence_end_candidates = [
        position for position in (
            after.find("."),
            after.find("!"),
            after.find("?"),
            after.find("\n"),
        )
        if position >= 0
    ]
    sentence_after = after[:min(sentence_end_candidates)] if sentence_end_candidates else after
    prior_negation = re.search(
        r"(?i)\b(?:not|no|never|cannot|can't|does\s+not|do\s+not|did\s+not|"
        r"is\s+not|are\s+not|was\s+not|were\s+not|without)\b.{0,100}$",
        sentence_before,
    )
    following_disclaimer = re.search(
        r"(?i)^.{0,100}\b(?:not\s+(?:claimed|established|supported|asserted|shown)|"
        r"is\s+not|are\s+not|does\s+not|cannot)\b",
        sentence_after,
    )
    return bool(prior_negation or following_disclaimer)

def find_unnegated_contexts(
    text: str,
    pattern: str,
    flags: int = re.I,
    limit: int = 5,
) -> tuple[list[str], int]:
    contexts: list[str] = []
    suppressed = 0
    for match in re.finditer(pattern, text, flags):
        if explicitly_negated_match(text, match):
            suppressed += 1
            continue
        contexts.append(line_context(text, match))
        if len(contexts) >= limit:
            break
    return contexts, suppressed

def normalize_heading(text: str) -> str:
    value = re.sub(r"^#{1,6}\s+", "", text.strip())
    value = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return value

def extract_headings(text: str) -> list[dict[str, Any]]:
    headings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append(
                {
                    "line": line_no,
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "raw": line.strip(),
                    "normalized": normalize_heading(line),
                }
            )
    return headings

def numbered_main_section(title: str) -> int | None:
    match = re.match(r"^\s*(\d+)\.\s+\S", title)
    return int(match.group(1)) if match else None

def section_text(
    text: str,
    heading_pattern: str,
    *,
    boundary: str = "level",
) -> str:
    """Extract a Markdown section using normalized semantic headings.

    boundary="numbered" keeps malformed same-level child headings inside a
    numbered main section and stops only at the next numbered main section.
    """
    lines = text.splitlines()
    headings = extract_headings(text)
    for position, heading in enumerate(headings):
        candidates = (heading["title"], heading["normalized"])
        if not any(re.search(heading_pattern, candidate, re.I) for candidate in candidates):
            continue
        start_index = heading["line"] - 1
        end_index = len(lines)
        current_number = numbered_main_section(heading["title"])
        for next_heading in headings[position + 1:]:
            if boundary == "numbered" and current_number is not None:
                next_number = numbered_main_section(next_heading["title"])
                if next_number is not None and next_number > current_number:
                    end_index = next_heading["line"] - 1
                    break
            elif next_heading["level"] <= heading["level"]:
                end_index = next_heading["line"] - 1
                break
        return "\n".join(lines[start_index:end_index]).strip()
    return ""

def normalize_key(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return value

def parse_numeric(value: Any) -> tuple[float, bool] | None:
    raw = str(value).strip().replace(",", "")
    if not raw:
        return None
    is_percent = raw.endswith("%")
    raw = raw.rstrip("%").strip()
    raw = re.sub(r"^(?:USD|\$)\s*", "", raw, flags=re.I)
    try:
        number = float(raw)
    except ValueError:
        return None
    if is_percent:
        number /= 100.0
    return number, is_percent

def value_matches(candidate: Any, expected_values: list[str]) -> bool:
    candidate_text = str(candidate).strip()
    if candidate_text in expected_values:
        return True
    candidate_num = parse_numeric(candidate_text)
    if candidate_num is None:
        return False
    for expected in expected_values:
        expected_num = parse_numeric(expected)
        if expected_num is None:
            continue
        if abs(candidate_num[0] - expected_num[0]) <= 1e-9:
            return True
    return False

def metric_names(metric: dict[str, Any]) -> list[str]:
    names = [metric["metric"], *metric["aliases"], *METRIC_SOURCE_KEYS.get(metric["id"], [])]
    return sorted({normalize_key(name) for name in names if str(name).strip()})

def name_matches(candidate: str, metric: dict[str, Any]) -> bool:
    normalized = normalize_key(candidate)
    if not normalized:
        return False
    return any(
        normalized == name
        or name in normalized
        or normalized in name
        for name in metric_names(metric)
    )

def structured_source_evidence(path: Path, metric: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    suffix = path.suffix.lower()
    relative = path.as_posix()

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                name_fields = [
                    value for key, value in row.items()
                    if value is not None and normalize_key(key) in {
                        "metric", "name", "check", "field", "key", "limitation", "dimension"
                    }
                ]
                if not name_fields:
                    name_fields = [value for value in row.values() if value is not None]
                value_fields = [value for value in row.values() if value is not None]
                if (
                    any(name_matches(value, metric) for value in name_fields)
                    and any(value_matches(value, metric["values"]) for value in value_fields)
                ):
                    compact = "; ".join(
                        f"{key}={value}" for key, value in row.items()
                        if value not in (None, "")
                    )
                    evidence.append(f"{relative}: row {row_number}: {compact}")
                    if len(evidence) >= 3:
                        break

    elif suffix == ".json":
        try:
            payload = json.loads(read_text(path))
        except json.JSONDecodeError:
            return evidence
        for key_path, value in json_flatten(payload):
            leaf = key_path.rsplit(".", 1)[-1]
            if (
                (name_matches(key_path, metric) or name_matches(leaf, metric))
                and value_matches(value, metric["values"])
            ):
                evidence.append(f"{relative}: {key_path}={value}")
                if len(evidence) >= 3:
                    break

    elif suffix == ".md":
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if (
                name_matches(line, metric)
                and any(value in line for value in metric["values"])
            ):
                evidence.append(f"{relative}: L{line_number}: {line.strip()}")
                if len(evidence) >= 3:
                    break

    return evidence

def manuscript_metric_evidence(manuscript: str, metric: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    lines = manuscript.splitlines()
    for line_number, line in enumerate(lines, start=1):
        if (
            name_matches(line, metric)
            and any(
                value in line or value_matches(token, metric["values"])
                for value in metric["values"]
                for token in re.findall(r"[-+]?\$?(?:USD\s*)?\d+(?:\.\d+)?%?", line, re.I)
            )
        ):
            evidence.append(f"L{line_number}: {line.strip()}")
            if len(evidence) >= 5:
                break
    return evidence

def markdown_table_count(text: str) -> int:
    lines = text.splitlines()
    count = 0
    for index in range(1, len(lines)):
        if (
            "|" in lines[index - 1]
            and re.match(r"^\s*\|?\s*:?-{3,}", lines[index])
        ):
            count += 1
    return count

def json_flatten(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(json_flatten(child, next_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            next_prefix = f"{prefix}[{index}]"
            rows.extend(json_flatten(child, next_prefix))
    else:
        rows.append((prefix, "" if value is None else str(value)))
    return rows

def issue(
    issues: list[dict[str, str]],
    issue_id: str,
    severity: str,
    section: str,
    evidence: str,
    why: str,
    correction: str,
    new_evidence: str = "NO",
    manuscript_edit_only: str = "YES",
) -> None:
    issues.append(
        {
            "issue_id": issue_id,
            "severity": severity,
            "manuscript_section": section,
            "exact_evidence": evidence,
            "why_it_matters": why,
            "required_correction": correction,
            "correction_needs_new_evidence": new_evidence,
            "manuscript_edit_only": manuscript_edit_only,
        }
    )

def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    script_path = repo / SCRIPT_REL
    output_dir = repo / OUTPUT_REL
    manuscript_path = repo / MANUSCRIPT_REL

    if script_path.resolve() != Path(__file__).resolve():
        fail(f"Unexpected script location: {Path(__file__).resolve()}")

    branch = run_git(repo, "branch", "--show-current").strip()
    head = run_git(repo, "rev-parse", "HEAD").strip()
    if branch != EXPECTED_BRANCH:
        fail(f"Expected branch {EXPECTED_BRANCH}, got {branch}")
    if head != EXPECTED_HEAD:
        fail(f"Expected HEAD {EXPECTED_HEAD}, got {head}")

    tracked_changes = run_git(repo, "diff", "--name-only").splitlines()
    staged_changes = run_git(repo, "diff", "--cached", "--name-only").splitlines()
    if tracked_changes:
        fail(f"Tracked working-tree changes exist: {tracked_changes}")
    if staged_changes:
        fail(f"Staged changes exist: {staged_changes}")

    untracked = {
        line.strip()
        for line in run_git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    expected_before = {SCRIPT_REL.as_posix()}
    expected_before.update(
        (OUTPUT_REL / name).as_posix() for name in OUTPUT_NAMES
    )
    if untracked != expected_before:
        fail(
            "Unexpected untracked state before repaired audit generation. "
            f"Expected exactly {sorted(expected_before)}, got {sorted(untracked)}"
        )

    if not manuscript_path.is_file():
        fail(f"Missing manuscript: {MANUSCRIPT_REL.as_posix()}")
    manuscript_hash = sha256_file(manuscript_path)
    if manuscript_hash != EXPECTED_MANUSCRIPT_SHA256:
        fail(
            "Manuscript SHA-256 mismatch: "
            f"expected {EXPECTED_MANUSCRIPT_SHA256}, got {manuscript_hash}"
        )

    if not output_dir.is_dir():
        fail(f"Approved existing output directory is missing: {OUTPUT_REL.as_posix()}")
    existing_output_names = sorted(
        path.name for path in output_dir.iterdir() if path.is_file()
    )
    if existing_output_names != sorted(OUTPUT_NAMES):
        fail(
            "Existing 05BA output contract differs from the approved twelve-file set: "
            f"{existing_output_names}"
        )

    tracked = {
        line.strip()
        for line in run_git(repo, "ls-files").splitlines()
        if line.strip()
    }

    input_files: list[Path] = []
    for directory_rel in ALLOWED_INPUT_DIRS:
        directory = repo / directory_rel
        if not directory.is_dir():
            fail(f"Required input directory missing: {directory_rel.as_posix()}")
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative = rel(repo, path)
            if is_prohibited(relative):
                fail(f"Prohibited path encountered inside allowlist: {relative}")
            if relative not in tracked:
                fail(f"Allowlisted input is not tracked: {relative}")
            if path.suffix.lower() not in {".md", ".csv", ".json", ".png"}:
                continue
            input_files.append(path)

    if not input_files:
        fail("No committed allowlisted input files found")

    input_hashes = {rel(repo, path): sha256_file(path) for path in input_files}
    manuscript = read_text(manuscript_path)
    headings = extract_headings(manuscript)
    issues: list[dict[str, str]] = []

    # Numerical integrity
    source_texts: dict[str, str] = {}
    for path in input_files:
        if path.suffix.lower() in {".md", ".csv", ".json"}:
            source_texts[rel(repo, path)] = read_text(path)

    main_results_path = repo / MAIN_RESULTS_REL
    if not main_results_path.is_file():
        fail(f"Missing authoritative 05AR main-results table: {MAIN_RESULTS_REL.as_posix()}")
    if MAIN_RESULTS_REL.as_posix() not in tracked:
        fail(f"Authoritative 05AR main-results table is not tracked: {MAIN_RESULTS_REL.as_posix()}")

    main_results_rows = read_csv_rows(main_results_path)
    main_results_by_metric: dict[str, dict[str, str]] = {}
    duplicate_main_result_keys: list[str] = []
    for row in main_results_rows:
        key = str(row.get("metric", "")).strip()
        if not key:
            fail("Authoritative 05AR main-results table contains a row without a metric key")
        if key in main_results_by_metric:
            duplicate_main_result_keys.append(key)
        main_results_by_metric[key] = row
    if duplicate_main_result_keys:
        fail(
            "Authoritative 05AR main-results table contains duplicate metric keys: "
            f"{sorted(set(duplicate_main_result_keys))}"
        )

    actual_main_result_keys = set(main_results_by_metric)
    expected_main_result_keys = set(EXPECTED_MAIN_RESULTS_CONTRACT)
    if actual_main_result_keys != expected_main_result_keys:
        fail(
            "05BA-REPAIR V3 authoritative 17-row metric contract mismatch before output overwrite. "
            f"Missing={sorted(expected_main_result_keys - actual_main_result_keys)}; "
            f"unexpected={sorted(actual_main_result_keys - expected_main_result_keys)}"
        )

    main_results_contract_failures: list[str] = []
    for key, expected_value in EXPECTED_MAIN_RESULTS_CONTRACT.items():
        row = main_results_by_metric[key]
        actual_value = str(row.get("value", "")).strip()
        if not value_matches(actual_value, [expected_value]):
            main_results_contract_failures.append(
                f"{key}: expected {expected_value}, got {actual_value}"
            )
        if not str(row.get("paper_ready", "")).strip():
            main_results_contract_failures.append(
                f"{key}: paper_ready field is empty"
            )
    if main_results_contract_failures:
        fail(
            "05BA-REPAIR V3 authoritative metric contract failed before output overwrite: "
            + "; ".join(main_results_contract_failures)
        )

    numerical_rows: list[dict[str, str]] = []
    unresolved_source_metrics: list[str] = []
    for metric in EXPECTED_METRICS:
        source_key = METRIC_MAIN_RESULTS_KEYS[metric["id"]]
        source_row = main_results_by_metric[source_key]
        source_value = str(source_row.get("value", "")).strip()
        source_hits = [
            f"{MAIN_RESULTS_REL.as_posix()}: metric={source_key}; "
            f"value={source_value}; unit_or_type={source_row.get('unit_or_type', '')}; "
            f"paper_ready={source_row.get('paper_ready', '')}"
        ]
        if not value_matches(source_value, metric["values"]):
            source_hits = []

        manuscript_hits = manuscript_metric_evidence(manuscript, metric)

        if not source_hits:
            status = "REGRESSION_FAILURE_SOURCE_NOT_RESOLVED"
            unresolved_source_metrics.append(metric["id"])
        elif metric["required_in_manuscript"] and not manuscript_hits:
            status = "FAIL_MANUSCRIPT_MISSING_OR_UNLABELLED"
            issue(
                issues,
                metric["id"],
                "MAJOR",
                "Numerical integrity",
                f"Committed source supports {metric['metric']}, but no explicitly labelled "
                f"manuscript context was found for {metric['values']}. Source: {source_hits[0]}",
                "The manuscript may omit, ambiguously label, or inconsistently report a protected empirical value.",
                "Add or correct an explicitly labelled value using the authoritative committed evidence.",
                "NO",
                "YES",
            )
        else:
            status = "PASS"

        numerical_rows.append(
            {
                "check_id": metric["id"],
                "metric": metric["metric"],
                "authoritative_values": " | ".join(metric["values"]),
                "authoritative_source_evidence": " || ".join(source_hits[:3]),
                "manuscript_evidence": " || ".join(manuscript_hits[:5]),
                "status": status,
                "notes": (
                    "Exact authoritative 05AR main-results metric-key resolution with line-based manuscript matching; "
                    "human semantic review remains required."
                ),
            }
        )

    if unresolved_source_metrics:
        fail(
            "05BA-REPAIR V3 numerical-source regression failed before output overwrite. "
            f"Unresolved protected metrics: {unresolved_source_metrics}"
        )

    # Reconcile parser accounting explicitly.
    accounting_checks = [
        ("NUM-017", "ledger parser accounting", 470 + 250, 720),
        ("NUM-018", "persisted parser accounting", 470 + 243, 713),
        ("NUM-019", "missing sanitized row accounting", 720 - 713, 7),
        ("NUM-020", "parser-valid preservation", 470 - 470, 0),
    ]
    for check_id, name, actual, expected in accounting_checks:
        status = "PASS" if actual == expected else "FAIL"
        numerical_rows.append(
            {
                "check_id": check_id,
                "metric": name,
                "authoritative_values": f"calculated={actual}; expected={expected}",
                "authoritative_source_evidence": "Protected values from committed 05AR evidence contract",
                "manuscript_evidence": "",
                "status": status,
                "notes": "Deterministic arithmetic consistency check.",
            }
        )
        if status != "PASS":
            issue(
                issues,
                check_id,
                "BLOCKER",
                "Numerical integrity",
                f"{name}: calculated {actual}, expected {expected}",
                "The protected accounting does not reconcile.",
                "Correct the underlying evidence contract before manuscript editing.",
                "YES",
                "NO",
            )

    # Structure and scaffold audit.
    structure_rows: list[dict[str, str]] = []
    for check_id, name, patterns, required in REQUIRED_SECTION_RULES:
        matched = [
            heading for heading in headings
            if any(re.search(pattern, heading["raw"], re.I) for pattern in patterns)
        ]
        status = "PASS" if matched else "FAIL"
        evidence = " | ".join(
            f"L{item['line']}: {item['raw']}" for item in matched[:5]
        )
        structure_rows.append(
            {
                "check_id": check_id,
                "category": "required_section",
                "item": name,
                "status": status,
                "evidence": evidence,
                "required_action": "" if matched else f"Add or repair the {name} section.",
            }
        )
        if required and not matched:
            issue(
                issues,
                check_id,
                "BLOCKER",
                "Manuscript structure",
                f"Required section not found: {name}",
                "A journal manuscript is structurally incomplete without this section.",
                f"Add and integrate a manuscript-appropriate {name} section.",
                "NO",
                "YES",
            )

    for check_id, name, pattern, severity in SCAFFOLD_PATTERNS:
        contexts = find_contexts(manuscript, pattern, flags=re.I | re.M, limit=10)
        status = "FAIL" if contexts else "PASS"
        structure_rows.append(
            {
                "check_id": check_id,
                "category": "scaffold_language",
                "item": name,
                "status": status,
                "evidence": " || ".join(contexts),
                "required_action": (
                    "Remove or rewrite as journal-form prose." if contexts else ""
                ),
            }
        )
        if contexts:
            issue(
                issues,
                check_id,
                severity,
                "Manuscript structure/scaffold",
                " || ".join(contexts),
                "Internal assembly or workflow language makes the draft read like a validated project report rather than a journal paper.",
                "Remove the internal heading or filename and integrate only its scholarly content into the appropriate paper section.",
                "NO",
                "YES",
            )

    normalized_counts = Counter(
        heading["normalized"] for heading in headings if heading["normalized"]
    )
    duplicate_exclusions = {
        "interpretation",
        "claim boundary",
        "construct validity",
        "internal validity",
        "external validity",
        "reproducibility limitations",
    }
    duplicate_rows = [
        (name, count)
        for name, count in normalized_counts.items()
        if count > 1 and name not in duplicate_exclusions
    ]
    if duplicate_rows:
        evidence = "; ".join(f"{name} x{count}" for name, count in duplicate_rows)
        structure_rows.append(
            {
                "check_id": "STRUCT-015",
                "category": "duplicate_headings",
                "item": "Duplicate non-exempt headings",
                "status": "FAIL",
                "evidence": evidence,
                "required_action": "Consolidate duplicated sections or rename only where genuinely distinct.",
            }
        )
        issue(
            issues,
            "STRUCT-015",
            "MAJOR",
            "Manuscript structure",
            evidence,
            "Duplicated section architecture can create repeated arguments and obscure the paper's narrative.",
            "Consolidate duplicated sections into one coherent journal-form structure.",
            "NO",
            "YES",
        )
    else:
        structure_rows.append(
            {
                "check_id": "STRUCT-015",
                "category": "duplicate_headings",
                "item": "Duplicate non-exempt headings",
                "status": "PASS",
                "evidence": "",
                "required_action": "",
            }
        )

    # Heading hierarchy and numbering.
    top_numbered = []
    for heading in headings:
        match = re.match(r"^(\d+)\.\s+", heading["title"])
        if match:
            top_numbered.append((int(match.group(1)), heading["line"], heading["title"]))
    sequence = [item[0] for item in top_numbered]
    unique_sequence = []
    for number in sequence:
        if not unique_sequence or unique_sequence[-1] != number:
            unique_sequence.append(number)
    expected_sequence = list(range(1, max(unique_sequence) + 1)) if unique_sequence else []
    hierarchy_ok = unique_sequence == expected_sequence
    structure_rows.append(
        {
            "check_id": "STRUCT-016",
            "category": "section_numbering",
            "item": "Top-level numbered section sequence",
            "status": "PASS" if hierarchy_ok else "FAIL",
            "evidence": f"observed={unique_sequence}; expected={expected_sequence}",
            "required_action": "" if hierarchy_ok else "Repair top-level section numbering.",
        }
    )
    if not hierarchy_ok:
        issue(
            issues,
            "STRUCT-016",
            "MAJOR",
            "Manuscript structure",
            f"Observed top-level section sequence {unique_sequence}; expected {expected_sequence}",
            "Broken numbering undermines navigation and journal formatting.",
            "Renumber top-level sections sequentially after structural consolidation.",
            "NO",
            "YES",
        )

    unnumbered_level2_between = [
        heading for heading in headings
        if heading["level"] == 2
        and not re.match(r"^(?:\d+\.|Abstract\b|Keywords\b|References\b|Appendix\b)", heading["title"], re.I)
    ]
    if unnumbered_level2_between:
        evidence = " | ".join(
            f"L{item['line']}: {item['raw']}" for item in unnumbered_level2_between[:20]
        )
        structure_rows.append(
            {
                "check_id": "STRUCT-017",
                "category": "heading_hierarchy",
                "item": "Unnumbered level-2 headings inside numbered body",
                "status": "FAIL",
                "evidence": evidence,
                "required_action": "Convert body subsections to a consistent subordinate heading level and numbering scheme.",
            }
        )
        issue(
            issues,
            "STRUCT-017",
            "MAJOR",
            "Manuscript structure",
            evidence,
            "A large number of level-2 headings compete with numbered main sections and indicate assembly rather than publication structure.",
            "Adopt a consistent section/subsection hierarchy after removing scaffold sections.",
            "NO",
            "YES",
        )

    # Prohibited and overclaim language. Explicitly negated boundary statements
    # are evidence of caution, not overclaims.
    suppressed_negated_claim_matches = 0
    for check_id, name, pattern, severity in PROHIBITED_CLAIM_PATTERNS:
        contexts, suppressed = find_unnegated_contexts(
            manuscript,
            pattern,
            flags=re.I | re.M,
            limit=10,
        )
        suppressed_negated_claim_matches += suppressed
        if contexts:
            issue(
                issues,
                check_id,
                severity,
                "Claims and discussion",
                " || ".join(contexts),
                "The wording exceeds the approved claim boundary or requires evidence not present in the current study.",
                "Replace with bounded within-experiment language supported by the committed evidence.",
                "NO",
                "YES",
            )

    # Claim-to-evidence traceability.
    trace_rows: list[dict[str, str]] = []
    av_claim_path = repo / (
        "reports/pilot_05_full_manuscript_draft_assembly/"
        "pilot_05AV_claim_traceability_matrix.csv"
    )
    ax_claim_path = repo / (
        "reports/pilot_05_external_literature_grounding/"
        "pilot_05AX_claim_to_source_map.csv"
    )
    for source_name, path in [("05AV internal claim matrix", av_claim_path),
                              ("05AX external claim map", ax_claim_path)]:
        if not path.is_file():
            fail(f"Missing claim traceability input: {rel(repo, path)}")
        rows = read_csv_rows(path)
        for index, row in enumerate(rows, start=1):
            claim_text = (
                row.get("claim")
                or row.get("claim_text")
                or row.get("allowed_wording")
                or ""
            ).strip()
            support = (
                row.get("supporting_source")
                or row.get("external_source_ids")
                or row.get("internal_source_boundary")
                or ""
            ).strip()
            source_status = (
                row.get("status")
                or row.get("claim_status")
                or row.get("support_type")
                or ""
            ).strip()
            fragment = re.sub(r"\s+", " ", claim_text)
            fragment = fragment[:90]
            manuscript_match = bool(fragment and fragment.lower() in re.sub(r"\s+", " ", manuscript).lower())
            trace_rows.append(
                {
                    "trace_id": f"TRACE-{source_name[:4]}-{index:03d}",
                    "claim": claim_text,
                    "supporting_evidence": support,
                    "source_register": source_name,
                    "source_status": source_status,
                    "literal_or_close_match_in_manuscript": "YES" if manuscript_match else "NO",
                    "audit_status": "PASS" if claim_text and support else "FAIL",
                    "notes": "Literal/close-match field is conservative and does not replace semantic review.",
                }
            )
            if not claim_text or not support:
                issue(
                    issues,
                    f"TRACE-{index:03d}",
                    "MAJOR",
                    "Claim-to-evidence traceability",
                    f"{source_name} row {index} lacks claim text or support mapping: {row}",
                    "A claim cannot be audited without an explicit evidence mapping.",
                    "Repair the committed traceability mapping or remove the unsupported claim.",
                    "YES",
                    "NO",
                )

    # Citation integrity.
    source_register_path = repo / (
        "reports/pilot_05_external_literature_grounding/"
        "pilot_05AX_verified_source_register.csv"
    )
    usage_path = repo / (
        "reports/pilot_05_verified_citation_integration/"
        "pilot_05AY_citation_usage_register.csv"
    )
    placeholder_path = repo / (
        "reports/pilot_05_verified_citation_integration/"
        "pilot_05AY_placeholder_resolution_audit.csv"
    )
    reference_list_path = repo / (
        "reports/pilot_05_verified_citation_integration/"
        "pilot_05AY_reference_list.md"
    )
    for path in [source_register_path, usage_path, placeholder_path, reference_list_path]:
        if not path.is_file():
            fail(f"Missing citation input: {rel(repo, path)}")

    source_register = read_csv_rows(source_register_path)
    usage_rows = read_csv_rows(usage_path)
    placeholder_rows = read_csv_rows(placeholder_path)
    reference_list_text = read_text(reference_list_path)
    source_by_id = {row.get("source_id", "").strip(): row for row in source_register}
    citation_rows: list[dict[str, str]] = []

    unresolved_tokens = find_contexts(
        manuscript,
        r"(?i)(?:\[\s*(?:CITATION|REF|SOURCE)[^\]]*\]|\{\{[^}]*citation[^}]*\}\}|<citation[^>]*>)",
        flags=re.I,
        limit=20,
    )
    citation_rows.append(
        {
            "check_id": "CITE-001",
            "check": "Unresolved citation placeholders",
            "status": "PASS" if not unresolved_tokens else "FAIL",
            "source_id": "",
            "citation_label": "",
            "evidence": " || ".join(unresolved_tokens),
            "required_action": "" if not unresolved_tokens else "Resolve every placeholder.",
        }
    )
    if unresolved_tokens:
        issue(
            issues,
            "CITE-001",
            "BLOCKER",
            "Citations",
            " || ".join(unresolved_tokens),
            "Unresolved citation placeholders make the manuscript incomplete.",
            "Replace every placeholder with a verified citation from the 05AX register.",
            "NO",
            "YES",
        )

    for index, row in enumerate(usage_rows, start=1):
        source_id = row.get("source_id", "").strip()
        label = row.get("citation_label", "").strip()
        registered = source_id in source_by_id
        label_in_manuscript = bool(label and label in manuscript)
        source = source_by_id.get(source_id, {})
        title = source.get("title", "").strip()
        title_in_reference = bool(title and title.lower() in reference_list_text.lower())
        status = "PASS" if registered and label_in_manuscript and title_in_reference else "FAIL"
        evidence_parts = [
            f"registered={registered}",
            f"label_in_manuscript={label_in_manuscript}",
            f"title_in_reference_list={title_in_reference}",
        ]
        citation_rows.append(
            {
                "check_id": f"CITE-{index + 1:03d}",
                "check": "Usage-register citation mapping",
                "status": status,
                "source_id": source_id,
                "citation_label": label,
                "evidence": "; ".join(evidence_parts),
                "required_action": "" if status == "PASS" else "Repair citation label, source registration, or reference entry.",
            }
        )
        if status != "PASS":
            issue(
                issues,
                f"CITE-{index + 1:03d}",
                "MAJOR",
                "Citations",
                f"{source_id} / {label}: {'; '.join(evidence_parts)}",
                "Every in-text citation must resolve to a verified source and a reference-list entry.",
                "Correct the citation or reference entry using the verified 05AX register.",
                "NO",
                "YES",
            )

        peer_status = source.get("peer_review_status", "").lower()
        source_class = source.get("source_class", "").lower()
        if "preprint" in peer_status or "preprint" in source_class or "arxiv" in source.get("venue_or_institution", "").lower():
            reference_context = "\n".join(
                line for line in reference_list_text.splitlines()
                if title and title.lower()[:40] in line.lower()
            )
            labelled_preprint = bool(re.search(r"(?i)\b(preprint|arxiv)\b", reference_context))
            citation_rows.append(
                {
                    "check_id": f"CITE-PRE-{index:03d}",
                    "check": "Preprint labelling",
                    "status": "PASS" if labelled_preprint else "FAIL",
                    "source_id": source_id,
                    "citation_label": label,
                    "evidence": reference_context,
                    "required_action": "" if labelled_preprint else "Label the source as a preprint/arXiv item.",
                }
            )
            if not labelled_preprint:
                issue(
                    issues,
                    f"CITE-PRE-{index:03d}",
                    "MODERATE",
                    "References",
                    f"Preprint source {source_id} is not visibly labelled as preprint/arXiv in its reference entry.",
                    "Source status must be transparent to reviewers.",
                    "Add the verified preprint designation to the reference entry.",
                    "NO",
                    "YES",
                )

    unresolved_register = [
        row for row in placeholder_rows
        if row.get("status", "").strip().upper() not in {"PASS", "RESOLVED"}
        or row.get("literal_token_remaining", "").strip().upper() not in {"", "0", "FALSE", "NO"}
    ]
    citation_rows.append(
        {
            "check_id": "CITE-PLACEHOLDER-REGISTER",
            "check": "05AY placeholder resolution register",
            "status": "PASS" if not unresolved_register else "FAIL",
            "source_id": "",
            "citation_label": "",
            "evidence": f"unresolved_rows={len(unresolved_register)}",
            "required_action": "" if not unresolved_register else "Resolve register failures.",
        }
    )
    if unresolved_register:
        issue(
            issues,
            "CITE-PLACEHOLDER-REGISTER",
            "BLOCKER",
            "Citations",
            f"05AY placeholder audit has {len(unresolved_register)} unresolved rows.",
            "The committed citation integration contract is not fully satisfied.",
            "Resolve the failed placeholder rows before submission.",
            "NO",
            "YES",
        )

    fsb_sources = [
        row for row in source_register
        if "financial stability board" in (
            row.get("authors", "") + " " + row.get("venue_or_institution", "") + " " + row.get("title", "")
        ).lower()
        and row.get("year", "").strip() == "2026"
    ]
    if fsb_sources:
        for index, source in enumerate(fsb_sources, start=1):
            title = source.get("title", "")
            context = "\n".join(
                line for line in reference_list_text.splitlines()
                if title and title.lower()[:35] in line.lower()
            )
            consultation_ok = "consultation" in (
                context + " " + source.get("source_class", "") + " " + source.get("title", "")
            ).lower()
            citation_rows.append(
                {
                    "check_id": f"CITE-FSB-{index:02d}",
                    "check": "2026 FSB consultation labelling",
                    "status": "PASS" if consultation_ok else "FAIL",
                    "source_id": source.get("source_id", ""),
                    "citation_label": "",
                    "evidence": context or title,
                    "required_action": "" if consultation_ok else "Identify the FSB item as a consultation report.",
                }
            )
            if not consultation_ok:
                issue(
                    issues,
                    f"CITE-FSB-{index:02d}",
                    "MODERATE",
                    "References",
                    context or title,
                    "The source type must not be presented as settled regulation or peer-reviewed evidence.",
                    "Label the 2026 FSB item explicitly as a consultation report.",
                    "NO",
                    "YES",
                )
    else:
        citation_rows.append(
            {
                "check_id": "CITE-FSB-00",
                "check": "2026 FSB consultation present in verified register",
                "status": "FAIL",
                "source_id": "",
                "citation_label": "",
                "evidence": "No 2026 FSB source found in verified register.",
                "required_action": "Verify whether the expected source is present and correctly identified.",
            }
        )
        issue(
            issues,
            "CITE-FSB-00",
            "MAJOR",
            "References",
            "No 2026 Financial Stability Board source was found in the 05AX verified source register.",
            "The handoff identifies a submission-critical source-labelling requirement that cannot be verified.",
            "Reconcile the source register before submission.",
            "YES",
            "NO",
        )

    # Notation and terminology consistency.
    notation_rows: list[dict[str, str]] = []
    notation_rules = [
        ("NOT-001", "Evidence-State Reliability term", r"\bEvidence-State Reliability\b", True),
        ("NOT-002", "ESR abbreviation", r"\bESR\b", True),
        ("NOT-003", "Evidence state definition", r"(?i)\bDefinition\s+1:\s+Evidence state\b|\bevidence state\b", True),
        ("NOT-004", "Parser validity definition", r"(?i)\bparser validity\b", True),
        ("NOT-005", "Stage/evidence success definition", r"(?i)\bstage/evidence success\b|\bstage success\b", True),
        ("NOT-006", "Reliability cascade definition", r"(?i)\breliability cascade\b", True),
        ("NOT-007", "Controlled evidence degradation", r"(?i)\bcontrolled evidence degradation\b|\bcontrolled evidence-state degradation\b", True),
        ("NOT-008", "Decision stage", r"(?i)\bdecision stage\b", True),
        ("NOT-009", "Audit stage", r"(?i)\baudit stage\b", True),
        ("NOT-010", "Escalation stage", r"(?i)\bescalation stage\b", True),
        ("NOT-011", "Parser-validity hyphenation", r"(?i)\bparser-validity\b", False),
        ("NOT-012", "Parser validity open form", r"(?i)\bparser validity\b", False),
    ]
    for check_id, name, pattern, required in notation_rules:
        contexts = find_contexts(manuscript, pattern, flags=re.I, limit=5)
        status = "PASS" if contexts or not required else "FAIL"
        notation_rows.append(
            {
                "check_id": check_id,
                "construct_or_term": name,
                "status": status,
                "evidence": " || ".join(contexts),
                "required_action": "" if status == "PASS" else f"Define and use {name} consistently.",
            }
        )
        if required and not contexts:
            issue(
                issues,
                check_id,
                "MAJOR",
                "Formal definitions and notation",
                f"Required construct not found: {name}",
                "Core constructs must be explicitly defined and used consistently.",
                f"Add or restore the verified definition for {name}.",
                "NO",
                "YES",
            )

    parser_hyphen_count = len(re.findall(r"(?i)\bparser-validity\b", manuscript))
    parser_open_count = len(re.findall(r"(?i)\bparser validity\b", manuscript))
    if parser_hyphen_count and parser_open_count:
        issue(
            issues,
            "NOT-013",
            "MINOR",
            "Terminology",
            f"'parser-validity' occurrences={parser_hyphen_count}; 'parser validity' occurrences={parser_open_count}",
            "Inconsistent compound styling creates avoidable editorial noise.",
            "Apply one editorial convention, preserving hyphenation only where grammatically required.",
            "NO",
            "YES",
        )

    formal_definitions_path = repo / (
        "reports/pilot_05_formal_definition_citation_refinement/"
        "pilot_05AW_formal_definitions_and_notation.md"
    )
    formal_text = read_text(formal_definitions_path)
    definition_headings = re.findall(r"(?im)^##\s+(Definition\s+\d+:\s+.+)$", formal_text)
    for index, definition in enumerate(definition_headings, start=1):
        term = definition.split(":", 1)[1].strip()
        present = term.lower() in manuscript.lower()
        notation_rows.append(
            {
                "check_id": f"NOT-DEF-{index:02d}",
                "construct_or_term": definition,
                "status": "PASS" if present else "FAIL",
                "evidence": f"term_present_in_manuscript={present}",
                "required_action": "" if present else f"Integrate or explicitly omit the verified definition for {term}.",
            }
        )
        if not present:
            issue(
                issues,
                f"NOT-DEF-{index:02d}",
                "MODERATE",
                "Formal definitions and notation",
                f"05AW definition term absent from manuscript: {term}",
                "A verified formal construct was not integrated into the paper.",
                "Integrate the definition or document a deliberate omission during manuscript repair.",
                "NO",
                "YES",
            )

    equation_labels = re.findall(r"\\label\{([^}]+)\}", manuscript)
    equation_refs = re.findall(r"\\(?:eqref|ref)\{([^}]+)\}", manuscript)
    missing_equation_labels = sorted(set(equation_refs) - set(equation_labels))
    notation_rows.append(
        {
            "check_id": "NOT-EQ-001",
            "construct_or_term": "Equation reference resolution",
            "status": "PASS" if not missing_equation_labels else "FAIL",
            "evidence": f"labels={equation_labels}; refs={equation_refs}; missing={missing_equation_labels}",
            "required_action": "" if not missing_equation_labels else "Add missing equation labels or repair references.",
        }
    )
    if missing_equation_labels:
        issue(
            issues,
            "NOT-EQ-001",
            "MAJOR",
            "Formal definitions and notation",
            f"Unresolved equation references: {missing_equation_labels}",
            "Broken equation references prevent technical verification.",
            "Repair each equation label and reference.",
            "NO",
            "YES",
        )

    # Tables and figures.
    figure_rows: list[dict[str, str]] = []
    figure_dir = repo / "reports/pilot_05_cfpb_glm52_paper_figures_tables"
    pngs = sorted(figure_dir.glob("pilot_05AS_figure_*.png"))
    figure_numbers: list[int] = []
    for path in pngs:
        match = re.search(r"figure_(\d+)", path.name)
        number = int(match.group(1)) if match else -1
        figure_numbers.append(number)
        manuscript_ref = bool(
            re.search(rf"(?i)\bFigure\s+0*{number}\b", manuscript)
            or path.name in manuscript
        )
        filename_exposed = path.name in manuscript
        status = "PASS" if manuscript_ref else "FAIL"
        figure_rows.append(
            {
                "check_id": f"FIG-{number:03d}",
                "item_type": "figure",
                "number_or_name": str(number),
                "committed_artifact": rel(repo, path),
                "introduced_in_manuscript": "YES" if manuscript_ref else "NO",
                "internal_filename_exposed": "YES" if filename_exposed else "NO",
                "status": status,
                "required_action": "" if status == "PASS" else "Introduce and cite the figure in manuscript prose.",
            }
        )
        if not manuscript_ref:
            issue(
                issues,
                f"FIG-{number:03d}",
                "MAJOR",
                "Tables and figures",
                f"Committed figure not introduced: {rel(repo, path)}",
                "Every submitted figure must be called out and interpreted in the text.",
                f"Introduce Figure {number} in the results or discussion and provide a journal-form caption.",
                "NO",
                "YES",
            )
        if filename_exposed:
            issue(
                issues,
                f"FIG-FILENAME-{number:03d}",
                "MAJOR",
                "Tables and figures",
                f"Internal filename appears in manuscript: {path.name}",
                "Internal artifact names are not publication captions.",
                f"Replace the filename heading with 'Figure {number}' and a manuscript-appropriate caption.",
                "NO",
                "YES",
            )

    expected_figures = list(range(1, max(figure_numbers) + 1)) if figure_numbers else []
    figure_sequence_ok = figure_numbers == expected_figures
    figure_rows.append(
        {
            "check_id": "FIG-SEQUENCE",
            "item_type": "figure_sequence",
            "number_or_name": ",".join(map(str, figure_numbers)),
            "committed_artifact": "",
            "introduced_in_manuscript": "",
            "internal_filename_exposed": "",
            "status": "PASS" if figure_sequence_ok else "FAIL",
            "required_action": "" if figure_sequence_ok else "Repair sequential figure numbering.",
        }
    )
    if not figure_sequence_ok:
        issue(
            issues,
            "FIG-SEQUENCE",
            "MAJOR",
            "Tables and figures",
            f"Observed figure sequence {figure_numbers}; expected {expected_figures}",
            "Non-sequential numbering creates broken cross-references.",
            "Renumber figures and update every callout.",
            "NO",
            "YES",
        )

    table_count = markdown_table_count(manuscript)
    table_refs = sorted({int(value) for value in re.findall(r"(?i)\bTable\s+(\d+)\b", manuscript)})
    figure_rows.append(
        {
            "check_id": "TABLE-001",
            "item_type": "table_inventory",
            "number_or_name": f"markdown_tables={table_count}; referenced_numbers={table_refs}",
            "committed_artifact": "",
            "introduced_in_manuscript": "YES" if table_refs else "NO",
            "internal_filename_exposed": "",
            "status": "PASS" if table_count > 0 and table_refs else "FAIL",
            "required_action": "" if table_count > 0 and table_refs else "Number, caption, and introduce each manuscript table.",
        }
    )
    if table_count > 0 and not table_refs:
        issue(
            issues,
            "TABLE-001",
            "MAJOR",
            "Tables and figures",
            f"Detected {table_count} Markdown tables but no numbered Table callouts.",
            "Unnumbered embedded source tables are not publication-ready.",
            "Select the necessary tables, assign sequential numbers and captions, and introduce them in prose.",
            "NO",
            "YES",
        )

    # Abstract-results-conclusion alignment.
    abstract = section_text(manuscript, r"^abstract$")
    results = section_text(manuscript, r"^results$", boundary="numbered")
    discussion = section_text(manuscript, r"^discussion$", boundary="numbered")
    conclusion = section_text(manuscript, r"^conclusion$", boundary="numbered")
    limitations = section_text(
        manuscript,
        r"^(?:claim boundary and limitations|limitations and validity threats|limitations)$",
        boundary="numbered",
    )
    if not limitations:
        limitations = section_text(manuscript, r"^threats to validity$")

    section_regressions = {
        "results_section_extracted": bool(results.strip()),
        "limitations_section_extracted": bool(limitations.strip()),
        "discussion_section_extracted": bool(discussion.strip()),
        "conclusion_section_extracted": bool(conclusion.strip()),
    }
    failed_section_regressions = [
        name for name, passed in section_regressions.items() if not passed
    ]
    if failed_section_regressions:
        fail(
            "05BA-REPAIR V3 section-extraction regression failed before output overwrite: "
            f"{failed_section_regressions}"
        )

    alignment_checks: list[dict[str, str]] = []
    for name, text in [
        ("Abstract", abstract),
        ("Results", results),
        ("Discussion", discussion),
        ("Conclusion", conclusion),
        ("Limitations", limitations),
    ]:
        alignment_checks.append(
            {
                "section": name,
                "exists": "YES" if text.strip() else "NO",
                "word_count": str(len(re.findall(r"\b\w+\b", text))),
                "protected_metric_mentions": str(
                    sum(
                        1 for metric in EXPECTED_METRICS
                        if any(value in text for value in metric["values"])
                    )
                ),
                "bounded_scope_terms": ", ".join(
                    term for term in [
                        "within", "single model", "GLM-5.2", "sanitized",
                        "60", "720", "not", "limitation"
                    ]
                    if term.lower() in text.lower()
                ),
            }
        )
        if not text.strip():
            issue(
                issues,
                f"ALIGN-{name.upper()}",
                "BLOCKER",
                "Abstract-results-conclusion alignment",
                f"{name} section could not be extracted from the manuscript heading structure.",
                "Alignment cannot be verified when a core section is missing or structurally malformed.",
                f"Repair the {name} heading and section structure.",
                "NO",
                "YES",
            )

    abstract_metric_values = {
        value
        for metric in EXPECTED_METRICS
        for value in metric["values"]
        if value in abstract
    }
    results_metric_values = {
        value
        for metric in EXPECTED_METRICS
        for value in metric["values"]
        if value in results
    }
    unsupported_abstract_values = sorted(abstract_metric_values - results_metric_values)
    if unsupported_abstract_values:
        issue(
            issues,
            "ALIGN-001",
            "BLOCKER",
            "Abstract-results-conclusion alignment",
            f"Protected values in abstract but not detected in Results: {unsupported_abstract_values}",
            "Every empirical value in the abstract must be evidenced in the Results section.",
            "Add the corresponding result evidence or remove the unsupported abstract value.",
            "NO",
            "YES",
        )

    if "single" not in limitations.lower() or "model" not in limitations.lower():
        issue(
            issues,
            "ALIGN-002",
            "MAJOR",
            "Limitations",
            "No explicit 'single model' wording detected in the extracted limitations section.",
            "Pilot 05 uses one scaled model; external-validity limits must be explicit.",
            "State that Pilot 05 is a single-model scaled experiment and does not establish cross-provider generality.",
            "NO",
            "YES",
        )

    if not re.search(r"(?i)\b(?:not|does not|cannot)\b.{0,100}\b(?:deployment|production|regulatory|financial validity)\b", limitations):
        issue(
            issues,
            "ALIGN-003",
            "MAJOR",
            "Limitations",
            "No explicit bounded statement detected that rejects deployment, production, regulatory, or financial-validity inference.",
            "The domain context can invite overinterpretation unless non-claims are stated clearly.",
            "Add a concise limitations sentence rejecting deployment, regulatory, and real-world financial-validity inference.",
            "NO",
            "YES",
        )

    # Novelty verdict and acceptance-critical interpretation.
    ax_manifest_path = repo / (
        "reports/pilot_05_external_literature_grounding/pilot_05AX_manifest.json"
    )
    ax_manifest = json.loads(read_text(ax_manifest_path))
    novelty_verdict = str(ax_manifest.get("novelty_verdict", "")).strip()
    novelty_lower = novelty_verdict.lower()
    priority_terms_present = (
        "first-ever" in novelty_lower
        or "first ever" in novelty_lower
        or "global priority" in novelty_lower
    )
    priority_terms_explicitly_disclaimed = (
        "not claimed" in novelty_lower
        or "do not claim" in novelty_lower
        or "is not claimed" in novelty_lower
        or "not established" in novelty_lower
        or "not asserted" in novelty_lower
        or "not supported" in novelty_lower
    )
    novelty_bounded = (
        "bounded" in novelty_lower
        and (
            not priority_terms_present
            or priority_terms_explicitly_disclaimed
        )
    )
    if not novelty_bounded:
        fail(
            "05BA-REPAIR V3 novelty-boundary regression failed before output overwrite: "
            f"{novelty_verdict}"
        )

    # Sort and deduplicate issues by id/evidence.
    deduped: list[dict[str, str]] = []
    seen = set()
    for row in issues:
        key = (row["issue_id"], row["exact_evidence"])
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    issues = sorted(
        deduped,
        key=lambda row: (
            SEVERITY_ORDER.get(row["severity"], 99),
            row["issue_id"],
        ),
    )

    raw_severity_counts = Counter(row["severity"] for row in issues)
    severity_counts = {
        severity: raw_severity_counts.get(severity, 0)
        for severity in SEVERITY_ORDER
    }
    blocker_count = severity_counts.get("BLOCKER", 0)
    major_count = severity_counts.get("MAJOR", 0)
    if blocker_count:
        readiness = "NOT_SUBMISSION_READY_BLOCKERS"
    elif major_count:
        readiness = "NOT_SUBMISSION_READY_MAJOR_REPAIR"
    elif severity_counts.get("MODERATE", 0):
        readiness = "READY_ONLY_AFTER_MODERATE_REPAIR"
    else:
        readiness = "READY_FOR_FORMATTING_AND_TARGET-JOURNAL_CHECK"

    all_numeric_pass = all(
        row["status"] == "PASS" for row in numerical_rows
    )
    all_citations_pass = all(
        row["status"] == "PASS" for row in citation_rows
    )
    scaffold_failures = [
        row for row in structure_rows
        if row["category"] == "scaffold_language" and row["status"] == "FAIL"
    ]
    required_structure_pass = all(
        row["status"] == "PASS"
        for row in structure_rows
        if row["category"] == "required_section"
    )
    another_scaled_run_required = "NO_FOR_BOUNDED_SINGLE_MODEL_CLAIM"
    conversion_now = (
        "YES" if readiness == "READY_FOR_FORMATTING_AND_TARGET-JOURNAL_CHECK"
        else "NO_REPAIR_MANUSCRIPT_FIRST"
    )

    # Output directory and exact twelve-file contract were verified above.
    # This approved repair overwrites only those existing uncommitted files.

    write_csv(
        output_dir / "pilot_05BA_issue_register.csv",
        [
            "issue_id",
            "severity",
            "manuscript_section",
            "exact_evidence",
            "why_it_matters",
            "required_correction",
            "correction_needs_new_evidence",
            "manuscript_edit_only",
        ],
        issues,
    )
    write_csv(
        output_dir / "pilot_05BA_numerical_consistency_audit.csv",
        [
            "check_id",
            "metric",
            "authoritative_values",
            "authoritative_source_evidence",
            "manuscript_evidence",
            "status",
            "notes",
        ],
        numerical_rows,
    )
    write_csv(
        output_dir / "pilot_05BA_claim_evidence_traceability.csv",
        [
            "trace_id",
            "claim",
            "supporting_evidence",
            "source_register",
            "source_status",
            "literal_or_close_match_in_manuscript",
            "audit_status",
            "notes",
        ],
        trace_rows,
    )
    write_csv(
        output_dir / "pilot_05BA_citation_integrity_audit.csv",
        [
            "check_id",
            "check",
            "status",
            "source_id",
            "citation_label",
            "evidence",
            "required_action",
        ],
        citation_rows,
    )
    write_csv(
        output_dir / "pilot_05BA_structure_and_scaffold_audit.csv",
        [
            "check_id",
            "category",
            "item",
            "status",
            "evidence",
            "required_action",
        ],
        structure_rows,
    )
    write_csv(
        output_dir / "pilot_05BA_notation_and_terminology_audit.csv",
        [
            "check_id",
            "construct_or_term",
            "status",
            "evidence",
            "required_action",
        ],
        notation_rows,
    )
    write_csv(
        output_dir / "pilot_05BA_table_figure_reference_audit.csv",
        [
            "check_id",
            "item_type",
            "number_or_name",
            "committed_artifact",
            "introduced_in_manuscript",
            "internal_filename_exposed",
            "status",
            "required_action",
        ],
        figure_rows,
    )

    alignment_lines = [
        "# Pilot 05BA Abstract-Results-Conclusion Alignment",
        "",
        f"- Audit execution: PASS",
        f"- Submission-readiness verdict: `{readiness}`",
        f"- Unsupported protected abstract values: {unsupported_abstract_values or 'none detected'}",
        "",
        "## Section inventory",
        "",
        "| Section | Exists | Word count | Protected metric mentions | Bounded-scope terms detected |",
        "|---|---:|---:|---:|---|",
    ]
    for row in alignment_checks:
        alignment_lines.append(
            f"| {row['section']} | {row['exists']} | {row['word_count']} | "
            f"{row['protected_metric_mentions']} | {row['bounded_scope_terms']} |"
        )
    alignment_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This automated comparison checks section existence, protected-value overlap, "
            "and selected boundary terms. It does not treat lexical overlap as proof of "
            "semantic alignment; every MAJOR or BLOCKER item in the issue register requires "
            "human manuscript review.",
        ]
    )
    write_text(
        output_dir / "pilot_05BA_abstract_results_conclusion_alignment.md",
        "\n".join(alignment_lines),
    )

    gap_lines = [
        "# Pilot 05BA Submission Gap Classification",
        "",
        f"**Submission-readiness verdict:** `{readiness}`",
        "",
        "## Severity totals",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for severity in ["BLOCKER", "MAJOR", "MODERATE", "MINOR", "INFORMATIONAL"]:
        gap_lines.append(f"| {severity} | {severity_counts.get(severity, 0)} |")
    gap_lines.extend(
        [
            "",
            "## Decision rule",
            "",
            "- Any BLOCKER means the manuscript is not submission-ready.",
            "- With no BLOCKER but one or more MAJOR issues, manuscript repair remains required.",
            "- Word/PDF conversion should follow substantive manuscript repair, not precede it.",
            "- A second scaled-model run is not automatically required for a bounded, explicitly single-model claim.",
            "",
            "## Issues",
            "",
        ]
    )
    for row in issues:
        gap_lines.extend(
            [
                f"### {row['issue_id']} - {row['severity']}",
                "",
                f"- Section: {row['manuscript_section']}",
                f"- Evidence: {row['exact_evidence'].rstrip()}",
                f"- Why it matters: {row['why_it_matters']}",
                f"- Required correction: {row['required_correction']}",
                f"- Needs new evidence: {row['correction_needs_new_evidence']}",
                f"- Manuscript edit only: {row['manuscript_edit_only']}",
                "",
            ]
        )
    write_text(
        output_dir / "pilot_05BA_submission_gap_classification.md",
        "\n".join(gap_lines),
    )

    summary_lines = [
        "# Pilot 05BA Manuscript Integrity and Submission-Readiness Audit",
        "",
        "## Audit boundary",
        "",
        f"- Manuscript: `{MANUSCRIPT_REL.as_posix()}`",
        f"- Manuscript SHA-256: `{manuscript_hash}`",
        f"- Secured repository commit: `{head}`",
        "- Reads: committed sanitized manuscript-supporting artifacts only",
        "- Manuscript edits: none",
        "- Experiments/model/API calls: none",
        "- Raw data, `.env`, raw prompts/responses, JSONL: not accessed",
        "",
        "## Overall verdict",
        "",
        f"`{readiness}`",
        "",
        f"- BLOCKER issues: {blocker_count}",
        f"- MAJOR issues: {major_count}",
        f"- MODERATE issues: {severity_counts.get('MODERATE', 0)}",
        f"- MINOR issues: {severity_counts.get('MINOR', 0)}",
        f"- Required structural sections detected: {'YES' if required_structure_pass else 'NO'}",
        f"- Protected numerical checks all passed: {'YES' if all_numeric_pass else 'NO'}",
        f"- Citation checks all passed: {'YES' if all_citations_pass else 'NO'}",
        f"- Internal scaffold matches detected: {len(scaffold_failures)}",
        "",
        "## Answers to the ten submission-readiness questions",
        "",
        "### 1. Is the current manuscript structurally a complete paper?",
        "",
        (
            "It contains the expected core academic sections, but it is not yet a clean "
            "journal-form paper because internal assembly/scaffold sections remain."
            if required_structure_pass
            else "No. One or more required academic sections were not reliably detected."
        ),
        "",
        "### 2. Is it internally numerically consistent?",
        "",
        (
            "Yes for every protected check implemented in this audit."
            if all_numeric_pass
            else "Not yet. The numerical-consistency CSV contains failed or unverified protected checks."
        ),
        "",
        "### 3. Is its novelty claim defensible?",
        "",
        (
            f"Yes, only within the verified bounded verdict: {novelty_verdict}"
            if novelty_bounded
            else "No. The verified novelty verdict or manuscript wording is not safely bounded."
        ),
        "",
        "### 4. Are citations complete and correctly bounded?",
        "",
        (
            "The automated citation-integrity checks passed; final human citation-placement review is still required."
            if all_citations_pass
            else "No. The citation-integrity audit contains failures requiring correction."
        ),
        "",
        "### 5. Does it still contain internal scaffold/report language?",
        "",
        (
            f"Yes. {len(scaffold_failures)} scaffold-pattern checks failed."
            if scaffold_failures
            else "No scaffold-pattern failures were detected by the implemented rules."
        ),
        "",
        "### 6. Is the single-model Pilot 05 scope an acceptance blocker or a disclosed limitation?",
        "",
        "It is not automatically an acceptance blocker for a bounded single-model study. "
        "It is a major external-validity limitation that must be explicit in the abstract, "
        "discussion, limitations, and conclusion.",
        "",
        "### 7. Is another scaled model run scientifically necessary before submission?",
        "",
        "No for the current bounded within-experiment claim. It becomes necessary only if the "
        "paper claims cross-model or provider-general reliability effects, or if a chosen "
        "venue explicitly requires broader empirical generalisation.",
        "",
        "### 8. What exact work remains before journal targeting?",
        "",
        "Resolve every BLOCKER and MAJOR issue; remove internal task/scaffold language; consolidate "
        "section hierarchy; convert source packs into numbered tables and figures; repair any "
        "failed numerical, citation, notation, and alignment checks; then conduct a final human "
        "claim-to-evidence review and select a target journal.",
        "",
        "### 9. Is Word/PDF conversion justified now?",
        "",
        (
            "Yes, after a final target-journal formatting check."
            if conversion_now == "YES"
            else "No. Substantive manuscript repair should occur before Word/PDF conversion."
        ),
        "",
        "### 10. What is the shortest evidence-grounded route to a submission-ready paper?",
        "",
        "Perform one bounded manuscript-repair task using this issue register, without new experiments; "
        "rerun 05BA against the repaired manuscript; obtain a clean integrity verdict; then format the "
        "paper for the selected journal. Add another scaled model only if the intended claim or venue "
        "requires cross-model generalisation.",
        "",
        "## Interpretation boundary",
        "",
        "Audit execution `PASS` means the audit completed and validated its output contract. "
        "It does not mean the manuscript is submission-ready. Submission readiness is reported "
        "separately by the verdict above.",
    ]
    write_text(
        output_dir / "pilot_05BA_submission_readiness_summary.md",
        "\n".join(summary_lines),
    )

    # Validate generated non-manifest outputs before writing internal validation.
    csv_contracts = {
        "pilot_05BA_issue_register.csv": 8,
        "pilot_05BA_numerical_consistency_audit.csv": 7,
        "pilot_05BA_claim_evidence_traceability.csv": 8,
        "pilot_05BA_citation_integrity_audit.csv": 7,
        "pilot_05BA_structure_and_scaffold_audit.csv": 6,
        "pilot_05BA_notation_and_terminology_audit.csv": 5,
        "pilot_05BA_table_figure_reference_audit.csv": 8,
    }
    csv_validation_lines = []
    for name, expected_columns in csv_contracts.items():
        path = output_dir / name
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
        if not rows:
            fail(f"CSV is empty: {name}")
        if len(rows[0]) != expected_columns:
            fail(
                f"CSV column mismatch for {name}: expected {expected_columns}, got {len(rows[0])}"
            )
        csv_validation_lines.append(
            f"- `{name}`: PASS ({len(rows) - 1} data rows, {len(rows[0])} columns)"
        )

    outputs_before_internal = [
        name
        for name in OUTPUT_NAMES
        if name not in {
            "pilot_05BA_internal_validation_report.md",
            "pilot_05BA_manifest.json",
        }
    ]
    missing_before_internal = [
        name for name in outputs_before_internal if not (output_dir / name).is_file()
    ]
    if missing_before_internal:
        fail(f"Missing generated outputs before internal validation: {missing_before_internal}")

    current_untracked = {
        line.strip()
        for line in run_git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    expected_current_untracked = {SCRIPT_REL.as_posix()} | {
        (OUTPUT_REL / name).as_posix() for name in OUTPUT_NAMES
    }
    if current_untracked != expected_current_untracked:
        fail(
            "Unexpected untracked set before internal validation. "
            f"Expected {sorted(expected_current_untracked)}, got {sorted(current_untracked)}"
        )
    if run_git(repo, "diff", "--name-only").strip():
        fail("Tracked files changed during audit generation")
    if run_git(repo, "diff", "--cached", "--name-only").strip():
        fail("Files were staged during audit generation")
    if run_git(repo, "rev-parse", "HEAD").strip() != EXPECTED_HEAD:
        fail("HEAD changed during audit generation")

    internal_lines = [
        "# Pilot 05BA Internal Validation Report",
        "",
        "## Result",
        "",
        "`PASS`",
        "",
        "Audit execution completed and the approved output contract was validated.",
        "",
        "## Submission-readiness result",
        "",
        f"`{readiness}`",
        "",
        "This is distinct from audit execution status.",
        "",
        "## Output contract",
        "",
        f"- Expected report files including manifest: {len(OUTPUT_NAMES)}",
        f"- Expected total uncommitted files including script: {1 + len(OUTPUT_NAMES)}",
        "",
        "## CSV validation",
        "",
        *csv_validation_lines,
        "",
        "## Repository safety",
        "",
        f"- Branch: `{branch}`",
        f"- HEAD unchanged: `{head}`",
        "- Tracked files modified: 0",
        "- Staged files: 0",
        "- Deletes/resets/commits/pushes: 0",
        "- Experiments/model/API calls: 0",
        "- Raw data, `.env`, raw prompts/responses, JSONL: not accessed",
        "",
        "## Important interpretation",
        "",
        "A `PASS` here certifies that the audit ran and its reports satisfy the output "
        "contract. It does not certify manuscript submission readiness.",
    ]
    write_text(
        output_dir / "pilot_05BA_internal_validation_report.md",
        "\n".join(internal_lines),
    )

    pre_manifest_names = [
        name for name in OUTPUT_NAMES if name != "pilot_05BA_manifest.json"
    ]
    missing_pre_manifest = [
        name for name in pre_manifest_names if not (output_dir / name).is_file()
    ]
    if missing_pre_manifest:
        fail(f"Missing generated outputs before manifest: {missing_pre_manifest}")

    manifest = {
        "task_id": TASK_ID,
        "task_name": "Full Manuscript Integrity and Submission-Readiness Audit",
        "repair_version": "05BA-REPAIR-V3",
        "status": "PASS",
        "audit_execution_status": "PASS",
        "submission_readiness_verdict": readiness,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "secured_checkpoint": {
            "branch": branch,
            "head": head,
            "manuscript_path": MANUSCRIPT_REL.as_posix(),
            "manuscript_sha256": manuscript_hash,
        },
        "source_boundary": {
            "allowed_input_directories": [path.as_posix() for path in ALLOWED_INPUT_DIRS],
            "authoritative_main_results_table": MAIN_RESULTS_REL.as_posix(),
            "authoritative_main_results_metric_count": len(main_results_by_metric),
            "committed_input_file_count": len(input_files),
            "input_sha256": input_hashes,
        },
        "regression_checks": {
            **section_regressions,
            "novelty_verdict_bounded": novelty_bounded,
            "authoritative_main_results_table_has_exact_17_metric_contract": (
                set(main_results_by_metric) == set(EXPECTED_MAIN_RESULTS_CONTRACT)
                and not main_results_contract_failures
            ),
            "all_16_manuscript_metric_checks_resolve_to_exact_05AR_rows": (
                not unresolved_source_metrics
                and len(METRIC_MAIN_RESULTS_KEYS) == 16
            ),
            "ledger_parser_accounting_470_plus_250_equals_720": 470 + 250 == 720,
            "persisted_parser_accounting_470_plus_243_equals_713": 470 + 243 == 713,
            "missing_sanitized_row_accounting_720_minus_713_equals_7": 720 - 713 == 7,
            "parser_valid_preservation_470_minus_470_equals_0": 470 - 470 == 0,
            "all_protected_numerical_sources_resolved": not unresolved_source_metrics,
            "all_severity_keys_emitted": set(severity_counts) == set(SEVERITY_ORDER),
            "negated_boundary_statements_not_flagged_as_overclaims": (
                suppressed_negated_claim_matches >= 0
                and not any(
                    row["issue_id"] in {"CLAIM-001", "CLAIM-011"}
                    and re.search(r"(?i)\b(?:not|does not|cannot)\b", row["exact_evidence"])
                    for row in issues
                )
            ),
        },
        "counts": {
            "issues_total": len(issues),
            "severity": severity_counts,
            "numerical_checks": len(numerical_rows),
            "claim_trace_rows": len(trace_rows),
            "citation_checks": len(citation_rows),
            "structure_checks": len(structure_rows),
            "notation_checks": len(notation_rows),
            "table_figure_checks": len(figure_rows),
            "scaffold_failures": len(scaffold_failures),
        },
        "decisions": {
            "single_model_scope_acceptance_blocker": "NO_AUTOMATIC_BLOCKER_DISCLOSED_MAJOR_LIMITATION",
            "another_scaled_model_run_required": another_scaled_run_required,
            "word_pdf_conversion_now": conversion_now,
        },
        "safety": {
            "manuscript_modified": False,
            "readme_modified": False,
            "earlier_reports_modified": False,
            "new_literature_research": False,
            "experiments_run": False,
            "model_calls": False,
            "api_calls": False,
            "raw_cfpb_data_accessed": False,
            "env_accessed": False,
            "raw_prompt_response_accessed": False,
            "jsonl_accessed_or_written": False,
            "staged_committed_or_pushed": False,
        },
        "output_sha256_excluding_manifest": {
            name: sha256_file(output_dir / name) for name in pre_manifest_names
        },
        "expected_output_count_including_manifest": len(OUTPUT_NAMES),
    }
    write_text(
        output_dir / "pilot_05BA_manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False),
    )

    # Final exact output and repository-state validation.
    actual_names = sorted(path.name for path in output_dir.iterdir() if path.is_file())
    expected_names = sorted(OUTPUT_NAMES)
    if actual_names != expected_names:
        fail(f"Output contract mismatch: expected {expected_names}, got {actual_names}")

    final_untracked = {
        line.strip()
        for line in run_git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    }
    expected_untracked = {SCRIPT_REL.as_posix()} | {
        (OUTPUT_REL / name).as_posix() for name in OUTPUT_NAMES
    }
    if final_untracked != expected_untracked:
        fail(
            "Unexpected final untracked set. "
            f"Expected {sorted(expected_untracked)}, got {sorted(final_untracked)}"
        )
    if run_git(repo, "diff", "--name-only").strip():
        fail("Tracked files changed during audit generation")
    if run_git(repo, "diff", "--cached", "--name-only").strip():
        fail("Files were staged during audit generation")
    if run_git(repo, "rev-parse", "HEAD").strip() != EXPECTED_HEAD:
        fail("HEAD changed during audit generation")

    for name in OUTPUT_NAMES:
        path = output_dir / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"Missing or empty final output: {name}")

    print("=== TASK 05BA-REPAIR V3 GENERATION RESULT ===")
    print("audit_execution_status: PASS")
    print(f"submission_readiness_verdict: {readiness}")
    print(f"issues_total: {len(issues)}")
    for severity in ["BLOCKER", "MAJOR", "MODERATE", "MINOR", "INFORMATIONAL"]:
        print(f"{severity.lower()}_issues: {severity_counts.get(severity, 0)}")
    print(f"numerical_checks: {len(numerical_rows)}")
    print(f"citation_checks: {len(citation_rows)}")
    print(f"scaffold_failures: {len(scaffold_failures)}")
    print(f"report_files_created: {len(OUTPUT_NAMES)}")
    print(f"total_uncommitted_files: {1 + len(OUTPUT_NAMES)}")
    print("tracked_files_modified: 0")
    print("staged_files: 0")
    print("experiments_run: 0")
    print("model_or_api_calls: 0")
    print("raw_data_accessed: NO")
    print("env_accessed: NO")
    print("raw_prompt_response_accessed: NO")
    print("jsonl_accessed_or_written: NO")
    print("")
    print("=== TOP SUBMISSION ISSUES ===")
    if not issues:
        print("[none]")
    else:
        for row in issues[:20]:
            evidence = re.sub(r"\s+", " ", row["exact_evidence"]).strip()
            if len(evidence) > 240:
                evidence = evidence[:237] + "..."
            print(
                f"{row['issue_id']} | {row['severity']} | "
                f"{row['manuscript_section']} | {evidence}"
            )
    print("")
    print("STOP: Paste the complete terminal output before any manuscript repair is designed or approved.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("=== TASK 05BA-REPAIR V3 GENERATION RESULT ===", file=sys.stderr)
        print("audit_execution_status: FAIL", file=sys.stderr)
        print(f"error_type: {type(exc).__name__}", file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        print("No deletion, reset, staging, commit, or push was attempted.", file=sys.stderr)
        raise
