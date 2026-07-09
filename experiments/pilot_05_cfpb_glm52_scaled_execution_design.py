#!/usr/bin/env python3
"""
TASK 05AM: Scaled Pilot 05 Real-Execution Design and Approval Package.

No API/model calls. No .env reads. No raw prompt/response/JSONL writes.
Creates only a 05AM experiment script and sanitized design/approval outputs.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

TASK_ID = "05AM"
EXPECTED_SHORT_HEAD = "a1d18a8"
EXPECTED_HEAD_SUBJECT = "Add Pilot 05 GLM-5.2 results interpretation"
REQUIRED_PRIOR_COMMITS = {
    "05AK": ("f9eb074", "Add Pilot 05 GLM-5.2 reliability cascade metrics"),
    "05AL": ("a1d18a8", "Add Pilot 05 GLM-5.2 results interpretation"),
}
SCRIPT_REL = Path("experiments/pilot_05_cfpb_glm52_scaled_execution_design.py")
OUTPUT_DIR_REL = Path("reports/pilot_05_cfpb_glm52_scaled_execution_design")

OUTPUT_FILES = {
    "manifest": "pilot_05_scaled_execution_design_manifest.json",
    "run_options": "pilot_05_scaled_run_options.csv",
    "call_count_cost": "pilot_05_scaled_call_count_and_cost_plan.csv",
    "evidence_conditions": "pilot_05_scaled_evidence_condition_plan.csv",
    "stage_plan": "pilot_05_scaled_stage_plan.csv",
    "safety_contract": "pilot_05_scaled_output_safety_contract.csv",
    "abort_rules": "pilot_05_scaled_abort_rules.csv",
    "expected_metrics": "pilot_05_scaled_expected_metrics.csv",
    "target_claims": "pilot_05_scaled_publication_target_claims.csv",
    "related_work": "pilot_05_scaled_related_work_gap_summary.csv",
    "approval_prompt": "pilot_05_scaled_execution_approval_prompt.md",
    "design_report": "pilot_05_scaled_execution_design_report.md",
}

EVIDENCE_CONDITIONS = ["clean", "compressed_lossy", "partial_dropout", "noisy_conflicting"]
STAGES = ["decision", "audit", "escalation"]

RELATED_WORK_ROWS = [
    {
        "area": "Holistic LLM evaluation beyond accuracy",
        "source": "Liang et al., Holistic Evaluation of Language Models (HELM)",
        "year": "2022",
        "url": "https://arxiv.org/abs/2211.09110",
        "what_existing_work_covers": "Model-level benchmark transparency across multiple scenarios and metrics including accuracy, calibration, robustness, fairness, bias, toxicity, and efficiency.",
        "remaining_gap_for_this_project": "Does not isolate degraded intermediate evidence states inside a staged decision pipeline or measure decision-audit-escalation cascade propagation on paired cases.",
        "translation_into_05am_design": "Keep parser/output validity separate from evidence-state, audit, escalation, and cascade metrics; report condition-stage interactions rather than only final accuracy.",
    },
    {
        "area": "RAG component evaluation and evidence/context quality",
        "source": "Es et al., RAGAS: Automated Evaluation of Retrieval Augmented Generation",
        "year": "2023",
        "url": "https://arxiv.org/abs/2309.15217",
        "what_existing_work_covers": "Reference-free RAG evaluation across retrieval context quality, answer relevancy, and faithfulness dimensions.",
        "remaining_gap_for_this_project": "RAG metrics test context-answer quality but do not directly model how controlled evidence degradation propagates through decision, audit, and escalation stages.",
        "translation_into_05am_design": "Use evidence-condition controls as the independent variable, not retrieval score alone; compute paired clean-vs-degraded deltas across all stages.",
    },
    {
        "area": "Automated RAG evaluation with domain shift",
        "source": "Saad-Falcon et al., ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems",
        "year": "2023",
        "url": "https://arxiv.org/abs/2311.09476",
        "what_existing_work_covers": "Automated assessment of context relevance, answer faithfulness, and answer relevance using lightweight judges and prediction-powered inference.",
        "remaining_gap_for_this_project": "Does not provide a reliability-cascade design for same-case evidence degradation across downstream decision/audit/escalation layers.",
        "translation_into_05am_design": "Use paired base cases and bootstrap uncertainty so the evidence degradation effect is estimable without overclaiming broad deployment validity.",
    },
    {
        "area": "RAG faithfulness and hallucination benchmarking",
        "source": "Tamber et al., Benchmarking LLM Faithfulness in RAG with Evolving Leaderboards / FaithJudge",
        "year": "2025",
        "url": "https://aclanthology.org/2025.emnlp-industry.54/",
        "what_existing_work_covers": "LLM faithfulness measurement for RAG/summarization settings where models can introduce unsupported information or contradictions even when given context.",
        "remaining_gap_for_this_project": "Faithfulness leaderboards do not show whether degraded evidence states create stage-specific audit false assurance or escalation recovery/loss in decision pipelines.",
        "translation_into_05am_design": "Add audit false-assurance rate, audit detection rate, escalation recovery rate, escalation loss rate, and cascade sequence patterns.",
    },
    {
        "area": "LLM agents and multi-turn decision-making",
        "source": "Liu et al., AgentBench: Evaluating LLMs as Agents",
        "year": "2024",
        "url": "https://proceedings.iclr.cc/paper_files/paper/2024/file/e9df36b21ff4ee211a8b71ee8b7e9f57-Paper-Conference.pdf",
        "what_existing_work_covers": "Agent evaluation across interactive environments, multi-turn reasoning, decision-making, and instruction-following failure reasons.",
        "remaining_gap_for_this_project": "Primarily task/agent capability evaluation; not a same-case evidence-state degradation experiment with explicit audit/escalation reliability layers.",
        "translation_into_05am_design": "Treat stages as reliability layers and require each stage output to be scored separately before any cascade-level interpretation.",
    },
    {
        "area": "Agent cascading failures and recovery/debugging",
        "source": "Zhu et al., Where LLM Agents Fail and How They can Learn From Failures / AgentErrorBench",
        "year": "2025",
        "url": "https://arxiv.org/abs/2509.25370",
        "what_existing_work_covers": "Systematic taxonomy of agent failures, annotated failure trajectories, and debugging/recovery in multi-step agent rollouts where root-cause errors can cascade.",
        "remaining_gap_for_this_project": "Targets agent module failures and recovery, not controlled real-data-backed evidence-state degradation before downstream decision-support reasoning.",
        "translation_into_05am_design": "Classify failure families, track cascade sequence patterns, and explicitly distinguish evidence-originated cascades from parser/schema failures.",
    },
    {
        "area": "Fault injection in multi-agent LLM systems",
        "source": "Jia et al., MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems",
        "year": "2026",
        "url": "https://arxiv.org/html/2602.19843v1",
        "what_existing_work_covers": "Fault-injection reliability evaluation for multi-agent LLM systems, including silent fault propagation and defensive responses.",
        "remaining_gap_for_this_project": "Fault injection is close, but the 05AM target is not generic agent fault injection; it is evidence-state degradation in a public-data-backed staged decision pipeline.",
        "translation_into_05am_design": "Keep degradation conditions controlled and paired; measure amplification, recovery, and false assurance across decision/audit/escalation, not only final task outcome.",
    },
    {
        "area": "AI risk management and generative AI governance",
        "source": "NIST AI RMF and Generative AI Profile",
        "year": "2024",
        "url": "https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence",
        "what_existing_work_covers": "Cross-sector risk-management guidance for trustworthy AI and generative AI validation, governance, monitoring, and risk controls.",
        "remaining_gap_for_this_project": "Governance guidance does not itself provide a concrete empirical metric package for evidence-state cascade measurement in LLM decision systems.",
        "translation_into_05am_design": "Produce a claim-boundary table, approval gate, abort rules, and auditable sanitized outputs that can support governance-facing evidence without deployment claims.",
    },
]


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def run_cmd(args: Sequence[str], cwd: Path, check: bool = True) -> str:
    proc = subprocess.run(
        list(args),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip()
        fail(f"command failed: {' '.join(args)}\n{msg}")
    return proc.stdout.strip()


def git(args: Sequence[str], repo: Path, check: bool = True) -> str:
    return run_cmd(["git", *args], cwd=repo, check=check)


def rel_path(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        seen: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.append(key)
        fieldnames = seen
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_porcelain_paths(status: str) -> List[str]:
    paths: List[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        raw = line[3:] if len(line) > 3 else line
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        raw = raw.strip().strip('"').replace("\\", "/")
        paths.append(raw)
    return paths


def validate_initial_repo_state(repo: Path) -> Dict[str, Any]:
    root = Path(git(["rev-parse", "--show-toplevel"], repo)).resolve()
    if root.resolve() != repo.resolve():
        # Running from a subpath is okay only if the supplied repo resolves to the git root.
        fail(f"RepoPath must be the repository root. Supplied {repo}; git root is {root}")

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], repo)
    full_head = git(["rev-parse", "HEAD"], repo)
    short_head = git(["rev-parse", "--short", "HEAD"], repo)
    subject = git(["log", "-1", "--pretty=%s"], repo)
    status_before = git(["status", "--porcelain=v1"], repo)
    staged_before = git(["diff", "--cached", "--name-only"], repo)

    if branch != "main":
        fail(f"Expected branch main, found {branch}")
    if short_head != EXPECTED_SHORT_HEAD:
        fail(f"Expected HEAD {EXPECTED_SHORT_HEAD}, found {short_head}")
    if subject != EXPECTED_HEAD_SUBJECT:
        fail(f"Expected latest commit subject '{EXPECTED_HEAD_SUBJECT}', found '{subject}'")
    if status_before.strip():
        fail("Working tree must be clean before 05AM generation. Current git status:\n" + status_before)
    if staged_before.strip():
        fail("Nothing should be staged before 05AM generation. Staged paths:\n" + staged_before)

    origin_head = git(["rev-parse", "origin/main"], repo)
    if origin_head != full_head:
        fail("main is not aligned with origin/main. HEAD and origin/main differ.")
    ahead_behind = git(["rev-list", "--left-right", "--count", "HEAD...origin/main"], repo)
    if ahead_behind.strip() != "0\t0" and ahead_behind.strip() != "0 0":
        fail(f"Expected HEAD...origin/main ahead/behind 0/0, found {ahead_behind}")

    return {
        "git_root": str(root),
        "branch": branch,
        "full_head": full_head,
        "short_head": short_head,
        "latest_subject": subject,
        "origin_main": origin_head,
        "ahead_behind_HEAD_origin_main": ahead_behind,
        "working_tree_clean_before_task": True,
        "nothing_staged_before_task": True,
    }


def validate_prior_commits_and_outputs(repo: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for label, (commit, expected_subject) in REQUIRED_PRIOR_COMMITS.items():
        exists_proc = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=str(repo))
        if exists_proc.returncode != 0:
            fail(f"Required prior commit missing: {label} {commit}")
        subject = git(["log", "-1", "--pretty=%s", commit], repo)
        if subject != expected_subject:
            fail(f"Required commit {commit} subject mismatch. Expected '{expected_subject}', found '{subject}'")
        files = [line.strip() for line in git(["show", "--name-only", "--format=", commit], repo).splitlines() if line.strip()]
        if not files:
            fail(f"No committed file list found for required commit {label} {commit}")
        missing = [p for p in files if not (repo / p).exists()]
        if missing:
            fail(f"Required committed outputs from {label} missing in working tree: {missing[:10]}")
        result[label] = {
            "commit": commit,
            "subject": subject,
            "committed_file_count": len(files),
            "all_committed_files_exist": True,
        }
    return result


def git_ls_files(repo: Path) -> List[str]:
    out = git(["ls-files"], repo)
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def is_forbidden_read_path(rel: str) -> bool:
    lower = rel.replace("\\", "/").lower()
    forbidden_parts = [
        ".env",
        ".jsonl",
        "data/raw",
        "/raw/",
        "raw_prompt",
        "raw_prompts",
        "raw_response",
        "raw_responses",
        "prompt_instance",
        "prompt_instances",
    ]
    return any(token in lower for token in forbidden_parts)


def read_csv_count_case_ids(path: Path) -> Dict[str, Any]:
    id_priority = [
        "base_case_id",
        "case_id",
        "base_packet_id",
        "packet_id",
        "evidence_packet_id",
        "source_packet_id",
        "complaint_id_hash",
        "row_id_hash",
        "record_id",
    ]
    row_count = 0
    unique_counts: Dict[str, int] = {}
    conditions = set()
    fieldnames: List[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        candidate_cols: List[str] = []
        for col in id_priority:
            if col in fieldnames:
                candidate_cols.append(col)
        for col in fieldnames:
            col_l = col.lower()
            if col not in candidate_cols and ("case" in col_l or "packet" in col_l or "record" in col_l or "hash" in col_l):
                if "condition" not in col_l and "label" not in col_l and "stage" not in col_l:
                    candidate_cols.append(col)
        buckets: Dict[str, set] = {col: set() for col in candidate_cols}
        for row in reader:
            row_count += 1
            for col in candidate_cols:
                val = (row.get(col) or "").strip()
                if val:
                    buckets[col].add(val)
            for cond_col in ("condition", "evidence_condition", "condition_name"):
                val = (row.get(cond_col) or "").strip()
                if val:
                    conditions.add(val)
        unique_counts = {col: len(vals) for col, vals in buckets.items()}
    best_col = ""
    best_count = 0
    for col in id_priority + list(unique_counts.keys()):
        if col in unique_counts and unique_counts[col] > best_count:
            best_col = col
            best_count = unique_counts[col]
    return {
        "row_count": row_count,
        "field_count": len(fieldnames),
        "id_columns_checked": ";".join(unique_counts.keys()),
        "best_id_column": best_col,
        "best_unique_id_count": best_count,
        "condition_values_count": len(conditions),
        "condition_values_detected": ";".join(sorted(list(conditions))[:12]),
    }


def read_json_count_case_ids(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as exc:
        return {"json_read_error": type(exc).__name__, "row_count": 0, "best_unique_id_count": 0}
    rows: List[Dict[str, Any]] = []
    if isinstance(obj, list):
        rows = [x for x in obj if isinstance(x, dict)]
    elif isinstance(obj, dict):
        for key in ("rows", "records", "items", "evidence_packets", "conditions", "data"):
            val = obj.get(key)
            if isinstance(val, list):
                rows = [x for x in val if isinstance(x, dict)]
                break
    if not rows:
        return {"row_count": 0, "field_count": 0, "best_id_column": "", "best_unique_id_count": 0}
    fieldnames = sorted({k for row in rows for k in row.keys()})
    candidate_cols = [c for c in fieldnames if any(token in c.lower() for token in ["case", "packet", "record", "hash"])]
    buckets: Dict[str, set] = {col: set() for col in candidate_cols}
    conditions = set()
    for row in rows:
        for col in candidate_cols:
            val = str(row.get(col) or "").strip()
            if val:
                buckets[col].add(val)
        for cond_col in ("condition", "evidence_condition", "condition_name"):
            val = str(row.get(cond_col) or "").strip()
            if val:
                conditions.add(val)
    unique_counts = {col: len(vals) for col, vals in buckets.items()}
    best_col = ""
    best_count = 0
    for col, count in unique_counts.items():
        if count > best_count:
            best_col = col
            best_count = count
    return {
        "row_count": len(rows),
        "field_count": len(fieldnames),
        "id_columns_checked": ";".join(unique_counts.keys()),
        "best_id_column": best_col,
        "best_unique_id_count": best_count,
        "condition_values_count": len(conditions),
        "condition_values_detected": ";".join(sorted(list(conditions))[:12]),
    }


def inspect_sanitized_evidence_inputs(repo: Path, git_files: List[str]) -> Dict[str, Any]:
    candidate_rows: List[Dict[str, Any]] = []
    for rel in git_files:
        lower = rel.lower()
        suffix = Path(rel).suffix.lower()
        if suffix not in {".csv", ".json"}:
            continue
        if "pilot_05" not in lower:
            continue
        if not any(token in lower for token in ["evidence", "packet", "condition"]):
            continue
        if is_forbidden_read_path(rel):
            continue
        if any(token in lower for token in ["prompt", "response", "execution", "raw", "jsonl"]):
            continue
        path = repo / rel
        if not path.exists():
            continue
        try:
            if suffix == ".csv":
                info = read_csv_count_case_ids(path)
            else:
                info = read_json_count_case_ids(path)
        except Exception as exc:
            info = {"read_error": type(exc).__name__, "row_count": 0, "best_unique_id_count": 0}
        info.update({"path": rel, "suffix": suffix})
        candidate_rows.append(info)

    if not candidate_rows:
        fail("No committed sanitized Pilot 05 evidence/evidence-state CSV or JSON inputs found without touching raw/prompt/response paths.")

    # Prefer evidence-state condition files with 4 detected conditions, then highest unique base count.
    def rank(row: Dict[str, Any]) -> Tuple[int, int, int]:
        lower_path = str(row.get("path", "")).lower()
        cond_bonus = 10 if "evidence_state_conditions" in lower_path or "condition" in lower_path else 0
        four_bonus = 20 if int(row.get("condition_values_count") or 0) >= 4 else 0
        return (four_bonus + cond_bonus, int(row.get("best_unique_id_count") or 0), int(row.get("row_count") or 0))

    best = sorted(candidate_rows, key=rank, reverse=True)[0]
    available_base_cases = int(best.get("best_unique_id_count") or 0)
    if available_base_cases <= 0:
        # Conservative fallback: if a condition file has 240 rows and 4 conditions, infer 60 cases; otherwise no inference.
        row_count = int(best.get("row_count") or 0)
        cond_count = int(best.get("condition_values_count") or 0)
        if row_count > 0 and cond_count >= 4 and row_count % cond_count == 0:
            available_base_cases = row_count // cond_count
            best["base_case_count_inference"] = "row_count_divided_by_condition_count"
        else:
            fail("Could not infer available sanitized base-case count from committed evidence-state inputs.")

    return {
        "candidate_file_count": len(candidate_rows),
        "candidate_files": candidate_rows,
        "selected_count_source": best,
        "available_sanitized_base_cases": available_base_cases,
        "required_minimum_base_cases_for_option_A": 60,
        "sufficient_for_option_A": available_base_cases >= 60,
        "sufficient_for_100_case_options": available_base_cases >= 100,
    }


def inspect_safe_local_cost_metadata(repo: Path, git_files: List[str]) -> Dict[str, Any]:
    # Conservative scan: only read committed non-raw metadata/config/design paths, never .env, raw, prompt, response, JSONL, or data/raw.
    candidate_files: List[str] = []
    for rel in git_files:
        lower = rel.lower()
        suffix = Path(rel).suffix.lower()
        if suffix not in {".py", ".md", ".json", ".csv", ".yml", ".yaml", ".toml", ".txt"}:
            continue
        if is_forbidden_read_path(rel):
            continue
        if "data/raw" in lower or ".env" in lower or lower.endswith(".jsonl"):
            continue
        if not any(token in lower for token in ["glm52", "glm-5.2", "cost", "price", "pricing", "approval", "config", "model"]):
            continue
        if any(token in lower for token in ["raw", "prompt_instances", "raw_response", "raw_prompt"]):
            continue
        candidate_files.append(rel)

    pricing_indicators = 0
    cap_indicators = 0
    model_mentions = 0
    exact_unit_pricing_found = False
    for rel in candidate_files[:200]:
        path = repo / rel
        try:
            # Read only small safe metadata files; no content is printed or exported.
            text = path.read_text(encoding="utf-8", errors="ignore")[:200_000]
        except Exception:
            continue
        lower_text = text.lower()
        if "glm-5.2" in lower_text or "glm52" in lower_text or "glm 5.2" in lower_text:
            model_mentions += 1
        if "cost cap" in lower_text or "approved cost" in lower_text or "budget" in lower_text:
            cap_indicators += 1
        if "price" in lower_text or "pricing" in lower_text or "per million" in lower_text or "per 1m" in lower_text or "per 1,000" in lower_text:
            pricing_indicators += 1
        if re.search(r"(input|output).{0,40}(price|cost).{0,40}(million|1m|1000|1,000|token)", lower_text):
            exact_unit_pricing_found = True

    # Do not compute exact cost even if ambiguous pricing strings exist; require user confirmation unless a future execution script has validated model pricing.
    return {
        "safe_metadata_files_scanned": len(candidate_files[:200]),
        "safe_metadata_files_matching_cost_or_model_terms": len(candidate_files),
        "model_mentions_detected": model_mentions,
        "cost_cap_or_budget_indicators_detected": cap_indicators,
        "pricing_indicators_detected": pricing_indicators,
        "exact_unit_pricing_found_in_safe_metadata": exact_unit_pricing_found,
        "exact_cost_status": "requires_user_confirmation",
        "reason": "05AM does not read .env, raw prompts/responses, JSONL, or provider billing APIs. It therefore reports call counts and cost formulas unless a validated unit price is explicitly approved by the user.",
    }


def build_run_options(available_cases: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    option_defs = [
        ("A", "minimum serious one-model run", 60, 4, 3, 1, "Minimum scaled run; first serious empirical upgrade beyond micro-pilot."),
        ("B", "stronger one-model run", 100, 4, 3, 1, "Stronger one-model precision if 100 sanitized base cases are available and cost is acceptable."),
        ("C", "stronger cross-model run", 60, 4, 3, 2, "Cross-model replication at the 60-case level; stronger generality but double model spend."),
        ("D", "publication-strength cross-model run", 100, 4, 3, 2, "Strongest planned option, but should wait until one-model signal is confirmed and budget is approved."),
    ]
    rows: List[Dict[str, Any]] = []
    for option, label, base_cases, conditions, stages, models, note in option_defs:
        call_count = base_cases * conditions * stages * models
        enough_cases = available_cases >= base_cases
        if option == "A":
            stat = "moderate; supports paired condition deltas and bootstrap intervals at the 60-base-case level"
            pub = "serious first empirical upgrade; enough to decide whether to replicate/scale"
            risk = "controlled"
            recommendation = "RECOMMENDED NEXT RUN" if enough_cases else "NOT CURRENTLY AVAILABLE: insufficient sanitized base cases"
        elif option == "B":
            stat = "stronger one-model precision than A"
            pub = "strong one-model evidence if budget allows"
            risk = "moderate cost/runtime"
            recommendation = "defer until Option A signal is known" if enough_cases else "requires more sanitized base cases"
        elif option == "C":
            stat = "stronger external-model reliability check than A"
            pub = "stronger publication value through cross-model replication"
            risk = "higher cost and model-comparison claim risk"
            recommendation = "defer until Option A passes; use as replication" if enough_cases else "requires more sanitized base cases"
        else:
            stat = "strongest among planned options"
            pub = "highest planned publication value, but expensive and premature before one-model signal"
            risk = "highest cost/runtime and broad-claim risk"
            recommendation = "not recommended as immediate next run" if enough_cases else "requires more sanitized base cases"
        rows.append({
            "option": option,
            "label": label,
            "base_cases": base_cases,
            "available_sanitized_base_cases_detected": available_cases,
            "evidence_conditions": conditions,
            "stages": stages,
            "models": models,
            "call_count": call_count,
            "call_count_formula": f"{base_cases} base cases × {conditions} evidence conditions × {stages} stages × {models} model(s)",
            "exact_cost_status": "requires_user_confirmation",
            "cost_formula": "total_cost = call_count × ((avg_input_tokens_per_call × input_price_per_token) + (avg_output_tokens_per_call × output_price_per_token)); exact GLM-5.2 unit pricing/currency must be confirmed before 05AN",
            "input_output_safety_constraints": "sanitized evidence only; no raw prompts; no raw responses; no JSONL; no .env read during design; execution must parse/store sanitized CSV/JSON/MD only",
            "expected_statistical_strength": stat,
            "expected_publication_value": pub,
            "risk_level": risk,
            "recommendation": recommendation,
            "note": note,
        })

    if available_cases >= 60:
        rec = {
            "recommended_option": "A",
            "recommended_base_cases": 60,
            "recommended_models": 1,
            "recommended_model_name": "GLM-5.2 / glm-5.2, subject to explicit user approval in 05AN",
            "recommended_call_count": 720,
            "recommendation_reason": "Big enough to move beyond the 36-call micro-pilot, still cost-controlled, supports paired clean-vs-degraded comparisons, and avoids premature cross-model spending.",
            "is_finish_line_minimum": True,
        }
    else:
        calls = available_cases * 4 * 3
        rec = {
            "recommended_option": "A-reduced",
            "recommended_base_cases": available_cases,
            "recommended_models": 1,
            "recommended_model_name": "GLM-5.2 / glm-5.2, subject to explicit user approval in 05AN",
            "recommended_call_count": calls,
            "recommendation_reason": "Available sanitized base-case count is below 60, so this is only a reduced preliminary scaled run and does not satisfy the stated finish-line minimum.",
            "is_finish_line_minimum": False,
        }
    return rows, rec


def build_call_count_cost_rows(run_options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for opt in run_options:
        call_count = int(opt["call_count"])
        rows.append({
            "option": opt["option"],
            "call_count": call_count,
            "calculation": opt["call_count_formula"],
            "exact_cost_gbp": "UNKNOWN_REQUIRES_USER_CONFIRMATION",
            "exact_cost_reason": "No provider billing/API call and no .env read are allowed in 05AM; exact unit pricing must be approved/confirmed before 05AN.",
            "cost_formula_per_call": "avg_input_tokens*input_price_per_token + avg_output_tokens*output_price_per_token",
            "cost_formula_total": "call_count * cost_formula_per_call",
            "recommended_cost_cap_rule_for_05AN": "User must approve a hard GBP cap before execution; runner must stop before exceeding approved cap.",
            "minimum_runtime_accounting_required": "persist sanitized call ledger with planned_call_id, stage, condition, base_case_id_hash, model, parser_status, usage tokens if available, and cost estimate if approved",
        })
    return rows


def build_evidence_condition_rows() -> List[Dict[str, Any]]:
    return [
        {
            "condition": "clean",
            "role_in_design": "baseline evidence state",
            "paired_comparison": "reference condition for all degraded deltas",
            "controlled_degradation": "none beyond existing sanitization",
            "expected_failure_signal": "should produce the highest stage/cascade reliability if the evidence-state hypothesis holds",
            "safety_note": "sanitized evidence only; no target labels inserted into evidence text",
        },
        {
            "condition": "compressed_lossy",
            "role_in_design": "tests summary compression / information loss",
            "paired_comparison": "clean vs compressed_lossy for same base case and stage",
            "controlled_degradation": "reduce detail, preserve broad issue category, remove supporting facts",
            "expected_failure_signal": "loss of nuance may increase incorrect decisions or weak audit justification while remaining parser-valid",
            "safety_note": "do not create raw narrative reconstruction; only use committed sanitized fields",
        },
        {
            "condition": "partial_dropout",
            "role_in_design": "tests missing evidence / incomplete context",
            "paired_comparison": "clean vs partial_dropout for same base case and stage",
            "controlled_degradation": "drop selected sanitized evidence fields or evidence fragments deterministically",
            "expected_failure_signal": "audit should detect insufficiency; false assurance is a key failure if it does not",
            "safety_note": "dropout should not reveal raw CFPB fields or target labels",
        },
        {
            "condition": "noisy_conflicting",
            "role_in_design": "tests conflict/noise sensitivity and downstream amplification",
            "paired_comparison": "clean vs noisy_conflicting for same base case and stage",
            "controlled_degradation": "inject controlled sanitized contradiction/noise markers created by existing evidence-state condition workflow",
            "expected_failure_signal": "decision errors, audit misses, or escalation loss can show reliability cascade behavior",
            "safety_note": "noise must be synthetic/sanitized and must not imply real company misconduct or real consumer harm prevalence",
        },
    ]


def build_stage_rows() -> List[Dict[str, Any]]:
    return [
        {
            "stage": "decision",
            "stage_question": "Can the model produce a valid controlled decision-support classification from the current evidence state?",
            "input_dependency": "single sanitized evidence-state row",
            "primary_outputs": "structured decision, confidence/uncertainty band if supported, evidence-use flags, parser status",
            "reliability_layer": "decision reliability and evidence degradation sensitivity",
            "failure_modes_to_track": "parser invalidity; unsupported decision; overconfident decision under degraded evidence; missing-insufficient-evidence recognition",
        },
        {
            "stage": "audit",
            "stage_question": "Can the model audit the decision/evidence relationship and detect degradation or insufficiency?",
            "input_dependency": "sanitized evidence state plus sanitized decision-stage output only",
            "primary_outputs": "audit verdict, detection flag, false-assurance flag, issue family, parser status",
            "reliability_layer": "audit reliability",
            "failure_modes_to_track": "audit false assurance; missed degradation; unsupported audit approval; parser invalidity",
        },
        {
            "stage": "escalation",
            "stage_question": "Can the model recover by escalating uncertain/degraded cases or does it lose/reinforce the cascade?",
            "input_dependency": "sanitized evidence state plus sanitized decision/audit outputs only",
            "primary_outputs": "escalation action, recovery/loss flag, final controlled recommendation, parser status",
            "reliability_layer": "escalation reliability and cascade reliability",
            "failure_modes_to_track": "failed escalation; escalation loss; unjustified closure; recovery under degraded evidence; parser invalidity",
        },
    ]


def build_safety_contract_rows() -> List[Dict[str, Any]]:
    return [
        {"rule_id": "S01", "contract_area": "API execution", "requirement": "05AM makes zero API/model calls. 05AN may call GLM-5.2 only after explicit user approval.", "validation": "manifest flags real_api_calls=0 and model_calls=0 for 05AM"},
        {"rule_id": "S02", "contract_area": "secrets", "requirement": "05AM must not read or write .env and must not print API keys.", "validation": "script contains no dotenv/env-file read; .env path is excluded from safe metadata scan"},
        {"rule_id": "S03", "contract_area": "raw data", "requirement": "Do not touch data/raw or raw CFPB browser export.", "validation": "script uses git metadata and committed sanitized evidence candidates only; data/raw paths are excluded"},
        {"rule_id": "S04", "contract_area": "raw prompts", "requirement": "Do not write raw prompt instances.", "validation": "05AM writes design tables only; output safety scan forbids prompt-instance artifacts"},
        {"rule_id": "S05", "contract_area": "raw responses", "requirement": "Do not write raw model responses.", "validation": "05AM writes no model outputs and no response dumps"},
        {"rule_id": "S06", "contract_area": "JSONL", "requirement": "Do not create JSONL files.", "validation": "post-generation file scan fails if any 05AM .jsonl exists"},
        {"rule_id": "S07", "contract_area": "sanitized outputs", "requirement": "Commit only sanitized CSV/JSON/MD design artifacts after validation and user approval.", "validation": "created extensions limited to .py/.csv/.json/.md in 05AM paths"},
        {"rule_id": "S08", "contract_area": "claims", "requirement": "Do not claim broad LLM/model, financial, legal, or deployment validity.", "validation": "publication target claims table separates allowed, conditional, and forbidden claims"},
        {"rule_id": "S09", "contract_area": "git", "requirement": "Do not stage, commit, push, delete, reset, or overwrite committed work without approval.", "validation": "05AM leaves changes unstaged and limited to 05AM script/output paths"},
    ]


def build_abort_rule_rows() -> List[Dict[str, Any]]:
    return [
        {"rule_id": "A01", "applies_to": "05AN execution", "abort_condition": "approved call cap would be exceeded", "required_action": "stop before next call; write sanitized abort summary only", "severity": "hard stop"},
        {"rule_id": "A02", "applies_to": "05AN execution", "abort_condition": "approved GBP cost cap would be exceeded or cannot be tracked", "required_action": "stop before next call; request user decision", "severity": "hard stop"},
        {"rule_id": "A03", "applies_to": "05AN execution", "abort_condition": "runner attempts to write raw prompt, raw response, JSONL, .env, or raw CFPB data", "required_action": "abort and fail validation", "severity": "hard stop"},
        {"rule_id": "A04", "applies_to": "05AN execution", "abort_condition": "input evidence source path resolves under data/raw or contains raw browser export", "required_action": "abort before model call", "severity": "hard stop"},
        {"rule_id": "A05", "applies_to": "05AN execution", "abort_condition": "sanitization validator fails on any persisted output", "required_action": "quarantine uncommitted local output and do not stage; report failure", "severity": "hard stop"},
        {"rule_id": "A06", "applies_to": "05AN execution", "abort_condition": "provider/API errors exceed a user-approved retry limit or produce ambiguous call accounting", "required_action": "stop and produce sanitized call-accounting report", "severity": "hard stop"},
        {"rule_id": "A07", "applies_to": "05AN execution", "abort_condition": "parser-invalid rate is unexpectedly high in the first 5-10% sample", "required_action": "pause before spending remaining budget unless user approves continuation", "severity": "pause gate"},
        {"rule_id": "A08", "applies_to": "05AN execution", "abort_condition": "model or provider differs from approved model", "required_action": "abort before call", "severity": "hard stop"},
        {"rule_id": "A09", "applies_to": "05AN execution", "abort_condition": "any output would support forbidden claims such as real-world financial safety, company misconduct, or provider superiority", "required_action": "flag claim-boundary failure; do not commit", "severity": "hard stop"},
    ]


def build_expected_metric_rows() -> List[Dict[str, Any]]:
    metrics = [
        ("parser_validity", "schema/output-parse layer", "share of outputs passing parser by stage, condition, and condition-stage", "Not equivalent to answer correctness or evidence-state reliability"),
        ("stage_validity", "stage layer", "stage-specific valid decision/audit/escalation outcome rate", "Must be computed separately for decision, audit, escalation"),
        ("condition_validity", "evidence-state layer", "validity by clean/compressed/dropout/noisy condition", "Shows condition sensitivity but not causal proof beyond controlled setup"),
        ("condition_stage_interaction", "cascade layer", "difference in condition effect across stages", "Key to cascade framing"),
        ("evidence_degradation_sensitivity", "evidence-state layer", "paired clean-vs-degraded delta for same base case", "Primary Evidence-State Reliability signal"),
        ("audit_false_assurance_rate", "audit layer", "audit approval/assurance despite degraded or insufficient evidence", "Core head-turner audit failure metric"),
        ("audit_detection_rate", "audit layer", "audit detection of degraded/insufficient/conflicting evidence", "Recovery/resilience metric"),
        ("escalation_recovery_rate", "escalation layer", "cases where escalation corrects or safely routes a degraded-evidence problem", "Recovery metric"),
        ("escalation_loss_rate", "escalation layer", "cases where escalation reinforces, misses, or closes a degraded-evidence problem", "Cascade amplification metric"),
        ("cascade_failure_rate", "cascade layer", "same-case chain-level failure across decision/audit/escalation", "Not reducible to parser validity"),
        ("clean_vs_degraded_paired_deltas", "paired inference layer", "within-case deltas for each degraded condition vs clean", "Controls base-case heterogeneity"),
        ("bootstrap_confidence_intervals", "uncertainty layer", "bootstrap or paired intervals around deltas/rates", "Needed before strong paper claims"),
        ("failure_family_distribution", "diagnostic layer", "distribution of parse/schema/evidence/audit/escalation failure families", "Explains mechanism without overclaiming"),
        ("cascade_sequence_patterns", "cascade layer", "decision→audit→escalation pattern frequencies", "Paper-ready cascade table/figure input"),
    ]
    return [
        {"metric": m, "reliability_layer": layer, "definition": definition, "claim_boundary_note": note}
        for m, layer, definition, note in metrics
    ]


def build_claim_rows() -> List[Dict[str, Any]]:
    return [
        {"claim_type": "allowed_after_05AM", "claim": "05AM prepared a no-call, sanitized, auditable scaled-execution design and approval gate.", "boundary": "Design only; no new model evidence."},
        {"claim_type": "allowed_after_05AM", "claim": "The recommended next run is a controlled paired evidence-state GLM-5.2 execution, subject to explicit user approval.", "boundary": "Recommendation, not execution."},
        {"claim_type": "conditional_after_successful_05AN", "claim": "Scaled GLM-5.2 evidence shows measurable stage/condition/cascade behavior under controlled sanitized evidence states.", "boundary": "Only if 05AN executes, validates, and metrics support it."},
        {"claim_type": "conditional_after_successful_05AN", "claim": "Evidence-State Reliability can be empirically separated from parser validity in this controlled Pilot 05 setting.", "boundary": "Only if parser-valid outputs still show evidence-state/cascade differences."},
        {"claim_type": "target_claim_not_yet_proven", "claim": "Evidence degradation produces measurable reliability cascades across decision, audit, and escalation.", "boundary": "Target claim; requires scaled evidence and uncertainty estimates."},
        {"claim_type": "forbidden", "claim": "GLM-5.2 is generally reliable or unreliable.", "boundary": "Provider/model-wide claim not supported."},
        {"claim_type": "forbidden", "claim": "The system is valid for real-world financial, legal, lending, or regulatory decisions.", "boundary": "Pilot is a research simulation over sanitized CFPB-backed evidence states."},
        {"claim_type": "forbidden", "claim": "Parser validity equals answer correctness or deployment safety.", "boundary": "Parser validity is only one layer."},
        {"claim_type": "forbidden", "claim": "CFPB complaints prove company misconduct or consumer harm prevalence.", "boundary": "No company/provider misconduct or prevalence claims."},
        {"claim_type": "forbidden", "claim": "Cross-model/provider superiority.", "boundary": "Requires separate approved cross-model design and evidence."},
    ]


def create_approval_prompt(rec: Dict[str, Any], cost_meta: Dict[str, Any]) -> str:
    return f"""# TASK 05AN approval prompt — scaled Pilot 05 GLM-5.2 real execution

