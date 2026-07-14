from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TASK_ID = "05BH"
VERSION = "05BH-FINAL-LEGEND-REPAIR-V1"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "120f05840f90e05c9b7101e50ff68f9fbde588e3"
EXPECTED_HEAD_MESSAGE = "Add Pilot 05 final figure repair"

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_REL = "experiments/pilot_05_final_legend_layout_repair.py"
VALIDATOR_REL = "experiments/pilot_05_final_submission_gate_validator.py"

OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_final_submission_gate"
FIGURE_PATH = OUTPUT_DIR / "pilot_05BH_final_figure_01.png"
MANUSCRIPT_PATH = OUTPUT_DIR / "pilot_05BH_final_manuscript.md"
TRACEABILITY_PATH = OUTPUT_DIR / "pilot_05BH_figure_layout_traceability.md"

SOURCE_DATA = (
    REPO_ROOT
    / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv"
)
SOURCE_MANUSCRIPT = (
    REPO_ROOT
    / "reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md"
)
SOURCE_05BG_MANIFEST = (
    REPO_ROOT
    / "reports/pilot_05_final_figure_revalidation/pilot_05BG_manifest.json"
)

OLD_FIGURE_PATH = "pilot_05BF_figure_01_parser_vs_esr_divergence.png"
NEW_FIGURE_PATH = "pilot_05BH_final_figure_01.png"

FIGURE_WIDTH_INCHES = 16
FIGURE_HEIGHT_INCHES = 10
FIGURE_DPI = 200
AXES_LEFT = 0.29
AXES_RIGHT = 0.97
AXES_BOTTOM = 0.12
AXES_TOP = 0.84
LEGEND_ANCHOR_X = 0.5
LEGEND_ANCHOR_Y = 0.975
LEGEND_LOCATION = "upper center"
LEGEND_NCOL = 2
TITLE_Y = 0.915
X_LIMIT_LOW = -0.72
X_LIMIT_HIGH = 0.65
Y_OFFSET = 0.13

CONDITIONS = ["compressed_lossy", "partial_dropout", "noisy_conflicting"]
STAGES = ["decision", "audit", "escalation"]
METRICS = ["parser_valid", "stage_success"]

EXPECTED_INITIAL_UNTRACKED = sorted([
    "experiments/pilot_05_final_figure_revalidation.py",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_figure_01_integrity_register.csv",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_figure_04_integrity_register.csv",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_independent_figure_revalidation.md",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_internal_validation_report.md",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_manifest.json",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_manuscript_binding_integrity_report.md",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_submission_readiness_verdict.md",
    SCRIPT_REL,
    VALIDATOR_REL,
])

EXPECTED_SOURCE_SHA256 = {
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv":
        "BE397FF00A2EBABD96A6FC55941B00F92D8EC0826FA4769E502490EA3B8AF7C2",
    "reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md":
        "A6C3CD10B2C6A17D9687221FE44CC50D5691C82FF84987B096BBC578B2E4ECA0",
    "reports/pilot_05_final_figure_revalidation/pilot_05BG_manifest.json":
        "90018C1E65A051FAB8F569D5B09342401D465BCFC0BA5DFE69A753E822481BD5",
}


class ContractError(RuntimeError):
    pass


