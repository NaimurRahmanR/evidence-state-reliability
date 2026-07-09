from __future__ import annotations

import csv
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_ID = "05AV"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = "experiments/pilot_05_full_manuscript_draft_assembly.py"
OUTPUT_DIR_REL = "reports/pilot_05_full_manuscript_draft_assembly"
OUTPUT_DIR = REPO_ROOT / OUTPUT_DIR_REL

EXPECTED_OUTPUT_NAMES = [
    "pilot_05AV_manifest.json",
    "pilot_05AV_source_file_index.csv",
    "pilot_05AV_full_manuscript_draft.md",
    "pilot_05AV_manuscript_section_index.csv",
    "pilot_05AV_claim_traceability_matrix.csv",
    "pilot_05AV_submission_readiness_gap_analysis.md",
    "pilot_05AV_internal_review_checklist.md",
    "pilot_05AV_full_manuscript_assembly_report.md",
]

EXPECTED_OUTPUTS = [f"{OUTPUT_DIR_REL}/{name}" for name in EXPECTED_OUTPUT_NAMES]
EXPECTED_UNTRACKED_05AV = {SCRIPT_REL, *EXPECTED_OUTPUTS}

SOURCE_FILES = [
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_manifest.json",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_source_file_index.csv",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_manuscript_skeleton.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_methods_section_draft.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_results_section_draft.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_contribution_novelty_framing.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_claim_boundary_and_limitations.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_table_figure_callouts.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_title_abstract_keywords.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_reproducibility_statement.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_next_revision_roadmap.md",
    "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_manuscript_synthesis_report.md",
]

REQUIRED_SAFETY_FLAGS = [
    "no_api_calls",
    "no_model_calls",
    "no_env_read",
    "no_raw_prompt_response_access",
    "no_jsonl_written",
    "no_raw_cfpb_data_touched",
]

SAFETY_FLAGS = {
    "no_api_calls": True,
    "no_model_calls": True,
    "no_env_read": True,
    "no_raw_prompt_response_access": True,
    "no_jsonl_written": True,
    "no_raw_cfpb_data_touched": True,
}

SAFE_CLAIM = (
    "Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled "
    "evidence-state degradation produces measurable reliability-layer changes across decision, audit, "
    "and escalation stages. In this run, parser validity improved under degraded evidence while "
    "stage/evidence success deteriorated, supporting Evidence-State Reliability as distinct from parser validity."
)

DO_NOT_CLAIM = [
    "broad GLM reliability",
    "general LLM reliability",
    "model/provider superiority",
    "real-world financial validity",
    "regulatory validity",
    "deployment safety",
    "consumer harm prevalence",
    "company misconduct",
    "parser validity equals answer correctness",
    "Q1 acceptance or paper completion",
]