Use this only after reviewing the 05AM outputs.

I approve **TASK 05AN: SCALED PILOT 05 GLM-5.2 REAL EXECUTION** with the following exact boundaries:

- Model provider/display: GLM-5.2
- API model name: `glm-5.2`
- Run option: {rec['recommended_option']}
- Base cases: {rec['recommended_base_cases']}
- Evidence conditions: 4 (`clean`, `compressed_lossy`, `partial_dropout`, `noisy_conflicting`)
- Stages: 3 (`decision`, `audit`, `escalation`)
- Models: {rec['recommended_models']}
- Maximum approved real model calls: {rec['recommended_call_count']}
- Hard cost cap: £____  **I will fill this before execution**
- Storage contract: sanitized CSV/JSON/MD outputs only
- Raw prompt storage: forbidden
- Raw response storage: forbidden
- JSONL storage: forbidden
- `.env` commit/read-print exposure: forbidden; API key may only be read by the approved execution runner if explicitly needed for 05AN and must never be printed
- Raw CFPB data access: forbidden
- Commit/push after execution: not approved until I separately approve after validation

Abort rules:

1. Stop before exceeding the approved call cap.
2. Stop before exceeding the approved cost cap.
3. Stop if raw prompts, raw responses, JSONL, `.env`, or raw CFPB data would be written or printed.
4. Stop if sanitization validation fails.
5. Stop if call accounting becomes ambiguous.
6. Pause if early parser-invalid rate is unexpectedly high and ask before spending the remaining cap.
7. Stop if the model/provider differs from approved GLM-5.2 / `glm-5.2`.