def run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def verify_starting_state() -> None:
    if run_git(["branch", "--show-current"]) != EXPECTED_BRANCH:
        raise ContractError("Expected branch main.")
    if run_git(["rev-parse", "HEAD"]) != EXPECTED_HEAD:
        raise ContractError("Unexpected HEAD before 05BH repair.")
    if run_git(["log", "-1", "--format=%s"]) != EXPECTED_HEAD_MESSAGE:
        raise ContractError("Unexpected HEAD message before 05BH repair.")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked modifications are not allowed before 05BH repair.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Staged files are not allowed before 05BH repair.")

    untracked = sorted(
        line.replace("\\", "/")
        for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    if untracked != EXPECTED_INITIAL_UNTRACKED:
        raise ContractError(
            f"Expected exactly the eight 05BG files and two 05BH scripts, got: {untracked}"
        )
    if OUTPUT_DIR.exists():
        raise ContractError("05BH output directory already exists.")

    local_origin = run_git(["rev-parse", "refs/remotes/origin/main"])
    remote_rows = run_git(
        ["ls-remote", "--heads", "origin", "refs/heads/main"]
    ).splitlines()
    if len(remote_rows) != 1:
        raise ContractError("Expected exactly one remote origin/main row.")
    remote_head = remote_rows[0].split()[0]
    if local_origin != EXPECTED_HEAD or remote_head != EXPECTED_HEAD:
        raise ContractError("Local or remote origin/main is not at the secured 05BF checkpoint.")


def verify_sources() -> list[dict[str, str]]:
    for relative_path, expected_hash in EXPECTED_SOURCE_SHA256.items():
        path = REPO_ROOT / relative_path
        if not path.is_file():
            raise ContractError(f"Required source is missing: {relative_path}")
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            raise ContractError(
                f"SHA-256 mismatch for {relative_path}: {actual_hash}"
            )

    manifest = json.loads(SOURCE_05BG_MANIFEST.read_text(encoding="utf-8"))
    if manifest["status"] != "PASS":
        raise ContractError("05BG revalidation execution did not pass.")
    if manifest["verdict"]["figure_01_data_integrity"] != "PASS":
        raise ContractError("05BG Figure 1 data integrity did not pass.")
    if manifest["verdict"]["figure_01_visual_readability"] != "ACTION_REQUIRED":
        raise ContractError("05BG does not preserve the legend-layout action.")
    findings = {item["finding_id"]: item for item in manifest["findings"]}
    if findings.get("FIG-L01", {}).get("status") != "OPEN":
        raise ContractError("05BG finding FIG-L01 is not open.")

    rows = read_csv(SOURCE_DATA)
    if len(rows) != 18:
        raise ContractError("Expected exactly 18 Figure 1 source rows.")

    keys = {
        (row["evidence_condition"], row["stage"], row["metric"])
        for row in rows
    }
    expected_keys = {
        (condition, stage, metric)
        for condition in CONDITIONS
        for stage in STAGES
        for metric in METRICS
    }
    if keys != expected_keys:
        raise ContractError("Figure 1 source key set mismatch.")

    parser_rows = [row for row in rows if row["metric"] == "parser_valid"]
    success_rows = [row for row in rows if row["metric"] == "stage_success"]
    if len(parser_rows) != 9 or len(success_rows) != 9:
        raise ContractError("Figure 1 metric row counts must be 9 and 9.")
    if not all(float(row["mean_delta_degraded_minus_clean"]) > 0 for row in parser_rows):
        raise ContractError("All parser-validity means must remain positive.")
    parser_crossing = [
        row for row in parser_rows
        if float(row["ci_95_low"]) <= 0 <= float(row["ci_95_high"])
    ]
    if len(parser_crossing) != 3 or {
        row["evidence_condition"] for row in parser_crossing
    } != {"partial_dropout"}:
        raise ContractError("Expected three partial-dropout parser intervals crossing zero.")
    if not all(float(row["ci_95_high"]) < 0 for row in success_rows):
        raise ContractError("All stage-success intervals must remain below zero.")

    return rows


def ordered_rows(rows: list[dict[str, str]], metric: str) -> list[dict[str, str]]:
    by_key = {
        (row["evidence_condition"], row["stage"], row["metric"]): row
        for row in rows
    }
    return [
        by_key[(condition, stage, metric)]
        for condition in CONDITIONS
        for stage in STAGES
    ]


def render_figure(rows: list[dict[str, str]], output_path: Path) -> None:
    labels = [
        f"{condition.replace('_', ' ').title()} — {stage.title()}"
        for condition in CONDITIONS
        for stage in STAGES
    ]
    y = np.arange(len(labels))

    figure, axes = plt.subplots(
        figsize=(FIGURE_WIDTH_INCHES, FIGURE_HEIGHT_INCHES),
        dpi=FIGURE_DPI,
    )
    figure.subplots_adjust(
        left=AXES_LEFT,
        right=AXES_RIGHT,
        bottom=AXES_BOTTOM,
        top=AXES_TOP,
    )

    handles = []
    series = [
        ("parser_valid", -Y_OFFSET, "o", "Parser validity"),
        ("stage_success", Y_OFFSET, "s", "Stage success"),
    ]
    for metric, offset, marker, label in series:
        metric_rows = ordered_rows(rows, metric)
        means = np.array([
            float(row["mean_delta_degraded_minus_clean"])
            for row in metric_rows
        ])
        lows = np.array([float(row["ci_95_low"]) for row in metric_rows])
        highs = np.array([float(row["ci_95_high"]) for row in metric_rows])
        asymmetric_errors = np.vstack([means - lows, highs - means])

        handle = axes.errorbar(
            means,
            y + offset,
            xerr=asymmetric_errors,
            fmt=marker,
            linestyle="none",
            capsize=5,
            markersize=7,
            label=label,
        )
        handles.append(handle)

    axes.axvline(0, linestyle="--", linewidth=1)
    axes.set_yticks(y)
    axes.set_yticklabels(labels)
    axes.invert_yaxis()
    axes.set_xlim(X_LIMIT_LOW, X_LIMIT_HIGH)
    axes.set_xlabel(
        "Paired degraded-minus-clean delta "
        "(mean with 95% bootstrap interval)"
    )
    axes.grid(axis="x", alpha=0.25)

    figure.legend(
        handles=handles,
        labels=["Parser validity", "Stage success"],
        loc=LEGEND_LOCATION,
        bbox_to_anchor=(LEGEND_ANCHOR_X, LEGEND_ANCHOR_Y),
        ncol=LEGEND_NCOL,
        frameon=False,
    )
    figure.suptitle(
        "Parser-validity and stage-success divergence under "
        "controlled evidence degradation",
        y=TITLE_Y,
        fontsize=16,
    )
    figure.savefig(
        output_path,
        metadata={
            "Creator": "Task 05BH",
            "Description": (
                "Legend outside axes; exact 18-row 05AP bootstrap contract"
            ),
        },
    )
    plt.close(figure)


def build_final_manuscript() -> str:
    source = SOURCE_MANUSCRIPT.read_text(encoding="utf-8")
    if source.count(OLD_FIGURE_PATH) != 1:
        raise ContractError("Expected exactly one 05BF Figure 1 path in the manuscript.")
    if NEW_FIGURE_PATH in source:
        raise ContractError("05BH final Figure 1 path already appears in the source manuscript.")

    final_text = source.replace(OLD_FIGURE_PATH, NEW_FIGURE_PATH, 1)
    restored = final_text.replace(NEW_FIGURE_PATH, OLD_FIGURE_PATH, 1)
    if restored != source:
        raise ContractError("The Figure 1 path replacement is not reversible.")

    return final_text


def build_traceability(rows: list[dict[str, str]]) -> str:
    return f"""# Task 05BH Final Figure Layout Traceability

## Closed finding

- Finding: `FIG-L01`
- Prior state: OPEN layout blocker for submission
- Repair: Figure 1 legend moved completely outside the plotting axes
- Scientific data changed: NO
- Caption changed: NO
- Numerical prose changed: NO

## Authoritative data contract

- Source: `{rel(SOURCE_DATA)}`
- Source rows: {len(rows)}/18
- Parser-validity rows: 9/9
- Stage-success rows: 9/9
- Parser-validity intervals crossing zero: 3/9, partial-dropout only
- Stage-success intervals below zero: 9/9
- Bootstrap resamples: 2,000
- Random seed: 5205

## Export layout contract

- Canvas: {FIGURE_WIDTH_INCHES * FIGURE_DPI} × {FIGURE_HEIGHT_INCHES * FIGURE_DPI} pixels
- Axes top: {AXES_TOP}
- Legend anchor: ({LEGEND_ANCHOR_X}, {LEGEND_ANCHOR_Y})
- Legend location: `{LEGEND_LOCATION}`
- Legend columns: {LEGEND_NCOL}
- Minimum normalized vertical separation between axes top and legend anchor: {LEGEND_ANCHOR_Y - AXES_TOP:.3f}
- Legend created with `figure.legend`, not `axes.legend`
- Legend overlaps plotting axes: NO

## Manuscript binding

- Source manuscript: `{rel(SOURCE_MANUSCRIPT)}`
- Final manuscript: `{rel(MANUSCRIPT_PATH)}`
- Approved manuscript differences relative to 05BF: 1
- Difference: Figure 1 asset path only
- Reverse restoration to byte-identical 05BF manuscript: YES

The final export remains subject to the separate 05BH submission-gate validator.
"""


def main() -> None:
    verify_starting_state()
    rows = verify_sources()

    OUTPUT_DIR.mkdir(parents=False, exist_ok=False)
    render_figure(rows, FIGURE_PATH)
    write_text(MANUSCRIPT_PATH, build_final_manuscript())
    write_text(TRACEABILITY_PATH, build_traceability(rows))

    if sha256_file(SOURCE_DATA) != EXPECTED_SOURCE_SHA256[rel(SOURCE_DATA)]:
        raise ContractError("Source data changed during repair.")
    if run_git(["rev-parse", "HEAD"]) != EXPECTED_HEAD:
        raise ContractError("HEAD changed during repair.")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked files changed during repair.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Files were staged during repair.")

    print("=== TASK 05BH LEGEND REPAIR RESULT ===")
    print("status: PASS")
    print(f"version: {VERSION}")
    print(f"source_HEAD: {EXPECTED_HEAD}")
    print("figure_01_authoritative_rows: 18/18")
    print("legend_location: OUTSIDE_PLOTTING_AXES")
    print(f"axes_top: {AXES_TOP}")
    print(f"legend_anchor_y: {LEGEND_ANCHOR_Y}")
    print("manuscript_changes_relative_to_05BF: 1")
    print("manuscript_change_scope: FIGURE_1_ASSET_PATH_ONLY")
    print(f"final_figure_sha256: {sha256_file(FIGURE_PATH)}")
    print(f"final_manuscript_sha256: {sha256_file(MANUSCRIPT_PATH)}")
    print(f"traceability_sha256: {sha256_file(TRACEABILITY_PATH)}")
    print("STOP: The independent 05BH submission-gate validator must run next.")


if __name__ == "__main__":
    main()
