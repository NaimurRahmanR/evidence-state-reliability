from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from experiments.pilot_03_dry_run_runner import (
    CONDITION_ORIGINAL,
    DEFAULT_CONDITIONS,
    get_visible_evidence_unit_ids_for_condition,
)
from experiments.pilot_03_zai_connection_check import (
    Pilot03ZAIConnectionCheckError,
    ZAI_CHAT_COMPLETIONS_URL,
    _extract_response_text,
    _get_secret,
    _post_zai_chat_completion,
)
from src.pilot_03_config import (
    DEFAULT_ENV_PATH,
    load_env_file,
    load_pilot_03_real_llm_config,
    summarise_config_safely,
)
from src.pilot_03_llm_client import Pilot03LLMCallRecord, REAL_CLIENT_MODE
from src.pilot_03_logging import make_pilot_03_run_id, write_pilot_03_raw_response_logs
from src.pilot_03_parser import (
    AUDIT_STAGE,
    DECISION_STAGE,
    ESCALATION_STAGE,
    Pilot03ParsedResponse,
    parse_and_validate_raw_response,
    summarise_parsed_responses,
)
from src.pilot_03_prompts import (
    Pilot03PromptRecord,
    build_audit_prompt_record,
    build_decision_prompt_record,
    build_escalation_prompt_record,
)
from src.pilot_03_tasks import Pilot03Task, generate_pilot_03_tasks, summarise_pilot_03_tasks


OUTPUT_DIR = Path("results/pilot_03_real_llm_analysis")
REAL_CHAIN_RUN_VERSION = "pilot_03_real_llm_small_chain_run_v5"
TASK_ID_PATTERN = re.compile(r"^P03-T(?P<number>\d{4})$")
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
SUPPORTED_PROVIDERS = {"zai", "anthropic"}


@dataclass(frozen=True)
class Pilot03RealChainResult:
    """One real GLM chain result for one task under one evidence condition."""

    task_id: str
    task_type: str
    condition: str
    gold_decision: str
    visible_evidence_unit_ids: list[str]
    decision_call: Pilot03LLMCallRecord
    audit_call: Pilot03LLMCallRecord
    escalation_call: Pilot03LLMCallRecord


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _make_visible_evidence_text(task: Pilot03Task, visible_evidence_unit_ids: list[str]) -> str:
    """Build the evidence text actually visible to the real model."""
    evidence_by_id = {unit.unit_id: unit for unit in task.original_evidence_units}

    lines: list[str] = []
    for unit_id in visible_evidence_unit_ids:
        unit = evidence_by_id[unit_id]
        lines.append(f"- {unit.unit_id}: {unit.text}")

    return "\n".join(lines)


def _make_zai_payload(model: str, prompt_text: str) -> dict[str, Any]:
    """Create one Z.ai chat-completions payload."""
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
        "stream": False,
        "do_sample": False,
    }


def _make_anthropic_payload(model: str, prompt_text: str) -> dict[str, Any]:
    """Create one Anthropic Messages API payload.

    Sampling parameters are intentionally omitted for Claude Opus 4.8 compatibility
    and to keep the comparison controlled by the shared Pilot 03 prompts.
    """
    return {
        "model": model,
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
    }


