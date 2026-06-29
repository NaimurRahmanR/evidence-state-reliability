from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.pilot_03_config import (
    DEFAULT_ENV_PATH,
    load_env_file,
    load_pilot_03_real_llm_config,
    summarise_config_safely,
)


ZAI_CHAT_COMPLETIONS_URL = "https://api.z.ai/api/paas/v4/chat/completions"


class Pilot03ZAIConnectionCheckError(RuntimeError):
    """Clean connection-check error that should not expose API keys."""


def _get_secret(name: str, env_file_values: dict[str, str]) -> str | None:
    """Read a secret value without printing it."""
    import os

    value = os.environ.get(name) or env_file_values.get(name)
    if value is None:
        return None

    value = value.strip()
    return value if value else None


def _make_zai_connection_payload(model: str) -> dict[str, Any]:
    """Create the smallest useful Z.ai connection-check payload."""
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: pilot03_connection_ok",
            }
        ],
        "stream": False,
        "do_sample": False,
    }


def _safe_json_loads(text: str) -> dict[str, Any]:
    """Parse JSON response text safely."""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"raw_non_json_response_prefix": text[:500]}

    return parsed if isinstance(parsed, dict) else {"raw_json_response": parsed}


def _summarise_zai_error(status_code: int, error_body: str) -> str:
    """Create a clean, short, key-safe Z.ai error message."""
    parsed = _safe_json_loads(error_body)
    error = parsed.get("error")

    if isinstance(error, dict):
        code = error.get("code", "unknown")
        message = error.get("message", "unknown")
    else:
        code = "unknown"
        message = error_body[:500]

    if status_code == 429 and "balance" in str(message).lower():
        return (
            "Z.ai connection check failed safely.\n"
            f"status: {status_code}\n"
            f"provider_error_code: {code}\n"
            f"provider_message: {message}\n"
            "interpretation: The API key reached Z.ai, but the account has insufficient balance "
            "or no active resource package.\n"
            "No successful real LLM response was produced."
        )

    return (
        "Z.ai connection check failed safely.\n"
        f"status: {status_code}\n"
        f"provider_error_code: {code}\n"
        f"provider_message: {message}\n"
        "No successful real LLM response was produced."
    )


def _post_zai_chat_completion(
    api_key: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Call Z.ai chat completions once.

    This function must never print the API key.
    """
    request_body = json.dumps(payload).encode("utf-8")

    request = Request(
        ZAI_CHAT_COMPLETIONS_URL,
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return json.loads(response_text)
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise Pilot03ZAIConnectionCheckError(
            _summarise_zai_error(exc.code, error_body)
        ) from exc
    except URLError as exc:
        raise Pilot03ZAIConnectionCheckError(
            "Z.ai connection check failed safely.\n"
            f"connection_error: {exc}\n"
            "No successful real LLM response was produced."
        ) from exc
    except json.JSONDecodeError as exc:
        raise Pilot03ZAIConnectionCheckError(
            "Z.ai connection check failed safely.\n"
            "reason: response was not valid JSON.\n"
            "No successful real LLM response was produced."
        ) from exc


def _extract_response_text(response_json: dict[str, Any]) -> str:
    """Extract assistant text from a Z.ai OpenAI-compatible response."""
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""


def run_connection_check(
    *,
    env_path: Path,
    confirm_real_llm_call: bool,
    timeout_seconds: int,
) -> int:
    """Run a guarded Z.ai connection check."""
    config = load_pilot_03_real_llm_config(env_path)
    safe_summary = summarise_config_safely(config)

    print("Pilot 03 Z.ai connection check")
    print("==============================")
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

    payload = _make_zai_connection_payload(config.model)

    print("Making one tiny real Z.ai API call.")
    print("API key value will not be printed.")
    print(f"model: {config.model}")
    print(f"endpoint: {ZAI_CHAT_COMPLETIONS_URL}")
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
        print("observed failed Z.ai connection-check attempt under current Pilot 03 real LLM connection-check conditions")
        return 1

    response_text = _extract_response_text(response_json)
    usage = response_json.get("usage", {})

    print("Connection check completed.")
    print(f"response_text: {response_text!r}")
    print(f"usage: {usage}")
    print()
    print("Safe wording:")
    print("observed result under current Pilot 03 real LLM connection-check conditions")

    if "pilot03_connection_ok" not in response_text:
        print()
        print("WARNING: Connection worked, but the response text did not exactly match the expected token.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded Pilot 03 Z.ai real LLM connection check."
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
        default=30,
        help="HTTP timeout in seconds. Default: 30",
    )

    args = parser.parse_args()

    return run_connection_check(
        env_path=Path(args.env_path),
        confirm_real_llm_call=args.confirm_real_llm_call,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    sys.exit(main())