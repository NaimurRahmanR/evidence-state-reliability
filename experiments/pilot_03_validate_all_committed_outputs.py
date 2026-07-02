from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALIDATION_COMMANDS = [
    {
        "name": "pilot_03_committed_outputs",
        "command": [
            sys.executable,
            "-m",
            "experiments.pilot_03_validate_committed_outputs",
        ],
        "description": "Validate existing committed Pilot 03 derived outputs.",
    },
    {
        "name": "pilot_03_anthropic_t0020_committed_report",
        "command": [
            sys.executable,
            "-m",
            "experiments.pilot_03_validate_anthropic_t0020_committed_report",
        ],
        "description": "Validate committed Anthropic/Claude T0020 sanitized report outputs.",
    },
]


@dataclass
class ValidationRun:
    name: str
    description: str
    return_code: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.return_code == 0

    def to_json_safe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "return_code": self.return_code,
            "passed": self.passed,
            "stdout_tail": self.stdout.splitlines()[-20:],
            "stderr_tail": self.stderr.splitlines()[-20:],
        }


def _run_command(item: dict[str, Any]) -> ValidationRun:
    completed = subprocess.run(
        item["command"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return ValidationRun(
        name=str(item["name"]),
        description=str(item["description"]),
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def validate_all() -> dict[str, Any]:
    runs = [_run_command(item) for item in VALIDATION_COMMANDS]
    failed = [run for run in runs if not run.passed]

    return {
        "status": "PASS" if not failed else "FAIL",
        "n_validation_commands": len(runs),
        "n_failed_validation_commands": len(failed),
        "real_api_calls": 0,
        "raw_response_inspection": False,
        "runs": [run.to_json_safe() for run in runs],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run all committed-output Pilot 03 validators. "
            "This command makes no real API calls and does not inspect raw responses."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable validation output.",
    )
    args = parser.parse_args()

    result = validate_all()

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("Pilot 03 master committed-output validation")
        print("===========================================")
        print(f"status: {result['status']}")
        print(f"n_validation_commands: {result['n_validation_commands']}")
        print(f"n_failed_validation_commands: {result['n_failed_validation_commands']}")
        print(f"real_api_calls: {result['real_api_calls']}")
        print(f"raw_response_inspection: {result['raw_response_inspection']}")
        print("")

        for run in result["runs"]:
            status = "PASS" if run["passed"] else "FAIL"
            print(f"- {run['name']}: {status}")
            print(f"  {run['description']}")

            if not run["passed"]:
                print("  stdout_tail:")
                for line in run["stdout_tail"]:
                    print(f"    {line}")
                print("  stderr_tail:")
                for line in run["stderr_tail"]:
                    print(f"    {line}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
