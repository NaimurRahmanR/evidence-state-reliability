from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

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
from src.pilot_03_parser import DECISION_STAGE, parse_and_validate_raw_response
from src.pilot_03_prompts import build_decision_prompt_record
from src.pilot_03_tasks import generate_pilot_03_tasks


OUTPUT_DIR = Path("results/pilot_03_real_llm_smoke")
SMOKE_TEST_VERSION = "pilot_03_zai_one_task_smoke_v1"


def _now_utc() -> str:
    """Return a compact UTC timestamp for call records."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _make_decision_payload(model: str, prompt_text: str) -> dict[str, Any]:
    """Create a single decision-stage Z.ai payload for Pilot 03 smoke testing."""
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


def _make_call_record(
    *,
    task_id: str,
    task_type: str,
    provider: str,
    model_name: str,
    prompt_version: str,
    prompt_text: str,
    raw_response_text: str,
    parsed_response: dict[str, Any],
    valid_schema: bool,
    parse_errors: list[str],
    usage: dict[str, Any],
    run_id: str,
) -> Pilot03LLMCallRecord:
    """Create one Pilot 03 call record from a real Z.ai smoke-test response."""
    error = None if valid_schema else "; ".join(parse_errors)

    return Pilot03LLMCallRecord(
        call_id=f"P03-GLM-SMOKE-{uuid4().hex[:12]}",
        task_id=task_id,
        task_type=task_type,
        stage=DECISION_STAGE,
        client_mode=REAL_CLIENT_MODE,
        provider=provider,
        model_name=model_name,
        dry_run=False,
        prompt_version=prompt_version,
        prompt_text=prompt_text,
        raw_response_text=raw_response_text,
        parsed_response=parsed_response,
        error=error,
        metadata={
            "smoke_test_version": SMOKE_TEST_VERSION,
            "run_id": run_id,
            "endpoint": ZAI_CHAT_COMPLETIONS_URL,
            "usage": usage,
            "safe_wording": "observed result under current Pilot 03 one-task GLM-5.2 smoke-test conditions",
            "scope_limitation": "one decision-stage smoke test only; not a Pilot 03 real LLM experiment",
        },
        created_at_utc=_now_utc(),
    )


def run_one_task_smoke(
    *,
    env_path: Path,
    confirm_real_llm_call: bool,
    timeout_seconds: int,
) -> int:
    """Run one guarded GLM-5.2 decision-stage smoke test."""
    config = load_pilot_03_real_llm_config(env_path)
    safe_summary = summarise_config_safely(config)

    print("Pilot 03 Z.ai one-task smoke test")
    print("=================================")
    print("Safe config summary:")
    print(safe_summary)
    print()

    if not config.real_llm_enabled:
        print("SKIPPED: PILOT03_REAL_LLM_ENABLED is false.")
        print("No real LLM call was made.")
        return 0

    if not confirm_real_llm_call:
        print("SKIPPED: --confirm-real-llm-call was not provided.")
        print("No real LLM call was made.")
        return 0

    if config.provider != "zai":
        print(f"SKIPPED: provider is {config.provider!r}, not 'zai'.")
        print("No real LLM call was made.")
        return 0

    env_file_values = load_env_file(env_path)
    api_key = _get_secret("ZAI_API_KEY", env_file_values)

    if not api_key:
        print("FAILED: ZAI_API_KEY is not available.")
        print("No real LLM call was made.")
        return 1

    task = generate_pilot_03_tasks(n_tasks=1)[0]
    prompt_record = build_decision_prompt_record(task)
    payload = _make_decision_payload(model=config.model, prompt_text=prompt_record.prompt_text)

    run_id = make_pilot_03_run_id(prefix="pilot_03_zai_one_task_smoke")

    print("Making one guarded real Z.ai / GLM-5.2 decision-stage smoke-test call.")
    print("API key value will not be printed.")
    print(f"model: {config.model}")
    print(f"endpoint: {ZAI_CHAT_COMPLETIONS_URL}")
    print(f"task_id: {task.task_id}")
    print(f"gold_decision: {task.gold_decision}")
    print(f"run_id: {run_id}")
    print()

    try:
        response_json = _post_zai_chat_completion(
            api_key=api_key,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
    except Pilot03ZAIConnectionCheckError as exc:
        print(str(exc))
        print()
        print("Safe wording:")
        print("observed failed Z.ai one-task smoke-test attempt under current Pilot 03 conditions")
        return 1

    raw_response_text = _extract_response_text(response_json)
    usage = response_json.get("usage", {})
    if not isinstance(usage, dict):
        usage = {"raw_usage": usage}

    parsed = parse_and_validate_raw_response(
        call_id=f"{run_id}_decision_preview",
        task_id=task.task_id,
        stage=DECISION_STAGE,
        raw_response_text=raw_response_text,
    )

    call_record = _make_call_record(
        task_id=task.task_id,
        task_type=task.task_type,
        provider=config.provider,
        model_name=config.model,
        prompt_version=prompt_record.prompt_version,
        prompt_text=prompt_record.prompt_text,
        raw_response_text=raw_response_text,
        parsed_response=parsed.parsed_response,
        valid_schema=parsed.valid_schema,
        parse_errors=parsed.errors,
        usage=usage,
        run_id=run_id,
    )

    paths = write_pilot_03_raw_response_logs(
        records=[call_record],
        output_dir=OUTPUT_DIR,
        run_id=run_id,
        extra_summary={
            "smoke_test_version": SMOKE_TEST_VERSION,
            "provider": config.provider,
            "model": config.model,
            "task_id": task.task_id,
            "gold_decision": task.gold_decision,
            "stage": DECISION_STAGE,
            "valid_json": parsed.valid_json,
            "valid_schema": parsed.valid_schema,
            "parse_errors": parsed.errors,
            "usage": usage,
            "safe_wording": "observed result under current Pilot 03 one-task GLM-5.2 smoke-test conditions",
            "scope_limitation": "one decision-stage smoke test only; not a Pilot 03 real LLM experiment",
        },
    )

    print("Smoke test completed.")
    print(f"valid_json: {parsed.valid_json}")
    print(f"valid_schema: {parsed.valid_schema}")
    print(f"errors: {parsed.errors}")
    print(f"parsed_response: {parsed.parsed_response}")
    print(f"usage: {usage}")
    print()
    print("Output files:")
    for name, path in paths.items():
        print(f"{name}: {path}")
    print()
    print("Safe wording:")
    print("observed result under current Pilot 03 one-task GLM-5.2 smoke-test conditions")
    print()
    print("Scope limitation:")
    print("This is one decision-stage smoke test only. It is not a Pilot 03 real LLM experiment.")

    return 0 if parsed.valid_schema else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded Pilot 03 one-task Z.ai / GLM-5.2 smoke test."
    )
    parser.add_argument(
        "--env-path",
        default=str(DEFAULT_ENV_PATH),
        help="Path to local .env file. Default: .env",
    )
    parser.add_argument(
        "--confirm-real-llm-call",
        action="store_true",
        help="Required to make one real Z.ai API call.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="HTTP timeout in seconds. Default: 60",
    )

    args = parser.parse_args()

    return run_one_task_smoke(
        env_path=Path(args.env_path),
        confirm_real_llm_call=args.confirm_real_llm_call,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    sys.exit(main())