Required 05AN outputs:

- sanitized execution manifest
- sanitized call-accounting table
- sanitized parsed output table
- parser validity by stage, condition, and condition-stage
- decision/audit/escalation validity tables
- cascade sequence metrics
- paired clean-vs-degraded deltas
- bootstrap confidence intervals or equivalent uncertainty estimates
- claim-boundary update
- final validation summary

Exact pricing status from 05AM: `{cost_meta['exact_cost_status']}`. If exact GLM-5.2 pricing is not available locally, do not run 05AN until I approve a hard cost cap.
"""


def create_report(
    repo_state: Dict[str, Any],
    prior: Dict[str, Any],
    evidence: Dict[str, Any],
    cost_meta: Dict[str, Any],
    run_options: List[Dict[str, Any]],
    rec: Dict[str, Any],
) -> str:
    selected = evidence["selected_count_source"]
    option_lines = "\n".join(
        f"- Option {r['option']}: {r['call_count']} calls — {r['recommendation']}"
        for r in run_options
    )
    related_lines = "\n".join(
        f"- **{r['area']}**: {r['what_existing_work_covers']} Gap for this project: {r['remaining_gap_for_this_project']}"
        for r in RELATED_WORK_ROWS
    )
    return f"""# TASK 05AM — Scaled Pilot 05 real-execution design and approval package

