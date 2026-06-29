from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


DEFAULT_ENV_PATH = Path(".env")

DEFAULT_PROVIDER = "zai"
DEFAULT_MODEL = "glm-5.2"
DEFAULT_COMPARISON_MODEL = "claude-opus-4-8"


@dataclass(frozen=True)
class Pilot03RealLLMConfig:
    """Safe Pilot 03 real LLM configuration.

    This config object must never print or expose raw API keys.
    """

    real_llm_enabled: bool
    provider: str
    model: str
    comparison_model: str
    zai_api_key_present: bool
    anthropic_api_key_present: bool


def _normalise_bool(value: str | None, *, default: bool = False) -> bool:
    """Convert common environment string values into a boolean."""
    if value is None:
        return default

    normalised = value.strip().lower()
    if normalised in {"1", "true", "yes", "y", "on"}:
        return True
    if normalised in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(
        "Invalid boolean value. Use one of: true, false, 1, 0, yes, no, on, off."
    )


def load_env_file(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a local .env file.

    This is intentionally small and dependency-free.

    It ignores:
    - missing .env files
    - blank lines
    - comment lines starting with '#'

    It does not print secrets.
    """
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}

    for line_number, raw_line in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE format.")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if not key:
            raise ValueError(f"Invalid .env line {line_number}: empty key.")

        loaded[key] = value

    return loaded


def _get_config_value(name: str, env_file_values: dict[str, str], default: str | None = None) -> str | None:
    """Read config from real environment first, then .env file, then default."""
    return os.environ.get(name) or env_file_values.get(name) or default


def load_pilot_03_real_llm_config(env_path: Path = DEFAULT_ENV_PATH) -> Pilot03RealLLMConfig:
    """Load Pilot 03 real LLM config without exposing API keys."""
    env_file_values = load_env_file(env_path)

    real_llm_enabled = _normalise_bool(
        _get_config_value("PILOT03_REAL_LLM_ENABLED", env_file_values, "false"),
        default=False,
    )

    provider = _get_config_value("PILOT03_LLM_PROVIDER", env_file_values, DEFAULT_PROVIDER)
    model = _get_config_value("PILOT03_LLM_MODEL", env_file_values, DEFAULT_MODEL)
    comparison_model = _get_config_value(
        "PILOT03_COMPARISON_MODEL",
        env_file_values,
        DEFAULT_COMPARISON_MODEL,
    )

    zai_api_key = _get_config_value("ZAI_API_KEY", env_file_values)
    anthropic_api_key = _get_config_value("ANTHROPIC_API_KEY", env_file_values)

    return Pilot03RealLLMConfig(
        real_llm_enabled=real_llm_enabled,
        provider="" if provider is None else provider.strip(),
        model="" if model is None else model.strip(),
        comparison_model="" if comparison_model is None else comparison_model.strip(),
        zai_api_key_present=bool(zai_api_key and zai_api_key.strip()),
        anthropic_api_key_present=bool(anthropic_api_key and anthropic_api_key.strip()),
    )


def summarise_config_safely(config: Pilot03RealLLMConfig) -> dict[str, object]:
    """Return a safe config summary with no secret values."""
    return {
        "real_llm_enabled": config.real_llm_enabled,
        "provider": config.provider,
        "model": config.model,
        "comparison_model": config.comparison_model,
        "zai_api_key_present": config.zai_api_key_present,
        "anthropic_api_key_present": config.anthropic_api_key_present,
        "api_key_values_printed": False,
    }


if __name__ == "__main__":
    config = load_pilot_03_real_llm_config()
    print("Pilot 03 real LLM config check")
    print("===============================")
    print("No API key values are printed by this script.")
    print(summarise_config_safely(config))