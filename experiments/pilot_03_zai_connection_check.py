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


def _get_secret(name: str, env_file_values: dict[str, str]) -> str | None:
    """Read a secret value without printing it.

    Environment variables should be preferred by the shell/runtime.
    The local .env file is the fallback for development only.
    """
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


def _post_zai_chat_completion(api_key: str, payload: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
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
        raise RuntimeError(
            f"Z.ai HTTP error: status={exc.code}, body={error_body[:500]}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Z.ai connection error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Z.ai response was not valid JSON.") from exc


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

    response_json = _post_zai_chat_completion(
        api_key=api_key,
        payload=payload,
        timeout_seconds=timeout_seconds,
    )

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