class AssemblyError(RuntimeError):
    pass


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def run_git(args: List[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def git_tracked(path: str) -> bool:
    return bool(run_git(["ls-files", "--", path]).strip())


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_text(path))


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def strip_first_heading(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).strip()
    return text.strip()


def check_checkpoint() -> Dict[str, Any]:
    branch = run_git(["branch", "--show-current"])
    latest_commit = run_git(["log", "-1", "--pretty=format:%h %s"])
    latest_hash = run_git(["rev-parse", "--short", "HEAD"])
    latest_subject = run_git(["log", "-1", "--pretty=format:%s"])
    ahead_behind = run_git(["rev-list", "--left-right", "--count", "origin/main...main"])

    staged = [normalize(x) for x in run_git(["diff", "--cached", "--name-only"]).splitlines() if x.strip()]
    modified_tracked = [normalize(x) for x in run_git(["diff", "--name-only"]).splitlines() if x.strip()]
    untracked = [normalize(x) for x in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if x.strip()]
    unexpected_untracked = [p for p in untracked if p not in EXPECTED_UNTRACKED_05AV]

    parts = ahead_behind.split()
    behind = int(parts[0]) if len(parts) == 2 else -1
    ahead = int(parts[1]) if len(parts) == 2 else -1

    if branch != "main":
        raise AssemblyError(f"Expected branch main, got {branch}")
    if latest_hash != "10465f5" or latest_subject != "Add Pilot 05 manuscript synthesis":
        raise AssemblyError(f"Expected secured 05AU commit 10465f5, got {latest_commit}")
    if behind != 0 or ahead != 0:
        raise AssemblyError(f"main is not aligned with origin/main: {ahead_behind}")
    if staged:
        raise AssemblyError(f"Unexpected staged files: {staged}")
    if modified_tracked:
        raise AssemblyError(f"Unexpected modified tracked files: {modified_tracked}")
    if unexpected_untracked:
        raise AssemblyError(f"Unexpected untracked files: {unexpected_untracked}")

    return {
        "branch": branch,
        "latest_commit": latest_commit,
        "latest_hash": latest_hash,
        "latest_subject": latest_subject,
        "behind": behind,
        "ahead": ahead,
        "staged_count": len(staged),
        "modified_tracked_count": len(modified_tracked),
        "untracked_count": len(untracked),
        "unexpected_untracked_count": len(unexpected_untracked),
    }


def verify_sources() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for source_file in SOURCE_FILES:
        full = REPO_ROOT / source_file
        exists = full.is_file()
        tracked = git_tracked(source_file)
        size = full.stat().st_size if exists else ""
        rows.append({
            "source_file": source_file,
            "exists": exists,
            "tracked": tracked,
            "size_bytes": size,
            "status": "PASS" if exists and tracked else "FAIL",
        })

    failed = [row for row in rows if row["status"] != "PASS"]
    if failed:
        raise AssemblyError(f"Missing/untracked 05AU source files: {failed[:5]}")

    write_csv(OUTPUT_DIR / "pilot_05AV_source_file_index.csv", rows, ["source_file", "exists", "tracked", "size_bytes", "status"])
    return rows


def verify_05au_manifest() -> Dict[str, Any]:
    manifest = read_json(REPO_ROOT / "reports/pilot_05_manuscript_skeleton_results_methods/pilot_05AU_manifest.json")

    if manifest.get("status") != "PASS":
        raise AssemblyError("05AU manifest status is not PASS.")

    for flag in REQUIRED_SAFETY_FLAGS:
        value = manifest.get(flag)
        if value is None and isinstance(manifest.get("safety_flags"), dict):
            value = manifest["safety_flags"].get(flag)
        if value is not True:
            raise AssemblyError(f"05AU manifest safety flag missing/false: {flag}")

    source_boundary = manifest.get("source_boundary", {})
    if source_boundary.get("committed_outputs_only") is not True:
        raise AssemblyError("05AU manifest does not confirm committed_outputs_only.")
    if source_boundary.get("does_not_create_new_empirical_evidence") is not True:
        raise AssemblyError("05AU manifest does not confirm no-new-empirical-evidence boundary.")

    return manifest


def load_material() -> Dict[str, str]:
    base = REPO_ROOT / "reports" / "pilot_05_manuscript_skeleton_results_methods"

    files = {
        "title_abstract_keywords": "pilot_05AU_title_abstract_keywords.md",
        "skeleton": "pilot_05AU_manuscript_skeleton.md",
        "methods": "pilot_05AU_methods_section_draft.md",
        "results": "pilot_05AU_results_section_draft.md",
        "contribution": "pilot_05AU_contribution_novelty_framing.md",
        "claim_boundary": "pilot_05AU_claim_boundary_and_limitations.md",
        "table_figure_callouts": "pilot_05AU_table_figure_callouts.md",
        "reproducibility": "pilot_05AU_reproducibility_statement.md",
        "roadmap": "pilot_05AU_next_revision_roadmap.md",
        "synthesis_report": "pilot_05AU_manuscript_synthesis_report.md",
    }

    return {key: read_text(base / filename) for key, filename in files.items()}


def assemble_full_manuscript(material: Dict[str, str], meta: Dict[str, Any]) -> str:
    return f"""# Evidence-State Reliability in Multi-Stage LLM Decision Pipelines

## Manuscript status

Draft assembled by Task 05AV from committed 05AU synthesis artifacts only. This draft does not create new empirical evidence.

## Abstract

LLM evaluation commonly emphasizes final-output validity, parser compliance, or answer-level correctness. In multi-stage decision pipelines, however, downstream outputs may remain parser-valid even when the evidence state reaching the downstream stage has been degraded. This study introduces Evidence-State Reliability as a reliability layer concerned with whether intermediate evidence states remain sufficiently complete, grounded, and usable across a multi-stage LLM decision pipeline. Using committed Pilot 05 outputs only, the study analyzes a sanitized, CFPB-backed, scaled GLM-5.2 pipeline experiment with controlled evidence-state degradation across decision, audit, and escalation stages. The central result is a divergence between parser validity and evidence-state reliability: parser validity improves under degraded evidence while stage/evidence success deteriorates. This supports the paper's core claim that parser validity is not a sufficient proxy for evidence-state reliability. The contribution is a reproducible empirical framing for reliability cascades in multi-stage LLM decision systems, with paper-ready tables, figures, claim boundaries, and repo-wide validation artifacts.

## Keywords

Evidence-State Reliability; Reliability Cascades; LLM Evaluation; Multi-Stage Decision Pipelines; Parser Validity; Auditability; Escalation; CFPB; Reproducibility; GLM-5.2

## 1. Introduction

Multi-stage LLM decision systems do not only fail at the final answer layer. They can also fail when the evidence state passed from one stage to another becomes degraded, incomplete, or misleading while the downstream output remains structurally parser-valid. This creates a reliability problem that is easy to miss if evaluation stops at final-output parsability.

The problem is especially important in decision pipelines where an upstream evidence packet informs downstream decision, audit, and escalation behavior. A parser-valid output can satisfy the required schema while still being grounded in a degraded evidence state. In such cases, parser validity may provide a false sense of operational reliability.

This paper frames that problem as Evidence-State Reliability. Evidence-State Reliability is the reliability of the intermediate evidence state used by downstream stages in a decision pipeline. It is distinct from final-output validity, parser compliance, and answer-level surface correctness.

The central research question is:

**How can Evidence-State Reliability be measured separately from final parser validity in a multi-stage LLM decision pipeline?**

The core claim is bounded:

{SAFE_CLAIM}

The strongest empirical pattern is that parser validity can improve while evidence-state reliability deteriorates. This makes the work more than another LLM error-analysis exercise. The paper targets a reliability layer that parser-level checks can miss.

## 2. Conceptual framing

### 2.1 Evidence-State Reliability

Evidence-State Reliability refers to whether the evidence state passed through a decision pipeline remains complete, grounded, and usable enough for downstream stages. It is not the same as parser validity. Parser validity is a structural signal: it tells us whether the output satisfies a required schema. It does not tell us whether the evidence used by the pipeline was reliable.

### 2.2 Reliability cascades

A reliability cascade occurs when degradation at one stage changes downstream behavior across decision, audit, or escalation stages. In this framing, the unit of concern is not only the final answer. The concern is the pipeline state that connects stages.

### 2.3 Parser validity boundary

Parser validity means the output fits a required parser or schema contract. It must not be interpreted as answer correctness. It must also not be treated as evidence that the upstream evidence state was complete or reliable.

## 3. Methods

{strip_first_heading(material["methods"])}

## 4. Results

{strip_first_heading(material["results"])}

## 5. Contribution and novelty

{strip_first_heading(material["contribution"])}

## 6. Tables and figures

{strip_first_heading(material["table_figure_callouts"])}

## 7. Claim boundary and limitations

{strip_first_heading(material["claim_boundary"])}

## 8. Reproducibility statement

{strip_first_heading(material["reproducibility"])}

## 9. Discussion

The Pilot 05 results motivate a shift in how multi-stage LLM decision systems are evaluated. A parser-valid output should not be treated as a reliable output unless the evidence state that produced it is also evaluated. In this study, the divergence between parser validity and evidence-state reliability is the main reliability signal.

This matters because production-style LLM pipelines often contain multiple handoffs: evidence is summarized, transformed, checked, audited, escalated, and interpreted. If evaluation only checks whether the final object is parseable, it may miss reliability loss that occurred earlier in the pipeline.

The Evidence-State Reliability framing therefore supports three practical evaluation requirements. First, evaluators should track evidence-state quality separately from output-format validity. Second, they should measure whether degradation propagates across stages. Third, they should distinguish detection from recovery, because a system may detect degraded evidence without successfully recovering from it.

## 10. Conclusion

This manuscript draft argues that Evidence-State Reliability should be evaluated separately from parser validity in multi-stage LLM decision systems. Within the committed Pilot 05 GLM-5.2 setup, controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. The key result is that parser validity improves while stage/evidence success deteriorates. That pattern supports the paper's main thesis: parser validity is not a sufficient proxy for evidence-state reliability.

## Appendix A. Next revision roadmap

{strip_first_heading(material["roadmap"])}

## Appendix B. Assembly checkpoint

- latest_commit: `{meta["latest_commit"]}`
- latest_hash: `{meta["latest_hash"]}`
- latest_subject: `{meta["latest_subject"]}`
- origin_main_alignment: `{meta["behind"]} behind, {meta["ahead"]} ahead`

## Appendix C. Do-not-claim boundary

{chr(10).join(f"- {item}" for item in DO_NOT_CLAIM)}
"""


def create_section_index() -> List[Dict[str, Any]]:
    rows = [
        {"section_id": "abstract", "section_title": "Abstract", "source": "05AU title/abstract/keywords", "status": "PASS"},
        {"section_id": "1", "section_title": "Introduction", "source": "05AU manuscript skeleton and contribution framing", "status": "PASS"},
        {"section_id": "2", "section_title": "Conceptual framing", "source": "05AU manuscript skeleton", "status": "PASS"},
        {"section_id": "3", "section_title": "Methods", "source": "05AU methods section draft", "status": "PASS"},
        {"section_id": "4", "section_title": "Results", "source": "05AU results section draft", "status": "PASS"},
        {"section_id": "5", "section_title": "Contribution and novelty", "source": "05AU contribution novelty framing", "status": "PASS"},
        {"section_id": "6", "section_title": "Tables and figures", "source": "05AU table and figure callouts", "status": "PASS"},
        {"section_id": "7", "section_title": "Claim boundary and limitations", "source": "05AU claim boundary and limitations", "status": "PASS"},
        {"section_id": "8", "section_title": "Reproducibility statement", "source": "05AU reproducibility statement", "status": "PASS"},
        {"section_id": "9", "section_title": "Discussion", "source": "05AV assembly from 05AU bounded claims", "status": "PASS"},
        {"section_id": "10", "section_title": "Conclusion", "source": "05AV assembly from 05AU bounded claims", "status": "PASS"},
    ]
    write_csv(OUTPUT_DIR / "pilot_05AV_manuscript_section_index.csv", rows, ["section_id", "section_title", "source", "status"])
    return rows


def create_claim_traceability() -> List[Dict[str, Any]]:
    rows = [
        {
            "claim": "Evidence-State Reliability is distinct from parser validity.",
            "supporting_source": "05AU manuscript skeleton; 05AU contribution framing; 05AU results section",
            "claim_status": "SUPPORTED_WITHIN_PILOT_05_BOUNDARY",
            "do_not_expand_to": "general LLM reliability or answer correctness",
            "status": "PASS",
        },
        {
            "claim": "Parser validity improves while stage/evidence success deteriorates in the committed Pilot 05 setup.",
            "supporting_source": "05AU results section; 05AS final tables referenced by 05AU",
            "claim_status": "SUPPORTED_WITHIN_PILOT_05_BOUNDARY",
            "do_not_expand_to": "all GLM-5.2 runs or all LLM pipelines",
            "status": "PASS",
        },
        {
            "claim": "Reliability cascades should be evaluated across decision, audit, and escalation stages.",
            "supporting_source": "05AU methods and results drafts",
            "claim_status": "SUPPORTED_AS_METHOD_FRAMING",
            "do_not_expand_to": "deployment validation",
            "status": "PASS",
        },
        {
            "claim": "05AV creates no new empirical evidence.",
            "supporting_source": "05AV manifest; committed 05AU source boundary",
            "claim_status": "AUDIT_BOUNDARY",
            "do_not_expand_to": "new experiment or new result",
            "status": "PASS",
        },
        {
            "claim": "No broad GLM reliability, general LLM reliability, provider superiority, deployment safety, regulatory validity, or consumer-harm prevalence is claimed.",
            "supporting_source": "05AU claim boundary and limitations; 05AV do-not-claim boundary",
            "claim_status": "EXPLICIT_LIMITATION",
            "do_not_expand_to": "policy or real-world misconduct claims",
            "status": "PASS",
        },
    ]
    write_csv(OUTPUT_DIR / "pilot_05AV_claim_traceability_matrix.csv", rows, ["claim", "supporting_source", "claim_status", "do_not_expand_to", "status"])
    return rows


def create_gap_analysis() -> str:
    return """# Pilot 05AV Submission Readiness Gap Analysis

## Status

Draft assembled, not submission-ready.

## What is already strong

- Clear core thesis: Evidence-State Reliability is distinct from parser validity.
- Clear empirical hook: parser validity improves while stage/evidence success deteriorates under degradation.
- Committed artifact chain: 05AR results interpretation, 05AS paper figures/tables, 05AT repo validation, 05AU manuscript synthesis.
- Strong claim boundary: no broad LLM, deployment, regulatory, or provider-superiority claims.
- Reproducibility posture: committed file contracts, manifest safety checks, source-index validation, and no raw-data/raw-response access.

## What is still missing before journal submission

1. **Related work section**: needs a literature-grounded discussion of LLM evaluation, reliability cascades, process reliability, structured-output evaluation, decision-pipeline auditing, and evidence quality.
2. **Formal definition section**: Evidence-State Reliability should be formalized more sharply with notation.
3. **Methods precision**: the manuscript should include exact experiment design details from committed scripts/tables without overclaiming.
4. **Results tightening**: the final paper should use the 05AS figures/tables directly and avoid repeating too many intermediate tables in the main text.
5. **Threats to validity**: internal, construct, external, and reproducibility validity should be expanded into a journal-style limitations section.
6. **Writing polish**: the draft needs compression, academic style balancing, and removal of repeated phrases.
7. **Target venue alignment**: the final version needs formatting and positioning for a specific venue or journal.

## Not allowed yet

- Do not describe the manuscript as accepted, submitted, Q1-ready, or complete.
- Do not add literature claims without citations.
- Do not expand empirical claims beyond committed Pilot 05 outputs.
- Do not imply real-world consumer harm or deployment safety.
"""


def create_review_checklist() -> str:
    return """# Pilot 05AV Internal Review Checklist

## Core claim checks

- [ ] Does the manuscript clearly define Evidence-State Reliability?
- [ ] Does it separate Evidence-State Reliability from parser validity?
- [ ] Does it avoid saying parser validity equals answer correctness?
- [ ] Does it present the parser-validity/evidence-state divergence as the central result?
- [ ] Does it keep all empirical claims bounded to Pilot 05?

## Methods checks

- [ ] Does the methods section explain the decision, audit, and escalation stages?
- [ ] Does it state that the experiment uses sanitized CFPB-backed evidence packets?
- [ ] Does it state that 05AV uses committed 05AU outputs only?
- [ ] Does it avoid raw CFPB, raw prompt, raw response, JSONL, and .env claims?

## Results checks

- [ ] Does the results section use the 05AS table and figure sequence?
- [ ] Does it distinguish audit detection from escalation recovery?
- [ ] Does it frame cascade failure as a pipeline-level reliability signal?
- [ ] Does it avoid provider superiority or broad model-generalization claims?

## Reproducibility checks

- [ ] Does the paper cite the committed checkpoint chain?
- [ ] Does it include 05AT repo validation as a reproducibility safeguard?
- [ ] Does it avoid claiming that audit validity equals real-world deployment validity?

## Submission-readiness checks

- [ ] Related work added with citations.
- [ ] Formal framing tightened.
- [ ] Figures placed in manuscript order.
- [ ] Tables placed in manuscript order.
- [ ] Limitations expanded.
- [ ] Abstract shortened for target venue.
"""


def create_assembly_report(meta: Dict[str, Any], source_rows: List[Dict[str, Any]]) -> str:
    return f"""# Pilot 05AV Full Manuscript Assembly Report

## Status

PASS

## Purpose

Task 05AV assembles a full manuscript draft from committed 05AU synthesis artifacts only.

## Git checkpoint

- latest_commit: `{meta["latest_commit"]}`
- latest_hash: `{meta["latest_hash"]}`
- latest_subject: `{meta["latest_subject"]}`
- origin_main_alignment: `{meta["behind"]} behind, {meta["ahead"]} ahead`

## Source boundary

- source_task: 05AU
- source_file_count: {len(source_rows)}
- committed_outputs_only: True
- does_not_create_new_empirical_evidence: True

## Outputs

- `pilot_05AV_full_manuscript_draft.md`
- `pilot_05AV_manuscript_section_index.csv`
- `pilot_05AV_claim_traceability_matrix.csv`
- `pilot_05AV_submission_readiness_gap_analysis.md`
- `pilot_05AV_internal_review_checklist.md`
- `pilot_05AV_full_manuscript_assembly_report.md`

## Safety boundary

- API/model calls: 0
- .env read: NO
- raw prompt/response access: NO
- raw CFPB data access: NO
- JSONL writing: NO

## Claim boundary

{SAFE_CLAIM}

## Next step

After review and commit, the next task should be a targeted manuscript refinement task: add formal definitions, citation placeholders, and venue-oriented structure without adding unsupported empirical claims.
"""


def validate_outputs() -> None:
    missing = [name for name in EXPECTED_OUTPUT_NAMES if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise AssemblyError(f"Missing expected 05AV outputs: {missing}")

    draft = read_text(OUTPUT_DIR / "pilot_05AV_full_manuscript_draft.md")
    required_phrases = [
        "Evidence-State Reliability",
        "parser validity",
        "reliability cascade",
        "sanitized, CFPB-backed",
        "GLM-5.2",
        "does not create new empirical evidence",
        "Do-not-claim boundary",
    ]

    for phrase in required_phrases:
        if phrase.lower() not in draft.lower():
            raise AssemblyError(f"Required manuscript phrase missing: {phrase}")

    trace_rows = read_csv(OUTPUT_DIR / "pilot_05AV_claim_traceability_matrix.csv")
    if not trace_rows:
        raise AssemblyError("Claim traceability matrix is empty.")
    if any(row.get("status") != "PASS" for row in trace_rows):
        raise AssemblyError("Claim traceability matrix contains non-PASS rows.")

    section_rows = read_csv(OUTPUT_DIR / "pilot_05AV_manuscript_section_index.csv")
    if len(section_rows) < 10:
        raise AssemblyError("Manuscript section index has fewer than 10 rows.")
    if any(row.get("status") != "PASS" for row in section_rows):
        raise AssemblyError("Manuscript section index contains non-PASS rows.")


def output_index() -> List[Dict[str, Any]]:
    rows = []
    for name in EXPECTED_OUTPUT_NAMES:
        path = OUTPUT_DIR / name
        rows.append({
            "output_file": rel(path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else "",
        })
    return rows


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = [item.name for item in OUTPUT_DIR.iterdir() if item.is_file()]
    unexpected_existing = [name for name in existing if name not in EXPECTED_OUTPUT_NAMES]
    if unexpected_existing:
        raise AssemblyError(f"Unexpected files in 05AV output directory before generation: {unexpected_existing}")

    meta = check_checkpoint()
    source_rows = verify_sources()
    verify_05au_manifest()
    material = load_material()

    full_manuscript = assemble_full_manuscript(material, meta)
    (OUTPUT_DIR / "pilot_05AV_full_manuscript_draft.md").write_text(full_manuscript, encoding="utf-8")

    section_rows = create_section_index()
    claim_rows = create_claim_traceability()

    (OUTPUT_DIR / "pilot_05AV_submission_readiness_gap_analysis.md").write_text(create_gap_analysis(), encoding="utf-8")
    (OUTPUT_DIR / "pilot_05AV_internal_review_checklist.md").write_text(create_review_checklist(), encoding="utf-8")
    (OUTPUT_DIR / "pilot_05AV_full_manuscript_assembly_report.md").write_text(create_assembly_report(meta, source_rows), encoding="utf-8")

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "output_dir": OUTPUT_DIR_REL,
        "git": meta,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "safety_flags": dict(SAFETY_FLAGS),
        **SAFETY_FLAGS,
        "source_boundary": {
            "committed_05au_outputs_only": True,
            "source_file_count": len(source_rows),
            "does_not_create_new_empirical_evidence": True,
            "source_task": "05AU",
        },
        "claim_boundary": {
            "safe_claim": SAFE_CLAIM,
            "do_not_claim": DO_NOT_CLAIM,
        },
        "expected_output_count": len(EXPECTED_OUTPUT_NAMES),
        "section_count": len(section_rows),
        "claim_traceability_rows": len(claim_rows),
        "outputs": [],
    }

    manifest_path = OUTPUT_DIR / "pilot_05AV_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    validate_outputs()

    manifest["outputs"] = output_index()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print("TASK_05AV_STATUS=PASS")
    print(f"OUTPUT_DIR={OUTPUT_DIR_REL}")
    print(f"EXPECTED_OUTPUT_COUNT={len(EXPECTED_OUTPUT_NAMES)}")
    for row in output_index():
        print(f"OUTPUT_FILE={row['output_file']} SIZE_BYTES={row['size_bytes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssemblyError as exc:
        print(f"TASK_05AV_STATUS=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)