def _post_zai_with_timeout_retry(
    *,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: int,
) -> tuple[dict[str, Any], int]:
    """Post to Z.ai and retry read timeouts only.

    Provider errors such as insufficient balance should not be hidden by retries.
    """
    attempts = 0

    while True:
        attempts += 1

        try:
            response_json = _post_zai_chat_completion(
                api_key=api_key,
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
            return response_json, attempts

        except Exception as exc:
            if attempts > max_retries:
                raise Pilot03ZAIConnectionCheckError(
                    "Z.ai real chain stage failed safely.\n"
                    f"reason: read timeout after {attempts} attempt(s)\n"
                    f"timeout_seconds_per_attempt: {timeout_seconds}\n"
                    "Partial completed chains, if any, will be saved."
                ) from exc

            print(
                f"WARNING: Z.ai retryable API/network error on attempt {attempts}. "
                f"Retrying after {retry_sleep_seconds} second(s)."
            )
            time.sleep(retry_sleep_seconds)


def _safe_json_loads(text: str) -> dict[str, Any]:
    """Parse a provider JSON response safely."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_non_json_response_prefix": text[:500]}

    return parsed if isinstance(parsed, dict) else {"raw_json_response": parsed}


def _summarise_anthropic_error(status_code: int, error_body: str) -> str:
    """Create a clean, key-safe Anthropic error message."""
    parsed = _safe_json_loads(error_body)
    error = parsed.get("error")

    if isinstance(error, dict):
        error_type = error.get("type", "unknown")
        message = error.get("message", "unknown")
    else:
        error_type = "unknown"
        message = error_body[:500]

    return (
        "Anthropic real chain stage failed safely.\n"
        f"status: {status_code}\n"
        f"provider_error_type: {error_type}\n"
        f"provider_message: {message}\n"
        "No API key value was printed."
    )


def _post_anthropic_messages(
    *,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Call the Anthropic Messages API once.

    This function must never print the API key.
    """
    request_body = json.dumps(payload).encode("utf-8")

    request = Request(
        ANTHROPIC_MESSAGES_URL,
        data=request_body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return json.loads(response_text)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise Pilot03ZAIConnectionCheckError(
            _summarise_anthropic_error(exc.code, error_body)
        ) from exc
    except URLError as exc:
        raise Pilot03ZAIConnectionCheckError(
            "Anthropic real chain stage failed safely.\n"
            f"connection_error: {exc}\n"
            "No successful real LLM response was produced."
        ) from exc
    except json.JSONDecodeError as exc:
        raise Pilot03ZAIConnectionCheckError(
            "Anthropic real chain stage failed safely.\n"
            "reason: response was not valid JSON.\n"
            "No successful real LLM response was produced."
        ) from exc


def _post_anthropic_with_timeout_retry(
    *,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: int,
) -> tuple[dict[str, Any], int]:
    """Post to Anthropic and retry API/network failures conservatively."""
    attempts = 0

    while True:
        attempts += 1

        try:
            response_json = _post_anthropic_messages(
                api_key=api_key,
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
            return response_json, attempts

        except Pilot03ZAIConnectionCheckError:
            raise

        except Exception as exc:
            if attempts > max_retries:
                raise Pilot03ZAIConnectionCheckError(
                    "Anthropic real chain stage failed safely.\n"
                    f"reason: retry limit reached after {attempts} attempt(s)\n"
                    f"timeout_seconds_per_attempt: {timeout_seconds}\n"
                    "Partial completed chains, if any, will be saved."
                ) from exc

            print(
                f"WARNING: Anthropic retryable API/network error on attempt {attempts}. "
                f"Retrying after {retry_sleep_seconds} second(s)."
            )
            time.sleep(retry_sleep_seconds)


def _extract_anthropic_response_text(response_json: dict[str, Any]) -> str:
    """Extract assistant text from an Anthropic Messages API response."""
    content = response_json.get("content")
    if not isinstance(content, list):
        return ""

    text_parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            text_parts.append(block["text"])

    return "\n".join(part.strip() for part in text_parts if part.strip()).strip()


def _normalise_usage(response_json: dict[str, Any]) -> dict[str, Any]:
    """Return provider usage and add total_tokens when possible."""
    usage = response_json.get("usage", {})
    if not isinstance(usage, dict):
        return {"raw_usage": usage}

    usage = dict(usage)
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        usage.setdefault("total_tokens", input_tokens + output_tokens)

    return usage


def _make_provider_payload(*, provider: str, model: str, prompt_text: str) -> dict[str, Any]:
    """Create the correct provider payload for one stage call."""
    if provider == "zai":
        return _make_zai_payload(model=model, prompt_text=prompt_text)

    if provider == "anthropic":
        return _make_anthropic_payload(model=model, prompt_text=prompt_text)

    raise ValueError(f"Unsupported provider: {provider!r}")


def _post_provider_with_timeout_retry(
    *,
    provider: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: int,
) -> tuple[dict[str, Any], int]:
    """Post to the selected provider with guarded retry behaviour."""
    if provider == "zai":
        return _post_zai_with_timeout_retry(
            api_key=api_key,
            payload=payload,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_sleep_seconds=retry_sleep_seconds,
        )

    if provider == "anthropic":
        return _post_anthropic_with_timeout_retry(
            api_key=api_key,
            payload=payload,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_sleep_seconds=retry_sleep_seconds,
        )

    raise ValueError(f"Unsupported provider: {provider!r}")


def _extract_provider_response_text(*, provider: str, response_json: dict[str, Any]) -> str:
    """Extract assistant text from the selected provider response."""
    if provider == "zai":
        return _extract_response_text(response_json)

    if provider == "anthropic":
        return _extract_anthropic_response_text(response_json)

    raise ValueError(f"Unsupported provider: {provider!r}")


def _safe_wording_for_provider(provider: str) -> str:
    """Return conservative wording for the current provider run."""
    if provider == "anthropic":
        return "observed comparison subset under current Pilot 03 real LLM experimental conditions"

    return "observed result under current Pilot 03 real LLM experimental conditions"


def _make_call_record(
    *,
    task: Pilot03Task,
    condition: str,
    visible_evidence_unit_ids: list[str],
    stage: str,
    provider: str,
    model_name: str,
    prompt_record: Pilot03PromptRecord,
    raw_response_text: str,
    parsed: Pilot03ParsedResponse,
    usage: dict[str, Any],
    run_id: str,
    attempts: int,
) -> Pilot03LLMCallRecord:
    """Create one standard Pilot 03 call record for a real provider response."""
    return Pilot03LLMCallRecord(
        call_id=f"P03-{provider.upper()}-CHAIN-{uuid4().hex[:12]}",
        task_id=task.task_id,
        task_type=task.task_type,
        stage=stage,
        client_mode=REAL_CLIENT_MODE,
        provider=provider,
        model_name=model_name,
        dry_run=False,
        prompt_version=prompt_record.prompt_version,
        prompt_text=prompt_record.prompt_text,
        raw_response_text=raw_response_text,
        parsed_response=parsed.parsed_response,
        error=None if parsed.valid_schema else "; ".join(parsed.errors),
        metadata={
            "run_version": REAL_CHAIN_RUN_VERSION,
            "run_id": run_id,
            "condition": condition,
            "visible_evidence_unit_ids": visible_evidence_unit_ids,
            "gold_decision": task.gold_decision,
            "endpoint": ANTHROPIC_MESSAGES_URL if provider == "anthropic" else ZAI_CHAT_COMPLETIONS_URL,
            "usage": usage,
            "attempts": attempts,
            "valid_json": parsed.valid_json,
            "valid_schema": parsed.valid_schema,
            "parse_errors": parsed.errors,
            "safe_wording": _safe_wording_for_provider(provider),
        },
        created_at_utc=_now_utc(),
    )


def _run_stage_call(
    *,
    api_key: str,
    task: Pilot03Task,
    condition: str,
    visible_evidence_unit_ids: list[str],
    stage: str,
    provider: str,
    model_name: str,
    prompt_record: Pilot03PromptRecord,
    run_id: str,
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: int,
) -> tuple[Pilot03LLMCallRecord, Pilot03ParsedResponse]:
    """Run one real provider stage call and parse/validate the raw response."""
    payload = _make_provider_payload(
        provider=provider,
        model=model_name,
        prompt_text=prompt_record.prompt_text,
    )

    response_json, attempts = _post_provider_with_timeout_retry(
        provider=provider,
        api_key=api_key,
        payload=payload,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        retry_sleep_seconds=retry_sleep_seconds,
    )

    raw_response_text = _extract_provider_response_text(
        provider=provider,
        response_json=response_json,
    )
    usage = _normalise_usage(response_json)

    preview_call_id = f"{run_id}_{task.task_id}_{condition}_{stage}"
    parsed = parse_and_validate_raw_response(
        call_id=preview_call_id,
        task_id=task.task_id,
        stage=stage,
        raw_response_text=raw_response_text,
    )

    call_record = _make_call_record(
        task=task,
        condition=condition,
        visible_evidence_unit_ids=visible_evidence_unit_ids,
        stage=stage,
        provider=provider,
        model_name=model_name,
        prompt_record=prompt_record,
        raw_response_text=raw_response_text,
        parsed=parsed,
        usage=usage,
        run_id=run_id,
        attempts=attempts,
    )

    return call_record, parsed


def _flatten_call_records(results: list[Pilot03RealChainResult]) -> list[Pilot03LLMCallRecord]:
    records: list[Pilot03LLMCallRecord] = []
    for result in results:
        records.extend([result.decision_call, result.audit_call, result.escalation_call])
    return records


def _summarise_real_chain_results(
    *,
    results: list[Pilot03RealChainResult],
    parsed_responses: list[Pilot03ParsedResponse],
    saved_call_records: list[Pilot03LLMCallRecord] | None = None,
    n_tasks_requested: int,
    selected_task_ids: list[str],
    requested_task_ids: list[str] | None,
    generated_task_count: int,
    conditions: list[str],
    run_status: str,
    failure_reason: str | None,
) -> dict[str, Any]:
    """Create a compact real-chain summary without overclaiming."""
    completed_call_records = _flatten_call_records(results)
    saved_records = list(saved_call_records) if saved_call_records is not None else list(completed_call_records)
    completed_call_ids = {record.call_id for record in completed_call_records}
    partial_stage_call_records = [
        record for record in saved_records if record.call_id not in completed_call_ids
    ]

    # Metrics derived from completed chains only.
    call_records = completed_call_records

    condition_counts = Counter(result.condition for result in results)
    gold_decisions = Counter(result.gold_decision for result in results)

    decision_correct = Counter()
    escalation_correct = Counter()
    audit_passed = Counter()
    stage_valid_schema: dict[str, dict[str, int]] = {}

    for stage in [DECISION_STAGE, AUDIT_STAGE, ESCALATION_STAGE]:
        stage_records = [record for record in call_records if record.stage == stage]
        stage_valid_schema[stage] = {
            "valid": sum(1 for record in stage_records if record.error is None),
            "invalid": sum(1 for record in stage_records if record.error is not None),
        }

    saved_stage_valid_schema: dict[str, dict[str, int]] = {}
    for stage in [DECISION_STAGE, AUDIT_STAGE, ESCALATION_STAGE]:
        stage_records = [record for record in saved_records if record.stage == stage]
        saved_stage_valid_schema[stage] = {
            "valid": sum(1 for record in stage_records if record.error is None),
            "invalid": sum(1 for record in stage_records if record.error is not None),
        }

    total_tokens = 0
    for record in call_records:
        usage = record.metadata.get("usage", {})
        if isinstance(usage, dict) and isinstance(usage.get("total_tokens"), int):
            total_tokens += usage["total_tokens"]

    total_tokens_saved = 0
    for record in saved_records:
        usage = record.metadata.get("usage", {})
        if isinstance(usage, dict) and isinstance(usage.get("total_tokens"), int):
            total_tokens_saved += usage["total_tokens"]

    for result in results:
        decision_value = result.decision_call.parsed_response.get("final_decision")
        escalation_value = result.escalation_call.parsed_response.get("final_decision")
        audit_value = result.audit_call.parsed_response.get("audit_passed")

        decision_correct[str(decision_value == result.gold_decision)] += 1
        escalation_correct[str(escalation_value == result.gold_decision)] += 1
        audit_passed[str(audit_value)] += 1

    return {
        "run_version": REAL_CHAIN_RUN_VERSION,
        "scope": "small controlled real LLM chain run",
        "run_status": run_status,
        "failure_reason": failure_reason,
        "safe_wording": _safe_wording_for_provider(saved_records[0].provider if saved_records else "zai"),
        "n_tasks_requested": n_tasks_requested,
        "generated_task_count": generated_task_count,
        "requested_task_ids": requested_task_ids,
        "selected_task_ids": selected_task_ids,
        "n_tasks_selected": len(selected_task_ids),
        "conditions": conditions,
        "n_chain_results_completed": len(results),
        "n_call_records_completed": len(call_records),
        "n_call_records_saved": len(saved_records),
        "n_call_records_in_completed_chains": len(completed_call_records),
        "n_partial_stage_call_records": len(partial_stage_call_records),
        "partial_stage_call_records": [
            {
                "task_id": record.task_id,
                "condition": record.metadata.get("condition"),
                "stage": record.stage,
                "valid_json": record.metadata.get("valid_json"),
                "valid_schema": record.metadata.get("valid_schema"),
                "note": "Completed stage call only; not a complete chain result.",
            }
            for record in partial_stage_call_records
        ],
        "partial_stage_call_records_note": (
            "Partial stage call records are completed stage calls saved from an interrupted "
            "or failed run before a full decision-audit-escalation chain was completed. "
            "They are not counted as completed chain results."
        ),
        "expected_call_count": len(selected_task_ids) * len(conditions) * 3,
        "condition_counts": dict(condition_counts),
        "gold_decisions": dict(gold_decisions),
        "stage_valid_schema": stage_valid_schema,
        "saved_stage_valid_schema": saved_stage_valid_schema,
        "decision_correct": dict(decision_correct),
        "escalation_correct": dict(escalation_correct),
        "audit_passed": dict(audit_passed),
        "total_tokens": total_tokens,
        "total_tokens_saved": total_tokens_saved,
        "parser_summary": summarise_parsed_responses(parsed_responses),
        "parser_summary_scope": (
            "All saved parsed stage calls, including partial stage records if a run "
            "was interrupted before a complete chain was formed."
        ),
        "completed_chain_metrics_scope": (
            "Decision correctness, escalation correctness, audit pass counts, and "
            "condition counts are computed from completed chains only."
        ),
        "scope_limitation": (
            "This is a small controlled real LLM run. It should not be generalised "
            "beyond the current Pilot 03 setup, model, prompts, tasks, and evidence conditions."
        ),
    }


def _write_outputs(
    *,
    records: list[Pilot03LLMCallRecord],
    results: list[Pilot03RealChainResult],
    parsed_responses: list[Pilot03ParsedResponse],
    tasks: list[Pilot03Task],
    run_id: str,
    n_tasks_requested: int,
    selected_task_ids: list[str],
    requested_task_ids: list[str] | None,
    generated_task_count: int,
    conditions: list[str],
    run_status: str,
    failure_reason: str | None,
) -> dict[str, Path]:
    """Write completed records, including partial records after failure."""
    summary = _summarise_real_chain_results(
        results=results,
        parsed_responses=parsed_responses,
        saved_call_records=records,
        n_tasks_requested=n_tasks_requested,
        selected_task_ids=selected_task_ids,
        requested_task_ids=requested_task_ids,
        generated_task_count=generated_task_count,
        conditions=conditions,
        run_status=run_status,
        failure_reason=failure_reason,
    )

    return write_pilot_03_raw_response_logs(
        records=records,
        output_dir=OUTPUT_DIR,
        run_id=run_id,
        extra_summary={
            "task_summary": summarise_pilot_03_tasks(tasks),
            "real_chain_summary": summary,
        },
    )


def _normalise_conditions(condition_args: list[str]) -> list[str]:
    """Convert CLI condition args into validated Pilot 03 condition names."""
    if not condition_args or any(item.lower() == "all" for item in condition_args):
        return list(DEFAULT_CONDITIONS)

    valid = set(DEFAULT_CONDITIONS)
    unknown = [condition for condition in condition_args if condition not in valid]
    if unknown:
        raise ValueError(f"Unknown condition(s): {unknown}. Valid conditions: {sorted(valid)} or all")

    return condition_args


def _task_number_from_task_id(task_id: str) -> int:
    """Return the integer task number from a canonical Pilot 03 task id."""
    match = TASK_ID_PATTERN.fullmatch(task_id)

    if not match:
        raise ValueError(f"Invalid task id: {task_id!r}. Expected format like P03-T0002.")

    task_number = int(match.group("number"))
    if task_number <= 0:
        raise ValueError(f"Invalid task id: {task_id!r}. Task number must be positive.")

    return task_number


def _normalise_task_ids(task_id_args: list[str] | None) -> list[str] | None:
    """Validate optional requested Pilot 03 task ids."""
    if not task_id_args:
        return None

    normalised: list[str] = []
    seen: set[str] = set()

    for raw_task_id in task_id_args:
        task_id = raw_task_id.strip()

        if not task_id:
            raise ValueError("Empty task id provided.")

        _task_number_from_task_id(task_id)

        if task_id not in seen:
            normalised.append(task_id)
            seen.add(task_id)

    return normalised


def _select_tasks(
    *,
    n_tasks: int,
    requested_task_ids: list[str] | None,
) -> tuple[list[Pilot03Task], int]:
    """Generate and optionally filter tasks by explicit task id."""
    if requested_task_ids is None:
        return generate_pilot_03_tasks(n_tasks=n_tasks), n_tasks

    max_requested_task_number = max(_task_number_from_task_id(task_id) for task_id in requested_task_ids)
    generated_task_count = max(n_tasks, max_requested_task_number)
    generated_tasks = generate_pilot_03_tasks(n_tasks=generated_task_count)
    tasks_by_id = {task.task_id: task for task in generated_tasks}

    missing = [task_id for task_id in requested_task_ids if task_id not in tasks_by_id]
    if missing:
        raise ValueError(
            f"Requested task id(s) were not generated: {missing}. "
            f"Generated task count: {generated_task_count}."
        )

    selected_tasks = [tasks_by_id[task_id] for task_id in requested_task_ids]
    return selected_tasks, generated_task_count


def _make_run_prefix(
    *,
    provider: str,
    selected_task_ids: list[str],
    requested_task_ids: list[str] | None,
) -> str:
    """Create a compact run id prefix."""
    safe_provider = provider.lower().replace("-", "_")
    if requested_task_ids is None:
        return f"pilot_03_{safe_provider}_small_chain_n{len(selected_task_ids)}"

    if len(selected_task_ids) == 1:
        safe_task_id = selected_task_ids[0].lower().replace("-", "_")
        return f"pilot_03_{safe_provider}_small_chain_{safe_task_id}"

    return f"pilot_03_{safe_provider}_small_chain_selected{len(selected_task_ids)}"


def run_small_chain(
    *,
    env_path: Path,
    confirm_real_llm_call: bool,
    n_tasks: int,
    requested_task_ids: list[str] | None,
    conditions: list[str],
    timeout_seconds: int,
    max_retries: int,
    retry_sleep_seconds: int,
) -> int:
    """Run a small guarded real LLM Pilot 03 chain."""
    config = load_pilot_03_real_llm_config(env_path)
    safe_summary = summarise_config_safely(config)

    print("Pilot 03 small real LLM chain run")
    print("=================================")
    print("Safe config summary:")
    print(safe_summary)
    print()

    if n_tasks <= 0:
        print("FAILED: --n-tasks must be positive.")
        return 1

    if not config.real_llm_enabled:
        print("SKIPPED: PILOT03_REAL_LLM_ENABLED is false.")
        print("No real LLM call was made.")
        return 0

    if not confirm_real_llm_call:
        print("SKIPPED: --confirm-real-llm-call was not provided.")
        print("No real LLM call was made.")
        return 0

    if config.provider not in SUPPORTED_PROVIDERS:
        print(f"SKIPPED: provider is {config.provider!r}, not one of {sorted(SUPPORTED_PROVIDERS)}.")
        print("No real LLM call was made.")
        return 0

    env_file_values = load_env_file(env_path)

    if config.provider == "anthropic":
        api_key = _get_secret("ANTHROPIC_API_KEY", env_file_values)
        model_name = config.comparison_model
        endpoint = ANTHROPIC_MESSAGES_URL
    else:
        api_key = _get_secret("ZAI_API_KEY", env_file_values)
        model_name = config.model
        endpoint = ZAI_CHAT_COMPLETIONS_URL

    if not api_key:
        required_secret = "ANTHROPIC_API_KEY" if config.provider == "anthropic" else "ZAI_API_KEY"
        print(f"FAILED: {required_secret} is not available.")
        print("No real LLM call was made.")
        return 1

    tasks, generated_task_count = _select_tasks(
        n_tasks=n_tasks,
        requested_task_ids=requested_task_ids,
    )
    selected_task_ids = [task.task_id for task in tasks]
    run_prefix = _make_run_prefix(
        provider=config.provider,
        selected_task_ids=selected_task_ids,
        requested_task_ids=requested_task_ids,
    )
    run_id = make_pilot_03_run_id(prefix=run_prefix)

    expected_calls = len(tasks) * len(conditions) * 3

    print(f"Running real {config.provider} Pilot 03 chain calls.")
    print("API key value will not be printed.")
    print(f"model: {model_name}")
    print(f"endpoint: {endpoint}")
    print(f"run_id: {run_id}")
    print(f"n_tasks_requested: {n_tasks}")
    print(f"generated_task_count: {generated_task_count}")
    print(f"requested_task_ids: {requested_task_ids}")
    print(f"selected_task_ids: {selected_task_ids}")
    print(f"conditions: {conditions}")
    print(f"expected_real_calls: {expected_calls}")
    print(f"timeout_seconds_per_attempt: {timeout_seconds}")
    print(f"max_retries_after_first_attempt: {max_retries}")
    print("stages: decision -> audit -> escalation")
    print()

    results: list[Pilot03RealChainResult] = []
    parsed_responses: list[Pilot03ParsedResponse] = []
    call_records: list[Pilot03LLMCallRecord] = []

    try:
        for task in tasks:
            for condition in conditions:
                visible_evidence_unit_ids = get_visible_evidence_unit_ids_for_condition(task, condition)
                evidence_text = _make_visible_evidence_text(task, visible_evidence_unit_ids)

                decision_prompt = build_decision_prompt_record(task=task, evidence_text=evidence_text)
                decision_call, decision_parsed = _run_stage_call(
                    api_key=api_key,
                    task=task,
                    condition=condition,
                    visible_evidence_unit_ids=visible_evidence_unit_ids,
                    stage=DECISION_STAGE,
                    provider=config.provider,
                    model_name=model_name,
                    prompt_record=decision_prompt,
                    run_id=run_id,
                    timeout_seconds=timeout_seconds,
                    max_retries=max_retries,
                    retry_sleep_seconds=retry_sleep_seconds,
                )
                parsed_responses.append(decision_parsed)
                call_records.append(decision_call)

                audit_prompt = build_audit_prompt_record(
                    task=task,
                    decision_json=decision_call.raw_response_text,
                    evidence_text=evidence_text,
                )
                audit_call, audit_parsed = _run_stage_call(
                    api_key=api_key,
                    task=task,
                    condition=condition,
                    visible_evidence_unit_ids=visible_evidence_unit_ids,
                    stage=AUDIT_STAGE,
                    provider=config.provider,
                    model_name=model_name,
                    prompt_record=audit_prompt,
                    run_id=run_id,
                    timeout_seconds=timeout_seconds,
                    max_retries=max_retries,
                    retry_sleep_seconds=retry_sleep_seconds,
                )
                parsed_responses.append(audit_parsed)
                call_records.append(audit_call)

                escalation_prompt = build_escalation_prompt_record(
                    task=task,
                    decision_json=decision_call.raw_response_text,
                    audit_json=audit_call.raw_response_text,
                    evidence_text=evidence_text,
                )
                escalation_call, escalation_parsed = _run_stage_call(
                    api_key=api_key,
                    task=task,
                    condition=condition,
                    visible_evidence_unit_ids=visible_evidence_unit_ids,
                    stage=ESCALATION_STAGE,
                    provider=config.provider,
                    model_name=model_name,
                    prompt_record=escalation_prompt,
                    run_id=run_id,
                    timeout_seconds=timeout_seconds,
                    max_retries=max_retries,
                    retry_sleep_seconds=retry_sleep_seconds,
                )
                parsed_responses.append(escalation_parsed)
                call_records.append(escalation_call)

                result = Pilot03RealChainResult(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    condition=condition,
                    gold_decision=task.gold_decision,
                    visible_evidence_unit_ids=visible_evidence_unit_ids,
                    decision_call=decision_call,
                    audit_call=audit_call,
                    escalation_call=escalation_call,
                )
                results.append(result)

                _write_outputs(
                    records=call_records,
                    results=results,
                    parsed_responses=parsed_responses,
                    tasks=tasks,
                    run_id=run_id,
                    n_tasks_requested=n_tasks,
                    selected_task_ids=selected_task_ids,
                    requested_task_ids=requested_task_ids,
                    generated_task_count=generated_task_count,
                    conditions=conditions,
                    run_status="partial_checkpoint",
                    failure_reason=None,
                )

                print(
                    f"{task.task_id} | condition={condition} | gold={task.gold_decision} | "
                    f"decision={decision_call.parsed_response.get('final_decision')} | "
                    f"audit_passed={audit_call.parsed_response.get('audit_passed')} | "
                    f"escalation={escalation_call.parsed_response.get('final_decision')} | "
                    f"valid=({decision_parsed.valid_schema}, {audit_parsed.valid_schema}, {escalation_parsed.valid_schema})"
                )

    except Pilot03ZAIConnectionCheckError as exc:
        failure_reason = str(exc)
        print()
        print(failure_reason)
        print()
        print("Saving partial completed results before exit.")

        paths = _write_outputs(
            records=call_records,
            results=results,
            parsed_responses=parsed_responses,
            tasks=tasks,
            run_id=run_id,
            n_tasks_requested=n_tasks,
            selected_task_ids=selected_task_ids,
            requested_task_ids=requested_task_ids,
            generated_task_count=generated_task_count,
            conditions=conditions,
            run_status="failed_partial",
            failure_reason=failure_reason,
        )

        print("Partial output files:")
        for name, path in paths.items():
            print(f"{name}: {path}")

        print()
        print("Safe wording:")
        print(f"observed failed {config.provider} real chain attempt under current Pilot 03 conditions")
        return 1

    except KeyboardInterrupt:
        failure_reason = (
            "KeyboardInterrupt received. Saved completed chains and any completed stage "
            "call records available before interruption. Partial stage records are not "
            "completed chain results."
        )
        print()
        print(failure_reason)
        print()
        print("Saving interrupted partial outputs before exit.")

        paths = _write_outputs(
            records=call_records,
            results=results,
            parsed_responses=parsed_responses,
            tasks=tasks,
            run_id=run_id,
            n_tasks_requested=n_tasks,
            selected_task_ids=selected_task_ids,
            requested_task_ids=requested_task_ids,
            generated_task_count=generated_task_count,
            conditions=conditions,
            run_status="interrupted_partial",
            failure_reason=failure_reason,
        )

        print("Interrupted partial output files:")
        for name, path in paths.items():
            print(f"{name}: {path}")

        print()
        print("Safe wording:")
        print(f"observed interrupted partial real {config.provider} run under current Pilot 03 real LLM experimental conditions")
        return 130

    paths = _write_outputs(
        records=call_records,
        results=results,
        parsed_responses=parsed_responses,
        tasks=tasks,
        run_id=run_id,
        n_tasks_requested=n_tasks,
        selected_task_ids=selected_task_ids,
        requested_task_ids=requested_task_ids,
        generated_task_count=generated_task_count,
        conditions=conditions,
        run_status="completed",
        failure_reason=None,
    )

    summary = _summarise_real_chain_results(
        results=results,
        parsed_responses=parsed_responses,
        saved_call_records=call_records,
        n_tasks_requested=n_tasks,
        selected_task_ids=selected_task_ids,
        requested_task_ids=requested_task_ids,
        generated_task_count=generated_task_count,
        conditions=conditions,
        run_status="completed",
        failure_reason=None,
    )

    print()
    print("Small real LLM chain run completed.")
    print(summary)
    print()
    print("Output files:")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print()
    print("Safe wording:")
    print(_safe_wording_for_provider(config.provider))

    invalid_count = sum(1 for parsed in parsed_responses if not parsed.valid_schema)
    return 0 if invalid_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded Pilot 03 small real LLM chain run with Z.ai or Anthropic support."
    )
    parser.add_argument(
        "--env-path",
        default=str(DEFAULT_ENV_PATH),
        help="Path to local .env file. Default: .env",
    )
    parser.add_argument(
        "--confirm-real-llm-call",
        action="store_true",
        help="Required to make real provider API calls.",
    )
    parser.add_argument(
        "--n-tasks",
        type=int,
        default=1,
        help=(
            "Number of Pilot 03 tasks to generate. Default: 1. "
            "If --task-ids is provided, enough tasks are generated to include those ids."
        ),
    )
    parser.add_argument(
        "--task-ids",
        nargs="+",
        default=None,
        help="Optional explicit Pilot 03 task ids to run, for example: P03-T0002",
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=[CONDITION_ORIGINAL],
        help="Evidence conditions to run, or 'all'. Default: original_evidence",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="HTTP timeout per attempt in seconds. Default: 120",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Number of retries after the first attempt for read timeouts. Default: 1",
    )
    parser.add_argument(
        "--retry-sleep-seconds",
        type=int,
        default=5,
        help="Seconds to wait before retrying a timeout. Default: 5",
    )

    args = parser.parse_args()
    conditions = _normalise_conditions(args.conditions)
    requested_task_ids = _normalise_task_ids(args.task_ids)

    return run_small_chain(
        env_path=Path(args.env_path),
        confirm_real_llm_call=args.confirm_real_llm_call,
        n_tasks=args.n_tasks,
        requested_task_ids=requested_task_ids,
        conditions=conditions,
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        retry_sleep_seconds=args.retry_sleep_seconds,
    )


if __name__ == "__main__":
    sys.exit(main())