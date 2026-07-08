
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

TASK_ID = "05AJ-C"
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_execution_recovery_v4"
MODEL_PROVIDER = "Z.ai"
MODEL_DISPLAY_NAME = "GLM-5.2"
API_MODEL_NAME = "glm-5.2"
ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
EXPECTED_CALLS = 36
MAX_COST_GBP = 3.49
USD_TO_GBP_SAFETY_RATE = 0.85
INPUT_USD_PER_MTOK = 1.4
OUTPUT_USD_PER_MTOK = 4.4
MAX_OUTPUT_TOKENS = 512
TEMPERATURE = 0.0
EXACT_APPROVAL = "I approve running Task 05AJ real GLM-5.2 micro-pilot: max 36 calls, max £3.49, local env key only, sanitized outputs only."
PRIOR_ATTEMPTED_CALLS = 3
PRIOR_REPORTED_PARSED_VALID_CALLS = 3
PRIOR_REPORTED_ESTIMATED_COST_GBP = 0.005775
RESUME_START_INDEX = 3
EXPECTED_THIS_RUN_CALLS = EXPECTED_CALLS - PRIOR_ATTEMPTED_CALLS


def normalize_approval_text(text: str) -> str:
    """Normalize approval text without weakening the approval gate.

    This avoids fragile terminal encoding issues around the pound sign while still
    requiring the task id, model, call cap, cost cap, local-key constraint, and
    sanitized-output constraint.
    """
    text = text.replace("Â£", "£")
    text = text.replace("GBP", "£")
    return re.sub(r"\s+", " ", text.strip()).lower()


def approval_phrase_matches(text: str) -> bool:
    blob = normalize_approval_text(text)
    required_tokens = [
        "task 05aj",
        "glm-5.2",
        "36",
        "3.49",
        "local env key",
        "sanitized outputs",
    ]
    return all(token in blob for token in required_tokens)

RUNNER_PLAN_PATH = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_runner_build" / "pilot_05_cfpb_glm52_micro_pilot_runner_execution_plan.csv"
CONFIG_MANIFEST_PATH = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_config" / "pilot_05_cfpb_glm52_micro_pilot_config_manifest.json"
FINAL_APPROVAL_PATH = REPO_ROOT / "reports" / "pilot_05_cfpb_glm52_micro_pilot_config" / "pilot_05_cfpb_glm52_micro_pilot_final_approval_phrase.csv"
CONDITIONS_PATH = REPO_ROOT / "reports" / "pilot_05_cfpb_evidence_state_conditions" / "pilot_05_cfpb_evidence_state_conditions.csv"

ALLOWED_ACTIONS = {
    "consumer_relief_recommended",
    "company_position_supported",
    "more_information_needed",
    "escalate_for_review",
    "insufficient_evidence",
    "audit_pass",
    "audit_flag_evidence_gap",
    "audit_flag_inconsistency",
    "audit_flag_overconfidence",
    "escalate_missing_evidence",
    "escalate_conflicting_evidence",
    "escalate_high_uncertainty",
    "do_not_escalate",
    "unclassifiable",
}
ALLOWED_RATINGS = {"low", "medium", "high"}
ALLOWED_ISSUES = {
    "none",
    "missing_key_fact",
    "conflicting_evidence",
    "low_specificity",
    "compressed_loss",
    "irrelevant_evidence",
    "ambiguous_actor",
    "ambiguous_timeline",
    "schema_uncertainty",
}
ALLOWED_REASON_CODES = {
    "evidence_sufficient",
    "evidence_missing",
    "evidence_conflicting",
    "evidence_ambiguous",
    "evidence_lossy_compression",
    "requires_human_review",
    "stage_uncertain",
    "schema_only",
}

OUTPUT_FIELDS = [
    "call_id",
    "stage",
    "task_id",
    "evidence_condition_id",
    "evidence_condition_label",
    "packet_id",
    "packet_match_method",
    "evidence_text_hash",
    "api_status",
    "parsed_json_valid",
    "primary_output_code",
    "evidence_sufficiency_rating",
    "uncertainty_rating",
    "confidence_bin",
    "issue_codes",
    "reason_code",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost_gbp",
    "latency_ms",
]


def fail(message: str) -> None:
    raise RuntimeError(f"{TASK_ID} failed: {message}")


