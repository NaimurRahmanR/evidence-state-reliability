from __future__ import annotations

import csv
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_ID = "05AT"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_REL = "experiments/pilot_05_repo_validation_reproducibility_audit.py"
OUTPUT_DIR_REL = "reports/pilot_05_repo_validation_reproducibility_audit"
OUTPUT_DIR = REPO_ROOT / OUTPUT_DIR_REL

EXPECTED_OUTPUT_NAMES = [
    "pilot_05AT_manifest.json",
    "pilot_05AT_repo_checkpoint_audit.csv",
    "pilot_05AT_committed_file_contract_audit.csv",
    "pilot_05AT_manifest_safety_audit.csv",
    "pilot_05AT_operation_aware_script_safety_scan.csv",
    "pilot_05AT_forbidden_file_audit.csv",
    "pilot_05AT_figure_integrity_audit.csv",
    "pilot_05AT_input_index_validation.csv",
    "pilot_05AT_reproducibility_claim_boundary_audit.csv",
    "pilot_05AT_repo_validation_reproducibility_report.md",
]

EXPECTED_OUTPUTS = [f"{OUTPUT_DIR_REL}/{name}" for name in EXPECTED_OUTPUT_NAMES]
EXPECTED_UNTRACKED_05AT = {SCRIPT_REL, *EXPECTED_OUTPUTS}

EXPECTED_SCRIPTS = [
    "experiments/pilot_05_cfpb_glm52_scaled_real_execution.py",
    "experiments/pilot_05_cfpb_glm52_scaled_real_execution_integrity.py",
    "experiments/pilot_05_cfpb_glm52_scaled_metrics.py",
    "experiments/pilot_05_cfpb_glm52_scaled_metrics_contract_patch.py",
    "experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py",
    "experiments/pilot_05_cfpb_glm52_paper_figures_tables.py",
]

EXPECTED_05AR_OUTPUTS = [
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_headline_empirical_findings.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_ready_main_results_table.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_parser_vs_evidence_state_divergence.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_audit_escalation_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_cascade_failure_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_failure_family_interpretation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_claim_boundary_table.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_limitations_and_validity_threats.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_figure_specifications.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_metric_validation.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_sanitized_input_file_index.csv",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_paper_results_section_outline.md",
    "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_report.md",
]

EXPECTED_05AS_OUTPUTS = [
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_manifest.json",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_input_file_index.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_final_main_results_table.tex",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_parser_vs_evidence_state_divergence_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_audit_escalation_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_cascade_failure_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_failure_family_figure_data.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_claim_boundary_table_final.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_limitations_and_validity_threats_final.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_metric_validation_summary.csv",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_caption_pack.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_table_pack.md",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_assets_report.md",
]

EXPECTED_05AS_FIGURES = [
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png",
    "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_04_failure_family_interpretation.png",
]