## Status

PASS is only valid if the terminal summary also reports PASS. This report is a design/approval artifact only. It does not add new model evidence.

## Verified checkpoint

- Branch: `{repo_state['branch']}`
- HEAD: `{repo_state['short_head']} {repo_state['latest_subject']}`
- `origin/main`: aligned with HEAD
- Working tree clean before generation: `{repo_state['working_tree_clean_before_task']}`
- Nothing staged before generation: `{repo_state['nothing_staged_before_task']}`
- Required 05AK/05AL committed outputs: verified

## Existing empirical status

Pilot 05 already has a real GLM-5.2 micro-pilot, but it is still too small for the target paper-level claim. 05AM therefore prepares the next real execution rather than treating no-call work as an achievement by itself.

Detected sanitized evidence-state base-case capacity:

- Selected source: `{selected.get('path')}`
- Detected available sanitized base cases: `{evidence['available_sanitized_base_cases']}`
- Sufficient for Option A / 720 calls: `{evidence['sufficient_for_option_A']}`
- Sufficient for 100-case options: `{evidence['sufficient_for_100_case_options']}`

## Related-work gap translated into design

{related_lines}

Practical gap for this project: existing work strongly covers broad LLM benchmarking, RAG faithfulness/context evaluation, and agent failure analysis. The narrower head-turner is to evaluate whether degraded intermediate evidence states create measurable downstream reliability cascades across decision, audit, and escalation, while separating parser validity, final-output validity, evidence-state reliability, audit reliability, escalation reliability, and cascade reliability.