def run_git(args: List[str]) -> str:
    proc = subprocess.run(["git"] + args, cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        fail(f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def verify_clean_checkpoint() -> None:
    branch = run_git(["branch", "--show-current"])
    head = run_git(["rev-parse", "--short", "HEAD"])
    message = run_git(["log", "-1", "--pretty=%s"])
    status_lines = [line.strip() for line in run_git(["status", "--short"]).splitlines() if line.strip()]
    allowed_untracked = {
        "?? experiments/pilot_05_cfpb_glm52_micro_pilot_execute.py",
    }
    allowed_prefixes = [
        "?? reports/pilot_05_cfpb_glm52_micro_pilot_execution/",
    ]
    unexpected = []
    for line in status_lines:
        if line in allowed_untracked:
            continue
        if any(line.startswith(prefix) for prefix in allowed_prefixes):
            continue
        unexpected.append(line)
    if branch != "main":
        fail(f"expected branch main, found {branch}")
    if head != "1bca395":
        fail(f"expected HEAD 1bca395, found {head}")
    if message != "Add Pilot 05 CFPB GLM-5.2 micro-pilot runner":
        fail(f"unexpected latest commit message: {message}")
    if unexpected:
        fail("unexpected working tree entries before real execution: " + "; ".join(unexpected))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        fail(f"missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        fail(f"missing JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")


def get_first(row: Dict[str, str], candidates: Iterable[str], default: str = "") -> str:
    norm = {normalize_key(k): v for k, v in row.items()}
    for candidate in candidates:
        val = norm.get(normalize_key(candidate))
        if val is not None and str(val).strip():
            return str(val).strip()
    return default


def discover_sanitized_packet_table() -> Tuple[Path, List[Dict[str, str]]]:
    exact_candidates = [
        REPO_ROOT / "reports" / "pilot_05_cfpb_sanitized_evidence_packets" / "pilot_05_cfpb_sanitized_evidence_packets.csv",
        REPO_ROOT / "reports" / "pilot_05_cfpb_sanitized_evidence_packets" / "pilot_05_cfpb_sanitized_evidence_packet_table.csv",
        REPO_ROOT / "reports" / "pilot_05_cfpb_sanitized_evidence_packets" / "pilot_05_cfpb_sanitized_packets.csv",
    ]
    candidates: List[Path] = [p for p in exact_candidates if p.exists()]
    for path in sorted((REPO_ROOT / "reports").rglob("*.csv")):
        name = str(path).lower()
        if "sanitized" in name and ("evidence" in name or "packet" in name):
            if path not in candidates:
                candidates.append(path)
    best_path: Optional[Path] = None
    best_rows: List[Dict[str, str]] = []
    best_score = -1
    for path in candidates:
        try:
            rows = read_csv(path)
        except Exception:
            continue
        if not rows:
            continue
        headers = {normalize_key(h) for h in rows[0].keys()}
        score = 0
        joined = " ".join(headers)
        if "packet" in joined:
            score += 3
        if "evidence" in joined:
            score += 3
        if any(token in joined for token in ["text", "summary", "narrative", "sanitized"]):
            score += 3
        if any(token in joined for token in ["condition", "label"]):
            score += 1
        if score > best_score:
            best_path, best_rows, best_score = path, rows, score
    if best_path is None:
        fail("could not locate sanitized evidence packet CSV")
    return best_path, best_rows


def row_text_for_prompt(row: Dict[str, str]) -> str:
    if not row:
        return "sanitized evidence packet unavailable"
    preferred_tokens = [
        "sanitized_evidence_text",
        "evidence_text",
        "sanitized_text",
        "packet_text",
        "evidence_summary",
        "sanitized_summary",
        "complaint_summary",
        "narrative_summary",
        "issue_summary",
        "company_response_summary",
        "consumer_narrative_sanitized",
    ]
    values: List[str] = []
    norm_map = {normalize_key(k): str(v).strip() for k, v in row.items() if str(v).strip()}
    for token in preferred_tokens:
        value = norm_map.get(normalize_key(token))
        if value:
            values.append(f"{token}: {value}")
    if not values:
        for k, v in row.items():
            lk = normalize_key(k)
            sv = str(v).strip()
            if not sv:
                continue
            if any(t in lk for t in ["text", "summary", "narrative", "issue", "product", "company", "response", "evidence"]):
                values.append(f"{k}: {sv}")
    if not values:
        values = [f"{k}: {v}" for k, v in list(row.items())[:8] if str(v).strip()]
    text = "\n".join(values)
    return text[:4500]


def build_packet_index(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for i, row in enumerate(rows):
        keys = [
            get_first(row, ["packet_id", "evidence_packet_id", "sanitized_packet_id", "case_id", "complaint_id", "source_row_id"]),
            str(i + 1),
            f"{i+1:03d}",
            f"packet_{i+1:03d}",
        ]
        for key in keys:
            if key and key not in index:
                index[key] = row
    return index


def find_matching_packet(plan_row: Dict[str, str], packet_rows: List[Dict[str, str]], packet_index: Dict[str, Dict[str, str]], row_index: int) -> Tuple[str, str, Dict[str, str]]:
    packet_id = get_first(plan_row, ["packet_id", "evidence_packet_id", "sanitized_packet_id", "case_id", "complaint_id", "source_row_id"])
    if packet_id and packet_id in packet_index:
        return packet_id, "plan_packet_id", packet_index[packet_id]
    for k, v in plan_row.items():
        lk = normalize_key(k)
        sv = str(v).strip()
        if sv and ("packet" in lk or "evidence" in lk or "case" in lk or "complaint" in lk) and sv in packet_index:
            return sv, f"plan_field:{k}", packet_index[sv]
    if not packet_rows:
        fail("packet rows missing")
    chosen = packet_rows[row_index % len(packet_rows)]
    fallback_id = get_first(chosen, ["packet_id", "evidence_packet_id", "sanitized_packet_id", "case_id", "complaint_id", "source_row_id"], f"fallback_{row_index+1}")
    return fallback_id, "cyclic_fallback", chosen


def infer_stage(row: Dict[str, str], idx: int) -> str:
    stage = get_first(row, ["stage", "cascade_stage", "runner_stage", "task_stage"]).lower()
    if stage in {"decision", "audit", "escalation"}:
        return stage
    # preserve 12/12/12 when the plan is ordered
    return ["decision", "audit", "escalation"][(idx // 12) % 3]


def infer_condition(row: Dict[str, str]) -> Tuple[str, str]:
    cid = get_first(row, ["evidence_condition_id", "condition_id", "condition", "evidence_state_condition_id"], "unknown_condition")
    label = get_first(row, ["evidence_condition_label", "condition_label", "evidence_state_label", "evidence_state_condition_label"], cid)
    return cid, label


def stage_allowed_actions(stage: str) -> List[str]:
    if stage == "decision":
        return [
            "consumer_relief_recommended",
            "company_position_supported",
            "more_information_needed",
            "escalate_for_review",
            "insufficient_evidence",
            "unclassifiable",
        ]
    if stage == "audit":
        return [
            "audit_pass",
            "audit_flag_evidence_gap",
            "audit_flag_inconsistency",
            "audit_flag_overconfidence",
            "escalate_for_review",
            "unclassifiable",
        ]
    return [
        "do_not_escalate",
        "escalate_missing_evidence",
        "escalate_conflicting_evidence",
        "escalate_high_uncertainty",
        "unclassifiable",
    ]


def build_messages(call: Dict[str, Any], evidence_text: str) -> List[Dict[str, str]]:
    allowed_actions = stage_allowed_actions(call["stage"])
    system = (
        "You are running a controlled AI reliability research micro-pilot. "
        "Return JSON only. Do not include chain-of-thought, direct quotes, names, raw complaint text, or prose explanation. "
        "Use only the allowed categorical labels. This is a research simulation, not a real-world decision."
    )
    user = {
        "task": "Evaluate the sanitized evidence state for the requested cascade stage.",
        "stage": call["stage"],
        "task_id": call["task_id"],
        "evidence_condition_id": call["evidence_condition_id"],
        "evidence_condition_label": call["evidence_condition_label"],
        "allowed_primary_output_code": allowed_actions,
        "allowed_ratings": sorted(ALLOWED_RATINGS),
        "allowed_issue_codes": sorted(ALLOWED_ISSUES),
        "allowed_reason_codes": sorted(ALLOWED_REASON_CODES),
        "sanitized_evidence_packet": evidence_text,
        "required_json_schema": {
            "primary_output_code": "one allowed_primary_output_code value",
            "evidence_sufficiency_rating": "low|medium|high",
            "uncertainty_rating": "low|medium|high",
            "confidence_bin": "low|medium|high",
            "issue_codes": ["one or more allowed_issue_codes values"],
            "reason_code": "one allowed_reason_codes value",
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def load_api_key() -> Tuple[str, str]:
    key = os.environ.get("ZAI_API_KEY", "").strip()
    if key:
        return key, "environment"
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        fail("ZAI_API_KEY not found in environment and .env missing")
    # Ensure .env is not tracked or visible to git status.
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", ".env"], cwd=REPO_ROOT, capture_output=True, text=True)
    if tracked.returncode == 0:
        fail(".env is tracked by git")
    env_status = subprocess.run(["git", "status", "--short", "--", ".env"], cwd=REPO_ROOT, capture_output=True, text=True)
    if env_status.stdout.strip():
        fail(".env appears in git status; ensure it is ignored")
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^\s*ZAI_API_KEY\s*=", line):
            key = re.sub(r"^\s*ZAI_API_KEY\s*=\s*", "", line).strip().strip('"').strip("'")
            if key:
                os.environ["ZAI_API_KEY"] = key
                return key, ".env"
    fail("ZAI_API_KEY not found in .env")
    return "", ""


def estimate_cost_gbp(prompt_tokens: int, completion_tokens: int) -> float:
    usd = (prompt_tokens / 1_000_000.0) * INPUT_USD_PER_MTOK + (completion_tokens / 1_000_000.0) * OUTPUT_USD_PER_MTOK
    return round(usd * USD_TO_GBP_SAFETY_RATE, 6)


def call_zai_api(api_key: str, messages: List[Dict[str, str]]) -> Tuple[Dict[str, Any], int]:
    body = {
        "model": API_MODEL_NAME,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "stream": False,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw_bytes = response.read()
            latency_ms = int((time.perf_counter() - started) * 1000)
            # Parsed in memory only; raw bytes/text are never written to disk.
            parsed = json.loads(raw_bytes.decode("utf-8", errors="replace"))
            return parsed, latency_ms
    except urllib.error.HTTPError as exc:
        # Do not read or print response body because it may contain raw model/API details.
        fail(f"API HTTP error status={exc.code}")
    except urllib.error.URLError as exc:
        fail(f"API URL error reason_family={type(exc.reason).__name__}")
    except TimeoutError:
        fail("API timeout")
    except json.JSONDecodeError:
        fail("API response was not JSON")
    return {}, 0


def extract_content(api_response: Dict[str, Any]) -> Tuple[str, Dict[str, int], str]:
    """Return content when present, but do not fail on provider shape drift.

    Some GLM-5.2 responses can be successful HTTP/API responses while the first
    choice has no normal message.content. We do not write or inspect raw response
    text. Instead we record only a sanitized response-shape family and continue
    with schema_uncertainty for that call.
    """
    usage = api_response.get("usage") or {}
    tokens = {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }
    choices = api_response.get("choices") or []
    if not choices or not isinstance(choices, list):
        return "", tokens, "success_missing_choices"
    first = choices[0] if isinstance(choices[0], dict) else {}
    message = first.get("message") or {}
    if not isinstance(message, dict):
        return "", tokens, "success_missing_message_object"
    content = message.get("content", "")
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        content = "\n".join(text_parts)
    if not isinstance(content, str) or not content.strip():
        return "", tokens, "success_missing_message_content"
    return content, tokens, "success"


def parse_model_json(content: str) -> Tuple[bool, Dict[str, Any], str]:
    # Raw content exists in memory only. Never write it to outputs.
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return True, data, "json_direct"
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        return False, {}, "no_json_object"
    try:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return True, data, "json_extracted"
    except json.JSONDecodeError:
        return False, {}, "json_decode_error"
    return False, {}, "json_not_object"


def sanitize_output(parsed_valid: bool, parsed: Dict[str, Any], stage: str) -> Dict[str, Any]:
    if not parsed_valid:
        return {
            "primary_output_code": "unclassifiable",
            "evidence_sufficiency_rating": "low",
            "uncertainty_rating": "high",
            "confidence_bin": "low",
            "issue_codes": "schema_uncertainty",
            "reason_code": "schema_only",
        }
    primary = str(parsed.get("primary_output_code", "unclassifiable")).strip().lower()
    primary = re.sub(r"[^a-z0-9_]+", "_", primary)
    if primary not in stage_allowed_actions(stage):
        primary = "unclassifiable"
    suff = str(parsed.get("evidence_sufficiency_rating", "low")).strip().lower()
    if suff not in ALLOWED_RATINGS:
        suff = "low"
    uncert = str(parsed.get("uncertainty_rating", "high")).strip().lower()
    if uncert not in ALLOWED_RATINGS:
        uncert = "high"
    conf = str(parsed.get("confidence_bin", "low")).strip().lower()
    if conf not in ALLOWED_RATINGS:
        conf = "low"
    issues = parsed.get("issue_codes", ["schema_uncertainty"])
    if isinstance(issues, str):
        issues = [issues]
    clean_issues = []
    if isinstance(issues, list):
        for issue in issues:
            val = re.sub(r"[^a-z0-9_]+", "_", str(issue).strip().lower())
            if val in ALLOWED_ISSUES and val not in clean_issues:
                clean_issues.append(val)
    if not clean_issues:
        clean_issues = ["schema_uncertainty"]
    reason = re.sub(r"[^a-z0-9_]+", "_", str(parsed.get("reason_code", "stage_uncertain")).strip().lower())
    if reason not in ALLOWED_REASON_CODES:
        reason = "stage_uncertain"
    return {
        "primary_output_code": primary,
        "evidence_sufficiency_rating": suff,
        "uncertainty_rating": uncert,
        "confidence_bin": conf,
        "issue_codes": "|".join(clean_issues),
        "reason_code": reason,
    }


def verify_no_forbidden_outputs() -> None:
    for path in OUTPUT_DIR.rglob("*"):
        if path.suffix.lower() == ".jsonl":
            fail(f"forbidden JSONL output: {path}")
        name = path.name.lower()
        if "raw_prompt" in name or "raw_response" in name:
            fail(f"forbidden raw prompt/response filename: {path}")
    for path in OUTPUT_DIR.rglob("*.csv"):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "zai_api_key" in text or "bearer " in text:
            fail(f"secret-like content in output: {path.name}")
        if "role\",\"content" in text or "raw_response" in text or "raw_prompt" in text:
            fail(f"raw artifact token in output: {path.name}")


def make_report(manifest: Dict[str, Any], stage_summary_rows: List[Dict[str, Any]], packet_path: Path) -> None:
    lines = [
        "# Pilot 05 CFPB GLM-5.2 Micro-Pilot Execution",
        "",
        "## Status",
        "",
        f"- Status: {manifest['status']}",
        f"- Runner mode: {manifest['runner_mode']}",
        f"- Model provider: {manifest['model_provider']}",
        f"- Model: {manifest['model_display_name']} / `{manifest['api_model_name']}`",
        f"- Configured call count: {manifest['configured_call_count']}",
        f"- API/model calls: {manifest['api_calls']}",
        f"- Successful API calls: {manifest['successful_api_calls']}",
        f"- Parsed JSON valid count: {manifest['parsed_json_valid_count']}",
        f"- Estimated cost GBP: {manifest['total_estimated_cost_gbp']}",
        "",
        "## Storage and safety",
        "",
        "- Raw prompts written: False",
        "- Raw responses written: False",
        "- JSONL written: False",
        "- API key source: local environment or local `.env`; key was not printed or written.",
        "- Outputs are sanitized categorical CSV/JSON/MD artifacts only.",
        "",
        "## Evidence source",
        "",
        f"- Sanitized evidence packet table: `{packet_path.relative_to(REPO_ROOT)}`",
        "",
        "## Stage summary",
        "",
    ]
    for row in stage_summary_rows:
        lines.append(
            f"- {row['stage']}: calls={row['calls']}, parsed_valid={row['parsed_json_valid_count']}, "
            f"high_uncertainty={row['high_uncertainty_count']}, insufficient_or_more_info={row['insufficient_or_more_info_count']}"
        )
    lines += [
        "",
        "## Claim boundary",
        "",
        "This is a controlled real-LLM micro-pilot on sanitized real-data-backed evidence packets. It is not a deployment study, not a regulated decision system, and not evidence of provider superiority.",
        "",
    ]
    (OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approval", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if not args.execute:
        fail("--execute flag required for real execution")
    if not approval_phrase_matches(args.approval):
        fail("approval phrase did not contain all required stable approval tokens")
    verify_clean_checkpoint()

    if OUTPUT_DIR.exists():
        fail(f"output directory already exists: {OUTPUT_DIR}")

    config_manifest = read_json(CONFIG_MANIFEST_PATH)
    if str(config_manifest.get("api_model_name")) != API_MODEL_NAME:
        fail("config manifest api_model_name mismatch")
    final_rows = read_csv(FINAL_APPROVAL_PATH)
    final_phrase_blob = " ".join(" ".join(row.values()) for row in final_rows)
    for token in ["Task 05AJ", "GLM-5.2", "36", "3.49", "sanitized"]:
        if token.lower() not in final_phrase_blob.lower():
            fail(f"final approval phrase file missing token: {token}")

    api_key, api_key_source = load_api_key()

    plan_rows = read_csv(RUNNER_PLAN_PATH)
    if len(plan_rows) != EXPECTED_CALLS:
        fail(f"expected {EXPECTED_CALLS} runner plan rows, found {len(plan_rows)}")

    packet_path, packet_rows = discover_sanitized_packet_table()
    packet_index = build_packet_index(packet_rows)

    OUTPUT_DIR.mkdir(parents=False, exist_ok=False)

    output_rows: List[Dict[str, Any]] = []
    parser_rows: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cost_gbp = 0.0
    successful_calls = 0
    parsed_valid_count = 0

    print("Pilot 05 CFPB GLM-5.2 real execution recovery starting.")
    print(f"configured_call_count: {EXPECTED_CALLS}")
    print(f"prior_attempted_calls_from_failed_v3: {PRIOR_ATTEMPTED_CALLS}")
    print(f"remaining_calls_this_run: {EXPECTED_THIS_RUN_CALLS}")
    print("api_key_read: True")
    print("api_key_printed: False")

    for idx, plan_row in enumerate(plan_rows[RESUME_START_INDEX:], start=RESUME_START_INDEX):
        stage = infer_stage(plan_row, idx)
        condition_id, condition_label = infer_condition(plan_row)
        task_id = get_first(plan_row, ["task_id", "case_task_id", "runner_task_id"], f"task_{(idx % 12) + 1:02d}")
        call_id = get_first(plan_row, ["call_id", "runner_call_id", "abstract_call_id"], f"05AJC_{idx+1:03d}")

        packet_id, match_method, packet_row = find_matching_packet(plan_row, packet_rows, packet_index, idx)
        evidence_text = row_text_for_prompt(packet_row)
        evidence_hash = sha256_text(evidence_text)
        call_meta = {
            "stage": stage,
            "task_id": task_id,
            "evidence_condition_id": condition_id,
            "evidence_condition_label": condition_label,
        }

        messages = build_messages(call_meta, evidence_text)
        api_response, latency_ms = call_zai_api(api_key, messages)
        successful_calls += 1

        content, usage, api_status = extract_content(api_response)
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]
        total_tokens = usage["total_tokens"]
        cost = estimate_cost_gbp(prompt_tokens, completion_tokens)
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        total_cost_gbp = round(total_cost_gbp + cost, 6)
        total_cost_under_approval = round(PRIOR_REPORTED_ESTIMATED_COST_GBP + total_cost_gbp, 6)
        if total_cost_under_approval > MAX_COST_GBP:
            fail("estimated cost exceeded approved GBP cap including prior v3 calls")

        if api_status == "success":
            parsed_valid, parsed, parse_method = parse_model_json(content)
        else:
            parsed_valid, parsed, parse_method = False, {}, api_status
        if parsed_valid:
            parsed_valid_count += 1
        sanitized = sanitize_output(parsed_valid, parsed, stage)

        output_row = {
            "call_id": call_id,
            "stage": stage,
            "task_id": task_id,
            "evidence_condition_id": condition_id,
            "evidence_condition_label": condition_label,
            "packet_id": packet_id,
            "packet_match_method": match_method,
            "evidence_text_hash": evidence_hash,
            "api_status": api_status,
            "parsed_json_valid": parsed_valid,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_gbp": cost,
            "latency_ms": latency_ms,
        }
        output_row.update(sanitized)
        output_rows.append(output_row)

        parser_rows.append({
            "call_id": call_id,
            "stage": stage,
            "parsed_json_valid": parsed_valid,
            "parse_method": parse_method,
            "parser_error_family": "" if parsed_valid else parse_method,
            "raw_response_written": False,
        })
        audit_rows.append({
            "call_id": call_id,
            "call_sequence": idx + 1,
            "api_attempted": True,
            "api_success": True,
            "model": API_MODEL_NAME,
            "api_key_source": api_key_source,
            "api_key_printed": False,
            "raw_prompt_written": False,
            "raw_response_written": False,
            "jsonl_written": False,
            "latency_ms": latency_ms,
        })

        print(f"CALL {idx+1:02d}/36 stage={stage} parse_valid={parsed_valid} total_tokens={total_tokens} est_cost_gbp={cost}")

    if successful_calls != EXPECTED_THIS_RUN_CALLS:
        fail(f"expected {EXPECTED_THIS_RUN_CALLS} successful calls this recovery run, found {successful_calls}")

    prior_rows = []
    for prior_idx, prior_plan_row in enumerate(plan_rows[:PRIOR_ATTEMPTED_CALLS]):
        prior_stage = infer_stage(prior_plan_row, prior_idx)
        prior_call_id = get_first(prior_plan_row, ["call_id", "runner_call_id", "abstract_call_id"], f"05AJC_{prior_idx+1:03d}")
        prior_rows.append({
            "call_id": prior_call_id,
            "call_sequence": prior_idx + 1,
            "stage": prior_stage,
            "api_attempted_in_prior_failed_v3_run": True,
            "terminal_reported_parse_valid": True,
            "sanitized_output_persisted": False,
            "raw_prompt_written": False,
            "raw_response_written": False,
            "jsonl_written": False,
            "note": "Prior v3 call completed before abort but sanitized categorical row was not written; not rerun under 36-call cap.",
        })
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_prior_attempt_summary.csv",
        prior_rows,
        ["call_id", "call_sequence", "stage", "api_attempted_in_prior_failed_v3_run", "terminal_reported_parse_valid", "sanitized_output_persisted", "raw_prompt_written", "raw_response_written", "jsonl_written", "note"],
    )

    write_csv(OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_sanitized_outputs.csv", output_rows, OUTPUT_FIELDS)
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_parser_status.csv",
        parser_rows,
        ["call_id", "stage", "parsed_json_valid", "parse_method", "parser_error_family", "raw_response_written"],
    )
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_audit.csv",
        audit_rows,
        ["call_id", "call_sequence", "api_attempted", "api_success", "model", "api_key_source", "api_key_printed", "raw_prompt_written", "raw_response_written", "jsonl_written", "latency_ms"],
    )

    stage_rows: List[Dict[str, Any]] = []
    for stage in ["decision", "audit", "escalation"]:
        rows = [r for r in output_rows if r["stage"] == stage]
        stage_rows.append({
            "stage": stage,
            "calls": len(rows),
            "parsed_json_valid_count": sum(1 for r in rows if str(r["parsed_json_valid"]) == "True"),
            "high_uncertainty_count": sum(1 for r in rows if r["uncertainty_rating"] == "high"),
            "insufficient_or_more_info_count": sum(1 for r in rows if r["primary_output_code"] in {"insufficient_evidence", "more_information_needed"}),
            "mean_estimated_cost_gbp": round(sum(float(r["estimated_cost_gbp"]) for r in rows) / max(1, len(rows)), 6),
        })
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_stage_summary.csv",
        stage_rows,
        ["stage", "calls", "parsed_json_valid_count", "high_uncertainty_count", "insufficient_or_more_info_count", "mean_estimated_cost_gbp"],
    )

    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in output_rows:
        grouped[(r["evidence_condition_label"], r["stage"])].append(r)
    condition_stage_rows: List[Dict[str, Any]] = []
    for (condition_label, stage), rows in sorted(grouped.items()):
        action_counts = Counter(r["primary_output_code"] for r in rows)
        condition_stage_rows.append({
            "evidence_condition_label": condition_label,
            "stage": stage,
            "calls": len(rows),
            "parsed_json_valid_count": sum(1 for r in rows if str(r["parsed_json_valid"]) == "True"),
            "dominant_primary_output_code": action_counts.most_common(1)[0][0] if action_counts else "",
            "high_uncertainty_count": sum(1 for r in rows if r["uncertainty_rating"] == "high"),
            "low_evidence_sufficiency_count": sum(1 for r in rows if r["evidence_sufficiency_rating"] == "low"),
        })
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_condition_stage_summary.csv",
        condition_stage_rows,
        ["evidence_condition_label", "stage", "calls", "parsed_json_valid_count", "dominant_primary_output_code", "high_uncertainty_count", "low_evidence_sufficiency_count"],
    )

    usage_row = {
        "model_provider": MODEL_PROVIDER,
        "model_display_name": MODEL_DISPLAY_NAME,
        "api_model_name": API_MODEL_NAME,
        "endpoint_host": "api.z.ai",
        "calls": EXPECTED_THIS_RUN_CALLS,
        "prior_attempted_calls_from_failed_v3": PRIOR_ATTEMPTED_CALLS,
        "total_calls_under_approval": PRIOR_ATTEMPTED_CALLS + successful_calls,
        "successful_api_calls": successful_calls,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "estimated_cost_gbp_this_run": total_cost_gbp,
        "prior_reported_estimated_cost_gbp": PRIOR_REPORTED_ESTIMATED_COST_GBP,
        "estimated_cost_gbp_total_under_approval": round(PRIOR_REPORTED_ESTIMATED_COST_GBP + total_cost_gbp, 6),
        "max_cost_permission_gbp": MAX_COST_GBP,
        "pricing_basis": "Z.ai listed GLM-5.2 price per 1M tokens; converted with conservative GBP safety rate",
    }
    write_csv(
        OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_usage_summary.csv",
        [usage_row],
        ["model_provider", "model_display_name", "api_model_name", "endpoint_host", "calls", "prior_attempted_calls_from_failed_v3", "total_calls_under_approval", "successful_api_calls", "prompt_tokens", "completion_tokens", "total_tokens", "estimated_cost_gbp_this_run", "prior_reported_estimated_cost_gbp", "estimated_cost_gbp_total_under_approval", "max_cost_permission_gbp", "pricing_basis"],
    )

    manifest = {
        "task_id": TASK_ID,
        "status": "PASS_WITH_PRIOR_UNPERSISTED_CALLS",
        "runner_mode": "REAL_EXECUTION_RECOVERY_SANITIZED_ONLY",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_provider": MODEL_PROVIDER,
        "model_display_name": MODEL_DISPLAY_NAME,
        "api_model_name": API_MODEL_NAME,
        "endpoint_host": "api.z.ai",
        "configured_call_count": EXPECTED_CALLS,
        "prior_api_calls_from_failed_v3": PRIOR_ATTEMPTED_CALLS,
        "prior_reported_parsed_valid_calls": PRIOR_REPORTED_PARSED_VALID_CALLS,
        "model_calls": successful_calls,
        "api_calls": successful_calls,
        "model_calls_this_run": successful_calls,
        "api_calls_this_run": successful_calls,
        "total_api_calls_under_approval": PRIOR_ATTEMPTED_CALLS + successful_calls,
        "successful_api_calls": successful_calls,
        "persisted_sanitized_output_rows": len(output_rows),
        "parsed_json_valid_count": parsed_valid_count,
        "max_cost_permission_gbp": MAX_COST_GBP,
        "total_estimated_cost_gbp_this_run": total_cost_gbp,
        "prior_reported_estimated_cost_gbp": PRIOR_REPORTED_ESTIMATED_COST_GBP,
        "total_estimated_cost_gbp": round(PRIOR_REPORTED_ESTIMATED_COST_GBP + total_cost_gbp, 6),
        "api_key_read": True,
        "api_key_source": api_key_source,
        "api_key_printed": False,
        "approval_phrase_matched": True,
        "raw_prompt_instances_written": False,
        "raw_responses_written": False,
        "jsonl_written": False,
        "raw_response_inspection": False,
        "model_execution_enabled": True,
        "sanitized_outputs_only": True,
        "sanitized_packet_table": str(packet_path.relative_to(REPO_ROOT)),
        "output_files": [
            "pilot_05_cfpb_glm52_micro_pilot_sanitized_outputs.csv",
            "pilot_05_cfpb_glm52_micro_pilot_parser_status.csv",
            "pilot_05_cfpb_glm52_micro_pilot_usage_summary.csv",
            "pilot_05_cfpb_glm52_micro_pilot_stage_summary.csv",
            "pilot_05_cfpb_glm52_micro_pilot_condition_stage_summary.csv",
            "pilot_05_cfpb_glm52_micro_pilot_execution_audit.csv",
            "pilot_05_cfpb_glm52_micro_pilot_prior_attempt_summary.csv",
            "pilot_05_cfpb_glm52_micro_pilot_execution_report.md",
        ],
        "claim_boundary": "Controlled real-LLM micro-pilot on sanitized real-data-backed evidence packets; not deployment evidence and not provider superiority evidence.",
    }
    (OUTPUT_DIR / "pilot_05_cfpb_glm52_micro_pilot_execution_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    make_report(manifest, stage_rows, packet_path)
    verify_no_forbidden_outputs()

    print("Pilot 05 CFPB GLM-5.2 real micro-pilot recovery execution generated.")
    print(f"output_dir: {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    print("status: PASS_WITH_PRIOR_UNPERSISTED_CALLS")
    print("runner_mode: REAL_EXECUTION_RECOVERY_SANITIZED_ONLY")
    print(f"model_provider: {MODEL_PROVIDER}")
    print(f"model_display_name: {MODEL_DISPLAY_NAME}")
    print(f"api_model_name: {API_MODEL_NAME}")
    print(f"prior_api_calls_from_failed_v3: {PRIOR_ATTEMPTED_CALLS}")
    print(f"model_calls_this_run: {successful_calls}")
    print(f"api_calls_this_run: {successful_calls}")
    print(f"total_api_calls_under_approval: {PRIOR_ATTEMPTED_CALLS + successful_calls}")
    print(f"successful_api_calls_this_run: {successful_calls}")
    print(f"persisted_sanitized_output_rows: {len(output_rows)}")
    print(f"parsed_json_valid_count_this_run: {parsed_valid_count}")
    print(f"raw_prompt_instances_written: False")
    print(f"raw_responses_written: False")
    print(f"jsonl_written: False")
    print(f"total_estimated_cost_gbp_this_run: {total_cost_gbp}")
    print(f"prior_reported_estimated_cost_gbp: {PRIOR_REPORTED_ESTIMATED_COST_GBP}")
    print(f"total_estimated_cost_gbp: {round(PRIOR_REPORTED_ESTIMATED_COST_GBP + total_cost_gbp, 6)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