MANIFEST_PATHS = [
    ("05AR", "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json"),
    ("05AS", "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_manifest.json"),
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

SAFE_TRACKED_SPECIAL_FILES = {
    ".env.example",
    "data/raw/cfpb_complaints/.gitignore",
    "data/raw/cfpb_complaints/README.md",
    "data/raw/hmda/.gitignore",
    "data/raw/hmda/README.md",
}

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


class AuditError(RuntimeError):
    pass


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def run_git(args: List[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


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


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows_to_markdown(rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> str:
    if not rows:
        return "_No rows._\n"

    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

    def fmt(value: Any) -> str:
        return ("" if value is None else str(value)).replace("\n", " ").replace("|", "\\|")

    lines = [
        "| " + " | ".join(fieldnames) + " |",
        "| " + " | ".join(["---"] * len(fieldnames)) + " |",
    ]

    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(col, "")) for col in fieldnames) + " |")

    return "\n".join(lines) + "\n"


def git_tracked(path: str) -> bool:
    return bool(run_git(["ls-files", "--", path]).strip())


def is_png(path: Path) -> bool:
    if not path.is_file():
        return False
    data = path.read_bytes()
    return len(data) > 8 and data[:4] == b"\x89PNG"


def is_forbidden_path(path: str) -> bool:
    p = normalize(path)
    low = p.lower()

    return (
        p.startswith("data/raw/")
        or p.endswith(".jsonl")
        or p == ".env"
        or p.startswith(".env.")
        or "/.env" in p
        or ".env." in p
        or "secret" in low
        or "api_key" in low
        or "api-key" in low
        or "raw_prompt" in low
        or "raw_response" in low
    )


def classify_code_line(line: str) -> str:
    text = line.strip()

    if not text:
        return "BENIGN_EMPTY"

    if text.startswith("#"):
        return "BENIGN_COMMENT"

    benign_fragments = [
        "FORBIDDEN_EXTENSIONS",
        "FORBIDDEN_NAME_FRAGMENTS",
        "RequiredSafetyFlags",
        "SAFETY_FLAGS",
        "safety_flags",
        "no_api_calls",
        "no_model_calls",
        "no_env_read",
        "no_raw_prompt_response_access",
        "no_jsonl_written",
        "no_raw_cfpb_data_touched",
        "DO_NOT_CLAIM",
        "SAFE_BOUNDED_CLAIM",
        "claim_boundary",
        "Not claimed",
        "Raw prompt/response inspection: NO",
        "Raw CFPB data access: NO",
        "JSONL writing: NO",
        "env_read: NO",
        "api_or_model_calls: 0",
        "raw_prompt_response_access: NO",
        "raw_cfpb_data_access: NO",
    ]

    for fragment in benign_fragments:
        if fragment in text:
            return "BENIGN_GUARDRAIL_OR_CLAIM_BOUNDARY_TEXT"

    risk_fragments = [
        ("actual_env_access", ["os.environ", "os.getenv", "load_dotenv", "dotenv_values"]),
        ("actual_api_client_call", ["client.chat", "chat.completions", "responses.create", "requests.post", "requests.get", "httpx.", "urllib.request", "anthropic.", "openai."]),
    ]

    for name, fragments in risk_fragments:
        if any(fragment in text for fragment in fragments):
            return f"RISK:{name}"

    low = text.lower()
    rw_ops = ["open(", "read_text(", "read_bytes(", "write_text(", "write_bytes(", "import-csv", "get-content", "jsonlines.open"]

    if ".env" in low and any(op in low for op in rw_ops):
        return "RISK:actual_env_file_read_or_write"
    if ".jsonl" in low and any(op in low for op in rw_ops):
        return "RISK:actual_jsonl_read_or_write"
    if ("raw_prompt" in low or "raw_response" in low or "prompt_response" in low) and any(op in low for op in rw_ops):
        return "RISK:actual_raw_prompt_response_read_or_write"
    if ("data/raw" in low or "data\\raw" in low) and any(op in low for op in rw_ops):
        return "RISK:actual_raw_data_read_or_write"

    return "BENIGN_NO_RISK_OPERATION"


def audit_checkpoint() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    branch = run_git(["branch", "--show-current"])
    latest_commit = run_git(["log", "-1", "--pretty=format:%h %s"])
    latest_hash = run_git(["rev-parse", "--short", "HEAD"])
    latest_subject = run_git(["log", "-1", "--pretty=format:%s"])
    ahead_behind = run_git(["rev-list", "--left-right", "--count", "origin/main...main"])

    staged = [normalize(x) for x in run_git(["diff", "--cached", "--name-only"]).splitlines() if x.strip()]
    modified_tracked = [normalize(x) for x in run_git(["diff", "--name-only"]).splitlines() if x.strip()]
    untracked = [normalize(x) for x in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if x.strip()]

    unexpected_untracked = [p for p in untracked if p not in EXPECTED_UNTRACKED_05AT]

    parts = ahead_behind.split()
    behind = int(parts[0]) if len(parts) == 2 else -1
    ahead = int(parts[1]) if len(parts) == 2 else -1

    rows = [
        {"check": "branch_is_main", "observed": branch, "status": "PASS" if branch == "main" else "FAIL"},
        {"check": "latest_hash_is_05AS", "observed": latest_hash, "status": "PASS" if latest_hash == "b1c95da" else "FAIL"},
        {"check": "latest_subject_is_05AS", "observed": latest_subject, "status": "PASS" if latest_subject == "Add Pilot 05 paper figures and final tables" else "FAIL"},
        {"check": "origin_main_alignment", "observed": ahead_behind, "status": "PASS" if behind == 0 and ahead == 0 else "FAIL"},
        {"check": "no_staged_files", "observed": "NONE" if not staged else ";".join(staged), "status": "PASS" if not staged else "FAIL"},
        {"check": "no_modified_tracked_files", "observed": "NONE" if not modified_tracked else ";".join(modified_tracked), "status": "PASS" if not modified_tracked else "FAIL"},
        {"check": "only_expected_untracked_05AT_files", "observed": f"untracked={len(untracked)} unexpected={len(unexpected_untracked)}", "status": "PASS" if not unexpected_untracked else "FAIL"},
    ]

    meta = {
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

    write_csv(OUTPUT_DIR / "pilot_05AT_repo_checkpoint_audit.csv", rows, ["check", "observed", "status"])
    return rows, meta


def audit_committed_file_contract() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    groups = [
        ("pilot05_script", EXPECTED_SCRIPTS),
        ("05AR_output", EXPECTED_05AR_OUTPUTS),
        ("05AS_output", EXPECTED_05AS_OUTPUTS),
    ]

    for group, paths in groups:
        for path in paths:
            full = REPO_ROOT / path
            exists = full.is_file()
            tracked = git_tracked(path)
            size = full.stat().st_size if exists else ""
            rows.append({
                "group": group,
                "path": path,
                "exists": exists,
                "tracked": tracked,
                "size_bytes": size,
                "status": "PASS" if exists and tracked else "FAIL",
            })

    bak_rel = "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_scaled_results_interpretation_manifest.json.bak"
    bak_path = REPO_ROOT / bak_rel
    rows.append({
        "group": "cleanup_absence",
        "path": bak_rel,
        "exists": bak_path.is_file(),
        "tracked": git_tracked(bak_rel),
        "size_bytes": bak_path.stat().st_size if bak_path.is_file() else "",
        "status": "PASS" if not bak_path.exists() and not git_tracked(bak_rel) else "FAIL",
    })

    write_csv(OUTPUT_DIR / "pilot_05AT_committed_file_contract_audit.csv", rows, ["group", "path", "exists", "tracked", "size_bytes", "status"])
    return rows


def audit_manifest_safety() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for label, path in MANIFEST_PATHS:
        manifest = read_json(REPO_ROOT / path)
        rows.append({
            "manifest": label,
            "field": "status",
            "value": manifest.get("status"),
            "status": "PASS" if manifest.get("status") == "PASS" else "FAIL",
        })

        for flag in REQUIRED_SAFETY_FLAGS:
            value = manifest.get(flag)
            if value is None and isinstance(manifest.get("safety_flags"), dict):
                value = manifest["safety_flags"].get(flag)

            rows.append({
                "manifest": label,
                "field": flag,
                "value": value,
                "status": "PASS" if value is True else "FAIL",
            })

        if label == "05AS":
            rows.append({
                "manifest": label,
                "field": "expected_output_count",
                "value": manifest.get("expected_output_count"),
                "status": "PASS" if manifest.get("expected_output_count") == 19 else "FAIL",
            })

    write_csv(OUTPUT_DIR / "pilot_05AT_manifest_safety_audit.csv", rows, ["manifest", "field", "value", "status"])
    return rows


def audit_operation_aware_script_scan() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    scripts = [
        "experiments/pilot_05_cfpb_glm52_scaled_results_interpretation.py",
        "experiments/pilot_05_cfpb_glm52_paper_figures_tables.py",
    ]

    relevant_fragments = [
        "env",
        "jsonl",
        "raw_prompt",
        "raw_response",
        "prompt_response",
        "data/raw",
        "data\\raw",
        "openai",
        "anthropic",
        "requests.",
        "httpx.",
        "client.chat",
        "responses.create",
    ]

    for script in scripts:
        lines = (REPO_ROOT / script).read_text(encoding="utf-8-sig").splitlines()
        for idx, line in enumerate(lines, start=1):
            if not any(fragment in line for fragment in relevant_fragments):
                continue

            classification = classify_code_line(line)
            is_risk = classification.startswith("RISK:")
            rows.append({
                "script": script,
                "line_number": idx,
                "classification": classification,
                "is_actual_risk": is_risk,
                "line_excerpt": line.strip()[:220],
                "status": "FAIL" if is_risk else "PASS",
            })

    write_csv(
        OUTPUT_DIR / "pilot_05AT_operation_aware_script_safety_scan.csv",
        rows,
        ["script", "line_number", "classification", "is_actual_risk", "line_excerpt", "status"],
    )
    return rows


def audit_forbidden_files() -> List[Dict[str, Any]]:
    tracked = [normalize(x) for x in run_git(["ls-files"]).splitlines() if x.strip()]
    untracked = [normalize(x) for x in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines() if x.strip()]

    rows: List[Dict[str, Any]] = []

    for kind, paths in [("tracked", tracked), ("untracked", untracked)]:
        for path in paths:
            if kind == "untracked" and path in EXPECTED_UNTRACKED_05AT:
                rows.append({
                    "kind": kind,
                    "path": path,
                    "safe_special_exception": True,
                    "forbidden": False,
                    "status": "PASS",
                })
                continue

            safe_special = path in SAFE_TRACKED_SPECIAL_FILES
            forbidden = is_forbidden_path(path) and not safe_special
            if forbidden or safe_special:
                rows.append({
                    "kind": kind,
                    "path": path,
                    "safe_special_exception": safe_special,
                    "forbidden": forbidden,
                    "status": "FAIL" if forbidden else "PASS",
                })

    if not rows:
        rows.append({
            "kind": "repo",
            "path": "NONE",
            "safe_special_exception": False,
            "forbidden": False,
            "status": "PASS",
        })

    write_csv(OUTPUT_DIR / "pilot_05AT_forbidden_file_audit.csv", rows, ["kind", "path", "safe_special_exception", "forbidden", "status"])
    return rows


def audit_figures() -> List[Dict[str, Any]]:
    rows = []

    for path in EXPECTED_05AS_FIGURES:
        full = REPO_ROOT / path
        exists = full.is_file()
        png = is_png(full)
        tracked = git_tracked(path)
        size = full.stat().st_size if exists else ""
        rows.append({
            "figure": path,
            "exists": exists,
            "tracked": tracked,
            "size_bytes": size,
            "is_png": png,
            "status": "PASS" if exists and tracked and png else "FAIL",
        })

    write_csv(OUTPUT_DIR / "pilot_05AT_figure_integrity_audit.csv", rows, ["figure", "exists", "tracked", "size_bytes", "is_png", "status"])
    return rows


def audit_input_index() -> List[Dict[str, Any]]:
    index_path = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_paper_figures_tables" / "pilot_05AS_input_file_index.csv"
    source_rows = read_csv(index_path)
    rows = []

    for row in source_rows:
        input_file = normalize(row.get("input_file", ""))
        full = REPO_ROOT / input_file
        exists = full.is_file()
        tracked = git_tracked(input_file)
        declared_exists = str(row.get("exists", "")).lower() == "true"

        rows.append({
            "input_file": input_file,
            "declared_exists": declared_exists,
            "actual_exists": exists,
            "tracked": tracked,
            "status": "PASS" if declared_exists and exists and tracked else "FAIL",
        })

    write_csv(OUTPUT_DIR / "pilot_05AT_input_index_validation.csv", rows, ["input_file", "declared_exists", "actual_exists", "tracked", "status"])
    return rows


def audit_claim_boundaries() -> List[Dict[str, Any]]:
    paths = [
        "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_assets_report.md",
        "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_caption_pack.md",
        "reports/pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_paper_table_pack.md",
        "reports/pilot_05_cfpb_glm52_scaled_results_interpretation/pilot_05AR_claim_boundary_table.csv",
    ]

    text = "\n".join((REPO_ROOT / path).read_text(encoding="utf-8-sig") for path in paths if (REPO_ROOT / path).is_file())
    low = text.lower()

    checks = [
        ("parser_validity_language_present", "parser" in low and ("validity" in low or "valid" in low)),
        ("evidence_state_language_present", "evidence-state" in low or "evidence state" in low),
        ("cascade_language_present", "cascade" in low),
        ("bounded_claim_language_present", "bounded" in low or "not claimed" in low or "does not create new empirical evidence" in low),
        ("do_not_claim_broad_glm_reliability_present", "broad glm reliability" in low),
        ("do_not_claim_general_llm_reliability_present", "general llm reliability" in low),
        ("do_not_claim_provider_superiority_present", "provider superiority" in low or "model/provider superiority" in low),
        ("do_not_claim_real_world_financial_validity_present", "real-world financial validity" in low),
        ("do_not_claim_deployment_safety_present", "deployment safety" in low),
    ]

    rows = []
    for check, observed in checks:
        rows.append({
            "claim_boundary_check": check,
            "observed": observed,
            "status": "PASS" if observed else "FAIL",
        })

    write_csv(OUTPUT_DIR / "pilot_05AT_reproducibility_claim_boundary_audit.csv", rows, ["claim_boundary_check", "observed", "status"])
    return rows


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


def create_report(sections: Dict[str, List[Dict[str, Any]]], meta: Dict[str, Any]) -> None:
    lines = [
        "# Pilot 05AT Repo-Wide Validation and Reproducibility Audit",
        "",
        "## Status",
        "",
        "PASS",
        "",
        "## Purpose",
        "",
        "Task 05AT records a repo-wide validation checkpoint after 05AR and 05AS were secured. It uses corrected operation-aware validation logic and allows only this task's approved expected untracked script/output files during local artifact generation.",
        "",
        "## Scope",
        "",
        "- No API/model calls.",
        "- No .env reads.",
        "- No raw prompt/response inspection.",
        "- No raw CFPB access.",
        "- No JSONL writing.",
        "- No staging, commit, or push during artifact generation.",
        "",
        "## Git checkpoint",
        "",
        f"- latest_commit: `{meta['latest_commit']}`",
        f"- latest_hash: `{meta['latest_hash']}`",
        f"- latest_subject: `{meta['latest_subject']}`",
        f"- origin_main_alignment: `{meta['behind']} behind, {meta['ahead']} ahead`",
        f"- staged_count: `{meta['staged_count']}`",
        f"- modified_tracked_count: `{meta['modified_tracked_count']}`",
        f"- unexpected_untracked_count: `{meta['unexpected_untracked_count']}`",
        "",
        "## Corrected validator rule",
        "",
        "Generated-task audits must not require a completely clean tree after the approved task script has been created. Instead, they must allow exactly the current task's expected untracked script/output files and fail on staged files, modified tracked files, Git divergence, or unexpected untracked files.",
        "",
        "## Claim boundary",
        "",
        "05AT is a reproducibility and safety audit artifact. It does not create new empirical evidence and does not expand the claim boundary.",
        "",
        "Allowed bounded interpretation: Pilot 05 provides scaled, CFPB-backed, sanitized, real GLM-5.2 evidence that controlled evidence-state degradation produces measurable reliability-layer changes across decision, audit, and escalation stages. In this run, parser validity improved under degraded evidence while stage/evidence success deteriorated, supporting the claim that Evidence-State Reliability is distinct from parser validity.",
        "",
        "Do not claim:",
        "",
    ]

    for item in DO_NOT_CLAIM:
        lines.append(f"- {item}")

    lines.extend(["", "## Audit sections", ""])

    for name, rows in sections.items():
        fail_count = sum(1 for row in rows if str(row.get("status", "")).upper() != "PASS")
        lines.extend([
            f"### {name}",
            "",
            f"- rows: {len(rows)}",
            f"- failed_rows: {fail_count}",
            "",
            rows_to_markdown(rows[:20]),
            "",
        ])

    (OUTPUT_DIR / "pilot_05AT_repo_validation_reproducibility_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = [item.name for item in OUTPUT_DIR.iterdir() if item.is_file()]
    unexpected_existing = [name for name in existing if name not in EXPECTED_OUTPUT_NAMES]
    if unexpected_existing:
        raise AuditError(f"Unexpected files in 05AT output directory before generation: {unexpected_existing}")

    checkpoint_rows, meta = audit_checkpoint()
    file_contract_rows = audit_committed_file_contract()
    manifest_rows = audit_manifest_safety()
    script_scan_rows = audit_operation_aware_script_scan()
    forbidden_file_rows = audit_forbidden_files()
    figure_rows = audit_figures()
    input_index_rows = audit_input_index()
    claim_rows = audit_claim_boundaries()

    sections = {
        "repo_checkpoint_audit": checkpoint_rows,
        "committed_file_contract_audit": file_contract_rows,
        "manifest_safety_audit": manifest_rows,
        "operation_aware_script_safety_scan": script_scan_rows,
        "forbidden_file_audit": forbidden_file_rows,
        "figure_integrity_audit": figure_rows,
        "input_index_validation": input_index_rows,
        "reproducibility_claim_boundary_audit": claim_rows,
    }

    failed_rows = []
    for section, rows in sections.items():
        for row in rows:
            if str(row.get("status", "")).upper() != "PASS":
                failed_rows.append({"section": section, **row})

    if failed_rows:
        raise AuditError(f"05AT audit has failed rows: {failed_rows[:5]}")

    create_report(sections, meta)

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
        "previous_05AT_failure_type": "FALSE_POSITIVE_CLEAN_TREE_CHECK_DURING_APPROVED_ARTIFACT_GENERATION",
        "corrected_validation_logic": {
            "allows_expected_untracked_current_task_files": True,
            "fails_on_unexpected_untracked_files": True,
            "fails_on_staged_files": True,
            "fails_on_modified_tracked_files": True,
            "fails_on_git_divergence": True,
            "operation_aware_script_scan": True,
        },
        "expected_output_count": len(EXPECTED_OUTPUT_NAMES),
        "outputs": output_index(),
        "claim_boundary": {
            "does_not_create_new_empirical_evidence": True,
            "do_not_claim": DO_NOT_CLAIM,
        },
    }

    manifest_path = OUTPUT_DIR / "pilot_05AT_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    manifest["outputs"] = output_index()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    missing = [name for name in EXPECTED_OUTPUT_NAMES if not (OUTPUT_DIR / name).is_file()]
    if missing:
        raise AuditError(f"Missing expected 05AT outputs: {missing}")

    print("TASK_05AT_STATUS=PASS")
    print(f"OUTPUT_DIR={OUTPUT_DIR_REL}")
    print(f"EXPECTED_OUTPUT_COUNT={len(EXPECTED_OUTPUT_NAMES)}")
    for row in output_index():
        print(f"OUTPUT_FILE={row['output_file']} SIZE_BYTES={row['size_bytes']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print(f"TASK_05AT_STATUS=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)