## Scaled run options

{option_lines}

## Recommendation

Recommended next run: **Option {rec['recommended_option']} — {rec['recommended_base_cases']} cases × 4 conditions × 3 stages × {rec['recommended_models']} model(s) = {rec['recommended_call_count']} calls**.

Reason: {rec['recommendation_reason']}

This recommendation is conservative: it moves beyond the 36-call micro-pilot without jumping immediately into cross-model spending. Cross-model replication should follow only if Option A produces a clean, interpretable, claim-bounded signal.

## Cost status

Exact GLM-5.2 pricing is marked as `{cost_meta['exact_cost_status']}`. 05AM does not call provider billing APIs and does not read `.env`. Therefore, 05AN must not run until the user explicitly approves a hard GBP cost cap.

Cost formula:

`total_cost = call_count × ((avg_input_tokens_per_call × input_price_per_token) + (avg_output_tokens_per_call × output_price_per_token))`

## Safety contract

05AM wrote only design/approval artifacts. 05AN must preserve the same claim boundary and must store sanitized outputs only.

Forbidden for 05AN unless separately approved: raw prompt storage, raw response storage, JSONL storage, raw CFPB access, broad model/provider claims, financial/legal/deployment validity claims, staging/commit/push.

## Approval gate

Use `pilot_05_scaled_execution_approval_prompt.md` as the next approval text. It requires explicit model, call count, cost cap, storage contract, and abort-rule approval before any real model calls.
"""


def validate_no_jsonl_created(output_dir: Path) -> None:
    jsonls = list(output_dir.rglob("*.jsonl"))
    if jsonls:
        fail("05AM must not create JSONL files: " + ", ".join(str(p) for p in jsonls))


def validate_created_paths(repo: Path) -> Dict[str, Any]:
    status_after = git(["status", "--porcelain=v1"], repo)
    staged_after = git(["diff", "--cached", "--name-only"], repo)
    if staged_after.strip():
        fail("05AM must leave nothing staged. Staged paths:\n" + staged_after)
    paths = parse_porcelain_paths(status_after)
    allowed_prefix = str(OUTPUT_DIR_REL).replace("\\", "/") + "/"
    allowed_exact = str(SCRIPT_REL).replace("\\", "/")
    unexpected = [p for p in paths if not (p == allowed_exact or p.startswith(allowed_prefix))]
    if unexpected:
        fail("Git status contains paths outside allowed 05AM script/output paths: " + ", ".join(unexpected))
    return {
        "git_status_after_generation": status_after,
        "changed_paths_after_generation": paths,
        "changed_path_count_after_generation": len(paths),
        "nothing_staged_after_generation": True,
        "git_status_limited_to_05AM_paths": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 05AM scaled execution design/approval outputs.")
    parser.add_argument("--repo-path", default=r"C:\Users\naimu\evidence-state-reliability", help="Repository root path")
    args = parser.parse_args()

    repo = Path(args.repo_path).expanduser().resolve()
    if not repo.exists():
        fail(f"Repo path does not exist: {repo}")

    print("=== TASK 05AM: VERIFY CLEAN CHECKPOINT BEFORE GENERATION ===")
    repo_state = validate_initial_repo_state(repo)
    print(f"PASS: {repo_state['short_head']} {repo_state['latest_subject']}")
    print("PASS: working tree clean before 05AM generation")
    print("PASS: main aligned with origin/main")

    print("\n=== VERIFY REQUIRED 05AK / 05AL COMMITTED OUTPUTS EXIST ===")
    prior = validate_prior_commits_and_outputs(repo)
    for label, info in prior.items():
        print(f"PASS: {label} {info['commit']} {info['subject']} ({info['committed_file_count']} files exist)")

    git_files = git_ls_files(repo)

    print("\n=== VERIFY SANITIZED PILOT 05 EVIDENCE-STATE INPUTS EXIST ===")
    evidence = inspect_sanitized_evidence_inputs(repo, git_files)
    print(f"PASS: sanitized candidate files checked: {evidence['candidate_file_count']}")
    print(f"selected_count_source: {evidence['selected_count_source'].get('path')}")
    print(f"available_sanitized_base_cases: {evidence['available_sanitized_base_cases']}")

    print("\n=== SAFE LOCAL COST METADATA CHECK ===")
    cost_meta = inspect_safe_local_cost_metadata(repo, git_files)
    print(f"safe_metadata_files_scanned: {cost_meta['safe_metadata_files_scanned']}")
    print(f"exact_cost_status: {cost_meta['exact_cost_status']}")

    output_dir = repo / OUTPUT_DIR_REL
    script_target = repo / SCRIPT_REL
    if output_dir.exists():
        fail(f"Output directory already exists before generation; refusing overwrite without approval: {output_dir}")
    if script_target.exists():
        fail(f"05AM script target already exists before generation; refusing overwrite without approval: {script_target}")

    print("\n=== WRITE 05AM SCRIPT AND SANITIZED DESIGN OUTPUTS ===")
    script_target.parent.mkdir(parents=True, exist_ok=True)
    source_script = Path(__file__).resolve()
    shutil.copyfile(source_script, script_target)
    output_dir.mkdir(parents=True, exist_ok=False)

    run_options, rec = build_run_options(evidence["available_sanitized_base_cases"])
    call_count_rows = build_call_count_cost_rows(run_options)
    evidence_condition_rows = build_evidence_condition_rows()
    stage_rows = build_stage_rows()
    safety_rows = build_safety_contract_rows()
    abort_rows = build_abort_rule_rows()
    expected_metric_rows = build_expected_metric_rows()
    claim_rows = build_claim_rows()

    write_csv(output_dir / OUTPUT_FILES["run_options"], run_options)
    write_csv(output_dir / OUTPUT_FILES["call_count_cost"], call_count_rows)
    write_csv(output_dir / OUTPUT_FILES["evidence_conditions"], evidence_condition_rows)
    write_csv(output_dir / OUTPUT_FILES["stage_plan"], stage_rows)
    write_csv(output_dir / OUTPUT_FILES["safety_contract"], safety_rows)
    write_csv(output_dir / OUTPUT_FILES["abort_rules"], abort_rows)
    write_csv(output_dir / OUTPUT_FILES["expected_metrics"], expected_metric_rows)
    write_csv(output_dir / OUTPUT_FILES["target_claims"], claim_rows)
    write_csv(output_dir / OUTPUT_FILES["related_work"], RELATED_WORK_ROWS)

    approval_prompt = create_approval_prompt(rec, cost_meta)
    (output_dir / OUTPUT_FILES["approval_prompt"]).write_text(approval_prompt, encoding="utf-8")

    report = create_report(repo_state, prior, evidence, cost_meta, run_options, rec)
    (output_dir / OUTPUT_FILES["design_report"]).write_text(report, encoding="utf-8")

    validate_no_jsonl_created(output_dir)

    # Manifest last, including hashes for all other output files.
    generated_paths = [script_target] + sorted(output_dir.glob("*"))
    generated_hashes = {rel_path(p, repo): sha256_file(p) for p in generated_paths if p.is_file()}
    post_git = validate_created_paths(repo)

    manifest = {
        "task_id": TASK_ID,
        "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "status": "PASS",
        "repo_state": repo_state,
        "prior_commits_verified": prior,
        "sanitized_evidence_inputs": evidence,
        "safe_cost_metadata_check": cost_meta,
        "recommendation": rec,
        "run_options_count": len(run_options),
        "expected_output_files": OUTPUT_FILES,
        "generated_hashes_sha256": generated_hashes,
        "safety_flags": {
            "real_api_calls": 0,
            "model_calls": 0,
            "api_key_read": False,
            "env_file_read": False,
            "env_file_written": False,
            "raw_prompts_written": False,
            "raw_responses_written": False,
            "jsonl_written": False,
            "raw_cfpb_data_touched": False,
            "staged": False,
            "committed": False,
            "pushed": False,
            "deleted_or_reset": False,
        },
        "post_generation_git_validation": post_git,
        "claim_boundary": {
            "broad_model_reliability_claimed": False,
            "real_world_financial_or_regulatory_validity_claimed": False,
            "provider_superiority_claimed": False,
            "target_research_claim_proven": False,
            "design_only": True,
        },
    }
    write_json(output_dir / OUTPUT_FILES["manifest"], manifest)

    # Revalidate status after manifest write.
    post_git = validate_created_paths(repo)

    print("PASS: wrote 05AM experiment script and design outputs")
    for rel in [str(SCRIPT_REL).replace("\\", "/")] + [str(OUTPUT_DIR_REL / name).replace("\\", "/") for name in OUTPUT_FILES.values()]:
        print(f"CREATED: {rel}")

    print("\n=== TASK 05AM FINAL VALIDATION SUMMARY ===")
    print("status: PASS")
    print(f"recommended_option: {rec['recommended_option']}")
    print(f"recommended_call_count: {rec['recommended_call_count']}")
    print(f"available_sanitized_base_cases: {evidence['available_sanitized_base_cases']}")
    print("real_api_calls: 0")
    print("model_calls: 0")
    print("api_key_read: False")
    print("env_file_read: False")
    print("raw_prompts_written: False")
    print("raw_responses_written: False")
    print("jsonl_written: False")
    print("raw_cfpb_data_touched: False")
    print("nothing_staged: True")
    print("git_status_limited_to_05AM_paths: True")
    print("\nNEXT: Review outputs. Do not commit/push until explicitly approved.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
